"""BigQuery cost calculator."""

from typing import Any, Optional
from dataclasses import dataclass
from .pricing import BigQueryPricing, REGIONAL_PRICING
from .schemas import CostTier


@dataclass
class CostResult:
    """Cost calculation result."""
    bytes_processed: int
    bytes_human: str
    cost_usd: float
    cost_human: str
    tier: CostTier
    breakdown: dict[str, Any]


class CostCalculator:
    """Calculate BigQuery costs."""
    
    def __init__(self, pricing: Optional[BigQueryPricing] = None):
        self.pricing = pricing or BigQueryPricing()
    
    def calculate(
        self,
        bytes_to_scan: int,
        region: str = "us",
        include_free_tier: bool = False
    ) -> CostResult:
        """Calculate estimated cost for a number of bytes."""
        billable_bytes = max(bytes_to_scan, self.pricing.MIN_BILLABLE_BYTES)
        
        if include_free_tier:
            billable_bytes = max(0, billable_bytes - self.pricing.FREE_TIER_BYTES_PER_MONTH)
        
        tb_scanned = billable_bytes / (1024 ** 4)
        price_per_tb = REGIONAL_PRICING.get(region, self.pricing.PRICE_PER_TB_USD)
        cost_usd = tb_scanned * price_per_tb
        
        tier = self._get_cost_tier(cost_usd, bytes_to_scan)
        
        return CostResult(
            bytes_processed=bytes_to_scan,
            bytes_human=self._format_bytes(bytes_to_scan),
            cost_usd=round(cost_usd, 6),
            cost_human=self._format_cost(cost_usd),
            tier=tier,
            breakdown={
                "bytes_raw": bytes_to_scan,
                "bytes_billable": billable_bytes,
                "tb_scanned": round(tb_scanned, 6),
                "price_per_tb": price_per_tb,
                "region": region,
                "free_tier_applied": include_free_tier,
            }
        )
    
    def _get_cost_tier(self, cost_usd: float, bytes_processed: int) -> CostTier:
        if bytes_processed < 10 * 1024 * 1024:
            return CostTier.FREE
        
        if cost_usd < 0.01:
            return CostTier.LOW
        elif cost_usd < 0.10:
            return CostTier.MEDIUM
        elif cost_usd < 1.00:
            return CostTier.HIGH
        else:
            return CostTier.DANGER
    
    def _format_bytes(self, bytes_count: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        size = float(bytes_count)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.2f} {units[unit_index]}"
    
    def _format_cost(self, cost_usd: float) -> str:
        if cost_usd < 0.001:
            return "< $0.001"
        elif cost_usd < 0.01:
            return f"${cost_usd:.4f}"
        elif cost_usd < 1:
            return f"${cost_usd:.3f}"
        elif cost_usd < 1000:
            return f"${cost_usd:.2f}"
        else:
            return f"${cost_usd:,.2f}"


calculator = CostCalculator()


def calculate_cost(bytes_to_scan: int, **kwargs) -> CostResult:
    """Helper function for quick calculation."""
    return calculator.calculate(bytes_to_scan, **kwargs)
