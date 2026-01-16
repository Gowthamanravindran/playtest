"""Configuration management using YAML files with split core and data configs."""
from functools import lru_cache
from typing import Optional, Literal, Any, Dict
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger


def load_yaml_file(file_path: Path) -> dict:
    """Load a single YAML file."""
    if file_path.exists():
        with open(file_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def find_config_file(filename: str, config_path: Optional[str] = None) -> Optional[Path]:
    """Find a config file in common locations."""
    if config_path:
        path = Path(config_path)
        if path.is_dir():
            path = path / filename
        return path if path.exists() else None
    
    possible_paths = [
        Path(filename),
        Path(f"configs/{filename}"),
        Path(__file__).parent / filename,
    ]
    
    for p in possible_paths:
        if p.exists():
            return p
    return None


def load_configs(
    core_config_path: Optional[str] = None,
    data_config_path: Optional[str] = None,
) -> Dict[str, dict]:
    """
    Load both core and data configuration files.
    
    Args:
        core_config_path: Path to core_config.yml
        data_config_path: Path to data_config.yml
    
    Returns:
        Dictionary with 'core' and 'data' config dictionaries
    """
    # Find and load core config
    core_path = find_config_file("core_config.yml", core_config_path)
    core_config = load_yaml_file(core_path) if core_path else {}
    
    # Find and load data config
    data_path = find_config_file("data_config.yml", data_config_path)
    data_config = load_yaml_file(data_path) if data_path else {}
    
    if core_path:
        logger.debug(f"Loaded core config from: {core_path}")
    if data_path:
        logger.debug(f"Loaded data config from: {data_path}")
    
    return {"core": core_config, "data": data_config}


# =============================================================================
# Core Configuration Classes
# =============================================================================

class BrowserConfig(BaseModel):
    """Browser/Playwright configuration."""
    
    type: Literal["chromium", "firefox", "webkit"] = Field(default="chromium")
    headless: bool = Field(default=True)
    slow_mo: int = Field(default=0)
    timeout: int = Field(default=30000, description="Default timeout in milliseconds")
    viewport_width: int = Field(default=1920)
    viewport_height: int = Field(default=1080)
    screenshot_on_failure: bool = Field(default=True)
    video_on_failure: bool = Field(default=False)
    trace_on_failure: bool = Field(default=True)

    @classmethod
    def from_yaml(cls, data: dict) -> "BrowserConfig":
        if not data:
            return cls()
        viewport = data.get("viewport", {})
        return cls(
            type=data.get("type", "chromium"),
            headless=data.get("headless", True),
            slow_mo=data.get("slow_mo", 0),
            timeout=data.get("timeout", 30000),
            viewport_width=viewport.get("width", 1920),
            viewport_height=viewport.get("height", 1080),
            screenshot_on_failure=data.get("screenshot_on_failure", True),
            video_on_failure=data.get("video_on_failure", False),
            trace_on_failure=data.get("trace_on_failure", True),
        )


class MobileFrameworkConfig(BaseModel):
    """Mobile framework configuration (Appium settings)."""
    
    appium_server: str = Field(default="http://localhost:4723")
    automation_name: str = Field(default="UiAutomator2")
    new_command_timeout: int = Field(default=300)
    no_reset: bool = Field(default=False)
    full_reset: bool = Field(default=False)

    @classmethod
    def from_yaml(cls, data: dict) -> "MobileFrameworkConfig":
        if not data:
            return cls()
        return cls(
            appium_server=data.get("appium_server", "http://localhost:4723"),
            automation_name=data.get("automation_name", "UiAutomator2"),
            new_command_timeout=data.get("new_command_timeout", 300),
            no_reset=data.get("no_reset", False),
            full_reset=data.get("full_reset", False),
        )


class AllureConfig(BaseModel):
    """Allure reporting configuration."""
    
    results_dir: str = Field(default="reports/allure-results")
    report_dir: str = Field(default="reports/allure-report")
    clean_results: bool = Field(default=True)

    @classmethod
    def from_yaml(cls, data: dict) -> "AllureConfig":
        if not data:
            return cls()
        return cls(
            results_dir=data.get("results_dir", "reports/allure-results"),
            report_dir=data.get("report_dir", "reports/allure-report"),
            clean_results=data.get("clean_results", True),
        )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    file_path: Optional[str] = Field(default="reports/logs/test.log")
    rotation: str = Field(default="10 MB")
    retention: str = Field(default="1 week")

    @classmethod
    def from_yaml(cls, data: dict) -> "LoggingConfig":
        if not data:
            return cls()
        return cls(
            level=data.get("level", "INFO"),
            file_path=data.get("file_path", "reports/logs/test.log"),
            rotation=data.get("rotation", "10 MB"),
            retention=data.get("retention", "1 week"),
        )


class CoreConfig(BaseModel):
    """Core framework configuration."""
    
    environment: Literal["local", "dev", "staging", "prod"] = Field(default="local")
    debug: bool = Field(default=False)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    mobile: MobileFrameworkConfig = Field(default_factory=MobileFrameworkConfig)
    allure: AllureConfig = Field(default_factory=AllureConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, data: dict) -> "CoreConfig":
        if not data:
            return cls()
        return cls(
            environment=data.get("environment", "local"),
            debug=data.get("debug", False),
            browser=BrowserConfig.from_yaml(data.get("browser", {})),
            mobile=MobileFrameworkConfig.from_yaml(data.get("mobile", {})),
            allure=AllureConfig.from_yaml(data.get("allure", {})),
            logging=LoggingConfig.from_yaml(data.get("logging", {})),
        )


# =============================================================================
# Data Configuration Classes
# =============================================================================

class UIDataConfig(BaseModel):
    """UI URLs configuration."""
    
    base_url: str = Field(default="http://localhost:3000")
    login_url: str = Field(default="/login")
    dashboard_url: str = Field(default="/dashboard")

    @classmethod
    def from_yaml(cls, data: dict) -> "UIDataConfig":
        if not data:
            return cls()
        return cls(
            base_url=data.get("base_url", "http://localhost:3000"),
            login_url=data.get("login_url", "/login"),
            dashboard_url=data.get("dashboard_url", "/dashboard"),
        )


class APIDataConfig(BaseModel):
    """API configuration."""
    
    base_url: str = Field(default="http://localhost:8000/api")
    version: str = Field(default="v1")

    @classmethod
    def from_yaml(cls, data: dict) -> "APIDataConfig":
        if not data:
            return cls()
        return cls(
            base_url=data.get("base_url", "http://localhost:8000/api"),
            version=data.get("version", "v1"),
        )


class TimeoutsConfig(BaseModel):
    """Timeout and wait configurations."""
    
    default: int = Field(default=30)
    page_load: int = Field(default=60)
    element_wait: int = Field(default=10)
    api_timeout: int = Field(default=30)
    implicit_wait: int = Field(default=10)

    @classmethod
    def from_yaml(cls, data: dict) -> "TimeoutsConfig":
        if not data:
            return cls()
        return cls(
            default=data.get("default", 30),
            page_load=data.get("page_load", 60),
            element_wait=data.get("element_wait", 10),
            api_timeout=data.get("api_timeout", 30),
            implicit_wait=data.get("implicit_wait", 10),
        )


class UserCredentials(BaseModel):
    """Single user credentials."""
    
    username: str = Field(default="")
    password: str = Field(default="")
    email: str = Field(default="")

    @classmethod
    def from_yaml(cls, data: dict) -> "UserCredentials":
        if not data:
            return cls()
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email", ""),
        )


