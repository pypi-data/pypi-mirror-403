"""Token management tools for New API MCP."""

from typing import Any

from .client import NewAPIClient
from .validators import validate_quota, validate_token_name


class TokenTools:
    """Token management tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client

    def create_token(
        self,
        name: str,
        unlimited_quota: bool = False,
        remain_quota: int | None = None,
    ) -> dict[str, Any]:
        """Create a new API token."""
        if not validate_token_name(name):
            raise ValueError(f"Invalid token name: {name}. Must be 1-64 characters.")

        if not unlimited_quota and remain_quota is None:
            raise ValueError("remain_quota required when unlimited_quota is False")

        if remain_quota is not None and not validate_quota(remain_quota):
            raise ValueError(f"Invalid quota: {remain_quota}. Must be between 0 and 9999999999.")

        return self.client.post(
            "/api/token",
            {
                "name": name,
                "unlimited_quota": unlimited_quota,
                "remain_quota": remain_quota,
            },
            auth_required=True,
        )
