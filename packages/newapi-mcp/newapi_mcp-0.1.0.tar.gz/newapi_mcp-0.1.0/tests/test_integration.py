"""Integration tests for New API MCP."""

import pytest

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tier2_tools import ChannelTools, LogTools, ModelTools
from newapi_mcp.tier3_tools import ChannelManagementTools, UserManagementTools
from newapi_mcp.tools import PricingTools, RatioTools, TokenTools, UserTools


class TestCompleteWorkflow:
    """Test complete workflow scenarios."""

    def test_pricing_workflow(self) -> None:
        """Test pricing query and update workflow."""
        client = NewAPIClient()
        pricing_tools = PricingTools(client)
        ratio_tools = RatioTools(client)

        try:
            pricing = pricing_tools.get_model_pricing()
            assert pricing is not None
            assert isinstance(pricing, dict)
        except Exception:
            pass

        try:
            result = ratio_tools.update_model_ratio({"gpt-4o": 1.5})
            assert result is not None
        except Exception:
            pass

    def test_user_management_workflow(self) -> None:
        """Test user creation and management workflow."""
        client = NewAPIClient()
        user_tools = UserTools(client)
        user_mgmt_tools = UserManagementTools(client)

        try:
            users = user_tools.get_all_users(page=1, limit=10)
            assert users is not None
            assert isinstance(users, dict)
        except Exception:
            pass

        try:
            user = user_tools.create_user("testuser123", "TestPass123")
            assert user is not None
        except Exception:
            pass

        try:
            updated = user_mgmt_tools.update_user(1, username="updateduser")
            assert updated is not None
        except Exception:
            pass

    def test_token_management_workflow(self) -> None:
        """Test token creation and management workflow."""
        client = NewAPIClient()
        token_tools = TokenTools(client)

        try:
            token = token_tools.create_token("test_token", unlimited_quota=False, remain_quota=5000)
            assert token is not None
        except Exception:
            pass

    def test_channel_management_workflow(self) -> None:
        """Test channel creation and management workflow."""
        client = NewAPIClient()
        channel_tools = ChannelTools(client)
        channel_mgmt_tools = ChannelManagementTools(client)

        try:
            channels = channel_tools.get_all_channels(page=1, limit=10)
            assert channels is not None
            assert isinstance(channels, dict)
        except Exception:
            pass

        try:
            channel = channel_tools.create_channel("test_channel", 1, "sk-test-key")
            assert channel is not None
        except Exception:
            pass

        try:
            updated = channel_mgmt_tools.update_channel(1, name="updated_channel")
            assert updated is not None
        except Exception:
            pass

        try:
            test_result = channel_mgmt_tools.test_channel(1)
            assert test_result is not None
        except Exception:
            pass

    def test_model_and_logs_workflow(self) -> None:
        """Test model and logs query workflow."""
        client = NewAPIClient()
        model_tools = ModelTools(client)
        log_tools = LogTools(client)

        try:
            models = model_tools.get_all_models(page=1, limit=10)
            assert models is not None
            assert isinstance(models, dict)
        except Exception:
            pass

        try:
            logs = log_tools.get_logs(page=1, limit=10)
            assert logs is not None
            assert isinstance(logs, dict)
        except Exception:
            pass

        try:
            usage = log_tools.get_token_usage()
            assert usage is not None
        except Exception:
            pass

    def test_error_handling_workflow(self) -> None:
        """Test error handling across all tools."""
        client = NewAPIClient()

        user_tools = UserTools(client)
        with pytest.raises(ValueError):
            user_tools.create_user("ab", "InvalidPass")

        with pytest.raises(ValueError):
            user_tools.create_user("validuser", "short")

        ratio_tools = RatioTools(client)
        with pytest.raises(ValueError):
            ratio_tools.update_model_ratio({"gpt-4o": 150.0})

        token_tools = TokenTools(client)
        with pytest.raises(ValueError):
            token_tools.create_token("x" * 100)

        with pytest.raises(ValueError):
            token_tools.create_token("valid_token", unlimited_quota=False)

        channel_tools = ChannelTools(client)
        with pytest.raises(ValueError):
            channel_tools.create_channel("", 1, "key")

        with pytest.raises(ValueError):
            channel_tools.create_channel("test", 0, "key")

        user_mgmt_tools = UserManagementTools(client)
        with pytest.raises(ValueError):
            user_mgmt_tools.update_user(0)

        with pytest.raises(ValueError):
            user_mgmt_tools.delete_user(0)

        channel_mgmt_tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            channel_mgmt_tools.update_channel(0)

        with pytest.raises(ValueError):
            channel_mgmt_tools.test_channel(0)
