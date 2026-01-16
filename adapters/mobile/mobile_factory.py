"""
Mobile Factory for centralized Appium driver management.

Supports configuration from:
1. Config files (core_config.yml + data_config.yml)
2. Environment variables (for Jenkins/CI)
3. CLI parameters (pytest command line)

Environment variable overrides:
- MOBILE_PLATFORM: android, ios
- MOBILE_DEVICE_NAME: device name or emulator
- MOBILE_PLATFORM_VERSION: OS version
- MOBILE_APP_PATH: path to APK/IPA
- MOBILE_APPIUM_SERVER: Appium server URL
- MOBILE_UDID: device UDID (for real devices)
- MOBILE_NO_RESET: true, false
- MOBILE_FULL_RESET: true, false
"""
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from loguru import logger
import allure

try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.options.ios import XCUITestOptions
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False
    logger.warning("Appium not installed. Mobile testing will not be available.")


@dataclass
class MobileConfig:
    """Mobile configuration with all options."""
    
    # Platform settings
    platform: str = "android"  # android or ios
    appium_server: str = "http://localhost:4723"
    
    # Android settings
    android_device_name: str = "emulator-5554"
    android_platform_version: str = "13"
    android_app_path: Optional[str] = None
    android_app_package: Optional[str] = None
    android_app_activity: Optional[str] = None
    android_automation_name: str = "UiAutomator2"
    
    # iOS settings
    ios_device_name: str = "iPhone 14"
    ios_platform_version: str = "16.0"
    ios_app_path: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    ios_udid: Optional[str] = None
    ios_automation_name: str = "XCUITest"
    
    # Common settings
    new_command_timeout: int = 300
    implicit_wait: int = 10
    no_reset: bool = False
    full_reset: bool = False
    
    # Artifact settings
    screenshot_on_failure: bool = True
    
    @classmethod
    def from_dict(
        cls,
        core_config: Dict[str, Any],
        data_config: Dict[str, Any],
    ) -> "MobileConfig":
        """Create MobileConfig from core and data config dictionaries."""
        mobile_core = core_config.get("mobile", {})
        mobile_data = data_config.get("mobile_app", {})
        android_data = mobile_data.get("android", {})
        ios_data = mobile_data.get("ios", {})
        
        return cls(
            # Platform
            platform=android_data.get("platform", "android"),
            appium_server=mobile_core.get("appium_server", "http://localhost:4723"),
            
            # Android
            android_device_name=android_data.get("device_name", "emulator-5554"),
            android_platform_version=android_data.get("platform_version", "13"),
            android_app_path=android_data.get("app_path"),
            android_app_package=android_data.get("app_package"),
            android_app_activity=android_data.get("app_activity"),
            android_automation_name=mobile_core.get("automation_name", "UiAutomator2"),
            
            # iOS
            ios_device_name=ios_data.get("device_name", "iPhone 14"),
            ios_platform_version=ios_data.get("platform_version", "16.0"),
            ios_app_path=ios_data.get("app_path"),
            ios_bundle_id=ios_data.get("bundle_id"),
            ios_udid=ios_data.get("udid"),
            ios_automation_name="XCUITest",
            
            # Common
            new_command_timeout=mobile_core.get("new_command_timeout", 300),
            implicit_wait=data_config.get("timeouts", {}).get("implicit_wait", 10),
            no_reset=mobile_core.get("no_reset", False),
            full_reset=mobile_core.get("full_reset", False),
            screenshot_on_failure=core_config.get("browser", {}).get("screenshot_on_failure", True),
        )


