"""Comprehensive test for optimized tools."""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from newapi_mcp.client import NewAPIClient
from newapi_mcp.tools_registry import ToolsRegistry


def load_test_config():
    """Load test configuration from testenv.json."""
    config_path = Path(__file__).parent / "testenv.json"
    with open(config_path) as f:
        return json.load(f)


def test_phase1_pricing_tools(tools: ToolsRegistry):
    """Test Phase 1: Simplified pricing tools."""
    print("\n" + "=" * 70)
    print("PHASE 1: SIMPLIFIED PRICING TOOLS")
    print("=" * 70)

    tests_passed = 0
    tests_total = 0

    # Test 1: get_model_list
    tests_total += 1
    try:
        result = tools.pricing.get_model_list()
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] get_model_list() - {result['total']} models")
            tests_passed += 1
        else:
            print(f"[FAIL] get_model_list() - Invalid response format")
    except Exception as e:
        print(f"[FAIL] get_model_list() - {e}")

    # Test 2: get_model_price_by_name
    tests_total += 1
    try:
        result = tools.pricing.get_model_price_by_name("claude-sonnet-4-20250514-BZ")
        if result.get("success") and result.get("data"):
            print(f"[PASS] get_model_price_by_name() - {result['data']['model_name']}")
            tests_passed += 1
        else:
            print(f"[FAIL] get_model_price_by_name() - {result.get('message')}")
    except Exception as e:
        print(f"[FAIL] get_model_price_by_name() - {e}")

    # Test 3: get_models_by_vendor
    tests_total += 1
    try:
        result = tools.pricing.get_models_by_vendor(2)
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] get_models_by_vendor(2) - {result['total']} models")
            tests_passed += 1
        else:
            print(f"[FAIL] get_models_by_vendor() - Invalid response")
    except Exception as e:
        print(f"[FAIL] get_models_by_vendor() - {e}")

    # Test 4: get_models_by_ratio_range
    tests_total += 1
    try:
        result = tools.pricing.get_models_by_ratio_range(0.1, 1.0)
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] get_models_by_ratio_range(0.1, 1.0) - {result['total']} models")
            tests_passed += 1
        else:
            print(f"[FAIL] get_models_by_ratio_range() - Invalid response")
    except Exception as e:
        print(f"[FAIL] get_models_by_ratio_range() - {e}")

    # Test 5: get_pricing_statistics
    tests_total += 1
    try:
        result = tools.pricing.get_pricing_statistics()
        if result.get("success") and result.get("data"):
            stats = result["data"]
            print(
                f"[PASS] get_pricing_statistics() - {stats['total_models']} models, {len(stats['vendors'])} vendors"
            )
            tests_passed += 1
        else:
            print(f"[FAIL] get_pricing_statistics() - Invalid response")
    except Exception as e:
        print(f"[FAIL] get_pricing_statistics() - {e}")

    print(f"\nPhase 1 Result: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def test_phase2_model_search(tools: ToolsRegistry):
    """Test Phase 2: Advanced model search tools."""
    print("\n" + "=" * 70)
    print("PHASE 2: ADVANCED MODEL SEARCH TOOLS")
    print("=" * 70)

    tests_passed = 0
    tests_total = 0

    # Test 1: search_models with keyword
    tests_total += 1
    try:
        result = tools.model_search.search_models(keyword="claude", limit=5)
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] search_models(keyword='claude') - {result['total']} results")
            tests_passed += 1
        else:
            print(f"[FAIL] search_models() - Invalid response")
    except Exception as e:
        print(f"[FAIL] search_models() - {e}")

    # Test 2: compare_models
    tests_total += 1
    try:
        result = tools.model_search.compare_models(
            ["claude-sonnet-4-20250514-BZ", "gpt-5-pro-time"]
        )
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] compare_models() - {result['total']} models compared")
            tests_passed += 1
        else:
            print(f"[FAIL] compare_models() - Invalid response")
    except Exception as e:
        print(f"[FAIL] compare_models() - {e}")

    # Test 3: get_cheapest_models
    tests_total += 1
    try:
        result = tools.model_search.get_cheapest_models(limit=5)
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] get_cheapest_models() - {result['total']} models")
            tests_passed += 1
        else:
            print(f"[FAIL] get_cheapest_models() - Invalid response")
    except Exception as e:
        print(f"[FAIL] get_cheapest_models() - {e}")

    # Test 4: get_fastest_models
    tests_total += 1
    try:
        result = tools.model_search.get_fastest_models(limit=5)
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] get_fastest_models() - {result['total']} models")
            tests_passed += 1
        else:
            print(f"[FAIL] get_fastest_models() - Invalid response")
    except Exception as e:
        print(f"[FAIL] get_fastest_models() - {e}")

    print(f"\nPhase 2 Result: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def test_phase3_token_management(tools: ToolsRegistry):
    """Test Phase 3: Token management tools."""
    print("\n" + "=" * 70)
    print("PHASE 3: TOKEN MANAGEMENT TOOLS")
    print("=" * 70)

    tests_passed = 0
    tests_total = 0

    # Test 1: get_token_info
    tests_total += 1
    try:
        result = tools.token_management.get_token_info()
        if result.get("success") and result.get("data"):
            print(f"[PASS] get_token_info() - Token: {result['data']['name']}")
            tests_passed += 1
        else:
            print(f"[FAIL] get_token_info() - {result.get('message')}")
    except Exception as e:
        print(f"[FAIL] get_token_info() - {e}")

    # Test 2: estimate_cost
    tests_total += 1
    try:
        result = tools.token_management.estimate_cost(
            "claude-sonnet-4-20250514-BZ", input_tokens=1000, output_tokens=500
        )
        if result.get("success") and result.get("data"):
            cost = result["data"]["estimated_cost"]
            print(f"[PASS] estimate_cost() - Estimated cost: ${cost}")
            tests_passed += 1
        else:
            print(f"[FAIL] estimate_cost() - {result.get('message')}")
    except Exception as e:
        print(f"[FAIL] estimate_cost() - {e}")

    # Test 3: list_available_models_for_token
    tests_total += 1
    try:
        result = tools.token_management.list_available_models_for_token()
        if result.get("success") and isinstance(result.get("data"), list):
            print(f"[PASS] list_available_models_for_token() - {result['total']} models")
            tests_passed += 1
        else:
            print(f"[FAIL] list_available_models_for_token() - Invalid response")
    except Exception as e:
        print(f"[FAIL] list_available_models_for_token() - {e}")

    print(f"\nPhase 3 Result: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def test_phase3_channel_tools(tools: ToolsRegistry):
    """Test Phase 3: Enhanced channel tools."""
    print("\n" + "=" * 70)
    print("PHASE 3: ENHANCED CHANNEL TOOLS")
    print("=" * 70)

    tests_passed = 0
    tests_total = 0

    # Test 1: get_channel_list
    tests_total += 1
    try:
        result = tools.channels.get_channel_list()
        if result.get("success"):
            print(f"[PASS] get_channel_list() - {result.get('total', 0)} channels")
            tests_passed += 1
        else:
            print(f"[FAIL] get_channel_list() - {result.get('message')}")
    except Exception as e:
        print(f"[FAIL] get_channel_list() - {e}")

    print(f"\nPhase 3 Channel Result: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def main():
    """Run all optimization tests."""
    print("\n" + "=" * 70)
    print("OPTIMIZED MCP TOOLS - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    config = load_test_config()
    print(f"\nConfiguration loaded:")
    print(f"  Base URL: {config['NEW_API_BASE_URL']}")
    print(f"  Token: {config['NEW_API_TOKEN'][:20]}...")

    client = NewAPIClient(
        base_url=config["NEW_API_BASE_URL"],
        token=config["NEW_API_TOKEN"],
        user_id=config["NEW_API_USER_ID"],
    )
    tools = ToolsRegistry(client)

    results = {
        "Phase 1 - Simplified Pricing": test_phase1_pricing_tools(tools),
        "Phase 2 - Advanced Search": test_phase2_model_search(tools),
        "Phase 3 - Token Management": test_phase3_token_management(tools),
        "Phase 3 - Channel Tools": test_phase3_channel_tools(tools),
    }

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for phase, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {phase}")

    print(f"\nTotal: {passed}/{total} phases passed")

    if passed == total:
        print("\n[SUCCESS] All optimization phases completed successfully!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} phase(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
