"""MCP server for New API."""

from mcp.server.fastmcp import FastMCP

from .client import NewAPIClient
from .tools_registry import ToolsRegistry

mcp = FastMCP("New API MCP Server")
client = NewAPIClient()
tools = ToolsRegistry(client)


@mcp.tool()
def get_model_pricing() -> dict:
    """Get all model pricing and ratios."""
    return tools.pricing.get_model_pricing()


@mcp.tool()
def get_model_list() -> dict:
    """Get all model names (simplified)."""
    return tools.pricing.get_model_list()


@mcp.tool()
def get_model_price_by_name(model_name: str) -> dict:
    """Get model price by name."""
    return tools.pricing.get_model_price_by_name(model_name)


@mcp.tool()
def get_models_by_vendor(vendor_id: int) -> dict:
    """Get models by vendor ID."""
    return tools.pricing.get_models_by_vendor(vendor_id)


@mcp.tool()
def get_models_by_ratio_range(min_ratio: float, max_ratio: float) -> dict:
    """Get models by ratio range."""
    return tools.pricing.get_models_by_ratio_range(min_ratio, max_ratio)


@mcp.tool()
def get_pricing_statistics() -> dict:
    """Get pricing statistics."""
    return tools.pricing.get_pricing_statistics()


@mcp.tool()
def search_models(
    keyword: str | None = None,
    vendor_id: int | None = None,
    min_ratio: float | None = None,
    max_ratio: float | None = None,
    limit: int = 10,
) -> dict:
    """Search models with advanced filtering."""
    return tools.model_search.search_models(keyword, vendor_id, min_ratio, max_ratio, limit)


@mcp.tool()
def compare_models(model_names: list[str]) -> dict:
    """Compare multiple models."""
    return tools.model_search.compare_models(model_names)


@mcp.tool()
def get_cheapest_models(limit: int = 10) -> dict:
    """Get cheapest models by ratio."""
    return tools.model_search.get_cheapest_models(limit)


@mcp.tool()
def get_fastest_models(limit: int = 10) -> dict:
    """Get fastest models by completion ratio."""
    return tools.model_search.get_fastest_models(limit)


@mcp.tool()
def update_model_ratio(model_ratios: dict) -> dict:
    """Update model ratios."""
    return tools.pricing.update_model_ratio(model_ratios)


@mcp.tool()
def update_model_price(model_prices: dict) -> dict:
    """Update model prices."""
    return tools.pricing.update_model_price(model_prices)


@mcp.tool()
def get_all_users(page: int = 1, limit: int = 10, sort: str = "-id") -> dict:
    """Get all users with pagination."""
    return tools.users.get_all_users(page, limit, sort)


@mcp.tool()
def create_user(username: str, password: str, group: str = "default") -> dict:
    """Create a new user."""
    return tools.users.create_user(username, password, group)


@mcp.tool()
def update_user(
    user_id: int,
    username: str | None = None,
    password: str | None = None,
    group: str | None = None,
) -> dict:
    """Update user information."""
    return tools.users.update_user(user_id, username, password, group)


@mcp.tool()
def delete_user(user_id: int) -> dict:
    """Delete a user."""
    return tools.users.delete_user(user_id)


@mcp.tool()
def create_token(
    name: str,
    unlimited_quota: bool = False,
    remain_quota: int | None = None,
) -> dict:
    """Create a new API token."""
    return tools.tokens.create_token(name, unlimited_quota, remain_quota)


@mcp.tool()
def get_token_info() -> dict:
    """Get current token information."""
    return tools.token_management.get_token_info()


@mcp.tool()
def estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> dict:
    """Estimate API call cost."""
    return tools.token_management.estimate_cost(model_name, input_tokens, output_tokens)


@mcp.tool()
def list_available_models_for_token() -> dict:
    """List all available models for current token."""
    return tools.token_management.list_available_models_for_token()


@mcp.tool()
def get_all_channels(page: int = 1, limit: int = 10, sort: str = "-id") -> dict:
    """Get all channels with pagination."""
    return tools.channels.get_all_channels(page, limit, sort)


@mcp.tool()
def get_channel_list() -> dict:
    """Get simplified channel list."""
    return tools.channels.get_channel_list()


@mcp.tool()
def get_channel_by_name(name: str) -> dict:
    """Get channel by name."""
    return tools.channels.get_channel_by_name(name)


@mcp.tool()
def create_channel(
    name: str,
    channel_type: int,
    key: str,
    priority: int = 1,
    status: int = 1,
) -> dict:
    """Create a new channel."""
    return tools.channels.create_channel(name, channel_type, key, priority, status)


@mcp.tool()
def update_channel(
    channel_id: int,
    name: str | None = None,
    key: str | None = None,
    priority: int | None = None,
    status: int | None = None,
) -> dict:
    """Update channel configuration."""
    return tools.channels.update_channel(channel_id, name, key, priority, status)


@mcp.tool()
def test_channel(channel_id: int) -> dict:
    """Test channel connectivity."""
    return tools.channels.test_channel(channel_id)


@mcp.tool()
def get_channel_status(channel_id: int) -> dict:
    """Get channel status."""
    return tools.channels.get_channel_status(channel_id)


@mcp.tool()
def get_all_models(page: int = 1, limit: int = 10, sort: str = "-id") -> dict:
    """Get all models with pagination."""
    return tools.models.get_all_models(page, limit, sort)


@mcp.tool()
def get_logs(
    page: int = 1,
    limit: int = 10,
    model: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:
    """Get logs with optional filtering."""
    return tools.logs.get_logs(page, limit, model, start_time, end_time)


@mcp.tool()
def get_token_usage() -> dict:
    """Get token usage statistics."""
    return tools.logs.get_token_usage()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
