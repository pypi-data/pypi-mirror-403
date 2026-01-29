"""SQL Parser using sqlglot for BigQuery dialect."""

import sqlglot
from sqlglot import exp
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ParsedQuery:
    """Result of SQL parsing."""
    query_type: str
    tables: list[dict]
    columns_by_table: dict[str, list[str]]
    
    # Structural analysis
    has_where: bool = False
    has_limit: bool = False
    has_order_by: bool = False
    has_group_by: bool = False
    has_having: bool = False
    has_join: bool = False
    has_subquery: bool = False
    has_cte: bool = False
    has_union: bool = False
    has_distinct: bool = False
    
    # Special flags
    is_select_star: bool = False
    uses_wildcard: bool = False  # table.*
    
    # Functions used
    functions_used: list[str] = field(default_factory=list)
    
    # Parsing errors/warnings
    warnings: list[str] = field(default_factory=list)


class SqlParser:
    """SQL parser specialized for BigQuery."""
    
    DIALECT = "bigquery"
    
    # Expensive functions to flag
    EXPENSIVE_FUNCTIONS = {
        "REGEXP_EXTRACT", "REGEXP_REPLACE", "REGEXP_CONTAINS",
        "JSON_EXTRACT", "JSON_EXTRACT_SCALAR",
        "ST_DISTANCE", "ST_AREA", "ST_INTERSECTION",
        "ML.PREDICT", "ML.EVALUATE",
        "APPROX_COUNT_DISTINCT",
    }
    
    def parse(self, sql: str) -> ParsedQuery:
        """
        Parse a SQL query and extract useful information.
        
        Args:
            sql: The SQL query to analyze
            
        Returns:
            ParsedQuery with all extracted information
        """
        warnings = []
        
        try:
            # Parse with BigQuery dialect
            parsed = sqlglot.parse_one(sql, read=self.DIALECT)
        except Exception as e:
            # Fallback to generic SQL parsing
            try:
                parsed = sqlglot.parse_one(sql)
                warnings.append(f"Parsed as generic SQL: {str(e)}")
            except Exception as e2:
                raise ValueError(f"SQL parsing error: {str(e2)}")
        
        # Extract information
        result = ParsedQuery(
            query_type=self._get_query_type(parsed),
            tables=[],
            columns_by_table={},
            warnings=warnings
        )
        
        # Tables
        result.tables = self._extract_tables(parsed)
        
        # Columns per table
        result.columns_by_table = self._extract_columns(parsed, result.tables)
        
        # Structural analysis
        result.has_where = self._has_clause(parsed, exp.Where)
        result.has_limit = self._has_clause(parsed, exp.Limit)
        result.has_order_by = self._has_clause(parsed, exp.Order)
        result.has_group_by = self._has_clause(parsed, exp.Group)
        result.has_having = self._has_clause(parsed, exp.Having)
        result.has_join = self._has_clause(parsed, exp.Join)
        result.has_subquery = self._has_subquery(parsed)
        result.has_cte = self._has_clause(parsed, exp.CTE)
        result.has_union = self._has_clause(parsed, exp.Union)
        result.has_distinct = self._has_clause(parsed, exp.Distinct)
        
        # SELECT *
        result.is_select_star = self._is_select_star(parsed)
        result.uses_wildcard = self._uses_wildcard(parsed)
        
        # Functions
        result.functions_used = self._extract_functions(parsed)
        
        return result
    
    def _get_query_type(self, parsed) -> str:
        """Determine the query type."""
        type_map = {
            exp.Select: "SELECT",
            exp.Insert: "INSERT",
            exp.Update: "UPDATE",
            exp.Delete: "DELETE",
            exp.Create: "CREATE",
            exp.Drop: "DROP",
            exp.Alter: "ALTER",
            exp.Merge: "MERGE",
        }
        
        for cls, name in type_map.items():
            if isinstance(parsed, cls):
                return name
        
        return "UNKNOWN"
    
    def _extract_tables(self, parsed) -> list[dict]:
        """Extract referenced tables."""
        tables = []
        seen = set()
        
        for table in parsed.find_all(exp.Table):
            full_name = self._get_full_table_name(table)
            
            if full_name and full_name not in seen:
                seen.add(full_name)
                tables.append({
                    "name": table.name,
                    "full_name": full_name,
                    "alias": table.alias if table.alias else None,
                    "catalog": table.catalog,  # project
                    "db": table.db,  # dataset
                })
        
        return tables
    
    def _get_full_table_name(self, table: exp.Table) -> Optional[str]:
        """Build the full table name."""
        parts = []
        
        if table.catalog:
            parts.append(table.catalog)
        if table.db:
            parts.append(table.db)
        if table.name:
            parts.append(table.name)
        
        if not parts:
            return None
        
        # Clean backticks
        return ".".join(p.replace("`", "") for p in parts)
    
    def _extract_columns(
        self, 
        parsed, 
        tables: list[dict]
    ) -> dict[str, list[str]]:
        """Extract columns used per table."""
        columns_by_table = {t["full_name"]: [] for t in tables}
        
        # Alias -> full_name mapping
        alias_map = {}
        for t in tables:
            if t["alias"]:
                alias_map[t["alias"]] = t["full_name"]
            alias_map[t["name"]] = t["full_name"]
        
        for column in parsed.find_all(exp.Column):
            col_name = column.name
            table_ref = column.table if column.table else None
            
            if table_ref:
                # Resolve alias
                full_name = alias_map.get(table_ref)
                if full_name and col_name not in columns_by_table.get(full_name, []):
                    columns_by_table[full_name].append(col_name)
            else:
                # No table reference, add to all (approximation)
                for full_name in columns_by_table:
                    if col_name not in columns_by_table[full_name]:
                        columns_by_table[full_name].append(col_name)
        
        return columns_by_table
    
    def _has_clause(self, parsed, clause_type) -> bool:
        """Check for clause presence."""
        return parsed.find(clause_type) is not None
    
    def _has_subquery(self, parsed) -> bool:
        """Check for subqueries."""
        # Count nested SELECTs
        selects = list(parsed.find_all(exp.Select))
        return len(selects) > 1
    
    def _is_select_star(self, parsed) -> bool:
        """Check if it's a SELECT *."""
        for star in parsed.find_all(exp.Star):
            # Check it's at SELECT level, not in COUNT(*)
            parent = star.parent
            while parent:
                if isinstance(parent, exp.Select):
                    return True
                if isinstance(parent, exp.Func):
                    break  # It's in a function
                parent = parent.parent
        return False
    
    def _uses_wildcard(self, parsed) -> bool:
        """Check for table.* usage."""
        for star in parsed.find_all(exp.Star):
            # Check if it's a qualified star (table.*)
            if hasattr(star, 'table') and star.table:
                return True
        return self._is_select_star(parsed)
    
    def _extract_functions(self, parsed) -> list[str]:
        """Extract functions used."""
        functions = set()
        
        for func in parsed.find_all(exp.Func):
            func_name = func.sql_name().upper()
            functions.add(func_name)
        
        return list(functions)
    
    def get_expensive_functions(self, parsed_query: ParsedQuery) -> list[str]:
        """Return expensive functions used."""
        return [
            f for f in parsed_query.functions_used 
            if f in self.EXPENSIVE_FUNCTIONS
        ]


# Default instance
parser = SqlParser()


def parse_sql(sql: str) -> ParsedQuery:
    """Helper function for quick parsing."""
    return parser.parse(sql)
