"""Token management and cost estimation tools."""

from typing import Any

from .client import NewAPIClient


class TokenManagementTools:
    """Token management and cost estimation tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client
        self._pricing_cache = None

    def _get_pricing_data(self) -> dict[str, Any]:
        """Get pricing data with caching."""
        if self._pricing_cache is None:
            self._pricing_cache = self.client.get("/api/pricing", auth_required=False)
        return self._pricing_cache

    def get_token_info(self) -> dict[str, Any]:
        """Get current token information."""
        try:
            response = self.client.get("/api/usage/token", auth_required=True)
            if response.get("code") or response.get("success"):
                data = response.get("data", {})
                return {
                    "success": True,
                    "data": {
                        "name": data.get("name", "default"),
                        "unlimited_quota": data.get("unlimited_quota", False),
                        "total_used": data.get("total_used", 0),
                        "total_available": data.get("total_available", 0),
                        "expires_at": data.get("expires_at", 0),
                        "model_limits_enabled": data.get("model_limits_enabled", False),
                    },
                    "message": "ok",
                }
            return {
                "success": False,
                "data": None,
                "message": "Failed to get token info",
                "code": 400,
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": str(e),
                "code": 500,
            }

    def estimate_cost(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> dict[str, Any]:
        """Estimate API call cost."""
        pricing_data = self._get_pricing_data()
        models_dict = {m["model_name"]: m for m in pricing_data.get("data", [])}

        if model_name not in models_dict:
            return {
                "success": False,
                "data": None,
                "message": f"Model '{model_name}' not found",
                "code": 404,
            }

        model = models_dict[model_name]
        model_ratio = model["model_ratio"]
        completion_ratio = model.get("completion_ratio", 1)

        input_cost = (input_tokens / 1000) * model_ratio
        output_cost = (output_tokens / 1000) * model_ratio * completion_ratio
        total_cost = input_cost + output_cost

        return {
            "success": True,
            "data": {
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "estimated_cost": round(total_cost, 6),
                "currency": "USD",
            },
            "message": "ok",
        }

    def list_available_models_for_token(self) -> dict[str, Any]:
        """List all available models for current token."""
        pricing_data = self._get_pricing_data()
        models = [m["model_name"] for m in pricing_data.get("data", [])]

        return {
            "success": True,
            "data": models,
            "total": len(models),
            "message": "ok",
        }
