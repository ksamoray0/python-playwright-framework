import pytest


@pytest.mark.smoke
def test_playwright_smoke(page):
    page.goto("https://example.com")
    assert page.title() == "Example Domain"
