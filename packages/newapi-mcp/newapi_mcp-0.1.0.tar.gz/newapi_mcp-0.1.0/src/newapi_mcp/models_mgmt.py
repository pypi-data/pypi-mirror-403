"""Model management tools for New API MCP."""

from typing import Any

from .client import NewAPIClient


class ModelTools:
    """Model management tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client

    def get_all_models(
        self,
        page: int = 1,
        limit: int = 10,
        sort: str = "-id",
    ) -> dict[str, Any]:
        """Get all models with pagination."""
        if page < 1 or limit < 1 or limit > 100:
            raise ValueError("Invalid pagination parameters")

        return self.client.get(
            "/api/models",
            auth_required=True,
            params={
                "page": page,
                "limit": limit,
                "sort": sort,
            },
        )
