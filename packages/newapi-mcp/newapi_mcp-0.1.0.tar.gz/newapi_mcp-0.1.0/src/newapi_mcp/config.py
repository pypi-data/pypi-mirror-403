"""Configuration management for New API MCP."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for New API MCP."""

    BASE_URL: str = os.getenv("NEW_API_BASE_URL", "http://localhost:3000")
    TOKEN: str = os.getenv("NEW_API_TOKEN", "")
    USER_ID: str = os.getenv("NEW_API_USER_ID", "1")

    # HTTP client settings
    CONNECT_TIMEOUT: float = 5.0
    READ_TIMEOUT: float = 30.0
    TOTAL_TIMEOUT: float = 60.0

    # Retry settings
    MAX_RETRIES: int = 3
    BASE_DELAY: float = 1.0
    MAX_DELAY: float = 60.0

    @classmethod
    def get_headers(cls) -> dict[str, str]:
        """Get default headers for API requests."""
        return {
            "Authorization": f"Bearer {cls.TOKEN}",
            "New-Api-User": cls.USER_ID,
            "Content-Type": "application/json",
        }

    @classmethod
    def get_timeout(cls) -> tuple[float, float]:
        """Get timeout tuple for requests."""
        return (cls.CONNECT_TIMEOUT, cls.READ_TIMEOUT)
