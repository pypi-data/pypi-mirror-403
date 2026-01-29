"""BigQuery pricing configuration."""

from dataclasses import dataclass


@dataclass
class BigQueryPricing:
    """BigQuery pricing configuration (January 2025)."""
    
    # On-demand pricing
    PRICE_PER_TB_USD: float = 5.00  # $5 per TB scanned
    
    # Free tier
    FREE_TIER_BYTES_PER_MONTH: int = 1_099_511_627_776  # 1 TB
    
    # Minimum billable
    MIN_BILLABLE_BYTES: int = 10 * 1024 * 1024  # 10 MB minimum


# Regional pricing variations
REGIONAL_PRICING: dict[str, float] = {
    "us": 5.00,
    "eu": 5.50,
    "asia-northeast1": 6.00,
    "asia-southeast1": 5.50,
    "australia-southeast1": 6.00,
    "southamerica-east1": 7.00,
}
