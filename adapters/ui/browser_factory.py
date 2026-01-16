"""
Browser Factory
Default parameters are overridden by below items
1. Config file (core_config.yml)
2. Environment variables (for Jenkins/CI)
3. CLI parameters (pytest command line)
"""
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from loguru import logger
import allure


@dataclass
class BrowserConfig:
    browser_type: str = "chromium"
    headless: bool = True
    slow_mo: int = 0
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    screenshot_on_failure: bool = True
    video_on_failure: bool = False
    trace_on_failure: bool = True
    args: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "BrowserConfig":
        """Create BrowserConfig from dictionary."""
        viewport = config.get("viewport", {})
        browser_type = config.get("type") or config.get("default", "chromium")
        
        # Get browser-specific args
        browser_specific = config.get(browser_type, {})
        args = browser_specific.get("args", [])
        
        return cls(
            browser_type=browser_type,
            headless=config.get("headless", True),
            slow_mo=config.get("slow_mo", 0),
            timeout=config.get("timeout", 30000),
            viewport_width=viewport.get("width", 1920),
            viewport_height=viewport.get("height", 1080),
            screenshot_on_failure=config.get("screenshot_on_failure", True),
            video_on_failure=config.get("video_on_failure", False),
            trace_on_failure=config.get("trace_on_failure", True),
            args=args,
        )


