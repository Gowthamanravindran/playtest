"""
Global pytest configuration and fixtures.

This file contains fixtures and hooks that are available to all tests.

CLI Options:
    --browser-type      Browser to use (chromium, firefox, webkit)
    --headed            Run browser in headed mode
    --slow-mo           Slow down browser operations by ms
    --core-config       Path to core_config.yml
    --data-config       Path to data_config.yml
"""
import os
import sys
import pytest
import allure
from typing import Generator, Optional
from pathlib import Path
from loguru import logger
from faker import Faker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from configs import Settings, get_settings
from adapters.ui import PlaywrightUIActions, BrowserFactory
from adapters.mobile import AppiumMobileActions, MobileFactory
from adapters.api import RequestsAPIActions
from api import APIClient


# ---------------------------------------------------------------------------
# Pytest CLI Options
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    """Add custom command line options for test configuration."""
    # Browser options
    parser.addoption(
        "--browser-type",
        action="store",
        default=None,
        choices=["chromium", "firefox", "webkit"],
        help="Browser to use for UI tests (default: from config)",
    )
    parser.addoption(
        "--slow-mo",
        action="store",
        type=int,
        default=None,
        help="Slow down browser operations by specified milliseconds",
    )
    
    # Mobile options
    parser.addoption(
        "--mobile-platform",
        action="store",
        default=None,
        choices=["android", "ios"],
        help="Mobile platform to use (default: from config)",
    )
    parser.addoption(
        "--device-name",
        action="store",
        default=None,
        help="Mobile device name or emulator/simulator name",
    )
    parser.addoption(
        "--app-path",
        action="store",
        default=None,
        help="Path to mobile app (APK/IPA)",
    )
    parser.addoption(
        "--udid",
        action="store",
        default=None,
        help="Device UDID for real device testing",
    )
    parser.addoption(
        "--no-reset",
        action="store_true",
        default=False,
        help="Don't reset app state before test",
    )
    
    # Config file options
    parser.addoption(
        "--core-config",
        action="store",
        default=None,
        help="Path to core configuration YAML file",
    )
    parser.addoption(
        "--data-config",
        action="store",
        default=None,
        help="Path to data configuration YAML file",
    )


# ---------------------------------------------------------------------------
# Configuration Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_config(request) -> Settings:
    """
    Get test configuration settings from core_config.yml and data_config.yml.
    
    Config file priority:
    1. CLI options (--core-config, --data-config)
    2. Environment variables (CORE_CONFIG_PATH, DATA_CONFIG_PATH)
    3. Default locations (configs/core_config.yml, configs/data_config.yml)
    """
    # Check CLI options first
    core_config_path = request.config.getoption("--core-config")
    data_config_path = request.config.getoption("--data-config")
    
    # Fall back to environment variables
    if not core_config_path:
        core_config_path = os.environ.get("CORE_CONFIG_PATH")
    if not data_config_path:
        data_config_path = os.environ.get("DATA_CONFIG_PATH")
    
    return get_settings(
        core_config_path=core_config_path,
        data_config_path=data_config_path,
    )


@pytest.fixture(scope="session")
def cli_browser_overrides(request) -> dict:
    """
    Get browser configuration overrides from CLI options.
    
    Returns:
        Dictionary of CLI overrides for browser configuration
    """
    overrides = {}
    
    browser_type = request.config.getoption("--browser-type")
    if browser_type:
        overrides["browser_type"] = browser_type
    
    if request.config.getoption("--headed"):
        overrides["headed"] = True
    
    slow_mo = request.config.getoption("--slow-mo")
    if slow_mo is not None:
        overrides["slow_mo"] = slow_mo
    
    return overrides


@pytest.fixture(scope="session")
def cli_mobile_overrides(request) -> dict:
    """
    Get mobile configuration overrides from CLI options.
    
    Returns:
        Dictionary of CLI overrides for mobile configuration
    """
    overrides = {}
    
    platform = request.config.getoption("--mobile-platform")
    if platform:
        overrides["platform"] = platform
    
    device_name = request.config.getoption("--device-name")
    if device_name:
        overrides["device_name"] = device_name
    
    app_path = request.config.getoption("--app-path")
    if app_path:
        overrides["app_path"] = app_path
    
    udid = request.config.getoption("--udid")
    if udid:
        overrides["udid"] = udid
    
    if request.config.getoption("--no-reset"):
        overrides["no_reset"] = True
    
    return overrides


@pytest.fixture(scope="session")
def faker() -> Faker:
    """Get Faker instance for generating test data."""
    return Faker()


# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------

