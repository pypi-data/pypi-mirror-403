"""Pydantic models for CostLens MCP Server."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ============== ENUMS ==============

class CostTier(str, Enum):
    """Cost level for UI display."""
    FREE = "free"       # < 10 MB, negligible
    LOW = "low"         # < $0.01
    MEDIUM = "medium"   # $0.01 - $0.10
    HIGH = "high"       # $0.10 - $1.00
    DANGER = "danger"   # > $1.00


class OptimizationSeverity(str, Enum):
    """Suggestion severity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OptimizationType(str, Enum):
    """Types of optimization suggestions."""
    SELECT_STAR = "select_star"
    NO_WHERE = "no_where"
    NO_PARTITION_FILTER = "no_partition_filter"
    NO_CLUSTER_FILTER = "no_cluster_filter"
    LIMIT_WARNING = "limit_warning"
    WIDE_TABLE = "wide_table"
    CROSS_JOIN = "cross_join"
    SUBQUERY = "subquery"
    EXPENSIVE_FUNCTION = "expensive_function"


# ============== MODELS ==============

class TableInfo(BaseModel):
    """Scanned table information."""
    name: str
    full_name: str  # project.dataset.table
    num_rows: Optional[int] = None
    size_bytes: Optional[int] = None
    size_human: Optional[str] = None
    columns_used: list[str] = []
    columns_total: Optional[int] = None
    
    # Partitioning
    is_partitioned: bool = False
    partition_column: Optional[str] = None
    partition_type: Optional[str] = None  # DAY, MONTH, YEAR, HOUR
    partition_filter_used: bool = False
    
    # Clustering
    is_clustered: bool = False
    cluster_columns: list[str] = []
    cluster_filter_used: bool = False
    
    # Estimation for this table
    estimated_bytes: Optional[int] = None
    estimated_cost: Optional[float] = None


class Optimization(BaseModel):
    """Optimization suggestion."""
    type: OptimizationType
    severity: OptimizationSeverity
    title: str
    message: str
    estimated_savings: Optional[str] = None
    code_suggestion: Optional[str] = None
    learn_more_url: Optional[str] = None
