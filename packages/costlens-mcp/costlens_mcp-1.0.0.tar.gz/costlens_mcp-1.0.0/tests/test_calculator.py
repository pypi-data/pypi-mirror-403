"""Tests for cost calculator."""

import pytest
from services.cost_calculator import CostCalculator, calculate_cost
from models.schemas import CostTier


class TestCostCalculator:
    """Test suite for CostCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = CostCalculator()
    
    def test_minimum_billable(self):
        """Test that minimum billable bytes are applied."""
        # 1 KB should be billed as 10 MB minimum
        result = self.calculator.calculate(1024)
        
        assert result.breakdown["bytes_billable"] == 10 * 1024 * 1024
    
    def test_cost_per_tb(self):
        """Test cost calculation at 1 TB."""
        one_tb = 1024 ** 4
        result = self.calculator.calculate(one_tb)
        
        # Should be $5.00 for US region
        assert result.cost_usd == pytest.approx(5.00, rel=0.01)
    
    def test_cost_tier_free(self):
        """Test FREE tier for small data."""
        result = self.calculator.calculate(1 * 1024 * 1024)  # 1 MB
        
        assert result.tier == CostTier.FREE
    
    def test_cost_tier_low(self):
        """Test LOW tier."""
        # ~1 GB should be ~$0.005
        result = self.calculator.calculate(1 * 1024 ** 3)
        
        assert result.tier == CostTier.LOW
    
    def test_cost_tier_medium(self):
        """Test MEDIUM tier."""
        # ~15 GB should be ~$0.073 (within $0.01 - $0.10)
        result = self.calculator.calculate(15 * 1024 ** 3)
        
        assert result.tier == CostTier.MEDIUM
    
    def test_cost_tier_high(self):
        """Test HIGH tier."""
        # ~200 GB should be ~$0.97
        result = self.calculator.calculate(200 * 1024 ** 3)
        
        assert result.tier == CostTier.HIGH
    
    def test_cost_tier_danger(self):
        """Test DANGER tier."""
        # 1 TB should be $5
        result = self.calculator.calculate(1024 ** 4)
        
        assert result.tier == CostTier.DANGER
    
    def test_regional_pricing(self):
        """Test regional pricing variations."""
        one_tb = 1024 ** 4
        
        us_result = self.calculator.calculate(one_tb, region="us")
        eu_result = self.calculator.calculate(one_tb, region="eu")
        
        assert eu_result.cost_usd > us_result.cost_usd
        assert eu_result.cost_usd == pytest.approx(5.50, rel=0.01)
    
    def test_bytes_formatting(self):
        """Test human-readable bytes formatting."""
        kb_result = self.calculator.calculate(1024)
        mb_result = self.calculator.calculate(1024 * 1024)
        gb_result = self.calculator.calculate(1024 ** 3)
        tb_result = self.calculator.calculate(1024 ** 4)
        
        assert "KB" in kb_result.bytes_human or "MB" in kb_result.bytes_human
        assert "MB" in mb_result.bytes_human
        assert "GB" in gb_result.bytes_human
        assert "TB" in tb_result.bytes_human
    
    def test_cost_formatting(self):
        """Test human-readable cost formatting."""
        tiny = self.calculator.calculate(1024 * 1024)
        small = self.calculator.calculate(10 * 1024 ** 3)
        large = self.calculator.calculate(1024 ** 4)
        
        assert "$" in tiny.cost_human
        assert "$" in small.cost_human
        assert "$" in large.cost_human
    
    def test_helper_function(self):
        """Test the calculate_cost helper function."""
        result = calculate_cost(1024 ** 4)
        
        assert result.cost_usd == pytest.approx(5.00, rel=0.01)
    
    def test_cost_context(self):
        """Test cost context generation."""
        # Expensive query
        contexts = self.calculator.get_cost_context(15.0)
        
        assert len(contexts) > 0
        assert any("coffee" in c for c in contexts)
    
    def test_estimate_from_tables_column_reduction(self):
        """Test cost reduction when specific columns are selected."""
        tables_info = [
            {
                "full_name": "project.dataset.wide_table",
                "size_bytes": 100 * 1024 ** 3,  # 100 GB
                "columns_count": 100,
            }
        ]
        columns_used = {
            "project.dataset.wide_table": ["id", "name", "email"]  # 3 columns
        }
        
        result = self.calculator.estimate_from_tables(tables_info, columns_used)
        
        # Should estimate ~3 GB (3% of columns)
        assert result.bytes_processed < 10 * 1024 ** 3
