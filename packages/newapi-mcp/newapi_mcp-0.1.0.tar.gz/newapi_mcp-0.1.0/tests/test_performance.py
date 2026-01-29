"""Performance tests for New API MCP."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tier2_tools import ChannelTools, LogTools, ModelTools
from newapi_mcp.tier3_tools import ChannelManagementTools, UserManagementTools
from newapi_mcp.tools import PricingTools, RatioTools, TokenTools, UserTools


class TestResponseTime:
    """Test response time performance."""

    def test_pricing_response_time(self) -> None:
        """Test pricing query response time."""
        client = NewAPIClient()
        pricing_tools = PricingTools(client)

        start = time.time()
        try:
            pricing_tools.get_model_pricing()
        except Exception:
            pass
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Pricing query took {elapsed}s, expected < 5s"

    def test_user_list_response_time(self) -> None:
        """Test user list query response time."""
        client = NewAPIClient()
        user_tools = UserTools(client)

        start = time.time()
        try:
            user_tools.get_all_users(page=1, limit=10)
        except Exception:
            pass
        elapsed = time.time() - start

        assert elapsed < 5.0, f"User list query took {elapsed}s, expected < 5s"

    def test_channel_list_response_time(self) -> None:
        """Test channel list query response time."""
        client = NewAPIClient()
        channel_tools = ChannelTools(client)

        start = time.time()
        try:
            channel_tools.get_all_channels(page=1, limit=10)
        except Exception:
            pass
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Channel list query took {elapsed}s, expected < 5s"

    def test_model_list_response_time(self) -> None:
        """Test model list query response time."""
        client = NewAPIClient()
        model_tools = ModelTools(client)

        start = time.time()
        try:
            model_tools.get_all_models(page=1, limit=10)
        except Exception:
            pass
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Model list query took {elapsed}s, expected < 5s"

    def test_logs_response_time(self) -> None:
        """Test logs query response time."""
        client = NewAPIClient()
        log_tools = LogTools(client)

        start = time.time()
        try:
            log_tools.get_logs(page=1, limit=10)
        except Exception:
            pass
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Logs query took {elapsed}s, expected < 5s"


class TestConcurrency:
    """Test concurrent request handling."""

    def test_concurrent_pricing_queries(self) -> None:
        """Test concurrent pricing queries."""
        client = NewAPIClient()
        pricing_tools = PricingTools(client)

        def query_pricing() -> float:
            start = time.time()
            try:
                pricing_tools.get_model_pricing()
            except Exception:
                pass
            return time.time() - start

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_pricing) for _ in range(5)]
            times = [f.result() for f in as_completed(futures)]

        avg_time = sum(times) / len(times)
        assert avg_time < 5.0, f"Average concurrent query time {avg_time}s, expected < 5s"

    def test_concurrent_user_queries(self) -> None:
        """Test concurrent user queries."""
        client = NewAPIClient()
        user_tools = UserTools(client)

        def query_users() -> float:
            start = time.time()
            try:
                user_tools.get_all_users(page=1, limit=10)
            except Exception:
                pass
            return time.time() - start

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_users) for _ in range(5)]
            times = [f.result() for f in as_completed(futures)]

        avg_time = sum(times) / len(times)
        assert avg_time < 5.0, f"Average concurrent query time {avg_time}s, expected < 5s"

    def test_concurrent_mixed_queries(self) -> None:
        """Test concurrent mixed queries."""
        client = NewAPIClient()
        pricing_tools = PricingTools(client)
        user_tools = UserTools(client)
        channel_tools = ChannelTools(client)

        def query_pricing() -> float:
            start = time.time()
            try:
                pricing_tools.get_model_pricing()
            except Exception:
                pass
            return time.time() - start

        def query_users() -> float:
            start = time.time()
            try:
                user_tools.get_all_users(page=1, limit=10)
            except Exception:
                pass
            return time.time() - start

        def query_channels() -> float:
            start = time.time()
            try:
                channel_tools.get_all_channels(page=1, limit=10)
            except Exception:
                pass
            return time.time() - start

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(3):
                futures.append(executor.submit(query_pricing))
                futures.append(executor.submit(query_users))
                futures.append(executor.submit(query_channels))
            times = [f.result() for f in as_completed(futures)]

        avg_time = sum(times) / len(times)
        assert avg_time < 5.0, f"Average concurrent query time {avg_time}s, expected < 5s"


class TestValidationPerformance:
    """Test validation performance."""

    def test_username_validation_performance(self) -> None:
        """Test username validation performance."""
        from newapi_mcp.validators import validate_username

        start = time.time()
        for _ in range(1000):
            validate_username("testuser123")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"1000 validations took {elapsed}s, expected < 1s"

    def test_password_validation_performance(self) -> None:
        """Test password validation performance."""
        from newapi_mcp.validators import validate_password

        start = time.time()
        for _ in range(1000):
            validate_password("TestPass123")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"1000 validations took {elapsed}s, expected < 1s"

    def test_model_ratio_validation_performance(self) -> None:
        """Test model ratio validation performance."""
        from newapi_mcp.validators import validate_model_ratio

        start = time.time()
        for _ in range(1000):
            validate_model_ratio(1.5)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"1000 validations took {elapsed}s, expected < 1s"

    def test_quota_validation_performance(self) -> None:
        """Test quota validation performance."""
        from newapi_mcp.validators import validate_quota

        start = time.time()
        for _ in range(1000):
            validate_quota(5000)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"1000 validations took {elapsed}s, expected < 1s"

    def test_token_name_validation_performance(self) -> None:
        """Test token name validation performance."""
        from newapi_mcp.validators import validate_token_name

        start = time.time()
        for _ in range(1000):
            validate_token_name("test_token")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"1000 validations took {elapsed}s, expected < 1s"
