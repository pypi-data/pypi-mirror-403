"""Channel management tools for New API MCP."""

from typing import Any

from .client import NewAPIClient


class ChannelTools:
    """Channel management tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client

    def get_all_channels(
        self,
        page: int = 1,
        limit: int = 10,
        sort: str = "-id",
    ) -> dict[str, Any]:
        """Get all channels with pagination."""
        if page < 1 or limit < 1 or limit > 100:
            raise ValueError("Invalid pagination parameters")

        return self.client.get(
            "/api/channel",
            auth_required=True,
            params={
                "page": page,
                "limit": limit,
                "sort": sort,
            },
        )

    def get_channel_list(self) -> dict[str, Any]:
        """Get simplified channel list."""
        try:
            response = self.get_all_channels(page=1, limit=100)
            if response.get("success"):
                channels = [
                    {
                        "id": ch.get("id"),
                        "name": ch.get("name"),
                        "status": ch.get("status"),
                    }
                    for ch in response.get("data", [])
                ]
                return {
                    "success": True,
                    "data": channels,
                    "total": len(channels),
                    "message": "ok",
                }
            return response
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": str(e),
                "code": 500,
            }

    def get_channel_by_name(self, name: str) -> dict[str, Any]:
        """Get channel by name."""
        try:
            response = self.get_all_channels(page=1, limit=100)
            if response.get("success"):
                for ch in response.get("data", []):
                    if ch.get("name") == name:
                        return {
                            "success": True,
                            "data": {
                                "id": ch.get("id"),
                                "name": ch.get("name"),
                                "type": ch.get("type"),
                                "priority": ch.get("priority"),
                                "status": ch.get("status"),
                            },
                            "message": "ok",
                        }
                return {
                    "success": False,
                    "data": None,
                    "message": f"Channel '{name}' not found",
                    "code": 404,
                }
            return response
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": str(e),
                "code": 500,
            }

    def create_channel(
        self,
        name: str,
        channel_type: int,
        key: str,
        priority: int = 1,
        status: int = 1,
    ) -> dict[str, Any]:
        """Create a new channel."""
        if not name or len(name) > 100:
            raise ValueError("Invalid channel name")
        if channel_type < 1:
            raise ValueError("Invalid channel type")
        if not key or len(key) > 1000:
            raise ValueError("Invalid channel key")
        if priority < 1 or priority > 100:
            raise ValueError("Invalid priority")
        if status not in (0, 1):
            raise ValueError("Invalid status")

        return self.client.post(
            "/api/channel",
            {
                "name": name,
                "type": channel_type,
                "key": key,
                "priority": priority,
                "status": status,
            },
            auth_required=True,
        )

    def update_channel(
        self,
        channel_id: int,
        name: str | None = None,
        key: str | None = None,
        priority: int | None = None,
        status: int | None = None,
    ) -> dict[str, Any]:
        """Update channel configuration."""
        if channel_id < 1:
            raise ValueError("Invalid channel ID")

        data: dict[str, Any] = {}
        if name is not None:
            if not name or len(name) > 100:
                raise ValueError("Invalid channel name")
            data["name"] = name
        if key is not None:
            if not key or len(key) > 1000:
                raise ValueError("Invalid channel key")
            data["key"] = key
        if priority is not None:
            if priority < 1 or priority > 100:
                raise ValueError("Invalid priority")
            data["priority"] = priority
        if status is not None:
            if status not in (0, 1):
                raise ValueError("Invalid status")
            data["status"] = status

        if not data:
            raise ValueError("At least one field must be provided")

        return self.client.put(
            f"/api/channel/{channel_id}",
            data,
            auth_required=True,
        )

    def test_channel(self, channel_id: int) -> dict[str, Any]:
        """Test channel connectivity."""
        if channel_id < 1:
            raise ValueError("Invalid channel ID")

        return self.client.get(
            f"/api/channel/test/{channel_id}",
            auth_required=True,
        )

    def get_channel_status(self, channel_id: int) -> dict[str, Any]:
        """Get channel status."""
        if channel_id < 1:
            raise ValueError("Invalid channel ID")

        try:
            response = self.test_channel(channel_id)
            return {
                "success": True,
                "data": {
                    "channel_id": channel_id,
                    "status": "active" if response.get("success") else "inactive",
                    "health": "healthy" if response.get("success") else "unhealthy",
                },
                "message": "ok",
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": str(e),
                "code": 500,
            }
