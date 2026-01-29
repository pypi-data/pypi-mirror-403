"""User management tools for New API MCP."""

from typing import Any

from .client import NewAPIClient
from .validators import validate_password, validate_username


class UserTools:
    """User management tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client

    def get_all_users(
        self,
        page: int = 1,
        limit: int = 10,
        sort: str = "-id",
    ) -> dict[str, Any]:
        """Get all users with pagination."""
        if page < 1 or limit < 1 or limit > 100:
            raise ValueError("Invalid pagination parameters")

        return self.client.get(
            "/api/user",
            auth_required=True,
            params={
                "page": page,
                "limit": limit,
                "sort": sort,
            },
        )

    def create_user(
        self,
        username: str,
        password: str,
        group: str = "default",
    ) -> dict[str, Any]:
        """Create a new user."""
        if not validate_username(username):
            raise ValueError(
                f"Invalid username: {username}. "
                "Must be 3-32 characters, alphanumeric, underscore, or hyphen."
            )

        if not validate_password(password):
            raise ValueError("Invalid password. Must be 6-128 characters with letters and numbers.")

        return self.client.post(
            "/api/user",
            {
                "username": username,
                "password": password,
                "group": group,
            },
            auth_required=True,
        )

    def update_user(
        self,
        user_id: int,
        username: str | None = None,
        password: str | None = None,
        group: str | None = None,
    ) -> dict[str, Any]:
        """Update user information."""
        if user_id < 1:
            raise ValueError("Invalid user ID")

        data: dict[str, Any] = {}
        if username is not None:
            data["username"] = username
        if password is not None:
            data["password"] = password
        if group is not None:
            data["group"] = group

        if not data:
            raise ValueError("At least one field must be provided")

        return self.client.put(
            f"/api/user/{user_id}",
            data,
            auth_required=True,
        )

    def delete_user(self, user_id: int) -> dict[str, Any]:
        """Delete a user."""
        if user_id < 1:
            raise ValueError("Invalid user ID")

        return self.client.post(
            f"/api/user/{user_id}",
            {"action": "delete"},
            auth_required=True,
        )
