"""Real NewAPI integration test using testenv.json configuration."""

import json
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tools_registry import ToolsRegistry


def load_test_config():
    """Load test configuration from testenv.json."""
    config_path = Path(__file__).parent / "testenv.json"
    with open(config_path) as f:
        return json.load(f)


def test_pricing_tools(tools: ToolsRegistry):
    """Test pricing tools."""
    print("\n" + "=" * 60)
    print("TEST 1: Pricing Tools")
    print("=" * 60)

    try:
        result = tools.pricing.get_model_pricing()
        print("[PASS] get_model_pricing() - SUCCESS")
        print(f"   Response keys: {list(result.keys())[:5]}...")
        if "data" in result:
            print(f"   Data type: {type(result['data'])}")
        return True
    except Exception as e:
        print(f"[FAIL] get_model_pricing() - FAILED: {e}")
        return False


def test_users_tools(tools: ToolsRegistry):
    """Test users tools."""
    print("\n" + "=" * 60)
    print("TEST 2: Users Tools")
    print("=" * 60)

    try:
        result = tools.users.get_all_users(page=1, limit=5)
        print("[PASS] get_all_users() - SUCCESS")
        print(f"   Response keys: {list(result.keys())}")
        if "data" in result:
            print(
                f"   Users count: {len(result['data']) if isinstance(result['data'], list) else 'N/A'}"
            )
        return True
    except Exception as e:
        print(f"[FAIL] get_all_users() - FAILED: {e}")
        return False


def test_channels_tools(tools: ToolsRegistry):
    """Test channels tools."""
    print("\n" + "=" * 60)
    print("TEST 3: Channels Tools")
    print("=" * 60)

    try:
        result = tools.channels.get_all_channels(page=1, limit=5)
        print("[PASS] get_all_channels() - SUCCESS")
        print(f"   Response keys: {list(result.keys())}")
        if "data" in result:
            print(
                f"   Channels count: {len(result['data']) if isinstance(result['data'], list) else 'N/A'}"
            )
        return True
    except Exception as e:
        print(f"[FAIL] get_all_channels() - FAILED: {e}")
        return False


def test_models_tools(tools: ToolsRegistry):
    """Test models tools."""
    print("\n" + "=" * 60)
    print("TEST 4: Models Tools")
    print("=" * 60)

    try:
        result = tools.models.get_all_models(page=1, limit=5)
        print("[PASS] get_all_models() - SUCCESS")
        print(f"   Response keys: {list(result.keys())}")
        if "data" in result:
            print(
                f"   Models count: {len(result['data']) if isinstance(result['data'], list) else 'N/A'}"
            )
        return True
    except Exception as e:
        print(f"[FAIL] get_all_models() - FAILED: {e}")
        return False


def test_logs_tools(tools: ToolsRegistry):
    """Test logs tools."""
    print("\n" + "=" * 60)
    print("TEST 5: Logs Tools")
    print("=" * 60)

    success = True

    try:
        result = tools.logs.get_logs(page=1, limit=5)
        print("[PASS] get_logs() - SUCCESS")
        print(f"   Response keys: {list(result.keys())}")
        if "data" in result:
            print(
                f"   Logs count: {len(result['data']) if isinstance(result['data'], list) else 'N/A'}"
            )
    except Exception as e:
        print(f"[FAIL] get_logs() - FAILED: {e}")
        success = False

    try:
        result = tools.logs.get_token_usage()
        print("[PASS] get_token_usage() - SUCCESS")
        print(f"   Response keys: {list(result.keys())}")
    except Exception as e:
        print(f"[FAIL] get_token_usage() - FAILED: {e}")
        success = False

    return success


def test_validators():
    """Test validators."""
    print("\n" + "=" * 60)
    print("TEST 6: Validators")
    print("=" * 60)

    from newapi_mcp.validators import (
        validate_pagination,
        validate_username,
        validate_password,
        validate_token_name,
        validate_quota,
        validate_channel_name,
        validate_channel_key,
        validate_channel_priority,
        validate_channel_status,
    )

    tests = [
        ("validate_pagination(1, 10)", validate_pagination(1, 10), True),
        ("validate_pagination(0, 10)", validate_pagination(0, 10), False),
        ("validate_pagination(1, 101)", validate_pagination(1, 101), False),
        ("validate_username('test_user')", validate_username("test_user"), True),
        ("validate_username('ab')", validate_username("ab"), False),
        ("validate_password('Test123')", validate_password("Test123"), True),
        ("validate_password('test')", validate_password("test"), False),
        ("validate_token_name('my-token')", validate_token_name("my-token"), True),
        ("validate_quota(1000)", validate_quota(1000), True),
        ("validate_quota(-1)", validate_quota(-1), False),
        ("validate_channel_name('test')", validate_channel_name("test"), True),
        ("validate_channel_name('')", validate_channel_name(""), False),
        ("validate_channel_key('key123')", validate_channel_key("key123"), True),
        ("validate_channel_priority(50)", validate_channel_priority(50), True),
        ("validate_channel_priority(101)", validate_channel_priority(101), False),
        ("validate_channel_status(1)", validate_channel_status(1), True),
        ("validate_channel_status(2)", validate_channel_status(2), False),
    ]

    passed = 0
    for test_name, result, expected in tests:
        if result == expected:
            print(f"[PASS] {test_name} = {result}")
            passed += 1
        else:
            print(f"[FAIL] {test_name} = {result} (expected {expected})")

    print(f"\n   Passed: {passed}/{len(tests)}")
    return passed == len(tests)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NewAPI MCP - Real Integration Tests")
    print("=" * 60)

    # Load configuration
    config = load_test_config()
    print(f"\nConfiguration loaded:")
    print(f"  Base URL: {config['NEW_API_BASE_URL']}")
    print(f"  Token: {config['NEW_API_TOKEN'][:20]}...")
    print(f"  User ID: {config['NEW_API_USER_ID']}")

    # Initialize client and tools
    client = NewAPIClient(
        base_url=config["NEW_API_BASE_URL"],
        token=config["NEW_API_TOKEN"],
        user_id=config["NEW_API_USER_ID"],
    )
    tools = ToolsRegistry(client)

    # Run tests
    results = {
        "Pricing Tools": test_pricing_tools(tools),
        "Users Tools": test_users_tools(tools),
        "Channels Tools": test_channels_tools(tools),
        "Models Tools": test_models_tools(tools),
        "Logs Tools": test_logs_tools(tools),
        "Validators": test_validators(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} test groups passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test group(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