class CredentialsConfig(BaseModel):
    """All credentials configuration."""
    
    valid_user: UserCredentials = Field(default_factory=UserCredentials)
    admin_user: UserCredentials = Field(default_factory=UserCredentials)
    invalid_user: UserCredentials = Field(default_factory=UserCredentials)

    @classmethod
    def from_yaml(cls, data: dict) -> "CredentialsConfig":
        if not data:
            return cls()
        return cls(
            valid_user=UserCredentials.from_yaml(data.get("valid_user", {})),
            admin_user=UserCredentials.from_yaml(data.get("admin_user", {})),
            invalid_user=UserCredentials.from_yaml(data.get("invalid_user", {})),
        )


class AndroidAppConfig(BaseModel):
    """Android app configuration."""
    
    platform: str = Field(default="android")
    platform_version: str = Field(default="13")
    device_name: str = Field(default="emulator-5554")
    app_path: Optional[str] = Field(default=None)
    app_package: Optional[str] = Field(default=None)
    app_activity: Optional[str] = Field(default=None)

    @classmethod
    def from_yaml(cls, data: dict) -> "AndroidAppConfig":
        if not data:
            return cls()
        return cls(
            platform=data.get("platform", "android"),
            platform_version=data.get("platform_version", "13"),
            device_name=data.get("device_name", "emulator-5554"),
            app_path=data.get("app_path"),
            app_package=data.get("app_package"),
            app_activity=data.get("app_activity"),
        )


