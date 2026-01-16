import os
import sys
import pytest
import allure
from typing import Generator, Optional
from pathlib import Path
from loguru import logger
from faker import Faker
from playwright.sync_api import expect

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def browser_factory(test_config: Settings, cli_browser_overrides: dict) -> Generator[BrowserFactory, None, None]:
    """
    Create and manage BrowserFactory for the test session.
    
    The factory handles:
    - Configuration from core_config.yml
    - Environment variable overrides (for Jenkins/CI)
    - CLI parameter overrides
    
    Yields:
        BrowserFactory instance
    """
    # Get browser config as dict
    browser_config = {
        "type": test_config.core.browser.type,
        "headless": test_config.core.browser.headless,
        "slow_mo": test_config.core.browser.slow_mo,
        "timeout": getattr(test_config.core.browser, "timeout", 30000),
        "viewport": {
            "width": test_config.core.browser.viewport_width,
            "height": test_config.core.browser.viewport_height,
        },
        "screenshot_on_failure": test_config.core.browser.screenshot_on_failure,
        "video_on_failure": test_config.core.browser.video_on_failure,
        "trace_on_failure": test_config.core.browser.trace_on_failure,
    }
    
    factory = BrowserFactory(browser_config, cli_browser_overrides)
    
    yield factory
    
    factory.close()


@pytest.fixture(scope="session")
def browser(browser_factory: BrowserFactory):
    return browser_factory.launch_browser()


@pytest.fixture
def context(browser_factory: BrowserFactory, browser):
    """
    Create browser context using the BrowserFactory.
    
    This enables tracing and video recording based on configuration.
    """
    context = browser_factory.create_context(browser)
    yield context
    browser_factory.close_context(context)


@pytest.fixture
def page(browser_factory: BrowserFactory, context):
    """
    Create page using the BrowserFactory.
    
    This sets proper timeouts based on configuration.
    """
    page = browser_factory.create_page(context)
    yield page
    browser_factory.close_page(page)


@pytest.fixture
def ui_actions(page) -> PlaywrightUIActions:
    """
    Get UI actions adapter wrapping the Playwright page.
    
    This fixture depends on pytest-playwright's 'page' fixture.
    """
    return PlaywrightUIActions(page)