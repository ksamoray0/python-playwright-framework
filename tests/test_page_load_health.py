import re
import pytest
from playwright.sync_api import Page

from utils.page_load_validator import PageLoadValidator, PageLoadOptions

ROUTES = [
    ("home", "/"),
]

VIEWPORTS = [
    ("desktop-1280", {"width": 1280, "height": 720}),
    ("mobile-390", {"width": 390, "height": 844}),
]


@pytest.mark.parametrize("route_name, path", ROUTES)
@pytest.mark.parametrize("vp_name, vp", VIEWPORTS)
def test_page_load_health(
    page: Page, base_url: str, route_name: str, path: str, vp_name: str, vp: dict
) -> None:
    page.set_viewport_size(vp)

    url = f"{base_url.rstrip('/')}{path}"

    validator = PageLoadValidator(
        page,
        console_error_allowlist=[
            # Add known/acceptable console errors here if needed
        ],
        request_failure_allowlist=[
            # Optional: allow common third-party noise if it appears
            # re.compile(r"google-analytics|analytics|segment|datadog", re.I),
            # re.compile(r"fonts\.gstatic\.com|fonts\.googleapis\.com", re.I),
        ],
        response_status_allowlist=[
            # Optional: allow known endpoints to return specific codes
            # (re.compile(r"/some-endpoint$"), {404}),
        ],
    )

    options = PageLoadOptions(
        url=url,
        wait_until="domcontentloaded",
        timeout_ms=45_000,
        js={
            "fail_on_console_errors": True,
            "fail_on_page_errors": True,
            "fail_on_unhandled_rejections": True,
        },
        network={
            "fail_on_request_failures": True,
            "fail_on_4xx5xx_responses": False,
        },
        metadata={
            # Light check: title exists and is non-trivial
            "title_regex": re.compile(r".{3,}"),
            # Turn on once you confirm favicon is consistently present/accessible
            "require_favicon": False,
        },
        security={
            # This site is HTTPS; enforce it
            "require_https": True,
        },
        visual={
            # Enable later when stable and you want baseline snapshots
            "enabled": False,
            "name": f"{route_name}-{vp_name}",
            "full_page": True,
        },
    )

    result = validator.validate_load(options)
    assert result["ok"], result["summary"]