class IOSAppConfig(BaseModel):
    """iOS app configuration."""
    
    platform: str = Field(default="ios")
    platform_version: str = Field(default="16.0")
    device_name: str = Field(default="iPhone 14")
    app_path: Optional[str] = Field(default=None)
    bundle_id: Optional[str] = Field(default=None)
    udid: Optional[str] = Field(default=None)

    @classmethod
    def from_yaml(cls, data: dict) -> "IOSAppConfig":
        if not data:
            return cls()
        return cls(
            platform=data.get("platform", "ios"),
            platform_version=data.get("platform_version", "16.0"),
            device_name=data.get("device_name", "iPhone 14"),
            app_path=data.get("app_path"),
            bundle_id=data.get("bundle_id"),
            udid=data.get("udid"),
        )


class MobileAppConfig(BaseModel):
    """Mobile app data configuration."""
    
    android: AndroidAppConfig = Field(default_factory=AndroidAppConfig)
    ios: IOSAppConfig = Field(default_factory=IOSAppConfig)

    @classmethod
    def from_yaml(cls, data: dict) -> "MobileAppConfig":
        if not data:
            return cls()
        return cls(
            android=AndroidAppConfig.from_yaml(data.get("android", {})),
            ios=IOSAppConfig.from_yaml(data.get("ios", {})),
        )


class DataConfig(BaseModel):
    """Data/test-specific configuration."""
    
    ui: UIDataConfig = Field(default_factory=UIDataConfig)
    api: APIDataConfig = Field(default_factory=APIDataConfig)
    timeouts: TimeoutsConfig = Field(default_factory=TimeoutsConfig)
    credentials: CredentialsConfig = Field(default_factory=CredentialsConfig)
    mobile_app: MobileAppConfig = Field(default_factory=MobileAppConfig)
    endpoints: dict = Field(default_factory=dict)
    test_data: dict = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, data: dict) -> "DataConfig":
        if not data:
            return cls()
        return cls(
            ui=UIDataConfig.from_yaml(data.get("ui", {})),
            api=APIDataConfig.from_yaml(data.get("api", {})),
            timeouts=TimeoutsConfig.from_yaml(data.get("timeouts", {})),
            credentials=CredentialsConfig.from_yaml(data.get("credentials", {})),
            mobile_app=MobileAppConfig.from_yaml(data.get("mobile_app", {})),
            endpoints=data.get("endpoints", {}),
            test_data=data.get("test_data", {}),
        )


# =============================================================================
# Main Settings Class
# =============================================================================

