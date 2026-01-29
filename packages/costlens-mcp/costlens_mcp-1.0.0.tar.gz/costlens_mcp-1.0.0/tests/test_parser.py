"""Tests for SQL parser."""

import pytest
from services.sql_parser import parse_sql, SqlParser


class TestSqlParser:
    """Test suite for SqlParser."""
    
    def test_simple_select(self):
        """Test parsing a simple SELECT query."""
        sql = "SELECT id, name FROM users"
        parsed = parse_sql(sql)
        
        assert parsed.query_type == "SELECT"
        assert len(parsed.tables) == 1
        assert parsed.tables[0]["name"] == "users"
        assert not parsed.is_select_star
        assert not parsed.has_where
    
    def test_select_star(self):
        """Test detection of SELECT *."""
        sql = "SELECT * FROM users"
        parsed = parse_sql(sql)
        
        assert parsed.is_select_star
    
    def test_select_star_in_count(self):
        """Test that COUNT(*) is not flagged as SELECT *."""
        sql = "SELECT COUNT(*) FROM users"
        parsed = parse_sql(sql)
        
        assert not parsed.is_select_star
    
    def test_where_clause(self):
        """Test WHERE clause detection."""
        sql = "SELECT id FROM users WHERE active = true"
        parsed = parse_sql(sql)
        
        assert parsed.has_where
    
    def test_limit_clause(self):
        """Test LIMIT clause detection."""
        sql = "SELECT id FROM users LIMIT 100"
        parsed = parse_sql(sql)
        
        assert parsed.has_limit
    
    def test_subquery_detection(self):
        """Test subquery detection."""
        sql = """
        SELECT * FROM users 
        WHERE id IN (SELECT user_id FROM orders)
        """
        parsed = parse_sql(sql)
        
        assert parsed.has_subquery
    
    def test_join_detection(self):
        """Test JOIN detection."""
        sql = """
        SELECT u.id, o.total 
        FROM users u 
        JOIN orders o ON u.id = o.user_id
        """
        parsed = parse_sql(sql)
        
        assert parsed.has_join
        assert len(parsed.tables) == 2
    
    def test_bigquery_fully_qualified_name(self):
        """Test parsing BigQuery fully qualified table names."""
        sql = "SELECT * FROM `project.dataset.table`"
        parsed = parse_sql(sql)
        
        assert len(parsed.tables) == 1
        assert parsed.tables[0]["full_name"] == "project.dataset.table"
    
    def test_cte_detection(self):
        """Test CTE (WITH) detection."""
        sql = """
        WITH active_users AS (
            SELECT id FROM users WHERE active = true
        )
        SELECT * FROM active_users
        """
        parsed = parse_sql(sql)
        
        assert parsed.has_cte
    
    def test_group_by_detection(self):
        """Test GROUP BY detection."""
        sql = "SELECT country, COUNT(*) FROM users GROUP BY country"
        parsed = parse_sql(sql)
        
        assert parsed.has_group_by
    
    def test_order_by_detection(self):
        """Test ORDER BY detection."""
        sql = "SELECT id, name FROM users ORDER BY name"
        parsed = parse_sql(sql)
        
        assert parsed.has_order_by
    
    def test_function_extraction(self):
        """Test function extraction."""
        sql = "SELECT COUNT(*), MAX(created_at), AVG(score) FROM users"
        parsed = parse_sql(sql)
        
        assert "COUNT" in parsed.functions_used
        assert "MAX" in parsed.functions_used
        assert "AVG" in parsed.functions_used
    
    def test_invalid_sql(self):
        """Test handling of invalid SQL."""
        sql = "(((invalid"  # Truly invalid
        
        with pytest.raises(ValueError):
            parse_sql(sql)
    
    def test_column_extraction_with_alias(self):
        """Test column extraction with table aliases."""
        sql = """
        SELECT u.id, u.name, o.total 
        FROM users u 
        JOIN orders o ON u.id = o.user_id
        """
        parsed = parse_sql(sql)
        
        # Check that columns are associated with tables
        assert len(parsed.tables) == 2