class MobileFactory:
    """
    Factory class for creating and managing Appium driver instances.
    
    This is the central point for mobile automation management in the framework.
    It handles:
    - Driver creation with proper configuration
    - Environment variable overrides for CI/CD
    - CLI parameter overrides
    - Resource cleanup
    
    Usage:
        factory = MobileFactory(core_config, data_config)
        driver = factory.create_driver()
        # ... use driver ...
        factory.close()
    """
    
    def __init__(
        self,
        core_config: Dict[str, Any],
        data_config: Dict[str, Any],
        cli_overrides: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize MobileFactory with configuration.
        
        Args:
            core_config: Core configuration dictionary
            data_config: Data configuration dictionary
            cli_overrides: Optional CLI parameter overrides
        """
        if not APPIUM_AVAILABLE:
            raise ImportError(
                "Appium is not installed. Install with: pip install Appium-Python-Client"
            )
        
        self._driver = None
        self._core_config = core_config
        self._data_config = data_config
        
        # Build configuration with overrides
        self.config = self._build_config(core_config, data_config, cli_overrides or {})
        
        logger.info(f"MobileFactory initialized: {self.config.platform}, "
                   f"device={self.get_device_name()}")
    
    def _build_config(
        self,
        core_config: Dict[str, Any],
        data_config: Dict[str, Any],
        cli_overrides: Dict[str, Any],
    ) -> MobileConfig:
        """Build final configuration with all overrides applied."""
        # Create base config
        config = MobileConfig.from_dict(core_config, data_config)
        
        # Apply environment variable overrides
        self._apply_env_overrides(config)
        
        # Apply CLI overrides
        self._apply_cli_overrides(config, cli_overrides)
        
        return config
    
    def _apply_env_overrides(self, config: MobileConfig) -> None:
        """Apply environment variable overrides."""
        # Platform override
        if os.environ.get("MOBILE_PLATFORM"):
            config.platform = os.environ["MOBILE_PLATFORM"].lower()
            logger.info(f"Environment override: platform={config.platform}")
        
        # Appium server override
        if os.environ.get("MOBILE_APPIUM_SERVER"):
            config.appium_server = os.environ["MOBILE_APPIUM_SERVER"]
            logger.info(f"Environment override: appium_server={config.appium_server}")
        
        # Device name override
        if os.environ.get("MOBILE_DEVICE_NAME"):
            device = os.environ["MOBILE_DEVICE_NAME"]
            config.android_device_name = device
            config.ios_device_name = device
            logger.info(f"Environment override: device_name={device}")
        
        # Platform version override
        if os.environ.get("MOBILE_PLATFORM_VERSION"):
            version = os.environ["MOBILE_PLATFORM_VERSION"]
            config.android_platform_version = version
            config.ios_platform_version = version
            logger.info(f"Environment override: platform_version={version}")
        
        # App path override
        if os.environ.get("MOBILE_APP_PATH"):
            app_path = os.environ["MOBILE_APP_PATH"]
            config.android_app_path = app_path
            config.ios_app_path = app_path
            logger.info(f"Environment override: app_path={app_path}")
        
        # UDID override (for real devices)
        if os.environ.get("MOBILE_UDID"):
            config.ios_udid = os.environ["MOBILE_UDID"]
            logger.info(f"Environment override: udid={config.ios_udid}")
        
        # Reset options
        if os.environ.get("MOBILE_NO_RESET"):
            config.no_reset = os.environ["MOBILE_NO_RESET"].lower() == "true"
            logger.info(f"Environment override: no_reset={config.no_reset}")
        
        if os.environ.get("MOBILE_FULL_RESET"):
            config.full_reset = os.environ["MOBILE_FULL_RESET"].lower() == "true"
            logger.info(f"Environment override: full_reset={config.full_reset}")
    
    def _apply_cli_overrides(
        self,
        config: MobileConfig,
        cli_overrides: Dict[str, Any],
    ) -> None:
        """Apply CLI parameter overrides."""
        if cli_overrides.get("platform"):
            config.platform = cli_overrides["platform"].lower()
            logger.info(f"CLI override: platform={config.platform}")
        
        if cli_overrides.get("device_name"):
            device = cli_overrides["device_name"]
            config.android_device_name = device
            config.ios_device_name = device
            logger.info(f"CLI override: device_name={device}")
        
        if cli_overrides.get("app_path"):
            app_path = cli_overrides["app_path"]
            config.android_app_path = app_path
            config.ios_app_path = app_path
            logger.info(f"CLI override: app_path={app_path}")
        
        if cli_overrides.get("udid"):
            config.ios_udid = cli_overrides["udid"]
            logger.info(f"CLI override: udid={config.ios_udid}")
        
        if cli_overrides.get("no_reset") is not None:
            config.no_reset = cli_overrides["no_reset"]
            logger.info(f"CLI override: no_reset={config.no_reset}")
    
    @property
    def platform(self) -> str:
        """Get the configured platform."""
        return self.config.platform
    
    @property
    def is_android(self) -> bool:
        """Check if running Android tests."""
        return self.config.platform.lower() == "android"
    
    @property
    def is_ios(self) -> bool:
        """Check if running iOS tests."""
        return self.config.platform.lower() == "ios"
    
    def get_device_name(self) -> str:
        """Get the configured device name."""
        if self.is_android:
            return self.config.android_device_name
        return self.config.ios_device_name
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Appium capabilities based on platform."""
        if self.is_android:
            caps = {
                "platformName": "Android",
                "platformVersion": self.config.android_platform_version,
                "deviceName": self.config.android_device_name,
                "automationName": self.config.android_automation_name,
                "newCommandTimeout": self.config.new_command_timeout,
                "noReset": self.config.no_reset,
                "fullReset": self.config.full_reset,
            }
            
            if self.config.android_app_path:
                caps["app"] = self.config.android_app_path
            if self.config.android_app_package:
                caps["appPackage"] = self.config.android_app_package
            if self.config.android_app_activity:
                caps["appActivity"] = self.config.android_app_activity
            
            return caps
        
        else:  # iOS
            caps = {
                "platformName": "iOS",
                "platformVersion": self.config.ios_platform_version,
                "deviceName": self.config.ios_device_name,
                "automationName": self.config.ios_automation_name,
                "newCommandTimeout": self.config.new_command_timeout,
                "noReset": self.config.no_reset,
                "fullReset": self.config.full_reset,
            }
            
            if self.config.ios_app_path:
                caps["app"] = self.config.ios_app_path
            if self.config.ios_bundle_id:
                caps["bundleId"] = self.config.ios_bundle_id
            if self.config.ios_udid:
                caps["udid"] = self.config.ios_udid
            
            return caps
    
    @allure.step("Create Appium driver: {self.config.platform}")
    def create_driver(self):
        """
        Create Appium driver with configured capabilities.
        
        Returns:
            Appium WebDriver instance
        """
        if self._driver is not None:
            return self._driver
        
        capabilities = self.get_capabilities()
        
        # Filter out None values
        capabilities = {k: v for k, v in capabilities.items() if v is not None}
        
        logger.info(f"Creating {self.config.platform} driver")
        logger.debug(f"Capabilities: {capabilities}")
        
        # Create appropriate options
        if self.is_android:
            options = UiAutomator2Options().load_capabilities(capabilities)
        else:
            options = XCUITestOptions().load_capabilities(capabilities)
        
        self._driver = webdriver.Remote(
            command_executor=self.config.appium_server,
            options=options,
        )
        
        # Set implicit wait
        self._driver.implicitly_wait(self.config.implicit_wait)
        
        # Attach capabilities to Allure report
        allure.attach(
            f"Platform: {self.config.platform}\n"
            f"Device: {self.get_device_name()}\n"
            f"Appium Server: {self.config.appium_server}\n"
            f"Capabilities: {capabilities}",
            name="Mobile Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        return self._driver
    
    def get_driver(self):
        """Get existing driver or create new one."""
        if self._driver is None:
            return self.create_driver()
        return self._driver
    
    def take_screenshot(self, name: str = "screenshot") -> Optional[bytes]:
        """Take a screenshot and optionally attach to Allure."""
        if self._driver is None:
            return None
        
        try:
            screenshot = self._driver.get_screenshot_as_png()
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
            logger.info(f"Screenshot captured: {name}")
            return screenshot
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
            return None
    
    def get_page_source(self) -> Optional[str]:
        """Get current page source XML."""
        if self._driver is None:
            return None
        
        try:
            return self._driver.page_source
        except Exception as e:
            logger.warning(f"Failed to get page source: {e}")
            return None
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information from driver."""
        if self._driver is None:
            return {}
        
        try:
            caps = self._driver.capabilities
            return {
                "platformName": caps.get("platformName"),
                "platformVersion": caps.get("platformVersion"),
                "deviceName": caps.get("deviceName"),
                "automationName": caps.get("automationName"),
                "udid": caps.get("udid"),
            }
        except Exception as e:
            logger.warning(f"Failed to get device info: {e}")
            return {}
    
    def reset_app(self) -> None:
        """Reset the app to initial state."""
        if self._driver:
            try:
                if self.is_android:
                    package = self.config.android_app_package
                    if package:
                        self._driver.terminate_app(package)
                        self._driver.activate_app(package)
                else:
                    bundle_id = self.config.ios_bundle_id
                    if bundle_id:
                        self._driver.terminate_app(bundle_id)
                        self._driver.activate_app(bundle_id)
                logger.info("App reset completed")
            except Exception as e:
                logger.warning(f"Failed to reset app: {e}")
    
    def close(self) -> None:
        """Close driver and cleanup resources."""
        if self._driver:
            try:
                self._driver.quit()
                logger.info("Mobile driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self._driver = None
    
    def __enter__(self) -> "MobileFactory":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Singleton instance for session-scoped usage
_factory_instance: Optional[MobileFactory] = None


def get_mobile_factory(
    core_config: Optional[Dict[str, Any]] = None,
    data_config: Optional[Dict[str, Any]] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    force_new: bool = False,
) -> MobileFactory:
    """
    Get or create a MobileFactory instance.
    
    Args:
        core_config: Core configuration dictionary
        data_config: Data configuration dictionary
        cli_overrides: CLI parameter overrides
        force_new: Force creation of new instance
    
    Returns:
        MobileFactory instance
    """
    global _factory_instance
    
    if _factory_instance is None or force_new:
        if core_config is None:
            core_config = {}
        if data_config is None:
            data_config = {}
        _factory_instance = MobileFactory(core_config, data_config, cli_overrides)
    
    return _factory_instance


def close_mobile_factory() -> None:
    """Close the global mobile factory instance."""
    global _factory_instance
    
    if _factory_instance:
        _factory_instance.close()
        _factory_instance = None

