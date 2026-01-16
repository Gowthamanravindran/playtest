"""JSON Schema definitions for API response validation."""
from jsonschema import validate, ValidationError
from typing import Any


# User schema
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": ["string", "integer"]},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "profile": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "avatar_url": {"type": ["string", "null"]},
            },
        },
    },
    "required": ["id", "username", "email"],
}

# Authentication response schema
AUTH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "refresh_token": {"type": "string"},
        "token_type": {"type": "string"},
        "expires_in": {"type": "integer"},
        "user": USER_SCHEMA,
    },
    "required": ["access_token"],
}

# Paginated list response schema
def paginated_schema(item_schema: dict) -> dict:
    """
    Create a paginated response schema.

    Args:
        item_schema: Schema for individual items

    Returns:
        Complete paginated response schema
    """
    return {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": item_schema,
            },
            "pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"},
                    "total": {"type": "integer"},
                    "total_pages": {"type": "integer"},
                },
                "required": ["page", "total"],
            },
        },
        "required": ["data"],
    }


# Error response schema
ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {"type": "string"},
        "message": {"type": "string"},
        "status_code": {"type": "integer"},
        "details": {"type": ["object", "array", "null"]},
    },
    "required": ["message"],
}


def validate_response(data: Any, schema: dict) -> bool:
    """
    Validate response data against a JSON schema.

    Args:
        data: Response data to validate
        schema: JSON schema to validate against

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    validate(instance=data, schema=schema)
    return True


def is_valid_response(data: Any, schema: dict) -> bool:
    """
    Check if response data is valid without raising exception.

    Args:
        data: Response data to validate
        schema: JSON schema to validate against

    Returns:
        True if valid, False otherwise
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError:
        return False

