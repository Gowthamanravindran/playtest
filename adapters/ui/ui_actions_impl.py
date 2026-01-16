"""Playwright implementation for UI automation actions."""
from typing import Optional
import allure
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeout
from loguru import logger

from adapters.base import BaseUIActions


class PlaywrightUIActions(BaseUIActions):
    def __init__(self, page: Page):
        self.page = page
        self._default_timeout = 30000  # 30 seconds in milliseconds

    def navigate(self, url: str) -> None:
        with allure.step(f"Navigate to: {url}"):
            logger.info(f"Navigating to: {url}")
            self.page.goto(url, wait_until="domcontentloaded")

    def click(self, locator: str) -> None:
        with allure.step(f"Click element: {locator}"):
            logger.info(f"Clicking element: {locator}")
            self.page.locator(locator).click()

    def fill(self, locator: str, text: str) -> None:
        with allure.step(f"Fill '{text}' into: {locator}"):
            logger.info(f"Filling text into: {locator}")
            self.page.locator(locator).fill(text)

    def get_text(self, locator: str) -> str:
        with allure.step(f"Get text from: {locator}"):
            text = self.page.locator(locator).text_content() or ""
            logger.info(f"Got text from {locator}: {text[:50]}...")
            return text

    def is_visible(self, locator: str, timeout: Optional[float] = None) -> bool:
        with allure.step(f"Check visibility: {locator}"):
            try:
                timeout_ms = int(timeout * 1000) if timeout else self._default_timeout
                self.page.locator(locator).wait_for(
                    state="visible", timeout=timeout_ms
                )
                logger.info(f"Element is visible: {locator}")
                return True
            except PlaywrightTimeout:
                logger.info(f"Element not visible: {locator}")
                return False

    def wait_for_element(self, locator: str, timeout: float = 30) -> None:
        with allure.step(f"Wait for element: {locator}"):
            logger.info(f"Waiting for element: {locator}")
            self.page.locator(locator).wait_for(
                state="visible", timeout=int(timeout * 1000)
            )

    def take_screenshot(self, name: str) -> bytes:
        with allure.step(f"Take screenshot: {name}"):
            logger.info(f"Taking screenshot: {name}")
            screenshot = self.page.screenshot()
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
            return screenshot

    def select_option(self, locator: str, value: str) -> None:
        with allure.step(f"Select '{value}' from: {locator}"):
            logger.info(f"Selecting option '{value}' from: {locator}")
            self.page.locator(locator).select_option(value)

    def get_attribute(self, locator: str, attribute: str) -> Optional[str]:
        with allure.step(f"Get attribute '{attribute}' from: {locator}"):
            value = self.page.locator(locator).get_attribute(attribute)
            logger.info(f"Got attribute {attribute}: {value}")
            return value

    def hover(self, locator: str) -> None:
        with allure.step(f"Hover over: {locator}"):
            logger.info(f"Hovering over: {locator}")
            self.page.locator(locator).hover()

    def double_click(self, locator: str) -> None:
        with allure.step(f"Double click: {locator}"):
            logger.info(f"Double clicking: {locator}")
            self.page.locator(locator).dblclick()

    def right_click(self, locator: str) -> None:
        with allure.step(f"Right click: {locator}"):
            logger.info(f"Right clicking: {locator}")
            self.page.locator(locator).click(button="right")

    def press_key(self, key: str) -> None:
        with allure.step(f"Press key: {key}"):
            logger.info(f"Pressing key: {key}")
            self.page.keyboard.press(key)

    def get_url(self) -> str:
        return self.page.url

    def get_title(self) -> str:
        return self.page.title()

    def wait_for_url(self, url_pattern: str, timeout: float = 30) -> None:
        with allure.step(f"Wait for URL pattern: {url_pattern}"):
            logger.info(f"Waiting for URL: {url_pattern}")
            self.page.wait_for_url(url_pattern, timeout=int(timeout * 1000))

    def wait_for_load_state(self, state: str = "load") -> None:
        with allure.step(f"Wait for load state: {state}"):
            logger.info(f"Waiting for load state: {state}")
            self.page.wait_for_load_state(state)

    def execute_script(self, script: str, *args) -> any:
        with allure.step("Execute JavaScript"):
            logger.info(f"Executing script: {script[:100]}...")
            return self.page.evaluate(script, *args)

    def get_element_count(self, locator: str) -> int:
        with allure.step(f"Get element count: {locator}"):
            count = self.page.locator(locator).count()
            logger.info(f"Element count for {locator}: {count}")
            return count

    def expect_visible(self, locator: str, timeout: float = 30) -> None:
        with allure.step(f"Expect visible: {locator}"):
            logger.info(f"Expecting element visible: {locator}")
            expect(self.page.locator(locator)).to_be_visible(
                timeout=int(timeout * 1000)
            )

    def expect_text(self, locator: str, text: str, timeout: float = 30) -> None:
        with allure.step(f"Expect text '{text}' in: {locator}"):
            logger.info(f"Expecting text '{text}' in element: {locator}")
            expect(self.page.locator(locator)).to_contain_text(
                text, timeout=int(timeout * 1000)
            )
