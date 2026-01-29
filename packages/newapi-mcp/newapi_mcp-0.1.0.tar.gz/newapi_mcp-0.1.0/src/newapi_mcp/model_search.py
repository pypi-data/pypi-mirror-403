"""Advanced model search and filtering tools."""

from difflib import SequenceMatcher
from typing import Any, Optional

from .client import NewAPIClient


class ModelSearchTools:
    """Advanced model search and filtering tools."""

    def __init__(self, client: NewAPIClient):
        self.client = client
        self._pricing_cache = None

    def _get_pricing_data(self) -> dict[str, Any]:
        """Get pricing data with caching."""
        if self._pricing_cache is None:
            self._pricing_cache = self.client.get("/api/pricing", auth_required=False)
        return self._pricing_cache

    def search_models(
        self,
        keyword: Optional[str] = None,
        vendor_id: Optional[int] = None,
        min_ratio: Optional[float] = None,
        max_ratio: Optional[float] = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search models with advanced filtering."""
        pricing_data = self._get_pricing_data()
        models = pricing_data.get("data", [])

        results = []
        for model in models:
            if vendor_id is not None and model["vendor_id"] != vendor_id:
                continue
            if min_ratio is not None and model["model_ratio"] < min_ratio:
                continue
            if max_ratio is not None and model["model_ratio"] > max_ratio:
                continue

            match_score = 1.0
            if keyword:
                ratio = SequenceMatcher(None, keyword.lower(), model["model_name"].lower()).ratio()
                if ratio < 0.3:
                    continue
                match_score = ratio

            results.append(
                {
                    "model_name": model["model_name"],
                    "vendor_id": model["vendor_id"],
                    "model_ratio": model["model_ratio"],
                    "completion_ratio": model.get("completion_ratio"),
                    "match_score": match_score,
                }
            )

        results.sort(key=lambda x: x["match_score"], reverse=True)
        results = results[:limit]

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "message": "ok",
        }

    def compare_models(self, model_names: list[str]) -> dict[str, Any]:
        """Compare multiple models."""
        pricing_data = self._get_pricing_data()
        models_dict = {m["model_name"]: m for m in pricing_data.get("data", [])}

        results = []
        for model_name in model_names:
            if model_name in models_dict:
                model = models_dict[model_name]
                results.append(
                    {
                        "model_name": model["model_name"],
                        "vendor_id": model["vendor_id"],
                        "model_ratio": model["model_ratio"],
                        "completion_ratio": model.get("completion_ratio"),
                        "price_per_1k_tokens": model["model_ratio"] * 0.001,
                    }
                )

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "message": "ok",
        }

    def get_cheapest_models(self, limit: int = 10) -> dict[str, Any]:
        """Get cheapest models by ratio."""
        pricing_data = self._get_pricing_data()
        models = pricing_data.get("data", [])

        sorted_models = sorted(models, key=lambda x: x["model_ratio"])
        results = [
            {
                "model_name": m["model_name"],
                "model_ratio": m["model_ratio"],
                "vendor_id": m["vendor_id"],
            }
            for m in sorted_models[:limit]
        ]

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "message": "ok",
        }

    def get_fastest_models(self, limit: int = 10) -> dict[str, Any]:
        """Get fastest models by completion ratio."""
        pricing_data = self._get_pricing_data()
        models = pricing_data.get("data", [])

        sorted_models = sorted(models, key=lambda x: x.get("completion_ratio", 0), reverse=True)
        results = [
            {
                "model_name": m["model_name"],
                "completion_ratio": m.get("completion_ratio"),
                "vendor_id": m["vendor_id"],
            }
            for m in sorted_models[:limit]
        ]

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "message": "ok",
        }
