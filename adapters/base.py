"""Base adapter interfaces defining the contract for all implementations."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseUIActions(ABC):
    """Abstract base class for UI automation actions."""

    @abstractmethod
    def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        pass

    @abstractmethod
    def click(self, locator: str) -> None:
        """Click on an element."""
        pass

    @abstractmethod
    def fill(self, locator: str, text: str) -> None:
        """Fill text into an input field."""
        pass

    @abstractmethod
    def get_text(self, locator: str) -> str:
        """Get text content of an element."""
        pass

    @abstractmethod
    def is_visible(self, locator: str, timeout: Optional[float] = None) -> bool:
        """Check if element is visible."""
        pass

    @abstractmethod
    def wait_for_element(self, locator: str, timeout: float = 30) -> None:
        """Wait for element to be present."""
        pass

    @abstractmethod
    def take_screenshot(self, name: str) -> bytes:
        """Take a screenshot."""
        pass

    @abstractmethod
    def select_option(self, locator: str, value: str) -> None:
        """Select an option from a dropdown."""
        pass

    @abstractmethod
    def get_attribute(self, locator: str, attribute: str) -> Optional[str]:
        """Get attribute value of an element."""
        pass

    @abstractmethod
    def hover(self, locator: str) -> None:
        """Hover over an element."""
        pass


class BaseMobileActions(ABC):
    """Abstract base class for mobile automation actions."""

    @abstractmethod
    def tap(self, locator: str) -> None:
        """Tap on an element."""
        pass

    @abstractmethod
    def send_keys(self, locator: str, text: str) -> None:
        """Send keys to an element."""
        pass

    @abstractmethod
    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500,
    ) -> None:
        """Perform swipe gesture."""
        pass

    @abstractmethod
    def scroll_to_element(self, locator: str) -> None:
        """Scroll until element is visible."""
        pass

    @abstractmethod
    def get_text(self, locator: str) -> str:
        """Get text content of an element."""
        pass

    @abstractmethod
    def is_displayed(self, locator: str) -> bool:
        """Check if element is displayed."""
        pass

    @abstractmethod
    def take_screenshot(self, name: str) -> bytes:
        """Take a screenshot."""
        pass

    @abstractmethod
    def wait_for_element(self, locator: str, timeout: float = 30) -> None:
        """Wait for element to be present."""
        pass

    @abstractmethod
    def hide_keyboard(self) -> None:
        """Hide the on-screen keyboard."""
        pass

    @abstractmethod
    def get_device_info(self) -> dict:
        """Get device information."""
        pass


class BaseAPIActions(ABC):
    """Abstract base class for API automation actions."""

    @abstractmethod
    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """Perform GET request."""
        pass

    @abstractmethod
    def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """Perform POST request."""
        pass

    @abstractmethod
    def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """Perform PUT request."""
        pass

    @abstractmethod
    def patch(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """Perform PATCH request."""
        pass

    @abstractmethod
    def delete(
        self,
        endpoint: str,
        headers: Optional[dict] = None,
    ) -> Any:
        """Perform DELETE request."""
        pass

    @abstractmethod
    def set_auth_token(self, token: str) -> None:
        """Set authentication token for requests."""
        pass

    @abstractmethod
    def get_last_response(self) -> Any:
        """Get the last response object."""
        pass
