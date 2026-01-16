"""API endpoint constants and builders."""


class Endpoints:
    """
    Centralized endpoint definitions for the API.
    
    Provides a single source of truth for all API endpoints,
    making maintenance easier and reducing magic strings.
    """

    # Authentication endpoints
    class Auth:
        LOGIN = "/auth/login"
        LOGOUT = "/auth/logout"
        REGISTER = "/auth/register"
        REFRESH_TOKEN = "/auth/refresh"
        FORGOT_PASSWORD = "/auth/forgot-password"
        RESET_PASSWORD = "/auth/reset-password"
        VERIFY_EMAIL = "/auth/verify-email"

    # User endpoints
    class Users:
        BASE = "/users"
        ME = "/users/me"
        
        @staticmethod
        def by_id(user_id: str) -> str:
            return f"/users/{user_id}"
        
        @staticmethod
        def profile(user_id: str) -> str:
            return f"/users/{user_id}/profile"
        
        @staticmethod
        def avatar(user_id: str) -> str:
            return f"/users/{user_id}/avatar"

    # Common resource endpoints
    class Posts:
        BASE = "/posts"
        
        @staticmethod
        def by_id(post_id: str) -> str:
            return f"/posts/{post_id}"
        
        @staticmethod
        def comments(post_id: str) -> str:
            return f"/posts/{post_id}/comments"

    class Comments:
        BASE = "/comments"
        
        @staticmethod
        def by_id(comment_id: str) -> str:
            return f"/comments/{comment_id}"

    # File upload endpoints
    class Files:
        UPLOAD = "/files/upload"
        
        @staticmethod
        def download(file_id: str) -> str:
            return f"/files/{file_id}"
        
        @staticmethod
        def delete(file_id: str) -> str:
            return f"/files/{file_id}"

    # System endpoints
    class System:
        HEALTH = "/health"
        VERSION = "/version"
        CONFIG = "/config"

    @staticmethod
    def build_query_string(**params) -> str:
        """
        Build a query string from parameters.

        Args:
            **params: Query parameters

        Returns:
            Query string (without leading ?)
        """
        filtered = {k: v for k, v in params.items() if v is not None}
        return "&".join(f"{k}={v}" for k, v in filtered.items())