class Settings(BaseModel):
    """
    Main settings combining core and data configurations.
    
    Attributes:
        core: Framework-level settings (browser, reporting, logging)
        data: Test-specific settings (URLs, credentials, timeouts)
    """
    
    model_config = ConfigDict(extra="ignore")
    
    core: CoreConfig = Field(default_factory=CoreConfig)
    data: DataConfig = Field(default_factory=DataConfig)

    @classmethod
    def from_yaml(
        cls,
        core_config_path: Optional[str] = None,
        data_config_path: Optional[str] = None,
    ) -> "Settings":
        """
        Create Settings from YAML configuration files.
        
        Args:
            core_config_path: Path to core_config.yml
            data_config_path: Path to data_config.yml
            
        Returns:
            Settings instance populated from YAML files
        """
        configs = load_configs(core_config_path, data_config_path)
        
        return cls(
            core=CoreConfig.from_yaml(configs["core"]),
            data=DataConfig.from_yaml(configs["data"]),
        )

    # -------------------------------------------------------------------------
    # Convenience Properties (backward compatibility)
    # -------------------------------------------------------------------------
    
    @property
    def environment(self) -> str:
        """Get current environment."""
        return self.core.environment

    @property
    def ui_base_url(self) -> str:
        """Get UI base URL."""
        return self.data.ui.base_url

    @property
    def api_base_url(self) -> str:
        """Get API base URL."""
        return self.data.api.base_url

    @property
    def valid_username(self) -> str:
        """Get valid test username."""
        return self.data.credentials.valid_user.username

    @property
    def valid_password(self) -> str:
        """Get valid test password."""
        return self.data.credentials.valid_user.password

    @property
    def default_timeout(self) -> int:
        """Get default timeout in seconds."""
        return self.data.timeouts.default

    @property
    def browser_timeout(self) -> int:
        """Get browser timeout in milliseconds."""
        return self.data.timeouts.default * 1000

    def get_mobile_capabilities(self, platform: str = "android") -> dict:
        """
        Get Appium capabilities based on platform.
        
        Args:
            platform: 'android' or 'ios'
            
        Returns:
            Dictionary of Appium capabilities
        """
        if platform.lower() == "android":
            app_config = self.data.mobile_app.android
            return {
                "platformName": "Android",
                "platformVersion": app_config.platform_version,
                "deviceName": app_config.device_name,
                "automationName": self.core.mobile.automation_name,
                "app": app_config.app_path,
                "appPackage": app_config.app_package,
                "appActivity": app_config.app_activity,
                "newCommandTimeout": self.core.mobile.new_command_timeout,
                "noReset": self.core.mobile.no_reset,
                "fullReset": self.core.mobile.full_reset,
            }
        else:  # iOS
            app_config = self.data.mobile_app.ios
            return {
                "platformName": "iOS",
                "platformVersion": app_config.platform_version,
                "deviceName": app_config.device_name,
                "automationName": "XCUITest",
                "app": app_config.app_path,
                "bundleId": app_config.bundle_id,
                "udid": app_config.udid,
                "newCommandTimeout": self.core.mobile.new_command_timeout,
                "noReset": self.core.mobile.no_reset,
                "fullReset": self.core.mobile.full_reset,
            }


# =============================================================================
# Settings Factory Functions
# =============================================================================

_settings_instance: Optional[Settings] = None


def get_settings(
    core_config_path: Optional[str] = None,
    data_config_path: Optional[str] = None,
    reload: bool = False,
) -> Settings:
    """
    Get settings instance (cached).
    
    Args:
        core_config_path: Optional path to core_config.yml
        data_config_path: Optional path to data_config.yml
        reload: Force reload of settings
        
    Returns:
        Settings instance
    """
    global _settings_instance
    
    if _settings_instance is None or reload:
        _settings_instance = Settings.from_yaml(core_config_path, data_config_path)
    
    return _settings_instance


def load_config(
    core_config_path: Optional[str] = None,
    data_config_path: Optional[str] = None,
) -> Settings:
    """
    Load configuration from specific YAML files (non-cached).
    
    Args:
        core_config_path: Path to core_config.yml
        data_config_path: Path to data_config.yml
        
    Returns:
        Settings instance
    """
    return Settings.from_yaml(core_config_path, data_config_path)
