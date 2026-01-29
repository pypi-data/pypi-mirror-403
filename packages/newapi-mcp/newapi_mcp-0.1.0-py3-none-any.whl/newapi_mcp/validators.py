"""Validation utilities for New API MCP."""

import re


def validate_username(username: str) -> bool:
    """Validate username format."""
    pattern = r"^[a-zA-Z0-9_-]{3,32}$"
    return bool(re.match(pattern, username))


def validate_password(password: str) -> bool:
    """Validate password format."""
    pattern = r"^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z0-9@$!%*?&]{6,128}$"
    return bool(re.match(pattern, password))


def validate_model_ratio(ratio: float) -> bool:
    """Validate model ratio range."""
    if not isinstance(ratio, (int, float)):
        return False
    if not (0.1 <= ratio <= 100.0):
        return False
    decimal_places = len(str(ratio).split(".")[-1])
    return decimal_places <= 2


def validate_quota(quota: int) -> bool:
    """Validate quota range."""
    return isinstance(quota, int) and 0 <= quota <= 9999999999


def validate_token_name(name: str) -> bool:
    """Validate token name format."""
    pattern = r"^[a-zA-Z0-9_\- ]{1,64}$"
    return bool(re.match(pattern, name))


def validate_pagination(page: int, limit: int) -> bool:
    """Validate pagination parameters."""
    return page >= 1 and limit >= 1 and limit <= 100


def validate_user_id(user_id: int) -> bool:
    """Validate user ID."""
    return user_id >= 1


def validate_channel_id(channel_id: int) -> bool:
    """Validate channel ID."""
    return channel_id >= 1


def validate_channel_name(name: str) -> bool:
    """Validate channel name."""
    return bool(name) and len(name) <= 100


def validate_channel_key(key: str) -> bool:
    """Validate channel key."""
    return bool(key) and len(key) <= 1000


def validate_channel_priority(priority: int) -> bool:
    """Validate channel priority."""
    return 1 <= priority <= 100


def validate_channel_status(status: int) -> bool:
    """Validate channel status."""
    return status in (0, 1)


def validate_channel_type(channel_type: int) -> bool:
    """Validate channel type."""
    return channel_type >= 1
