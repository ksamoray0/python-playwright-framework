from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern, Tuple, Set

from playwright.sync_api import (
    Page,
    ConsoleMessage,
    Request,
    Response,
    Error as PWError,
    expect,
)


WaitUntil = str  # "load" | "domcontentloaded" | "networkidle" | "commit"


@dataclass
class PageLoadOptions:
    url: str
    wait_until: WaitUntil = "domcontentloaded"
    timeout_ms: int = 45_000

    js: Optional[Dict[str, Any]] = None
    network: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    security: Optional[Dict[str, Any]] = None
    visual: Optional[Dict[str, Any]] = None


class PageLoadValidator:
    def __init__(
        self,
        page: Page,
        console_error_allowlist: Optional[List[Pattern[str]]] = None,
        request_failure_allowlist: Optional[List[Pattern[str]]] = None,
        response_status_allowlist: Optional[List[Tuple[Pattern[str], Set[int]]]] = None,
    ) -> None:
        self.page = page
        self.console_error_allowlist = console_error_allowlist or []
        self.request_failure_allowlist = request_failure_allowlist or []
        self.response_status_allowlist = response_status_allowlist or []

        self._console_errors: List[Dict[str, Any]] = []
        self._page_errors: List[str] = []
        self._request_failures: List[Dict[str, Any]] = []
        self._bad_responses: List[Dict[str, Any]] = []

        # In Playwright Python there is no `page.off(...)`.
        # We bind listeners once per validator instance and rely on the test runner
        # creating/closing pages between tests.
        self._listeners_bound = False

    def validate_load(self, options: PageLoadOptions) -> Dict[str, Any]:
        started = time.time()

        self._reset()
        self._bind_listeners()

        js_cfg = options.js or {}
        net_cfg = options.network or {}
        meta_cfg = options.metadata or {}
        sec_cfg = options.security or {}
        vis_cfg = options.visual or {}

        main_response: Optional[Response] = None
        final_url: Optional[str] = None

        main_response = self.page.goto(
            options.url,
            wait_until=options.wait_until,
            timeout=options.timeout_ms,
        )
        final_url = self.page.url

        # Micro wait to capture late console/network noise right after load
        self.page.wait_for_timeout(250)

        try:
            title = self.page.title()
        except Exception:
            title = None

        favicon_href, favicon_ok = self._check_favicon(meta_cfg)

        is_https = (self.page.url or "").lower().startswith("https://")

        # Optional visual baseline (Playwright snapshot comparison)
        if vis_cfg.get("enabled"):
            self._run_visual_snapshot(vis_cfg)

        nav_ms = int((time.time() - started) * 1000)
        status = main_response.status if main_response else None

        unhandled = []
        if js_cfg.get("fail_on_unhandled_rejections", True):
            unhandled = self._get_unhandled_rejections()

        result: Dict[str, Any] = {
            "ok": True,
            "url": options.url,
            "final_url": final_url,
            "status": status,
            "summary": "",
            "timings": {"navigation_ms": nav_ms},
            "js": {
                "console_errors": list(self._console_errors),
                "page_errors": list(self._page_errors),
                "unhandled_rejections": unhandled,
            },
            "network": {
                "request_failures": list(self._request_failures),
                "bad_responses": list(self._bad_responses),
            },
            "metadata": {
                "title": title,
                "favicon_href": favicon_href,
                "favicon_ok": favicon_ok,
            },
            "security": {
                "is_https": is_https,
            },
        }

        failures: List[str] = []

        # Navigation sanity
        if main_response is None:
            failures.append("No main document response from goto()")
        if isinstance(status, int) and status >= 400:
            failures.append(f"Main document returned HTTP {status}")

        # JS gates
        if (
            js_cfg.get("fail_on_console_errors", True)
            and len(result["js"]["console_errors"]) > 0
        ):
            failures.append(f"Console errors: {len(result['js']['console_errors'])}")
        if (
            js_cfg.get("fail_on_page_errors", True)
            and len(result["js"]["page_errors"]) > 0
        ):
            failures.append(f"Page errors: {len(result['js']['page_errors'])}")
        if (
            js_cfg.get("fail_on_unhandled_rejections", True)
            and len(result["js"]["unhandled_rejections"]) > 0
        ):
            failures.append(
                f"Unhandled rejections: {len(result['js']['unhandled_rejections'])}"
            )

        # Network gates
        if (
            net_cfg.get("fail_on_request_failures", True)
            and len(result["network"]["request_failures"]) > 0
        ):
            failures.append(
                f"Request failures: {len(result['network']['request_failures'])}"
            )

        if (
            net_cfg.get("fail_on_4xx5xx_responses", False)
            and len(result["network"]["bad_responses"]) > 0
        ):
            failures.append(f"Bad responses: {len(result['network']['bad_responses'])}")

        # Metadata gates
        title_exact = meta_cfg.get("title_exact")
        title_regex = meta_cfg.get("title_regex")

        if title_exact and title != title_exact:
            failures.append(
                f'Title mismatch. Expected "{title_exact}", got "{title or ""}"'
            )

        if title_regex and (not title or not title_regex.search(title)):
            failures.append(f"Title did not match regex {title_regex.pattern}")

        if meta_cfg.get("require_favicon") and favicon_ok is False:
            failures.append("Favicon request failed")

        # Security gates
        if sec_cfg.get("require_https") and not is_https:
            failures.append(f'Expected HTTPS but final URL was "{self.page.url}"')

        result["ok"] = len(failures) == 0
        result["summary"] = (
            f"OK: loaded in {nav_ms}ms (status {status})"
            if result["ok"]
            else "FAIL: " + " | ".join(failures)
        )

        return result

    def _reset(self) -> None:
        self._console_errors = []
        self._page_errors = []
        self._request_failures = []
        self._bad_responses = []

    def _bind_listeners(self) -> None:
        if self._listeners_bound:
            return
        self._listeners_bound = True

        self.page.on("console", self._on_console)
        self.page.on("pageerror", self._on_page_error)
        self.page.on("requestfailed", self._on_request_failed)
        self.page.on("response", self._on_response)

        # Capture unhandled promise rejections inside the page
        self.page.add_init_script(
            """
            (() => {
              window.__pwUnhandledRejections = [];
              window.addEventListener('unhandledrejection', (event) => {
                const r = event && event.reason;
                const text = (typeof r === 'string')
                  ? r
                  : (r && r.message) ? r.message : JSON.stringify(r);
                window.__pwUnhandledRejections.push(String(text));
              });
            })();
            """
        )

    def _is_allowlisted(self, text: str, allowlist: List[Pattern[str]]) -> bool:
        return any(r.search(text) for r in allowlist)

    def _on_console(self, msg: ConsoleMessage) -> None:
        # Playwright Python: type/text/location are methods
        if msg.type() != "error":
            return

        text = msg.text() or ""
        if self._is_allowlisted(text, self.console_error_allowlist):
            return

        loc = msg.location() or {}
        location = None
        if loc.get("url"):
            location = f"{loc.get('url')}:{loc.get('lineNumber', '')}:{loc.get('columnNumber', '')}"

        self._console_errors.append(
            {"type": msg.type(), "text": text, "location": location}
        )

    def _on_page_error(self, error: PWError) -> None:
        text = getattr(error, "message", None) or str(error)
        if self._is_allowlisted(text, self.console_error_allowlist):
            return
        self._page_errors.append(text)

    def _on_request_failed(self, request: Request) -> None:
        url = request.url
        if self._is_allowlisted(url, self.request_failure_allowlist):
            return

        failure = request.failure()
        self._request_failures.append(
            {
                "url": url,
                "method": request.method,
                "resource_type": request.resource_type,
                "error_text": failure.get("errorText") if failure else None,
            }
        )

    def _on_response(self, response: Response) -> None:
        status = response.status
        if status < 400:
            return

        url = response.url

        for rule_url, allowed_statuses in self.response_status_allowlist:
            if rule_url.search(url) and status in allowed_statuses:
                return

        self._bad_responses.append({"url": url, "status": status})

    def _get_unhandled_rejections(self) -> List[str]:
        try:
            data = self.page.evaluate("() => window.__pwUnhandledRejections || []")
            if isinstance(data, list):
                return [str(x) for x in data]
            return []
        except Exception:
            return []

    def _check_favicon(
        self, meta_cfg: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[bool]]:
        if not meta_cfg.get("require_favicon"):
            return None, None

        try:
            favicon_href = self.page.evaluate(
                """() => {
                  const el = document.querySelector('link[rel~="icon"]');
                  return el ? el.href : null;
                }"""
            )
        except Exception:
            return None, False

        if not favicon_href:
            return None, False

        try:
            res = self.page.request.get(str(favicon_href), timeout=15_000)
            return str(favicon_href), res.ok
        except Exception:
            return str(favicon_href), False

    def _run_visual_snapshot(self, vis_cfg: Dict[str, Any]) -> None:
        name = vis_cfg["name"]
        full_page = bool(vis_cfg.get("full_page", True))
        mask_selectors = vis_cfg.get("mask_selectors", [])

        mask = (
            [self.page.locator(sel) for sel in mask_selectors]
            if mask_selectors
            else None
        )

        expect(self.page).to_have_screenshot(
            f"{name}.png",
            full_page=full_page,
            mask=mask,
        )