class BrowserFactory:
    def __init__(
        self,
        config: Dict[str, Any],
        cli_overrides: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize BrowserFactory with configuration.
        
        Args:
            config: Browser configuration dictionary from core_config
            cli_overrides: Optional CLI parameter overrides
        """
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: List[BrowserContext] = []
        self._pages: List[Page] = []
        
        # Build configuration with overrides
        self.config = self._build_config(config, cli_overrides or {})
        
        logger.info(f"BrowserFactory initialized: {self.config.browser_type}, "
                   f"headless={self.config.headless}")
    
    def _build_config(
        self,
        config: Dict[str, Any],
        cli_overrides: Dict[str, Any],
    ) -> BrowserConfig:
        merged = dict(config)
        self._apply_env_overrides(merged)
        self._apply_cli_overrides(merged, cli_overrides)
        return BrowserConfig.from_dict(merged)
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            "BROWSER_TYPE": ("type", str),
            "BROWSER_HEADLESS": ("headless", lambda x: x.lower() == "true"),
            "BROWSER_SLOW_MO": ("slow_mo", int),
            "BROWSER_TIMEOUT": ("timeout", int),
            "BROWSER_VIEWPORT_WIDTH": ("viewport.width", int),
            "BROWSER_VIEWPORT_HEIGHT": ("viewport.height", int),
        }
        
        for env_var, (config_key, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if "." in config_key:
                    # Nested key like viewport.width
                    parts = config_key.split(".")
                    config.setdefault(parts[0], {})[parts[1]] = converter(value)
                else:
                    config[config_key] = converter(value)
                logger.info(f"Environment override: {env_var}={value}")
    
    def _apply_cli_overrides(
        self,
        config: Dict[str, Any],
        cli_overrides: Dict[str, Any],
    ) -> None:
        """Apply CLI parameter overrides."""
        if cli_overrides.get("browser_type"):
            config["type"] = cli_overrides["browser_type"]
            logger.info(f"CLI override: browser_type={cli_overrides['browser_type']}")
        
        if cli_overrides.get("headed"):
            config["headless"] = False
            logger.info("CLI override: headed mode enabled")
        
        if cli_overrides.get("headless") is not None:
            config["headless"] = cli_overrides["headless"]
        
        if cli_overrides.get("slow_mo") is not None:
            config["slow_mo"] = cli_overrides["slow_mo"]
            logger.info(f"CLI override: slow_mo={cli_overrides['slow_mo']}")
    
    @property
    def browser_type(self) -> str:
        """Get the configured browser type."""
        return self.config.browser_type
    
    @property
    def is_headless(self) -> bool:
        """Check if running in headless mode."""
        return self.config.headless
    
    def get_launch_options(self) -> Dict[str, Any]:
        """Get browser launch options."""
        options = {
            "headless": self.config.headless,
            "slow_mo": self.config.slow_mo,
        }
        
        if self.config.args:
            options["args"] = self.config.args
        
        return options
    
    def get_context_options(self) -> Dict[str, Any]:
        """Get browser context options."""
        options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "ignore_https_errors": True,
        }
        
        # Video recording
        if self.config.video_on_failure:
            options["record_video_dir"] = "reports/videos"
        
        return options
    
    @allure.step("Launch browser: {self.config.browser_type}")
    def launch_browser(self) -> Browser:
        if self._browser is not None and self._browser.is_connected():
            return self._browser
        
        self._playwright = sync_playwright().start()
        launch_options = self.get_launch_options()
        
        logger.info(f"Launching {self.config.browser_type} browser")
        logger.debug(f"Launch options: {launch_options}")
        
        # Get the browser launcher based on type
        browser_launcher = getattr(self._playwright, self.config.browser_type)
        self._browser = browser_launcher.launch(**launch_options)
        
        allure.attach(
            f"Browser: {self.config.browser_type}\n"
            f"Headless: {self.config.headless}\n"
            f"Slow Mo: {self.config.slow_mo}ms",
            name="Browser Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        return self._browser
    
    @allure.step("Create browser context")
    def create_context(
        self,
        browser: Optional[Browser] = None,
        **extra_options,
    ) -> BrowserContext:
        """
        Create a new browser context.
        
        Args:
            browser: Browser instance (uses internal if not provided)
            **extra_options: Additional context options to merge
        
        Returns:
            BrowserContext instance
        """
        if browser is None:
            browser = self.launch_browser()
        
        context_options = self.get_context_options()
        context_options.update(extra_options)
        
        logger.debug(f"Creating context with options: {context_options}")
        
        context = browser.new_context(**context_options)
        
        # Start tracing if configured
        if self.config.trace_on_failure:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            logger.debug("Tracing started for context")
        
        self._contexts.append(context)
        return context
    
    @allure.step("Create new page")
    def create_page(
        self,
        context: Optional[BrowserContext] = None,
    ) -> Page:
        if context is None:
            context = self.create_context()
        
        page = context.new_page()
        
        # Set default timeout
        page.set_default_timeout(self.config.timeout)
        page.set_default_navigation_timeout(self.config.timeout)
        
        logger.debug(f"Created new page with timeout: {self.config.timeout}ms")
        
        self._pages.append(page)
        return page
    
    def stop_tracing(
        self,
        context: BrowserContext,
        save_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Stop tracing and optionally save to file.
        
        Args:
            context: The context to stop tracing for
            save_path: Optional path to save trace file
        
        Returns:
            Trace data as bytes if no save_path provided
        """
        if not self.config.trace_on_failure:
            return None
        
        try:
            if save_path:
                context.tracing.stop(path=save_path)
                logger.info(f"Trace saved to: {save_path}")
                return None
            else:
                import tempfile
                temp_path = tempfile.mktemp(suffix=".zip")
                context.tracing.stop(path=temp_path)
                
                with open(temp_path, "rb") as f:
                    trace_data = f.read()
                
                os.unlink(temp_path)
                return trace_data
        except Exception as e:
            logger.warning(f"Failed to stop tracing: {e}")
            return None
    
    def close_page(self, page: Page) -> None:
        """Close a specific page."""
        try:
            if page in self._pages:
                self._pages.remove(page)
            page.close()
        except Exception as e:
            logger.warning(f"Error closing page: {e}")
    
    def close_context(self, context: BrowserContext) -> None:
        """Close a specific context."""
        try:
            if context in self._contexts:
                self._contexts.remove(context)
            context.close()
        except Exception as e:
            logger.warning(f"Error closing context: {e}")
    
    def close(self) -> None:
        """Close browser and cleanup all resources."""
        logger.info("Closing browser factory resources...")
        
        # Close all pages
        for page in self._pages[:]:
            try:
                page.close()
            except Exception:
                pass
        self._pages.clear()
        
        # Close all contexts
        for context in self._contexts[:]:
            try:
                context.close()
            except Exception:
                pass
        self._contexts.clear()
        
        # Close browser
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        
        # Stop playwright
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        
        logger.info("Browser factory resources cleaned up")
    
    def __enter__(self) -> "BrowserFactory":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Singleton instance for session-scoped usage
_factory_instance: Optional[BrowserFactory] = None


def get_browser_factory(
    config: Optional[Dict[str, Any]] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    force_new: bool = False,
) -> BrowserFactory:
    """
    Get or create a BrowserFactory instance.
    
    Args:
        config: Browser configuration dictionary
        cli_overrides: CLI parameter overrides
        force_new: Force creation of new instance
    
    Returns:
        BrowserFactory instance
    """
    global _factory_instance
    
    if _factory_instance is None or force_new:
        if config is None:
            config = {}
        _factory_instance = BrowserFactory(config, cli_overrides)
    
    return _factory_instance


def close_browser_factory() -> None:
    """Close the global browser factory instance."""
    global _factory_instance
    
    if _factory_instance:
        _factory_instance.close()
        _factory_instance = None

