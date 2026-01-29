"""Cost estimation endpoints."""

from fastapi import APIRouter, HTTPException
from models.schemas import (
    EstimateRequest,
    CostEstimate,
    TableInfo,
    QueryAnalysis,
)
from services.sql_parser import parse_sql
from services.cost_calculator import calculator
from services.optimizer import optimizer
from services.bigquery_client import get_bigquery_client

router = APIRouter(prefix="/estimate", tags=["estimation"])


@router.post("", response_model=CostEstimate)
async def estimate_cost(request: EstimateRequest) -> CostEstimate:
    """
    Estimate the cost of a BigQuery SQL query.
    
    This endpoint parses the SQL, fetches table metadata (if connected to GCP),
    calculates the estimated cost, and provides optimization suggestions.
    """
    try:
        # 1. Parse SQL
        parsed = parse_sql(request.sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 2. Get table metadata
    bq_client = get_bigquery_client(request.project_id)
    tables_info: list[TableInfo] = []
    
    for table_data in parsed.tables:
        full_name = table_data["full_name"]
        info = bq_client.get_table_info(full_name)
        if info:
            # Add column usage info
            info.columns_used = parsed.columns_by_table.get(full_name, [])
            tables_info.append(info)
    
    # 3. Calculate cost
    total_bytes = sum(t.size_bytes or 0 for t in tables_info)
    
    # Apply column reduction for columnar storage
    if not parsed.is_select_star:
        for table in tables_info:
            if table.columns_used and table.columns_total:
                ratio = len(table.columns_used) / table.columns_total
                if table.estimated_bytes is None:
                    table.estimated_bytes = int((table.size_bytes or 0) * ratio)
        total_bytes = sum(t.estimated_bytes or t.size_bytes or 0 for t in tables_info)
    
    cost_result = calculator.calculate(total_bytes)
    
    # 4. Generate optimizations
    optimizations = optimizer.analyze(parsed, tables_info, request.sql)
    
    # 5. Calculate quality score
    quality_score, quality_grade = optimizer.calculate_quality_score(optimizations)
    
    # 6. Build query analysis
    analysis = QueryAnalysis(
        query_type=parsed.query_type,
        has_where=parsed.has_where,
        has_limit=parsed.has_limit,
        has_order_by=parsed.has_order_by,
        has_group_by=parsed.has_group_by,
        has_join=parsed.has_join,
        has_subquery=parsed.has_subquery,
        is_select_star=parsed.is_select_star,
        tables_count=len(tables_info),
        estimated_complexity=_get_complexity(parsed),
    )
    
    # 7. Determine estimation method
    estimation_method = "precise" if request.project_id else "approximate"
    
    # 8. Build warnings
    warnings = list(parsed.warnings)
    if not request.project_id:
        warnings.append("Using approximate estimation (no GCP connection)")
    
    return CostEstimate(
        estimated_bytes=cost_result.bytes_processed,
        estimated_bytes_human=cost_result.bytes_human,
        estimated_cost_usd=cost_result.cost_usd,
        cost_tier=cost_result.tier,
        tables=tables_info,
        analysis=analysis,
        optimizations=optimizations,
        warnings=warnings,
        estimation_method=estimation_method,
        cached=False,
        quality_score=quality_score,
        quality_grade=quality_grade,
    )


def _get_complexity(parsed) -> str:
    """Determine query complexity."""
    complexity_points = 0
    
    if parsed.has_join:
        complexity_points += 2
    if parsed.has_subquery:
        complexity_points += 2
    if parsed.has_cte:
        complexity_points += 1
    if parsed.has_union:
        complexity_points += 1
    if parsed.has_group_by:
        complexity_points += 1
    if len(parsed.tables) > 3:
        complexity_points += 1
    
    if complexity_points <= 1:
        return "simple"
    elif complexity_points <= 4:
        return "moderate"
    else:
        return "complex"
