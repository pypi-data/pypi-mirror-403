"""Tests for Tier 3 tools."""

import pytest

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tier3_tools import ChannelManagementTools, UserManagementTools


class TestUserManagementTools:
    """Test advanced user management tools."""

    def test_update_user_invalid_id(self) -> None:
        """Test that invalid user ID raises error."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_user(0)

    def test_update_user_no_fields(self) -> None:
        """Test that no fields raises error."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_user(1)

    def test_update_user_with_username(self) -> None:
        """Test that valid username is accepted."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        try:
            tools.update_user(1, username="newuser")
        except ValueError:
            pytest.fail("Valid username should not raise ValueError")

    def test_update_user_with_password(self) -> None:
        """Test that valid password is accepted."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        try:
            tools.update_user(1, password="NewPass123")
        except ValueError:
            pytest.fail("Valid password should not raise ValueError")

    def test_update_user_with_group(self) -> None:
        """Test that valid group is accepted."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        try:
            tools.update_user(1, group="admin")
        except ValueError:
            pytest.fail("Valid group should not raise ValueError")

    def test_update_user_with_multiple_fields(self) -> None:
        """Test that multiple fields are accepted."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        try:
            tools.update_user(1, username="newuser", password="NewPass123", group="admin")
        except ValueError:
            pytest.fail("Valid fields should not raise ValueError")

    def test_delete_user_invalid_id(self) -> None:
        """Test that invalid user ID raises error."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        with pytest.raises(ValueError):
            tools.delete_user(0)

    def test_delete_user_valid_id(self) -> None:
        """Test that valid user ID is accepted."""
        client = NewAPIClient()
        tools = UserManagementTools(client)
        try:
            tools.delete_user(1)
        except ValueError:
            pytest.fail("Valid user ID should not raise ValueError")


class TestChannelManagementTools:
    """Test advanced channel management tools."""

    def test_update_channel_invalid_id(self) -> None:
        """Test that invalid channel ID raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_channel(0)

    def test_update_channel_no_fields(self) -> None:
        """Test that no fields raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_channel(1)

    def test_update_channel_invalid_name(self) -> None:
        """Test that invalid channel name raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_channel(1, name="")

    def test_update_channel_invalid_key(self) -> None:
        """Test that invalid channel key raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_channel(1, key="")

    def test_update_channel_invalid_priority(self) -> None:
        """Test that invalid priority raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_channel(1, priority=0)

    def test_update_channel_invalid_status(self) -> None:
        """Test that invalid status raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.update_channel(1, status=2)

    def test_update_channel_with_name(self) -> None:
        """Test that valid name is accepted."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        try:
            tools.update_channel(1, name="new-channel")
        except ValueError:
            pytest.fail("Valid name should not raise ValueError")

    def test_update_channel_with_key(self) -> None:
        """Test that valid key is accepted."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        try:
            tools.update_channel(1, key="sk-new-key")
        except ValueError:
            pytest.fail("Valid key should not raise ValueError")

    def test_update_channel_with_priority(self) -> None:
        """Test that valid priority is accepted."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        try:
            tools.update_channel(1, priority=5)
        except ValueError:
            pytest.fail("Valid priority should not raise ValueError")

    def test_update_channel_with_status(self) -> None:
        """Test that valid status is accepted."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        try:
            tools.update_channel(1, status=0)
        except ValueError:
            pytest.fail("Valid status should not raise ValueError")

    def test_update_channel_with_multiple_fields(self) -> None:
        """Test that multiple fields are accepted."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        try:
            tools.update_channel(1, name="new-channel", key="sk-new-key", priority=5, status=1)
        except ValueError:
            pytest.fail("Valid fields should not raise ValueError")

    def test_test_channel_invalid_id(self) -> None:
        """Test that invalid channel ID raises error."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        with pytest.raises(ValueError):
            tools.test_channel(0)

    def test_test_channel_valid_id(self) -> None:
        """Test that valid channel ID is accepted."""
        client = NewAPIClient()
        tools = ChannelManagementTools(client)
        try:
            tools.test_channel(1)
        except ValueError:
            pytest.fail("Valid channel ID should not raise ValueError")
