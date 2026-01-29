"""Query optimizer that generates optimization suggestions."""

from typing import Optional
from services.sql_parser import ParsedQuery
from models.schemas import (
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
        """
        Analyze a query and generate optimization suggestions.
        
        Args:
            parsed: Parsing result
            tables_info: Table metadata
            sql: Original SQL
            
        Returns:
            List of optimization suggestions sorted by severity
        """
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
                learn_more_url=f"{self.DOCS_BASE}/best-practices-performance-compute#select_only_the_columns_you_need"
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
                estimated_savings="Variable depending on filters applied",
                learn_more_url=f"{self.DOCS_BASE}/best-practices-performance-compute#filter_data_before_joining_or_aggregating"
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
                        f"but your query doesn't filter on this column. "
                        f"Adding a partition filter can drastically reduce costs."
                    ),
                    estimated_savings="Potentially 90%+ if targeting a specific period",
                    code_suggestion=self._suggest_partition_filter(table),
                    learn_more_url=f"{self.DOCS_BASE}/partitioned-tables"
                ))
        
        # Rule 4: Clustered tables without optimal filter
        for table in tables_info:
            if table.is_clustered and not self._has_cluster_filter(parsed, table, sql):
                optimizations.append(Optimization(
                    type=OptimizationType.NO_CLUSTER_FILTER,
                    severity=OptimizationSeverity.LOW,
                    title=f"Clustering optimization possible: {table.name}",
                    message=(
                        f"Table '{table.name}' is clustered on {table.cluster_columns}. "
                        f"Filtering or grouping on these columns can improve performance."
                    ),
                    estimated_savings="Performance improvement (similar cost)",
                    learn_more_url=f"{self.DOCS_BASE}/clustered-tables"
                ))
        
        # Rule 5: LIMIT doesn't reduce costs
        if parsed.has_limit:
            optimizations.append(Optimization(
                type=OptimizationType.LIMIT_WARNING,
                severity=OptimizationSeverity.LOW,
                title="LIMIT doesn't reduce cost",
                message=(
                    "Warning: LIMIT does NOT reduce the volume of data scanned in BigQuery. "
                    "The entire table is scanned, then results are limited. "
                    "Use WHERE filters to reduce costs."
                ),
                learn_more_url=f"{self.DOCS_BASE}/best-practices-performance-compute"
            ))
        
        # Rule 6: Very wide tables
        for table in tables_info:
            if table.columns_total and table.columns_total > 50:
                cols_used = len(table.columns_used) if table.columns_used else 0
                if cols_used < table.columns_total * 0.3:
                    optimizations.append(Optimization(
                        type=OptimizationType.WIDE_TABLE,
                        severity=OptimizationSeverity.MEDIUM,
                        title=f"Wide table: {table.name}",
                        message=(
                            f"Table '{table.name}' has {table.columns_total} columns "
                            f"but you're only using {cols_used}. "
                            f"Verify you're selecting only needed columns."
                        ),
                        estimated_savings=f"~{100 - int(cols_used/table.columns_total*100)}% by selecting only used columns"
                    ))
        
        # Rule 7: CROSS JOIN
        if "CROSS JOIN" in sql.upper() or (parsed.has_join and "ON" not in sql.upper()):
            optimizations.append(Optimization(
                type=OptimizationType.CROSS_JOIN,
                severity=OptimizationSeverity.CRITICAL,
                title="CROSS JOIN detected",
                message=(
                    "A CROSS JOIN produces the Cartesian product of two tables, "
                    "which can explode in data volume and cost. "
                    "Verify this is what you want."
                ),
                estimated_savings="Potentially huge if unintentional"
            ))
        
        # Rule 8: Subqueries in WHERE
        if parsed.has_subquery and self._has_subquery_in_where(sql):
            optimizations.append(Optimization(
                type=OptimizationType.SUBQUERY,
                severity=OptimizationSeverity.MEDIUM,
                title="Subquery in WHERE",
                message=(
                    "Subqueries in WHERE can be less efficient "
                    "than a JOIN or CTE (WITH). Consider rewriting the query."
                ),
                learn_more_url=f"{self.DOCS_BASE}/best-practices-performance-nested"
            ))
        
        # Rule 9: Expensive functions
        expensive_funcs = self._get_expensive_functions(parsed)
        if expensive_funcs:
            optimizations.append(Optimization(
                type=OptimizationType.EXPENSIVE_FUNCTION,
                severity=OptimizationSeverity.LOW,
                title="Expensive functions detected",
                message=(
                    f"Your query uses potentially expensive functions: "
                    f"{', '.join(expensive_funcs)}. "
                    f"These functions can impact performance."
                ),
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
    
    def _has_partition_filter(
        self, 
        parsed: ParsedQuery, 
        table: TableInfo,
        sql: str
    ) -> bool:
        """Check if query filters on partition column."""
        if not table.partition_column:
            return False
        
        sql_upper = sql.upper()
        partition_col = table.partition_column.upper()
        
        if "WHERE" in sql_upper:
            where_part = sql_upper.split("WHERE", 1)[1]
            if partition_col in where_part or "_PARTITIONTIME" in where_part:
                return True
        
        return False
    
    def _has_cluster_filter(
        self,
        parsed: ParsedQuery,
        table: TableInfo,
        sql: str
    ) -> bool:
        """Check if query uses cluster columns."""
        if not table.cluster_columns:
            return False
        
        sql_upper = sql.upper()
        
        for col in table.cluster_columns:
            if col.upper() in sql_upper:
                return True
        
        return False
    
    def _suggest_column_selection(
        self,
        parsed: ParsedQuery,
        tables_info: list[TableInfo]
    ) -> Optional[str]:
        """Suggest column list instead of SELECT *."""
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
        """Suggest partition filter."""
        col = table.partition_column or "_PARTITIONTIME"
        
        if table.partition_type == "DAY":
            return f"WHERE {col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
        elif table.partition_type == "MONTH":
            return f"WHERE {col} >= DATE_TRUNC(CURRENT_DATE(), MONTH)"
        else:
            return f"WHERE {col} BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'"
    
    def _has_subquery_in_where(self, sql: str) -> bool:
        """Check if subquery is in WHERE."""
        sql_upper = sql.upper()
        if "WHERE" not in sql_upper:
            return False
        
        where_part = sql_upper.split("WHERE", 1)[1]
        return "SELECT" in where_part
    
    def _get_expensive_functions(self, parsed: ParsedQuery) -> list[str]:
        """Return expensive functions used."""
        expensive = {
            "REGEXP_EXTRACT", "REGEXP_REPLACE", "REGEXP_CONTAINS",
            "JSON_EXTRACT", "JSON_EXTRACT_SCALAR", "JSON_QUERY",
            "ST_DISTANCE", "ST_AREA", "ST_INTERSECTION", "ST_CONTAINS",
            "ML.PREDICT", "ML.EVALUATE",
            "APPROX_COUNT_DISTINCT", "APPROX_QUANTILES",
            "NORMALIZE", "NORMALIZE_AND_CASEFOLD",
        }
        
        return [f for f in parsed.functions_used if f.upper() in expensive]
    
    def calculate_quality_score(
        self,
        optimizations: list[Optimization]
    ) -> tuple[int, str]:
        """
        Calculate quality score based on optimizations.
        
        Returns:
            Tuple (score 0-100, grade A-F)
        """
        penalties = {
            OptimizationSeverity.CRITICAL: 30,
            OptimizationSeverity.HIGH: 20,
            OptimizationSeverity.MEDIUM: 10,
            OptimizationSeverity.LOW: 5,
        }
        
        total_penalty = sum(
            penalties.get(opt.severity, 0) 
            for opt in optimizations
        )
        
        score = max(0, 100 - total_penalty)
        
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return score, grade


# Default instance
optimizer = QueryOptimizer()
