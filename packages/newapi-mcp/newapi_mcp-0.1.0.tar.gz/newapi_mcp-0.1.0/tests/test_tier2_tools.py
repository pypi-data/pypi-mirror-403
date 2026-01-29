"""Tests for Tier 2 tools."""

import pytest

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tier2_tools import ChannelTools, LogTools, ModelTools


class TestChannelTools:
    """Test channel management tools."""

    def test_get_all_channels_invalid_pagination(self) -> None:
        """Test that invalid pagination raises error."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        with pytest.raises(ValueError):
            tools.get_all_channels(page=0)

    def test_get_all_channels_valid_pagination(self) -> None:
        """Test that valid pagination is accepted."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        try:
            tools.get_all_channels(page=1, limit=10)
        except ValueError:
            pytest.fail("Valid pagination should not raise ValueError")

    def test_create_channel_invalid_name(self) -> None:
        """Test that invalid channel name raises error."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        with pytest.raises(ValueError):
            tools.create_channel("", 1, "key")

    def test_create_channel_invalid_type(self) -> None:
        """Test that invalid channel type raises error."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        with pytest.raises(ValueError):
            tools.create_channel("test", 0, "key")

    def test_create_channel_invalid_key(self) -> None:
        """Test that invalid channel key raises error."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        with pytest.raises(ValueError):
            tools.create_channel("test", 1, "")

    def test_create_channel_invalid_priority(self) -> None:
        """Test that invalid priority raises error."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        with pytest.raises(ValueError):
            tools.create_channel("test", 1, "key", priority=0)

    def test_create_channel_invalid_status(self) -> None:
        """Test that invalid status raises error."""
        client = NewAPIClient()
        tools = ChannelTools(client)
        with pytest.raises(ValueError):
            tools.create_channel("test", 1, "key", status=2)


class TestModelTools:
    """Test model management tools."""

    def test_get_all_models_invalid_pagination(self) -> None:
        """Test that invalid pagination raises error."""
        client = NewAPIClient()
        tools = ModelTools(client)
        with pytest.raises(ValueError):
            tools.get_all_models(page=0)

    def test_get_all_models_valid_pagination(self) -> None:
        """Test that valid pagination is accepted."""
        client = NewAPIClient()
        tools = ModelTools(client)
        try:
            tools.get_all_models(page=1, limit=10)
        except ValueError:
            pytest.fail("Valid pagination should not raise ValueError")


class TestLogTools:
    """Test log and statistics tools."""

    def test_get_logs_invalid_pagination(self) -> None:
        """Test that invalid pagination raises error."""
        client = NewAPIClient()
        tools = LogTools(client)
        with pytest.raises(ValueError):
            tools.get_logs(page=0)

    def test_get_logs_valid_pagination(self) -> None:
        """Test that valid pagination is accepted."""
        client = NewAPIClient()
        tools = LogTools(client)
        try:
            tools.get_logs(page=1, limit=10)
        except ValueError:
            pytest.fail("Valid pagination should not raise ValueError")

    def test_get_logs_with_filters(self) -> None:
        """Test that logs with filters are accepted."""
        client = NewAPIClient()
        tools = LogTools(client)
        try:
            tools.get_logs(
                page=1,
                limit=10,
                model="gpt-4o",
                start_time="2024-01-01",
                end_time="2024-01-31",
            )
        except ValueError:
            pytest.fail("Valid filters should not raise ValueError")

    def test_get_token_usage_raises_on_error(self) -> None:
        """Test that get_token_usage raises on error."""
        client = NewAPIClient(base_url="http://invalid-url")
        tools = LogTools(client)
        with pytest.raises(Exception):
            tools.get_token_usage()
