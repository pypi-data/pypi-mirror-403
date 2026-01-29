"""BigQuery cost calculator."""

from typing import Any, Optional
from dataclasses import dataclass
from core.pricing import BigQueryPricing, REGIONAL_PRICING
from models.schemas import CostTier


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
        """
        Calculate estimated cost for a number of bytes.
        
        Args:
            bytes_to_scan: Number of bytes to be scanned
            region: GCP region (affects pricing)
            include_free_tier: Subtract monthly free tier
        
        Returns:
            CostResult with all details
        """
        # Apply minimum billable
        billable_bytes = max(bytes_to_scan, self.pricing.MIN_BILLABLE_BYTES)
        
        # Free tier
        if include_free_tier:
            billable_bytes = max(0, billable_bytes - self.pricing.FREE_TIER_BYTES_PER_MONTH)
        
        # Calculate cost
        tb_scanned = billable_bytes / (1024 ** 4)
        price_per_tb = REGIONAL_PRICING.get(region, self.pricing.PRICE_PER_TB_USD)
        cost_usd = tb_scanned * price_per_tb
        
        # Determine tier
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
    
    def estimate_from_tables(
        self,
        tables_info: list[dict],
        columns_used: dict[str, list[str]],
        has_where: bool = False,
        has_partition_filter: bool = False
    ) -> CostResult:
        """
        Estimate cost based on table information.
        
        Applies heuristics to estimate actual bytes scanned.
        """
        total_bytes = 0
        
        for table in tables_info:
            table_bytes = table.get("size_bytes", 0)
            table_name = table.get("full_name", "")
            
            if table_bytes == 0:
                continue
            
            # Reduction factor based on columns used
            cols_used = columns_used.get(table_name, [])
            total_cols = table.get("columns_count", 0)
            
            if cols_used and total_cols > 0 and len(cols_used) < total_cols:
                # BigQuery is columnar, we can estimate reduction
                column_ratio = len(cols_used) / total_cols
                table_bytes = int(table_bytes * column_ratio)
            
            # Reduction factor for partitioned tables
            if table.get("is_partitioned") and has_partition_filter:
                # Heuristic: assume filter reduces by 90%
                table_bytes = int(table_bytes * 0.1)
            
            total_bytes += table_bytes
        
        return self.calculate(total_bytes)
    
    def _get_cost_tier(self, cost_usd: float, bytes_processed: int) -> CostTier:
        """Determine cost tier for UI."""
        # Very little data = essentially free
        if bytes_processed < 10 * 1024 * 1024:  # < 10 MB
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
        """Format bytes in human readable format."""
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
        """Format cost in human readable format."""
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
    
    def get_cost_context(self, cost_usd: float) -> list[str]:
        """
        Provide context about the cost for the user.
        Helps understand the impact.
        """
        contexts = []
        
        if cost_usd >= 0.10:
            coffees = cost_usd / 4.00
            if coffees >= 1:
                contexts.append(f"≈ {coffees:.1f} coffee{'s' if coffees > 1 else ''} ☕")
        
        if cost_usd >= 1.00:
            daily_at_rate = cost_usd * 10  # 10 queries/day
            monthly = daily_at_rate * 22  # work days
            contexts.append(f"If 10 queries/day: ~${monthly:.0f}/month")
        
        if cost_usd >= 10.00:
            contexts.append("⚠️ Expensive query - check optimizations")
        
        if cost_usd >= 100.00:
            contexts.append("🚨 ALERT: This query is very expensive!")
        
        return contexts


# Default instance
calculator = CostCalculator()


def calculate_cost(bytes_to_scan: int, **kwargs) -> CostResult:
    """Helper function for quick calculation."""
    return calculator.calculate(bytes_to_scan, **kwargs)
