"""CostLens MCP - FinOps for BigQuery.

A Model Context Protocol server providing cost estimation, query optimization,
and safe execution for BigQuery queries.

Installation:
    pip install costlens-mcp

Usage:
    # With ADC (Application Default Credentials)
    costlens-mcp --project my-gcp-project
    
    # With service account key
    costlens-mcp --project my-gcp-project --key-file /path/to/key.json
    
    # Enable query execution with cost limit
    costlens-mcp --project my-gcp-project --allow-execute --max-cost 5.0
"""

from .server import main, mcp, CONFIG
from .schemas import (
    CostTier,
    OptimizationType,
    OptimizationSeverity,
    TableInfo,
    Optimization,
)
from .sql_parser import parse_sql, ParsedQuery
from .cost_calculator import calculator, calculate_cost, CostResult
from .optimizer import optimizer, QueryOptimizer
from .bigquery_client import (
    BigQueryClient,
    MockBigQueryClient,
    get_bigquery_client,
    DryRunResult,
    QueryResult,
)

__version__ = "1.0.0"
__all__ = [
    # Entry point
    "main",
    "mcp",
    "CONFIG",
    # Schemas
    "CostTier",
    "OptimizationType",
    "OptimizationSeverity",
    "TableInfo",
    "Optimization",
    # Parser
    "parse_sql",
    "ParsedQuery",
    # Calculator
    "calculator",
    "calculate_cost",
    "CostResult",
    # Optimizer
    "optimizer",
    "QueryOptimizer",
    # BigQuery Client
    "BigQueryClient",
    "MockBigQueryClient",
    "get_bigquery_client",
    "DryRunResult",
    "QueryResult",
    # Version
    "__version__",
]
