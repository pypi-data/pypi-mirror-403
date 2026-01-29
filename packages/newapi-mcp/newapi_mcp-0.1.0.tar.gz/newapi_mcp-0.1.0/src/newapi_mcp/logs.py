"""Log and statistics tools for New API MCP."""

from typing import Any

from .client import NewAPIClient


class LogTools:
    """Log and statistics tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client

    def get_logs(
        self,
        page: int = 1,
        limit: int = 10,
        model: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Get logs with optional filtering."""
        if page < 1 or limit < 1 or limit > 100:
            raise ValueError("Invalid pagination parameters")

        params: dict[str, Any] = {
            "page": page,
            "limit": limit,
        }
        if model:
            params["model"] = model
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return self.client.get(
            "/api/log",
            auth_required=True,
            params=params,
        )

    def get_token_usage(self) -> dict[str, Any]:
        """Get token usage statistics."""
        return self.client.get(
            "/api/usage/token",
            auth_required=True,
        )
