"""Pydantic data models for NewAPI MCP."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standard API response format."""

    success: bool
    data: Optional[Any] = None
    message: str = "ok"
    code: int = 200


class ModelInfo(BaseModel):
    """Model information."""

    model_name: str
    vendor_id: int
    model_ratio: float
    model_price: float = 0
    completion_ratio: Optional[int] = None
    quota_type: int = 0
    owner_by: str = ""
    enable_groups: List[str] = Field(default_factory=list)
    supported_endpoint_types: List[str] = Field(default_factory=list)


class ModelPricingInfo(BaseModel):
    """Simplified model pricing info."""

    model_name: str
    vendor_id: int
    model_ratio: float
    model_price: float = 0
    completion_ratio: Optional[int] = None


class TokenInfo(BaseModel):
    """Token information."""

    name: str
    unlimited_quota: bool
    total_used: int
    total_available: int
    expires_at: int
    model_limits: Dict[str, Any] = Field(default_factory=dict)
    model_limits_enabled: bool = False


class ChannelInfo(BaseModel):
    """Channel information."""

    id: int
    name: str
    type: int
    priority: int
    status: int
    key: Optional[str] = None


class CostEstimate(BaseModel):
    """Cost estimation."""

    model_name: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    currency: str = "USD"


class PricingStatistics(BaseModel):
    """Pricing statistics."""

    total_models: int
    vendors: Dict[int, Dict[str, Any]]
    ratio_distribution: Dict[float, int]
    price_distribution: Dict[float, int]


class ModelComparison(BaseModel):
    """Model comparison data."""

    model_name: str
    vendor_id: int
    model_ratio: float
    completion_ratio: Optional[int] = None
    price_per_1k_tokens: float