def configure_logging(settings: Settings) -> None:
    """Configure loguru logging."""
    logger.remove()  # Remove default handler
    
    logging_config = settings.core.logging
    
    # Console handler
    logger.add(
        sys.stderr,
        format=logging_config.format,
        level=logging_config.level,
        colorize=True,
    )
    
    # File handler
    if logging_config.file_path:
        log_path = Path(logging_config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            logging_config.file_path,
            format=logging_config.format,
            level=logging_config.level,
            rotation=logging_config.rotation,
            retention=logging_config.retention,
        )


# ---------------------------------------------------------------------------
# Playwright UI Fixtures (using BrowserFactory)
# ---------------------------------------------------------------------------

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
    """
    Launch browser using the BrowserFactory.
    
    This overrides pytest-playwright's browser fixture to use our factory.
    """
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


# ---------------------------------------------------------------------------
# Appium Mobile Fixtures (using MobileFactory)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mobile_factory(
    test_config: Settings,
    cli_mobile_overrides: dict,
) -> Generator[MobileFactory, None, None]:
    """
    Create and manage MobileFactory for the test session.
    
    The factory handles:
    - Configuration from core_config.yml and data_config.yml
    - Environment variable overrides (for Jenkins/CI)
    - CLI parameter overrides
    
    Yields:
        MobileFactory instance
    """
    # Get core config as dict
    core_config = {
        "mobile": {
            "appium_server": test_config.core.mobile.appium_server,
            "automation_name": test_config.core.mobile.automation_name,
            "new_command_timeout": test_config.core.mobile.new_command_timeout,
            "no_reset": test_config.core.mobile.no_reset,
            "full_reset": test_config.core.mobile.full_reset,
        },
        "browser": {
            "screenshot_on_failure": test_config.core.browser.screenshot_on_failure,
        },
    }
    
    # Get data config as dict
    data_config = {
        "mobile_app": {
            "android": {
                "platform": test_config.data.mobile_app.android.platform,
                "device_name": test_config.data.mobile_app.android.device_name,
                "platform_version": test_config.data.mobile_app.android.platform_version,
                "app_path": test_config.data.mobile_app.android.app_path,
                "app_package": test_config.data.mobile_app.android.app_package,
                "app_activity": test_config.data.mobile_app.android.app_activity,
            },
            "ios": {
                "platform": test_config.data.mobile_app.ios.platform,
                "device_name": test_config.data.mobile_app.ios.device_name,
                "platform_version": test_config.data.mobile_app.ios.platform_version,
                "app_path": test_config.data.mobile_app.ios.app_path,
                "bundle_id": test_config.data.mobile_app.ios.bundle_id,
                "udid": test_config.data.mobile_app.ios.udid,
            },
        },
        "timeouts": {
            "implicit_wait": test_config.data.timeouts.implicit_wait,
        },
    }
    
    factory = MobileFactory(core_config, data_config, cli_mobile_overrides)
    
    yield factory
    
    factory.close()


@pytest.fixture(scope="session")
def appium_driver(mobile_factory: MobileFactory):
    """
    Create Appium driver using the MobileFactory.
    
    This uses the factory for centralized driver management.
    """
    return mobile_factory.create_driver()


@pytest.fixture
def mobile_actions(appium_driver) -> AppiumMobileActions:
    """Get mobile actions adapter wrapping the Appium driver."""
    return AppiumMobileActions(appium_driver)


# ---------------------------------------------------------------------------
# API Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_actions(test_config: Settings) -> Generator[RequestsAPIActions, None, None]:
    """Get API actions adapter."""
    api_config = test_config.data.api
    timeout = test_config.data.timeouts.api_timeout
    actions = RequestsAPIActions(api_config.base_url, timeout)
    yield actions
    actions.close()


