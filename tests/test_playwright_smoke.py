import pytest


@pytest.mark.smoke
def test_playwright_smoke(page):
    page.goto("https://automationintesting.online/")
    assert page.title() == "Restful-booker-platform demo"
