"""Pydantic models for CostLens API."""

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


# ============== REQUEST MODELS ==============

class EstimateRequest(BaseModel):
    """Cost estimation request."""
    sql: str = Field(..., min_length=1, max_length=100000)
    project_id: Optional[str] = Field(None, description="GCP Project ID")
    use_cache: bool = Field(True, description="Use metadata cache")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sql": "SELECT * FROM `project.dataset.users` WHERE created_at > '2024-01-01'",
                "project_id": "my-gcp-project"
            }
        }
    }


# ============== RESPONSE MODELS ==============

class ColumnInfo(BaseModel):
    """Column information."""
    name: str
    data_type: str
    is_nullable: bool = True
    description: Optional[str] = None


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


class QueryAnalysis(BaseModel):
    """Query analysis result."""
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, etc.
    has_where: bool
    has_limit: bool
    has_order_by: bool
    has_group_by: bool
    has_join: bool
    has_subquery: bool
    is_select_star: bool
    tables_count: int
    estimated_complexity: str  # simple, moderate, complex


class CostEstimate(BaseModel):
    """Complete estimation response."""
    # Cost
    estimated_bytes: int
    estimated_bytes_human: str
    estimated_cost_usd: float
    cost_tier: CostTier
    
    # Details
    tables: list[TableInfo]
    analysis: QueryAnalysis
    optimizations: list[Optimization]
    
    # Meta
    warnings: list[str] = []
    estimation_method: str  # "precise" or "approximate"
    cached: bool = False
    
    # Score
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    quality_grade: Optional[str] = None  # A, B, C, D, F
