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
    
    def parse(self, sql: str) -> ParsedQuery:
        """Parse a SQL query and extract useful information."""
        warnings = []
        
        try:
            parsed = sqlglot.parse_one(sql, read=self.DIALECT)
        except Exception as e:
            try:
                parsed = sqlglot.parse_one(sql)
                warnings.append(f"Parsed as generic SQL: {str(e)}")
            except Exception as e2:
                raise ValueError(f"SQL parsing error: {str(e2)}")
        
        result = ParsedQuery(
            query_type=self._get_query_type(parsed),
            tables=[],
            columns_by_table={},
            warnings=warnings
        )
        
        result.tables = self._extract_tables(parsed)
        result.columns_by_table = self._extract_columns(parsed, result.tables)
        
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
        
        result.is_select_star = self._is_select_star(parsed)
        result.uses_wildcard = self._uses_wildcard(parsed)
        result.functions_used = self._extract_functions(parsed)
        
        return result
    
    def _get_query_type(self, parsed) -> str:
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
                    "catalog": table.catalog,
                    "db": table.db,
                })
        
        return tables
    
    def _get_full_table_name(self, table: exp.Table) -> Optional[str]:
        parts = []
        
        if table.catalog:
            parts.append(table.catalog)
        if table.db:
            parts.append(table.db)
        if table.name:
            parts.append(table.name)
        
        if not parts:
            return None
        
        return ".".join(p.replace("`", "") for p in parts)
    
    def _extract_columns(self, parsed, tables: list[dict]) -> dict[str, list[str]]:
        columns_by_table = {t["full_name"]: [] for t in tables}
        
        alias_map = {}
        for t in tables:
            if t["alias"]:
                alias_map[t["alias"]] = t["full_name"]
            alias_map[t["name"]] = t["full_name"]
        
        for column in parsed.find_all(exp.Column):
            col_name = column.name
            table_ref = column.table if column.table else None
            
            if table_ref:
                full_name = alias_map.get(table_ref)
                if full_name and col_name not in columns_by_table.get(full_name, []):
                    columns_by_table[full_name].append(col_name)
            else:
                for full_name in columns_by_table:
                    if col_name not in columns_by_table[full_name]:
                        columns_by_table[full_name].append(col_name)
        
        return columns_by_table
    
    def _has_clause(self, parsed, clause_type) -> bool:
        return parsed.find(clause_type) is not None
    
    def _has_subquery(self, parsed) -> bool:
        selects = list(parsed.find_all(exp.Select))
        return len(selects) > 1
    
    def _is_select_star(self, parsed) -> bool:
        for star in parsed.find_all(exp.Star):
            parent = star.parent
            while parent:
                if isinstance(parent, exp.Select):
                    return True
                if isinstance(parent, exp.Func):
                    break
                parent = parent.parent
        return False
    
    def _uses_wildcard(self, parsed) -> bool:
        for star in parsed.find_all(exp.Star):
            if hasattr(star, 'table') and star.table:
                return True
        return self._is_select_star(parsed)
    
    def _extract_functions(self, parsed) -> list[str]:
        functions = set()
        
        for func in parsed.find_all(exp.Func):
            func_name = func.sql_name().upper()
            functions.add(func_name)
        
        return list(functions)


parser = SqlParser()


def parse_sql(sql: str) -> ParsedQuery:
    """Helper function for quick parsing."""
    return parser.parse(sql)
