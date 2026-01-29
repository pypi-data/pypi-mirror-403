"""BigQuery pricing configuration."""

from dataclasses import dataclass
from enum import Enum


class PricingModel(str, Enum):
    """BigQuery pricing models."""
    ON_DEMAND = "on_demand"
    FLAT_RATE = "flat_rate"
    EDITIONS = "editions"


@dataclass
class BigQueryPricing:
    """BigQuery pricing configuration (January 2025)."""
    
    # On-demand pricing
    PRICE_PER_TB_USD: float = 5.00  # $5 per TB scanned
    
    # Free tier
    FREE_TIER_BYTES_PER_MONTH: int = 1_099_511_627_776  # 1 TB
    FREE_QUERIES_PER_DAY: int = 1_000_000
    
    # Minimum billable
    MIN_BILLABLE_BYTES: int = 10 * 1024 * 1024  # 10 MB minimum
    
    # Storage (for reference)
    STORAGE_ACTIVE_PER_GB_MONTH: float = 0.02  # $0.02/GB/month
    STORAGE_LONG_TERM_PER_GB_MONTH: float = 0.01  # $0.01/GB/month (>90 days)
    
    # Streaming inserts
    STREAMING_INSERT_PER_GB: float = 0.01  # $0.01/200MB


# Regional pricing variations
REGIONAL_PRICING: dict[str, float] = {
    "us": 5.00,
    "eu": 5.50,
    "asia-northeast1": 6.00,
    "asia-southeast1": 5.50,
    "australia-southeast1": 6.00,
    "southamerica-east1": 7.00,
}


def get_regional_price(region: str = "us") -> float:
    """Get price per TB for a given region."""
    return REGIONAL_PRICING.get(region, 5.00)
