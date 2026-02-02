import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

try:
    import pytest_html
except Exception:
    pytest_html = None


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def pytest_addoption(parser: pytest.Parser) -> None:
    # Do NOT define --browser/--headed/--slowmo here.
    # pytest-playwright already defines those, and adding them causes argparse conflicts.
    #
    # Keep only truly custom options.
    parser.addoption(
        "--pw-trace",
        action="store_true",
        default=False,
        help="Enable Playwright tracing (also enabled via PW_TRACE=1 env var)",
    )


@pytest.fixture(scope="session")
def artifacts_dir() -> Path:
    # Always resolve artifacts relative to repo root, not the current working directory
    root = Path(__file__).resolve().parents[1]
    path = root / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def base_url() -> str:
    # Default base URL for this project
    return os.getenv("BASE_URL", "https://automationintesting.online")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

    # Only attach links after teardown (artifact files exist then)
    if rep.when != "teardown":
        return

    # Only for failed tests
    if not hasattr(item, "rep_call") or not item.rep_call.failed:
        return

    artifacts = getattr(item, "_artifacts", None)
    if not artifacts:
        return

    if pytest_html is None:
        return

    extra = getattr(rep, "extra", [])

    screenshot_path = artifacts.get("screenshot")
    if screenshot_path and Path(screenshot_path).exists():
        rel = f"../artifacts/screenshots/{Path(screenshot_path).name}"
        extra.append(pytest_html.extras.url(rel, name="Screenshot"))

    trace_path = artifacts.get("trace")
    if trace_path and Path(trace_path).exists():
        rel = f"../artifacts/traces/{Path(trace_path).name}"
        extra.append(pytest_html.extras.url(rel, name="Trace (.zip)"))

    rep.extra = extra


@pytest.fixture(scope="function", autouse=True)
def capture_artifacts_on_failure(
    request: pytest.FixtureRequest, page, artifacts_dir: Path
):
    # Enable trace if either:
    # - env var PW_TRACE is truthy, OR
    # - user passes --pw-trace
    trace_enabled = _bool_env("PW_TRACE", default=False) or bool(
        request.config.getoption("--pw-trace")
    )

    # Start tracing when enabled, but only SAVE it on failure
    if trace_enabled:
        try:
            page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        except Exception:
            trace_enabled = False

    yield

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if not failed:
        # Stop tracing without saving on pass
        if trace_enabled:
            try:
                page.context.tracing.stop()
            except Exception:
                pass
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    test_id = _safe_nodeid(request.node.nodeid)

    screenshots_dir = artifacts_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    screenshot_file: Optional[Path] = screenshots_dir / f"{test_id}_{timestamp}.png"
    try:
        page.screenshot(path=str(screenshot_file), full_page=True)
    except Exception:
        screenshot_file = None

    trace_path: Optional[Path] = None
    if trace_enabled:
        trace_path = artifacts_dir / "traces" / f"{test_id}.zip"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.context.tracing.stop(path=str(trace_path))
        except Exception:
            trace_path = None

    artifacts = getattr(request.node, "_artifacts", {})
    if screenshot_file is not None:
        artifacts["screenshot"] = str(screenshot_file)
    if trace_path is not None:
        artifacts["trace"] = str(trace_path)
    setattr(request.node, "_artifacts", artifacts)


def _safe_nodeid(nodeid: str) -> str:
    return (
        nodeid.replace("::", "__")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace("[", "_")
        .replace("]", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace(":", "_")
    )
