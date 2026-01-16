"""API client wrapper providing high-level API operations."""
from typing import Optional, Any
import allure
from loguru import logger

from adapters.api import RequestsAPIActions


class APIClient:
    """
    High-level API client for interacting with the application API.
    
    Provides business-level methods that encapsulate raw API calls
    and common patterns like authentication flows.
    """

    def __init__(self, base_url: str, timeout: float = 30):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API
            timeout: Default timeout in seconds
        """
        self.api = RequestsAPIActions(base_url, timeout)
        self._token: Optional[str] = None

    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticate and store the access token.

        Args:
            username: Username for authentication
            password: Password for authentication

        Returns:
            Authentication response data
        """
        with allure.step(f"Authenticate user: {username}"):
            logger.info(f"Authenticating user: {username}")
            
            response = self.api.post(
                "/auth/login",
                json_data={"username": username, "password": password},
            )
            
            if response.status_code == 200:
                data = response.json()
                self._token = data.get("access_token") or data.get("token")
                if self._token:
                    self.api.set_auth_token(self._token)
                    logger.info("Authentication successful, token stored")
                return data
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                raise AuthenticationError(
                    f"Authentication failed with status {response.status_code}"
                )

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        **extra_fields,
    ) -> dict:
        """
        Register a new user.

        Args:
            username: Username for the new user
            email: Email address
            password: Password
            **extra_fields: Additional fields for registration

        Returns:
            Registration response data
        """
        with allure.step(f"Register user: {username}"):
            logger.info(f"Registering user: {username}")
            
            payload = {
                "username": username,
                "email": email,
                "password": password,
                **extra_fields,
            }
            
            response = self.api.post("/auth/register", json_data=payload)
            return response.json()

    def get_current_user(self) -> dict:
        """
        Get the current authenticated user's profile.

        Returns:
            User profile data
        """
        with allure.step("Get current user profile"):
            logger.info("Fetching current user profile")
            response = self.api.get("/users/me")
            self.api.assert_status_code(200)
            return response.json()

    def update_user(self, user_id: str, **fields) -> dict:
        """
        Update a user's information.

        Args:
            user_id: ID of the user to update
            **fields: Fields to update

        Returns:
            Updated user data
        """
        with allure.step(f"Update user: {user_id}"):
            logger.info(f"Updating user: {user_id}")
            response = self.api.patch(f"/users/{user_id}", json_data=fields)
            return response.json()

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: ID of the user to delete

        Returns:
            True if deletion was successful
        """
        with allure.step(f"Delete user: {user_id}"):
            logger.info(f"Deleting user: {user_id}")
            response = self.api.delete(f"/users/{user_id}")
            return response.status_code in (200, 204)

    def get_resource(self, resource_type: str, resource_id: str) -> dict:
        """
        Get a specific resource by type and ID.

        Args:
            resource_type: Type of resource (e.g., 'posts', 'comments')
            resource_id: ID of the resource

        Returns:
            Resource data
        """
        with allure.step(f"Get {resource_type}/{resource_id}"):
            logger.info(f"Fetching {resource_type}/{resource_id}")
            response = self.api.get(f"/{resource_type}/{resource_id}")
            return response.json()

    def list_resources(
        self,
        resource_type: str,
        page: int = 1,
        per_page: int = 20,
        **filters,
    ) -> dict:
        """
        List resources with pagination and filters.

        Args:
            resource_type: Type of resource to list
            page: Page number
            per_page: Items per page
            **filters: Additional filter parameters

        Returns:
            List response with data and pagination info
        """
        with allure.step(f"List {resource_type} (page {page})"):
            logger.info(f"Listing {resource_type}, page {page}")
            
            params = {"page": page, "per_page": per_page, **filters}
            response = self.api.get(f"/{resource_type}", params=params)
            return response.json()

    def create_resource(self, resource_type: str, **data) -> dict:
        """
        Create a new resource.

        Args:
            resource_type: Type of resource to create
            **data: Resource data

        Returns:
            Created resource data
        """
        with allure.step(f"Create {resource_type}"):
            logger.info(f"Creating {resource_type}")
            response = self.api.post(f"/{resource_type}", json_data=data)
            return response.json()

    def update_resource(
        self,
        resource_type: str,
        resource_id: str,
        **data,
    ) -> dict:
        """
        Update an existing resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of resource to update
            **data: Updated resource data

        Returns:
            Updated resource data
        """
        with allure.step(f"Update {resource_type}/{resource_id}"):
            logger.info(f"Updating {resource_type}/{resource_id}")
            response = self.api.put(
                f"/{resource_type}/{resource_id}",
                json_data=data,
            )
            return response.json()

    def delete_resource(self, resource_type: str, resource_id: str) -> bool:
        """
        Delete a resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of resource to delete

        Returns:
            True if deletion was successful
        """
        with allure.step(f"Delete {resource_type}/{resource_id}"):
            logger.info(f"Deleting {resource_type}/{resource_id}")
            response = self.api.delete(f"/{resource_type}/{resource_id}")
            return response.status_code in (200, 204)

    def health_check(self) -> bool:
        """
        Check API health status.

        Returns:
            True if API is healthy
        """
        with allure.step("API health check"):
            logger.info("Performing health check")
            try:
                response = self.api.get("/health")
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return False

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._token is not None

    @property
    def token(self) -> Optional[str]:
        """Get the current authentication token."""
        return self._token

    def clear_auth(self) -> None:
        """Clear authentication."""
        self._token = None
        self.api.remove_header("Authorization")

    def close(self) -> None:
        """Close the API client session."""
        self.api.close()


class AuthenticationError(Exception):
    """Exception raised for authentication failures."""
    pass

