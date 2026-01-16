"""Requests/HTTPX implementation for API automation actions."""
from typing import Optional, Any, Union
import allure
import requests
from requests import Response
from loguru import logger
import json

from adapters.base import BaseAPIActions


class RequestsAPIActions(BaseAPIActions):
    """Requests-based API automation implementation."""

    def __init__(self, base_url: str, timeout: float = 30):
        """
        Initialize with base URL and default timeout.

        Args:
            base_url: Base URL for all API requests
            timeout: Default timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._last_response: Optional[Response] = None
        self._default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session.headers.update(self._default_headers)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _log_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Any = None,
    ) -> None:
        """Log request details."""
        logger.info(f"{method} {url}")
        if params:
            logger.debug(f"Params: {params}")
        if data:
            logger.debug(f"Body: {json.dumps(data, indent=2)[:500]}")

    def _log_response(self, response: Response) -> None:
        """Log response details."""
        logger.info(f"Response: {response.status_code}")
        try:
            body = response.json()
            logger.debug(f"Response body: {json.dumps(body, indent=2)[:500]}")
        except (json.JSONDecodeError, ValueError):
            logger.debug(f"Response text: {response.text[:500]}")

    def _attach_to_allure(
        self,
        method: str,
        url: str,
        response: Response,
        request_body: Any = None,
    ) -> None:
        """Attach request/response details to Allure report."""
        # Attach request details
        request_details = {
            "method": method,
            "url": url,
            "headers": dict(self.session.headers),
        }
        if request_body:
            request_details["body"] = request_body

        allure.attach(
            json.dumps(request_details, indent=2, default=str),
            name="Request",
            attachment_type=allure.attachment_type.JSON,
        )

        # Attach response details
        response_details = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }
        try:
            response_details["body"] = response.json()
        except (json.JSONDecodeError, ValueError):
            response_details["body"] = response.text

        allure.attach(
            json.dumps(response_details, indent=2, default=str),
            name="Response",
            attachment_type=allure.attachment_type.JSON,
        )

    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Response:
        """Perform GET request."""
        url = self._build_url(endpoint)
        with allure.step(f"GET {endpoint}"):
            self._log_request("GET", url, headers, params)

            self._last_response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            self._log_response(self._last_response)
            self._attach_to_allure("GET", url, self._last_response)
            return self._last_response

    def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Response:
        """Perform POST request."""
        url = self._build_url(endpoint)
        body = json_data or data
        with allure.step(f"POST {endpoint}"):
            self._log_request("POST", url, headers, data=body)

            self._last_response = self.session.post(
                url,
                data=data if not json_data else None,
                json=json_data,
                headers=headers,
                timeout=self.timeout,
            )

            self._log_response(self._last_response)
            self._attach_to_allure("POST", url, self._last_response, body)
            return self._last_response

    def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Response:
        """Perform PUT request."""
        url = self._build_url(endpoint)
        body = json_data or data
        with allure.step(f"PUT {endpoint}"):
            self._log_request("PUT", url, headers, data=body)

            self._last_response = self.session.put(
                url,
                data=data if not json_data else None,
                json=json_data,
                headers=headers,
                timeout=self.timeout,
            )

            self._log_response(self._last_response)
            self._attach_to_allure("PUT", url, self._last_response, body)
            return self._last_response

    def patch(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Response:
        """Perform PATCH request."""
        url = self._build_url(endpoint)
        body = json_data or data
        with allure.step(f"PATCH {endpoint}"):
            self._log_request("PATCH", url, headers, data=body)

            self._last_response = self.session.patch(
                url,
                data=data if not json_data else None,
                json=json_data,
                headers=headers,
                timeout=self.timeout,
            )

            self._log_response(self._last_response)
            self._attach_to_allure("PATCH", url, self._last_response, body)
            return self._last_response

    def delete(
        self,
        endpoint: str,
        headers: Optional[dict] = None,
    ) -> Response:
        """Perform DELETE request."""
        url = self._build_url(endpoint)
        with allure.step(f"DELETE {endpoint}"):
            self._log_request("DELETE", url, headers)

            self._last_response = self.session.delete(
                url,
                headers=headers,
                timeout=self.timeout,
            )

            self._log_response(self._last_response)
            self._attach_to_allure("DELETE", url, self._last_response)
            return self._last_response

    def set_auth_token(self, token: str) -> None:
        """Set authentication token for requests."""
        with allure.step("Set authentication token"):
            logger.info("Setting auth token")
            self.session.headers["Authorization"] = f"Bearer {token}"

    def set_basic_auth(self, username: str, password: str) -> None:
        """Set basic authentication."""
        with allure.step("Set basic authentication"):
            logger.info(f"Setting basic auth for user: {username}")
            self.session.auth = (username, password)

    def set_header(self, key: str, value: str) -> None:
        """Set a custom header."""
        logger.info(f"Setting header: {key}")
        self.session.headers[key] = value

    def remove_header(self, key: str) -> None:
        """Remove a header."""
        logger.info(f"Removing header: {key}")
        self.session.headers.pop(key, None)

    def get_last_response(self) -> Optional[Response]:
        """Get the last response object."""
        return self._last_response

    def get_last_status_code(self) -> Optional[int]:
        """Get the last response status code."""
        if self._last_response:
            return self._last_response.status_code
        return None

    def get_last_json(self) -> Optional[dict]:
        """Get the last response as JSON."""
        if self._last_response:
            try:
                return self._last_response.json()
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    def assert_status_code(self, expected: int) -> None:
        """Assert the last response has expected status code."""
        with allure.step(f"Assert status code is {expected}"):
            actual = self.get_last_status_code()
            assert actual == expected, (
                f"Expected status code {expected}, got {actual}"
            )

    def assert_json_field(self, field: str, expected: Any) -> None:
        """Assert a field in the last JSON response."""
        with allure.step(f"Assert JSON field '{field}' equals {expected}"):
            json_data = self.get_last_json()
            assert json_data is not None, "Response is not valid JSON"
            
            # Support nested fields with dot notation
            keys = field.split(".")
            value = json_data
            for key in keys:
                assert key in value, f"Field '{key}' not found in response"
                value = value[key]
            
            assert value == expected, (
                f"Expected '{field}' to be {expected}, got {value}"
            )

    def upload_file(
        self,
        endpoint: str,
        file_path: str,
        file_field: str = "file",
        additional_data: Optional[dict] = None,
    ) -> Response:
        """Upload a file."""
        url = self._build_url(endpoint)
        with allure.step(f"Upload file to {endpoint}"):
            logger.info(f"Uploading file: {file_path}")

            with open(file_path, "rb") as f:
                files = {file_field: f}
                self._last_response = self.session.post(
                    url,
                    files=files,
                    data=additional_data,
                    timeout=self.timeout,
                )

            self._log_response(self._last_response)
            return self._last_response

    def close(self) -> None:
        """Close the session."""
        self.session.close()

