"""Tests for query optimizer."""

import pytest
from services.optimizer import QueryOptimizer
from services.sql_parser import parse_sql
from models.schemas import TableInfo, OptimizationType, OptimizationSeverity


class TestQueryOptimizer:
    """Test suite for QueryOptimizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = QueryOptimizer()
    
    def test_select_star_detection(self):
        """Test SELECT * optimization detection."""
        sql = "SELECT * FROM users"
        parsed = parse_sql(sql)
        tables = [TableInfo(name="users", full_name="project.dataset.users")]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        select_star_opts = [o for o in optimizations if o.type == OptimizationType.SELECT_STAR]
        assert len(select_star_opts) == 1
        assert select_star_opts[0].severity == OptimizationSeverity.HIGH
    
    def test_no_where_detection(self):
        """Test missing WHERE clause detection."""
        sql = "SELECT id FROM users"
        parsed = parse_sql(sql)
        tables = [TableInfo(name="users", full_name="project.dataset.users")]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        no_where_opts = [o for o in optimizations if o.type == OptimizationType.NO_WHERE]
        assert len(no_where_opts) == 1
    
    def test_where_present_no_warning(self):
        """Test that WHERE clause doesn't trigger warning."""
        sql = "SELECT id FROM users WHERE active = true"
        parsed = parse_sql(sql)
        tables = [TableInfo(name="users", full_name="project.dataset.users")]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        no_where_opts = [o for o in optimizations if o.type == OptimizationType.NO_WHERE]
        assert len(no_where_opts) == 0
    
    def test_partition_filter_missing(self):
        """Test detection of missing partition filter."""
        sql = "SELECT id FROM sales"
        parsed = parse_sql(sql)
        tables = [TableInfo(
            name="sales",
            full_name="project.dataset.sales",
            is_partitioned=True,
            partition_column="date",
            partition_type="DAY"
        )]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        partition_opts = [o for o in optimizations if o.type == OptimizationType.NO_PARTITION_FILTER]
        assert len(partition_opts) == 1
        assert partition_opts[0].severity == OptimizationSeverity.CRITICAL
    
    def test_partition_filter_present(self):
        """Test that partition filter is detected."""
        sql = "SELECT id FROM sales WHERE date >= '2024-01-01'"
        parsed = parse_sql(sql)
        tables = [TableInfo(
            name="sales",
            full_name="project.dataset.sales",
            is_partitioned=True,
            partition_column="date",
            partition_type="DAY"
        )]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        partition_opts = [o for o in optimizations if o.type == OptimizationType.NO_PARTITION_FILTER]
        assert len(partition_opts) == 0
    
    def test_limit_warning(self):
        """Test LIMIT warning."""
        sql = "SELECT * FROM users LIMIT 100"
        parsed = parse_sql(sql)
        tables = [TableInfo(name="users", full_name="project.dataset.users")]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        limit_opts = [o for o in optimizations if o.type == OptimizationType.LIMIT_WARNING]
        assert len(limit_opts) == 1
    
    def test_cross_join_detection(self):
        """Test CROSS JOIN detection."""
        sql = "SELECT * FROM users CROSS JOIN orders"
        parsed = parse_sql(sql)
        tables = [
            TableInfo(name="users", full_name="project.dataset.users"),
            TableInfo(name="orders", full_name="project.dataset.orders")
        ]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        cross_join_opts = [o for o in optimizations if o.type == OptimizationType.CROSS_JOIN]
        assert len(cross_join_opts) == 1
        assert cross_join_opts[0].severity == OptimizationSeverity.CRITICAL
    
    def test_wide_table_detection(self):
        """Test wide table optimization suggestion."""
        sql = "SELECT id, name FROM wide_table"
        parsed = parse_sql(sql)
        tables = [TableInfo(
            name="wide_table",
            full_name="project.dataset.wide_table",
            columns_total=100,
            columns_used=["id", "name"]
        )]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        wide_opts = [o for o in optimizations if o.type == OptimizationType.WIDE_TABLE]
        assert len(wide_opts) == 1
    
    def test_quality_score_perfect(self):
        """Test quality score for optimized query."""
        optimizations = []  # No issues
        
        score, grade = self.optimizer.calculate_quality_score(optimizations)
        
        assert score == 100
        assert grade == "A"
    
    def test_quality_score_degraded(self):
        """Test quality score with multiple issues."""
        sql = "SELECT * FROM users"
        parsed = parse_sql(sql)
        tables = [TableInfo(name="users", full_name="project.dataset.users")]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        score, grade = self.optimizer.calculate_quality_score(optimizations)
        
        # SELECT * is HIGH severity (-20) + no WHERE is MEDIUM (-10)
        # Plus LIMIT warning might not appear here
        assert score < 100
        assert grade in ["B", "C", "D"]
    
    def test_optimization_sorting(self):
        """Test that optimizations are sorted by severity."""
        sql = "SELECT * FROM sales LIMIT 100"
        parsed = parse_sql(sql)
        tables = [TableInfo(
            name="sales",
            full_name="project.dataset.sales",
            is_partitioned=True,
            partition_column="date"
        )]
        
        optimizations = self.optimizer.analyze(parsed, tables, sql)
        
        # First should be CRITICAL (partition), then HIGH (SELECT *)
        assert len(optimizations) >= 2
        assert optimizations[0].severity == OptimizationSeverity.CRITICAL
