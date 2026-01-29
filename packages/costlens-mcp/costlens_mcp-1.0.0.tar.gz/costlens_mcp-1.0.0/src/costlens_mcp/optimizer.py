"""Query optimizer that generates optimization suggestions."""

from typing import Optional
from .sql_parser import ParsedQuery
from .schemas import (
    Optimization, 
    OptimizationType, 
    OptimizationSeverity,
    TableInfo
)


class QueryOptimizer:
    """Generate optimization suggestions for BigQuery queries."""
    
    DOCS_BASE = "https://cloud.google.com/bigquery/docs"
    
    def analyze(
        self,
        parsed: ParsedQuery,
        tables_info: list[TableInfo],
        sql: str
    ) -> list[Optimization]:
        """Analyze a query and generate optimization suggestions."""
        optimizations = []
        
        # Rule 1: SELECT *
        if parsed.is_select_star:
            optimizations.append(Optimization(
                type=OptimizationType.SELECT_STAR,
                severity=OptimizationSeverity.HIGH,
                title="SELECT * detected",
                message=(
                    "You're using SELECT * which scans all columns. "
                    "Since BigQuery uses columnar storage, specifying only "
                    "the needed columns can significantly reduce costs."
                ),
                estimated_savings="Potentially 50-90% depending on column count",
                code_suggestion=self._suggest_column_selection(parsed, tables_info),
                learn_more_url=f"{self.DOCS_BASE}/best-practices-performance-compute"
            ))
        
        # Rule 2: No WHERE
        if not parsed.has_where and parsed.query_type == "SELECT":
            optimizations.append(Optimization(
                type=OptimizationType.NO_WHERE,
                severity=OptimizationSeverity.MEDIUM,
                title="No WHERE clause",
                message=(
                    "Your query has no WHERE clause, meaning all table data "
                    "will be scanned. Add filters to reduce data volume."
                ),
                estimated_savings="Variable depending on filters applied"
            ))
        
        # Rule 3: Partitioned tables without filter
        for table in tables_info:
            if table.is_partitioned and not self._has_partition_filter(parsed, table, sql):
                optimizations.append(Optimization(
                    type=OptimizationType.NO_PARTITION_FILTER,
                    severity=OptimizationSeverity.CRITICAL,
                    title=f"Partitioned table without filter: {table.name}",
                    message=(
                        f"Table '{table.name}' is partitioned on '{table.partition_column}' "
                        f"but your query doesn't filter on this column."
                    ),
                    estimated_savings="Potentially 90%+ if targeting a specific period",
                    code_suggestion=self._suggest_partition_filter(table)
                ))
        
        # Rule 4: LIMIT doesn't reduce costs
        if parsed.has_limit:
            optimizations.append(Optimization(
                type=OptimizationType.LIMIT_WARNING,
                severity=OptimizationSeverity.LOW,
                title="LIMIT doesn't reduce cost",
                message=(
                    "Warning: LIMIT does NOT reduce the volume of data scanned in BigQuery. "
                    "Use WHERE filters to reduce costs."
                )
            ))
        
        # Rule 5: CROSS JOIN
        if "CROSS JOIN" in sql.upper() or (parsed.has_join and "ON" not in sql.upper()):
            optimizations.append(Optimization(
                type=OptimizationType.CROSS_JOIN,
                severity=OptimizationSeverity.CRITICAL,
                title="CROSS JOIN detected",
                message=(
                    "A CROSS JOIN produces the Cartesian product of two tables, "
                    "which can explode in data volume and cost."
                ),
                estimated_savings="Potentially huge if unintentional"
            ))
        
        # Sort by severity
        severity_order = {
            OptimizationSeverity.CRITICAL: 0,
            OptimizationSeverity.HIGH: 1,
            OptimizationSeverity.MEDIUM: 2,
            OptimizationSeverity.LOW: 3,
        }
        optimizations.sort(key=lambda x: severity_order.get(x.severity, 99))
        
        return optimizations
    
    def _has_partition_filter(self, parsed: ParsedQuery, table: TableInfo, sql: str) -> bool:
        if not table.partition_column:
            return False
        
        sql_upper = sql.upper()
        partition_col = table.partition_column.upper()
        
        if "WHERE" in sql_upper:
            where_part = sql_upper.split("WHERE", 1)[1]
            if partition_col in where_part or "_PARTITIONTIME" in where_part:
                return True
        
        return False
    
    def _suggest_column_selection(self, parsed: ParsedQuery, tables_info: list[TableInfo]) -> Optional[str]:
        if not tables_info:
            return None
        
        all_columns = []
        for table in tables_info:
            if table.columns_used:
                all_columns.extend(table.columns_used)
        
        if not all_columns:
            return "-- Specify needed columns:\n-- SELECT col1, col2, col3 FROM ..."
        
        unique_cols = list(dict.fromkeys(all_columns))[:10]
        return f"SELECT\n    {', '.join(unique_cols)}\nFROM ..."
    
    def _suggest_partition_filter(self, table: TableInfo) -> str:
        col = table.partition_column or "_PARTITIONTIME"
        
        if table.partition_type == "DAY":
            return f"WHERE {col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
        elif table.partition_type == "MONTH":
            return f"WHERE {col} >= DATE_TRUNC(CURRENT_DATE(), MONTH)"
        else:
            return f"WHERE {col} BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'"


optimizer = QueryOptimizer()
