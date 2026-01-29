"""Pricing and model ratio management tools for New API MCP."""

import json
from collections import defaultdict
from typing import Any

from .client import NewAPIClient
from .validators import validate_model_ratio


class PricingTools:
    """Pricing management tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client
        self._pricing_cache = None

    def _get_pricing_data(self) -> dict[str, Any]:
        """Get pricing data with caching."""
        if self._pricing_cache is None:
            response = self.client.get("/api/pricing", auth_required=False)
            self._pricing_cache = response
        return self._pricing_cache

    def get_model_pricing(self) -> dict[str, Any]:
        """Get all model pricing and ratios."""
        return self._get_pricing_data()

    def get_model_list(self) -> dict[str, Any]:
        """Get all model names (simplified)."""
        pricing_data = self._get_pricing_data()
        models = [model["model_name"] for model in pricing_data.get("data", [])]
        return {
            "success": True,
            "data": models,
            "total": len(models),
            "message": "ok",
        }

    def get_model_price_by_name(self, model_name: str) -> dict[str, Any]:
        """Get model price by name."""
        pricing_data = self._get_pricing_data()
        for model in pricing_data.get("data", []):
            if model.get("model_name") == model_name:
                return {
                    "success": True,
                    "data": {
                        "model_name": model.get("model_name"),
                        "vendor_id": model.get("vendor_id"),
                        "model_ratio": model.get("model_ratio"),
                        "model_price": model.get("model_price"),
                        "completion_ratio": model.get("completion_ratio"),
                    },
                    "message": "ok",
                }
        return {
            "success": False,
            "data": None,
            "message": f"Model '{model_name}' not found",
            "code": 404,
        }

    def get_models_by_vendor(self, vendor_id: int) -> dict[str, Any]:
        """Get models by vendor ID."""
        pricing_data = self._get_pricing_data()
        models = []
        for model in pricing_data.get("data", []):
            if model.get("vendor_id") == vendor_id:
                models.append(
                    {
                        "model_name": model.get("model_name"),
                        "model_ratio": model.get("model_ratio"),
                        "completion_ratio": model.get("completion_ratio"),
                    }
                )
        return {
            "success": True,
            "data": models,
            "total": len(models),
            "message": "ok",
        }

    def get_models_by_ratio_range(self, min_ratio: float, max_ratio: float) -> dict[str, Any]:
        """Get models by ratio range."""
        pricing_data = self._get_pricing_data()
        models = []
        for model in pricing_data.get("data", []):
            ratio = model.get("model_ratio", 0)
            if min_ratio <= ratio <= max_ratio:
                models.append(
                    {
                        "model_name": model.get("model_name"),
                        "model_ratio": ratio,
                        "vendor_id": model.get("vendor_id"),
                    }
                )
        return {
            "success": True,
            "data": models,
            "total": len(models),
            "message": "ok",
        }

    def get_pricing_statistics(self) -> dict[str, Any]:
        """Get pricing statistics."""
        pricing_data = self._get_pricing_data()
        models = pricing_data.get("data", [])

        vendors = defaultdict(int)
        ratio_dist = defaultdict(int)
        price_dist = defaultdict(int)

        for model in models:
            vendor_id = model.get("vendor_id")
            if vendor_id is not None:
                vendors[vendor_id] += 1

            ratio = model.get("model_ratio")
            if ratio is not None:
                ratio_dist[ratio] += 1

            price = model.get("model_price")
            if price is not None:
                price_dist[price] += 1

        return {
            "success": True,
            "data": {
                "total_models": len(models),
                "vendors": dict(vendors),
                "ratio_distribution": dict(ratio_dist),
                "price_distribution": dict(price_dist),
            },
            "message": "ok",
        }

    def update_model_ratio(self, model_ratios: dict[str, float]) -> dict[str, Any]:
        """Update model ratios."""
        for model, ratio in model_ratios.items():
            if not validate_model_ratio(ratio):
                raise ValueError(
                    f"Invalid ratio for {model}: {ratio}. "
                    "Must be between 0.1 and 100.0 with max 2 decimal places."
                )

        return self.client.put(
            "/api/option",
            {
                "key": "ModelRatio",
                "value": json.dumps(model_ratios),
            },
            auth_required=True,
        )

    def update_model_price(self, model_prices: dict[str, float]) -> dict[str, Any]:
        """Update model prices."""
        return self.client.put(
            "/api/option",
            {
                "key": "ModelPrice",
                "value": json.dumps(model_prices),
            },
            auth_required=True,
        )