@pytest.fixture
def api_client(test_config: Settings) -> Generator[APIClient, None, None]:
    """Get API client instance."""
    api_config = test_config.data.api
    timeout = test_config.data.timeouts.api_timeout
    client = APIClient(api_config.base_url, timeout)
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Pytest Hooks
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Configure pytest with settings from config files and CLI options."""
    # Get config paths from CLI or environment
    core_config_path = config.getoption("--core-config", default=None)
    data_config_path = config.getoption("--data-config", default=None)
    
    if not core_config_path:
        core_config_path = os.environ.get("CORE_CONFIG_PATH")
    if not data_config_path:
        data_config_path = os.environ.get("DATA_CONFIG_PATH")
    
    settings = get_settings(
        core_config_path=core_config_path,
        data_config_path=data_config_path,
    )
    configure_logging(settings)
    
    # Log configuration summary
    browser_type = config.getoption("--browser-type", default=None) or settings.core.browser.type
    headed = config.getoption("--headed", default=False)
    mobile_platform = config.getoption("--mobile-platform", default=None) or "android"
    
    logger.info(f"Test Configuration:")
    logger.info(f"  Environment: {settings.core.environment}")
    logger.info(f"  Browser: {browser_type} ({'headed' if headed else 'headless'})")
    logger.info(f"  Mobile Platform: {mobile_platform}")
    logger.info(f"  UI Base URL: {settings.data.ui.base_url}")
    logger.info(f"  API Base URL: {settings.data.api.base_url}")
    logger.info(f"  Appium Server: {settings.core.mobile.appium_server}")
    
    # Create reports directory
    allure_config = settings.core.allure
    Path(allure_config.results_dir).mkdir(parents=True, exist_ok=True)
    
    # Clean previous results if configured
    if allure_config.clean_results:
        results_path = Path(allure_config.results_dir)
        if results_path.exists():
            for file in results_path.glob("*"):
                if file.is_file():
                    file.unlink()
    
    # Register custom markers
    config.addinivalue_line("markers", "smoke: mark test as smoke test")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "ui: mark test as UI test")
    config.addinivalue_line("markers", "mobile: mark test as mobile test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Modify collected tests."""
    for item in items:
        # Auto-add markers based on test path
        if "/api/" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "/ui/" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        elif "/mobile/" in str(item.fspath):
            item.add_marker(pytest.mark.mobile)
        elif "/cross/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook for processing test results and attaching artifacts on failure."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        core_config_path = os.environ.get("CORE_CONFIG_PATH")
        data_config_path = os.environ.get("DATA_CONFIG_PATH")
        settings = get_settings(
            core_config_path=core_config_path,
            data_config_path=data_config_path,
        )
        
        test_name = item.name
        
        # Attach failure artifacts for UI tests (Playwright)
        if settings.core.browser.screenshot_on_failure and hasattr(item, "funcargs"):
            _attach_playwright_artifacts(item, test_name)
            
            # Attach failure artifacts for mobile tests (Appium)
            _attach_appium_artifacts(item, test_name)


