"""Simulate LLM calling MCP tools and validate responses."""

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


def save_response(tool_name: str, method_name: str, response: dict, status: str = "success"):
    """Save API response to file."""
    output_dir = Path(__file__).parent / "api_responses"
    output_dir.mkdir(exist_ok=True)

    filename = output_dir / f"{tool_name}_{method_name}_{status}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2, ensure_ascii=False)

    return str(filename)


def simulate_llm_call(tools: ToolsRegistry):
    """Simulate LLM calling MCP tools."""
    print("\n" + "=" * 70)
    print("SIMULATING LLM CALLING MCP TOOLS")
    print("=" * 70)

    # Scenario 1: LLM wants to get model pricing
    print("\n[LLM Request 1] Get current model pricing information")
    print("-" * 70)
    try:
        response = tools.pricing.get_model_pricing()
        print(f"[MCP Response] Status: SUCCESS")
        print(f"[MCP Response] Keys: {list(response.keys())}")
        if "data" in response and isinstance(response["data"], list):
            print(f"[MCP Response] Models count: {len(response['data'])}")
            if response["data"]:
                print(f"[MCP Response] First model: {response['data'][0]}")

        saved_path = save_response("pricing", "get_model_pricing", response, "success")
        print(f"[Saved] Response saved to: {saved_path}")
    except Exception as e:
        print(f"[MCP Response] Status: FAILED")
        print(f"[MCP Response] Error: {e}")
        save_response("pricing", "get_model_pricing", {"error": str(e)}, "failed")

    # Scenario 2: LLM wants to get all channels
    print("\n[LLM Request 2] List all available channels")
    print("-" * 70)
    try:
        response = tools.channels.get_all_channels(page=1, limit=10)
        print(f"[MCP Response] Status: SUCCESS")
        print(f"[MCP Response] Keys: {list(response.keys())}")
        if "data" in response:
            print(f"[MCP Response] Data type: {type(response['data'])}")

        saved_path = save_response("channels", "get_all_channels", response, "success")
        print(f"[Saved] Response saved to: {saved_path}")
    except Exception as e:
        print(f"[MCP Response] Status: FAILED")
        print(f"[MCP Response] Error: {e}")
        save_response("channels", "get_all_channels", {"error": str(e)}, "failed")

    # Scenario 3: LLM wants to get all models
    print("\n[LLM Request 3] Get all available models")
    print("-" * 70)
    try:
        response = tools.models.get_all_models(page=1, limit=10)
        print(f"[MCP Response] Status: SUCCESS")
        print(f"[MCP Response] Keys: {list(response.keys())}")
        if "data" in response:
            print(f"[MCP Response] Data type: {type(response['data'])}")

        saved_path = save_response("models", "get_all_models", response, "success")
        print(f"[Saved] Response saved to: {saved_path}")
    except Exception as e:
        print(f"[MCP Response] Status: FAILED")
        print(f"[MCP Response] Error: {e}")
        save_response("models", "get_all_models", {"error": str(e)}, "failed")

    # Scenario 4: LLM wants to get logs
    print("\n[LLM Request 4] Get recent API logs")
    print("-" * 70)
    try:
        response = tools.logs.get_logs(page=1, limit=5)
        print(f"[MCP Response] Status: SUCCESS")
        print(f"[MCP Response] Keys: {list(response.keys())}")
        if "data" in response:
            print(f"[MCP Response] Data type: {type(response['data'])}")

        saved_path = save_response("logs", "get_logs", response, "success")
        print(f"[Saved] Response saved to: {saved_path}")
    except Exception as e:
        print(f"[MCP Response] Status: FAILED")
        print(f"[MCP Response] Error: {e}")
        save_response("logs", "get_logs", {"error": str(e)}, "failed")

    # Scenario 5: LLM wants to get token usage
    print("\n[LLM Request 5] Get token usage statistics")
    print("-" * 70)
    try:
        response = tools.logs.get_token_usage()
        print(f"[MCP Response] Status: SUCCESS")
        print(f"[MCP Response] Keys: {list(response.keys())}")
        if "data" in response:
            print(f"[MCP Response] Data: {response['data']}")

        saved_path = save_response("logs", "get_token_usage", response, "success")
        print(f"[Saved] Response saved to: {saved_path}")
    except Exception as e:
        print(f"[MCP Response] Status: FAILED")
        print(f"[MCP Response] Error: {e}")
        save_response("logs", "get_token_usage", {"error": str(e)}, "failed")

    # Scenario 6: LLM wants to create a token (dry run - validation only)
    print("\n[LLM Request 6] Validate token creation parameters")
    print("-" * 70)
    try:
        # Just validate, don't actually create
        from newapi_mcp.validators import validate_token_name, validate_quota

        token_name = "test-token-123"
        quota = 10000

        name_valid = validate_token_name(token_name)
        quota_valid = validate_quota(quota)

        print(f"[MCP Response] Status: SUCCESS (validation only)")
        print(f"[MCP Response] Token name '{token_name}' valid: {name_valid}")
        print(f"[MCP Response] Quota {quota} valid: {quota_valid}")

        response = {
            "validation": {
                "token_name": token_name,
                "token_name_valid": name_valid,
                "quota": quota,
                "quota_valid": quota_valid,
                "can_create": name_valid and quota_valid,
            }
        }

        saved_path = save_response("tokens", "validate_create_token", response, "success")
        print(f"[Saved] Response saved to: {saved_path}")
    except Exception as e:
        print(f"[MCP Response] Status: FAILED")
        print(f"[MCP Response] Error: {e}")
        save_response("tokens", "validate_create_token", {"error": str(e)}, "failed")


def validate_response_format():
    """Validate saved response formats."""
    print("\n" + "=" * 70)
    print("VALIDATING RESPONSE FORMATS")
    print("=" * 70)

    response_dir = Path(__file__).parent / "api_responses"
    if not response_dir.exists():
        print("[WARNING] No responses saved yet")
        return

    response_files = list(response_dir.glob("*.json"))
    print(f"\nFound {len(response_files)} response files:")

    for response_file in sorted(response_files):
        print(f"\n[File] {response_file.name}")
        try:
            with open(response_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"  [Format] Valid JSON: YES")
            print(f"  [Keys] {list(data.keys())}")

            # Check for common response patterns
            if "success" in data:
                print(f"  [Pattern] Has 'success' field: {data['success']}")
            if "data" in data:
                print(f"  [Pattern] Has 'data' field: {type(data['data']).__name__}")
            if "error" in data:
                print(f"  [Pattern] Has 'error' field: {data['error']}")
            if "message" in data:
                print(f"  [Pattern] Has 'message' field: {data['message']}")

        except json.JSONDecodeError as e:
            print(f"  [Format] Valid JSON: NO - {e}")
        except Exception as e:
            print(f"  [Error] {e}")


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("LLM MCP TOOL SIMULATION & RESPONSE VALIDATION")
    print("=" * 70)

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

    # Simulate LLM calls
    simulate_llm_call(tools)

    # Validate response formats
    validate_response_format()

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    print("\nResponse files saved to: tests/api_responses/")
    print("You can review the JSON files to verify response formats.")


if __name__ == "__main__":
    main()
