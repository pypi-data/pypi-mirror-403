"""Tests for Tier 1 tools."""

import pytest

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tools import PricingTools, RatioTools, TokenTools, UserTools
from newapi_mcp.validators import (
    validate_model_ratio,
    validate_password,
    validate_quota,
    validate_token_name,
    validate_username,
)


class TestValidators:
    """Test validation functions."""

    def test_validate_username_valid(self) -> None:
        """Test valid usernames."""
        assert validate_username("user123")
        assert validate_username("test-user")
        assert validate_username("test_user")

    def test_validate_username_invalid(self) -> None:
        """Test invalid usernames."""
        assert not validate_username("ab")
        assert not validate_username("a" * 33)
        assert not validate_username("user@123")

    def test_validate_password_valid(self) -> None:
        """Test valid passwords."""
        assert validate_password("Pass123")
        assert validate_password("MyPassword2024")

    def test_validate_password_invalid(self) -> None:
        """Test invalid passwords."""
        assert not validate_password("short")
        assert not validate_password("onlyletters")
        assert not validate_password("12345678")

    def test_validate_model_ratio_valid(self) -> None:
        """Test valid model ratios."""
        assert validate_model_ratio(0.1)
        assert validate_model_ratio(1.0)
        assert validate_model_ratio(100.0)
        assert validate_model_ratio(2.5)

    def test_validate_model_ratio_invalid(self) -> None:
        """Test invalid model ratios."""
        assert not validate_model_ratio(0.05)
        assert not validate_model_ratio(150.0)
        assert not validate_model_ratio(1.999)

    def test_validate_quota_valid(self) -> None:
        """Test valid quotas."""
        assert validate_quota(0)
        assert validate_quota(5000)
        assert validate_quota(9999999999)

    def test_validate_quota_invalid(self) -> None:
        """Test invalid quotas."""
        assert not validate_quota(-1)
        assert not validate_quota(10000000000)

    def test_validate_token_name_valid(self) -> None:
        """Test valid token names."""
        assert validate_token_name("my_token")
        assert validate_token_name("prod-token-v1")
        assert validate_token_name("My API Token")

    def test_validate_token_name_invalid(self) -> None:
        """Test invalid token names."""
        assert not validate_token_name("")
        assert not validate_token_name("a" * 65)
        assert not validate_token_name("token@name")


class TestPricingTools:
    """Test pricing tools."""

    def test_get_model_pricing_raises_on_error(self) -> None:
        """Test that get_model_pricing raises on error."""
        client = NewAPIClient(base_url="http://invalid-url")
        tools = PricingTools(client)
        with pytest.raises(Exception):
            tools.get_model_pricing()


class TestRatioTools:
    """Test ratio tools."""

    def test_update_model_ratio_invalid_ratio(self) -> None:
        """Test that invalid ratios raise error."""
        client = NewAPIClient()
        tools = RatioTools(client)
        with pytest.raises(ValueError):
            tools.update_model_ratio({"gpt-4o": 150.0})

    def test_update_model_ratio_valid_ratio(self) -> None:
        """Test that valid ratios are accepted."""
        client = NewAPIClient()
        tools = RatioTools(client)
        try:
            tools.update_model_ratio({"gpt-4o": 2.0})
        except ValueError:
            pytest.fail("Valid ratio should not raise ValueError")


class TestUserTools:
    """Test user tools."""

    def test_get_all_users_invalid_pagination(self) -> None:
        """Test that invalid pagination raises error."""
        client = NewAPIClient()
        tools = UserTools(client)
        with pytest.raises(ValueError):
            tools.get_all_users(page=0)

    def test_create_user_invalid_username(self) -> None:
        """Test that invalid username raises error."""
        client = NewAPIClient()
        tools = UserTools(client)
        with pytest.raises(ValueError):
            tools.create_user("ab", "Pass123")

    def test_create_user_invalid_password(self) -> None:
        """Test that invalid password raises error."""
        client = NewAPIClient()
        tools = UserTools(client)
        with pytest.raises(ValueError):
            tools.create_user("validuser", "short")


class TestTokenTools:
    """Test token tools."""

    def test_create_token_invalid_name(self) -> None:
        """Test that invalid token name raises error."""
        client = NewAPIClient()
        tools = TokenTools(client)
        with pytest.raises(ValueError):
            tools.create_token("")

    def test_create_token_missing_quota(self) -> None:
        """Test that missing quota raises error."""
        client = NewAPIClient()
        tools = TokenTools(client)
        with pytest.raises(ValueError):
            tools.create_token("test_token", unlimited_quota=False)

    def test_create_token_invalid_quota(self) -> None:
        """Test that invalid quota raises error."""
        client = NewAPIClient()
        tools = TokenTools(client)
        with pytest.raises(ValueError):
            tools.create_token("test_token", unlimited_quota=False, remain_quota=-1)