def _attach_playwright_artifacts(item, test_name: str) -> None:
    """Attach Playwright artifacts (screenshot, page source, URL, trace) on failure."""
    page = None
    context = None
    
    # Try to get page from various fixtures
    if "page" in item.funcargs:
        page = item.funcargs["page"]
    elif "ui_actions" in item.funcargs:
        ui_actions = item.funcargs["ui_actions"]
        if hasattr(ui_actions, "page"):
            page = ui_actions.page
    
    # Try to get context for trace
    if "context" in item.funcargs:
        context = item.funcargs["context"]
    elif page and hasattr(page, "context"):
        context = page.context
    
    if page is None:
        return
    
    # 1. Attach screenshot
    try:
        screenshot = page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=f"Screenshot - {test_name}",
            attachment_type=allure.attachment_type.PNG,
        )
        logger.info(f"Attached failure screenshot for: {test_name}")
    except Exception as e:
        logger.warning(f"Failed to capture screenshot: {e}")
    
    # 2. Attach current URL
    try:
        current_url = page.url
        allure.attach(
            current_url,
            name="Page URL",
            attachment_type=allure.attachment_type.TEXT,
        )
    except Exception as e:
        logger.warning(f"Failed to capture URL: {e}")
    
    # 3. Attach page HTML source
    try:
        page_source = page.content()
        allure.attach(
            page_source,
            name="Page Source",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception as e:
        logger.warning(f"Failed to capture page source: {e}")
    
    # 4. Attach Playwright trace (if tracing was enabled)
    if context:
        try:
            import tempfile
            trace_path = tempfile.mktemp(suffix=".zip")
            context.tracing.stop(path=trace_path)
            
            with open(trace_path, "rb") as trace_file:
                trace_data = trace_file.read()
                allure.attach(
                    trace_data,
                    name=f"Trace - {test_name}.zip",
                    attachment_type="application/zip",
                    extension="zip",
                )
            logger.info(f"Attached Playwright trace for: {test_name}")
            
            # Clean up temp file
            import os
            os.unlink(trace_path)
        except Exception as e:
            logger.warning(f"Failed to capture trace: {e}")
    
    # 5. Attach video if it exists
    try:
        if page.video:
            video_path = page.video.path()
            if video_path:
                with open(video_path, "rb") as video_file:
                    video_data = video_file.read()
                    allure.attach(
                        video_data,
                        name=f"Video - {test_name}.webm",
                        attachment_type="video/webm",
                        extension="webm",
                    )
                logger.info(f"Attached video for: {test_name}")
    except Exception as e:
        logger.warning(f"Failed to capture video: {e}")


def _attach_appium_artifacts(item, test_name: str) -> None:
    """Attach Appium artifacts (screenshot, page source) on failure."""
    driver = None
    
    # Try to get driver from various fixtures
    if "appium_driver" in item.funcargs:
        driver = item.funcargs["appium_driver"]
    elif "mobile_actions" in item.funcargs:
        mobile_actions = item.funcargs["mobile_actions"]
        if hasattr(mobile_actions, "driver"):
            driver = mobile_actions.driver
    
    if driver is None:
        return
    
    try:
        # Attach screenshot
        screenshot = driver.get_screenshot_as_png()
        allure.attach(
            screenshot,
            name=f"Screenshot - {test_name}",
            attachment_type=allure.attachment_type.PNG,
        )
        logger.info(f"Attached mobile failure screenshot for: {test_name}")
    except Exception as e:
        logger.warning(f"Failed to capture mobile screenshot: {e}")
    
    try:
        # Attach page source (XML for mobile)
        page_source = driver.page_source
        allure.attach(
            page_source,
            name="Page Source (XML)",
            attachment_type=allure.attachment_type.XML,
        )
    except Exception as e:
        logger.warning(f"Failed to capture mobile page source: {e}")
    
    try:
        # Attach device info
        device_info = {
            "platformName": driver.capabilities.get("platformName"),
            "platformVersion": driver.capabilities.get("platformVersion"),
            "deviceName": driver.capabilities.get("deviceName"),
            "automationName": driver.capabilities.get("automationName"),
        }
        import json
        allure.attach(
            json.dumps(device_info, indent=2),
            name="Device Info",
            attachment_type=allure.attachment_type.JSON,
        )
    except Exception as e:
        logger.warning(f"Failed to capture device info: {e}")


# ---------------------------------------------------------------------------
# Screenshot Helper Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def screenshot_on_failure(request, test_config: Settings):
    """
    Fixture that automatically takes a screenshot on test failure.
    
    Usage:
        def test_example(self, ui_actions, screenshot_on_failure):
            # Test code here
            pass  # Screenshot will be taken automatically if test fails
    """
    yield
    
    # This is handled by pytest_runtest_makereport hook
    # This fixture is for explicit opt-in if needed


@pytest.fixture
def take_screenshot(request):
    """
    Fixture that provides a function to take screenshots at any point.
    
    Usage:
        def test_example(self, ui_actions, take_screenshot):
            # ... do something
            take_screenshot("after_login")
            # ... continue test
    """
    def _take_screenshot(name: str = "screenshot"):
        # Try to find page or driver
        page = None
        driver = None
        
        if hasattr(request, "node") and hasattr(request.node, "funcargs"):
            funcargs = request.node.funcargs
            
            # Check for Playwright page
            if "page" in funcargs:
                page = funcargs["page"]
            elif "ui_actions" in funcargs:
                ui_actions = funcargs["ui_actions"]
                if hasattr(ui_actions, "page"):
                    page = ui_actions.page
            
            # Check for Appium driver
            if "appium_driver" in funcargs:
                driver = funcargs["appium_driver"]
            elif "mobile_actions" in funcargs:
                mobile_actions = funcargs["mobile_actions"]
                if hasattr(mobile_actions, "driver"):
                    driver = mobile_actions.driver
        
        if page:
            try:
                screenshot = page.screenshot(full_page=True)
                allure.attach(
                    screenshot,
                    name=name,
                    attachment_type=allure.attachment_type.PNG,
                )
                logger.info(f"Screenshot captured: {name}")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot '{name}': {e}")
        
        elif driver:
            try:
                screenshot = driver.get_screenshot_as_png()
                allure.attach(
                    screenshot,
                    name=name,
                    attachment_type=allure.attachment_type.PNG,
                )
                logger.info(f"Mobile screenshot captured: {name}")
            except Exception as e:
                logger.warning(f"Failed to capture mobile screenshot '{name}': {e}")
        else:
            logger.warning(f"No page or driver found for screenshot: {name}")
    
    return _take_screenshot


# ---------------------------------------------------------------------------
# Session Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_session(test_config: Settings):
    """Setup test session."""
    logger.info(f"Starting test session in {test_config.core.environment} environment")
    logger.info(f"UI Base URL: {test_config.data.ui.base_url}")
    logger.info(f"API Base URL: {test_config.data.api.base_url}")
    
    yield
    
    logger.info("Test session completed")


@pytest.fixture(autouse=True)
def log_test_info(request):
    """Log test information."""
    logger.info(f"Starting test: {request.node.name}")
    yield
    logger.info(f"Completed test: {request.node.name}")
