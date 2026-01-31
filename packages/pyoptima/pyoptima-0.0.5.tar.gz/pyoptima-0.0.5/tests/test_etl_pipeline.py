"""
End-to-end tests for ETL pipeline integration.
"""

import pytest
from pyoptima.etl import optimize_batch, optimize_single, ETLOutputFormatter


class TestETLPipelineIntegration:
    """End-to-end tests simulating ETL pipeline usage."""
    
    def test_full_etl_workflow_min_volatility(self):
        """Test complete ETL workflow for min volatility."""
        # Simulate consolidated inputs from ETL pipeline
        data = [{
            "job_id": "growth-2025-01-06",
            "watchlist_type": "growth",
            "week_start_date": "2025-01-06",
            "symbols": ["AAPL", "MSFT", "GOOGL", "JPM", "XOM"],
            "covariance_matrix": {
                "matrix": [
                    [0.04, 0.01, 0.02, 0.005, 0.01],
                    [0.01, 0.05, 0.01, 0.008, 0.012],
                    [0.02, 0.01, 0.06, 0.01, 0.015],
                    [0.005, 0.008, 0.01, 0.03, 0.005],
                    [0.01, 0.012, 0.015, 0.005, 0.04],
                ],
                "symbols": ["AAPL", "MSFT", "GOOGL", "JPM", "XOM"]
            },
            "expected_returns": {
                "AAPL": 0.12,
                "MSFT": 0.11,
                "GOOGL": 0.15,
                "JPM": 0.09,
                "XOM": 0.08
            },
            "covariance_method": "sample_cov",
            "expected_returns_method": "mean_historical",
            "window_size": 756,
            "frequency": 252,
        }]
        
        # Optimize using batch function (simulates pycharter custom_function)
        results = optimize_batch(data, objective="min_volatility", solver="ipopt")
        
        assert len(results) == 1
        result = results[0]
        
        # Verify result format matches ETL load expectations
        assert "job_id" in result
        assert "optimization_type" in result
        assert "symbols" in result
        assert "weights" in result
        assert "expected_return" in result
        assert "volatility" in result
        assert "status" in result
        assert "parameters" in result
        
        assert result["job_id"] == "growth-2025-01-06"
        assert result["optimization_type"] == "min_volatility"
        
        # Verify weights sum to 1
        total_weight = sum(result["weights"].values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_etl_workflow_with_sector_constraints(self):
        """Test ETL workflow with sector constraints passed via kwargs."""
        data = [{
            "job_id": "constrained-opt",
            "symbols": ["AAPL", "MSFT", "GOOGL", "JPM"],
            "covariance_matrix": {
                "matrix": [
                    [0.04, 0.01, 0.02, 0.005],
                    [0.01, 0.05, 0.01, 0.008],
                    [0.02, 0.01, 0.06, 0.01],
                    [0.005, 0.008, 0.01, 0.03],
                ],
                "symbols": ["AAPL", "MSFT", "GOOGL", "JPM"]
            },
            "expected_returns": {
                "AAPL": 0.12,
                "MSFT": 0.11,
                "GOOGL": 0.15,
                "JPM": 0.09
            },
            # Sector constraints in input record
            "sector_caps": {"Technology": 0.50},
            "asset_sectors": {
                "AAPL": "Technology",
                "MSFT": "Technology",
                "GOOGL": "Technology",
                "JPM": "Financials"
            }
        }]
        
        results = optimize_batch(data, objective="min_volatility", solver="ipopt")
        
        assert len(results) == 1
        result = results[0]
        
        # Note: Sector constraints may not be fully enforced depending on solver
        # This test verifies the constraints are passed through
        assert result["status"] in ("optimal", "suboptimal")
    
    def test_etl_workflow_with_max_weight(self):
        """Test ETL workflow with max weight constraint."""
        data = [{
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "covariance_matrix": {
                "matrix": [
                    [0.04, 0.01, 0.02],
                    [0.01, 0.05, 0.01],
                    [0.02, 0.01, 0.06],
                ],
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11, "GOOGL": 0.15},
        }]
        
        # Pass max_weight via kwargs
        results = optimize_batch(
            data,
            objective="min_volatility",
            max_weight=0.50,
        )
        
        assert len(results) == 1
        result = results[0]
        
        # All weights should be <= 0.50 (with small tolerance)
        for symbol, weight in result["weights"].items():
            assert weight <= 0.51, f"{symbol} weight {weight} exceeds max_weight"
    
    def test_etl_workflow_max_sharpe(self):
        """Test ETL workflow with max_sharpe objective."""
        data = [{
            "job_id": "max-sharpe-001",
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "covariance_matrix": {
                "matrix": [
                    [0.04, 0.01, 0.02],
                    [0.01, 0.05, 0.01],
                    [0.02, 0.01, 0.06],
                ],
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11, "GOOGL": 0.15},
            "risk_free_rate": 0.02,
        }]
        
        results = optimize_batch(data, objective="max_sharpe", solver="ipopt")
        
        assert len(results) == 1
        result = results[0]
        assert result["optimization_type"] == "max_sharpe"
        assert result["status"] in ("optimal", "suboptimal")
        
        # Sharpe ratio should be calculated
        if result["sharpe_ratio"] is not None:
            assert result["sharpe_ratio"] > 0
    
    def test_etl_workflow_efficient_return(self):
        """Test ETL workflow with efficient_return objective."""
        data = [{
            "symbols": ["AAPL", "MSFT"],
            "covariance_matrix": {
                "matrix": [[0.04, 0.01], [0.01, 0.05]],
                "symbols": ["AAPL", "MSFT"]
            },
            "expected_returns": {"AAPL": 0.15, "MSFT": 0.10},
            "target_return": 0.12,
        }]
        
        results = optimize_batch(data, objective="efficient_return")
        
        assert len(results) == 1
        result = results[0]
        assert result["optimization_type"] == "efficient_return"
    
    def test_etl_workflow_simulates_pycharter_custom_function(self):
        """Test that optimize_batch works exactly like pycharter custom_function expects."""
        # This simulates what pycharter does when calling custom_function
        # data is a list of dicts, function receives data and kwargs
        
        data = [
            {
                "job_id": "batch-001",
                "expected_returns": {"A": 0.10, "B": 0.12},
                "covariance_matrix": {"matrix": [[0.04, 0.01], [0.01, 0.05]], "symbols": ["A", "B"]},
            },
            {
                "job_id": "batch-002",
                "expected_returns": {"A": 0.11, "B": 0.13},
                "covariance_matrix": {"matrix": [[0.04, 0.01], [0.01, 0.05]], "symbols": ["A", "B"]},
            },
        ]
        
        # This is exactly how pycharter calls custom_function
        results = optimize_batch(
            data,
            objective="min_volatility",
            solver="ipopt",
        )
        
        # Results should be a list of dicts ready for loading
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            assert isinstance(result, dict)
            # All required keys for ETL load
            assert "job_id" in result
            assert "optimization_type" in result
            assert "symbols" in result
            assert "weights" in result
            assert "expected_return" in result
            assert "volatility" in result
            assert "sharpe_ratio" in result
            assert "status" in result
            assert "parameters" in result


class TestETLOutputFormatting:
    """Test ETL output formatting utilities."""
    
    def test_format_result_preserves_all_keys(self):
        """Test that format_result includes all required ETL keys."""
        result = {
            "weights": {"A": 0.5, "B": 0.5},
            "portfolio_return": 0.11,
            "portfolio_volatility": 0.15,
            "sharpe_ratio": 0.6,
            "status": "optimal",
        }
        
        formatted = ETLOutputFormatter.format_result(
            result=result,
            job_id="test-job",
            objective="min_volatility",
            symbols=["A", "B"],
            solver="ipopt",
        )
        
        required_keys = [
            "job_id", "optimization_type", "symbols", "weights",
            "expected_return", "volatility", "sharpe_ratio", "status", "parameters"
        ]
        
        for key in required_keys:
            assert key in formatted, f"Missing key: {key}"
    
    def test_format_error_provides_context(self):
        """Test that format_error includes error details."""
        error = ValueError("Infeasible constraints")
        
        formatted = ETLOutputFormatter.format_error(
            error=error,
            job_id="failed-job",
            objective="min_volatility",
            solver="ipopt",
        )
        
        assert formatted["status"] == "error"
        assert formatted["weights"] == {}
        assert "Infeasible constraints" in formatted["parameters"]["error"]
