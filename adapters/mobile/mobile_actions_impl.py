"""Appium implementation for mobile automation actions."""
from typing import Optional
import allure
from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

from adapters.base import BaseMobileActions


class AppiumMobileActions(BaseMobileActions):
    """Appium-based mobile automation implementation."""

    def __init__(self, driver: WebDriver):
        """
        Initialize with an Appium driver instance.

        Args:
            driver: Appium WebDriver object
        """
        self.driver = driver
        self._default_timeout = 30

    def _get_locator_strategy(self, locator: str) -> tuple:
        """
        Parse locator string and return appropriate strategy and value.

        Supported formats:
            - id=element_id
            - xpath=//xpath/expression
            - accessibility_id=acc_id
            - class=class_name
            - name=element_name
            - css=css_selector (for web views)
            - android_uiautomator=expression
            - ios_predicate=expression
            - ios_class_chain=expression
        """
        if "=" not in locator:
            # Default to accessibility_id if no strategy specified
            return AppiumBy.ACCESSIBILITY_ID, locator

        strategy, value = locator.split("=", 1)
        strategy = strategy.lower().strip()

        strategy_map = {
            "id": AppiumBy.ID,
            "xpath": AppiumBy.XPATH,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "class": AppiumBy.CLASS_NAME,
            "name": AppiumBy.NAME,
            "css": AppiumBy.CSS_SELECTOR,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "ios_predicate": AppiumBy.IOS_PREDICATE,
            "ios_class_chain": AppiumBy.IOS_CLASS_CHAIN,
        }

        return strategy_map.get(strategy, AppiumBy.ACCESSIBILITY_ID), value

    def _find_element(self, locator: str):
        by, value = self._get_locator_strategy(locator)
        return self.driver.find_element(by, value)

    def _find_elements(self, locator: str):
        by, value = self._get_locator_strategy(locator)
        return self.driver.find_elements(by, value)

    def tap(self, locator: str) -> None:
        with allure.step(f"Tap element: {locator}"):
            logger.info(f"Tapping element: {locator}")
            element = self._find_element(locator)
            element.click()

    def send_keys(self, locator: str, text: str) -> None:
        with allure.step(f"Send keys '{text}' to: {locator}"):
            logger.info(f"Sending keys to: {locator}")
            element = self._find_element(locator)
            element.clear()
            element.send_keys(text)

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500,
    ) -> None:
        """Perform swipe gesture."""
        with allure.step(
            f"Swipe from ({start_x}, {start_y}) to ({end_x}, {end_y})"
        ):
            logger.info(
                f"Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y})"
            )
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def scroll_to_element(self, locator: str, max_scrolls: int = 10) -> None:
        with allure.step(f"Scroll to element: {locator}"):
            logger.info(f"Scrolling to element: {locator}")
            screen_size = self.driver.get_window_size()
            start_x = screen_size["width"] // 2
            start_y = int(screen_size["height"] * 0.8)
            end_y = int(screen_size["height"] * 0.2)

            for i in range(max_scrolls):
                try:
                    element = self._find_element(locator)
                    if element.is_displayed():
                        logger.info(f"Element found after {i} scrolls")
                        return
                except NoSuchElementException:
                    pass

                self.swipe(start_x, start_y, start_x, end_y, 500)

            raise NoSuchElementException(
                f"Element {locator} not found after {max_scrolls} scrolls"
            )

    def get_text(self, locator: str) -> str:
        with allure.step(f"Get text from: {locator}"):
            element = self._find_element(locator)
            text = element.text or element.get_attribute("text") or ""
            logger.info(f"Got text from {locator}: {text[:50]}...")
            return text

    def is_displayed(self, locator: str) -> bool:
        with allure.step(f"Check if displayed: {locator}"):
            try:
                element = self._find_element(locator)
                is_visible = element.is_displayed()
                logger.info(f"Element displayed status for {locator}: {is_visible}")
                return is_visible
            except NoSuchElementException:
                logger.info(f"Element not found: {locator}")
                return False

    def take_screenshot(self, name: str) -> bytes:
        with allure.step(f"Take screenshot: {name}"):
            logger.info(f"Taking screenshot: {name}")
            screenshot = self.driver.get_screenshot_as_png()
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
            return screenshot

    def wait_for_element(self, locator: str, timeout: float = 30) -> None:
        with allure.step(f"Wait for element: {locator}"):
            logger.info(f"Waiting for element: {locator}")
            by, value = self._get_locator_strategy(locator)
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )

    def wait_for_element_visible(self, locator: str, timeout: float = 30) -> None:
        with allure.step(f"Wait for element visible: {locator}"):
            logger.info(f"Waiting for element visible: {locator}")
            by, value = self._get_locator_strategy(locator)
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )

    def wait_for_element_clickable(self, locator: str, timeout: float = 30) -> None:
        with allure.step(f"Wait for element clickable: {locator}"):
            logger.info(f"Waiting for element clickable: {locator}")
            by, value = self._get_locator_strategy(locator)
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )

    def hide_keyboard(self) -> None:
        with allure.step("Hide keyboard"):
            logger.info("Hiding keyboard")
            try:
                self.driver.hide_keyboard()
            except Exception as e:
                logger.warning(f"Could not hide keyboard: {e}")

    def get_device_info(self) -> dict:
        with allure.step("Get device info"):
            capabilities = self.driver.capabilities
            info = {
                "platform_name": capabilities.get("platformName"),
                "platform_version": capabilities.get("platformVersion"),
                "device_name": capabilities.get("deviceName"),
                "udid": capabilities.get("udid"),
                "automation_name": capabilities.get("automationName"),
            }
            logger.info(f"Device info: {info}")
            return info

    def long_press(self, locator: str, duration: int = 1000) -> None:
        with allure.step(f"Long press: {locator}"):
            logger.info(f"Long pressing element: {locator}")
            element = self._find_element(locator)
            # Using touch actions for long press
            from appium.webdriver.common.touch_action import TouchAction
            action = TouchAction(self.driver)
            action.long_press(element, duration=duration).release().perform()

    def get_attribute(self, locator: str, attribute: str) -> Optional[str]:
        with allure.step(f"Get attribute '{attribute}' from: {locator}"):
            element = self._find_element(locator)
            value = element.get_attribute(attribute)
            logger.info(f"Got attribute {attribute}: {value}")
            return value

    def set_value(self, locator: str, value: str) -> None:
        with allure.step(f"Set value '{value}' on: {locator}"):
            logger.info(f"Setting value on: {locator}")
            element = self._find_element(locator)
            element.set_value(value)

    def back(self) -> None:
        with allure.step("Press back button"):
            logger.info("Pressing back button")
            self.driver.back()

    def launch_app(self) -> None:
        with allure.step("Launch app"):
            logger.info("Launching app")
            self.driver.activate_app(
                self.driver.capabilities.get("appPackage")
                or self.driver.capabilities.get("bundleId")
            )

    def close_app(self) -> None:
        with allure.step("Close app"):
            logger.info("Closing app")
            self.driver.terminate_app(
                self.driver.capabilities.get("appPackage")
                or self.driver.capabilities.get("bundleId")
            )

    def reset_app(self) -> None:
        with allure.step("Reset app"):
            logger.info("Resetting app")
            self.close_app()
            self.launch_app()

    def get_page_source(self) -> str:
        return self.driver.page_source

    def get_context(self) -> str:
        return self.driver.current_context

    def switch_context(self, context: str) -> None:
        with allure.step(f"Switch to context: {context}"):
            logger.info(f"Switching to context: {context}")
            self.driver.switch_to.context(context)

    def get_contexts(self) -> list:
        return self.driver.contexts

