"""
Tests for ETL integration functionality.
"""

import pytest
import numpy as np
from pyoptima.etl import (
    ETLInputAdapter,
    ETLOutputFormatter,
    optimize_batch,
    optimize_single,
    validate_inputs,
    SUPPORTED_OBJECTIVES,
)


class TestETLInputAdapter:
    """Tests for ETL input adapter."""
    
    def test_normalize_nested_covariance_format(self):
        """Test adapter with nested covariance format."""
        inputs = {
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "covariance_matrix": {
                "matrix": [[0.04, 0.01, 0.02], [0.01, 0.05, 0.01], [0.02, 0.01, 0.06]],
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11, "GOOGL": 0.15},
            "covariance_method": "sample_cov",
            "expected_returns_method": "mean_historical",
            "window_size": 252,
            "frequency": 252,
        }
        
        result = ETLInputAdapter.normalize(inputs)
        
        assert "expected_returns" in result
        assert "covariance_matrix" in result
        assert "symbols" in result
        assert len(result["symbols"]) == 3
        assert len(result["covariance_matrix"]) == 3
        assert len(result["expected_returns"]) == 3
    
    def test_normalize_flat_covariance_format(self):
        """Test adapter with dict-of-dicts covariance format."""
        inputs = {
            "symbols": ["AAPL", "MSFT"],
            "covariance_matrix": {
                "AAPL": {"AAPL": 0.04, "MSFT": 0.01},
                "MSFT": {"AAPL": 0.01, "MSFT": 0.05}
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
        }
        
        result = ETLInputAdapter.normalize(inputs)
        
        assert len(result["symbols"]) == 2
        assert "covariance_matrix" in result
    
    def test_normalize_list_covariance_format(self):
        """Test adapter with list-of-lists covariance format."""
        inputs = {
            "symbols": ["AAPL", "MSFT"],
            "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]],
            "expected_returns": [0.12, 0.11],
        }
        
        result = ETLInputAdapter.normalize(inputs)
        
        assert len(result["symbols"]) == 2
        assert result["covariance_matrix"] == [[0.04, 0.01], [0.01, 0.05]]
        # expected_returns stays as list (numpy-compatible format for PortfolioTemplate)
        assert isinstance(result["expected_returns"], list)
        assert result["expected_returns"] == [0.12, 0.11]
    
    def test_normalize_extracts_symbols_from_covariance(self):
        """Test that symbols are extracted from covariance matrix."""
        inputs = {
            "covariance_matrix": {
                "matrix": [[0.04, 0.01], [0.01, 0.05]],
                "symbols": ["AAPL", "MSFT"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
        }
        
        result = ETLInputAdapter.normalize(inputs)
        
        assert result["symbols"] == ["AAPL", "MSFT"]
    
    def test_normalize_extracts_symbols_from_expected_returns(self):
        """Test that symbols are extracted from expected_returns dict."""
        inputs = {
            "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]],
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
        }
        
        result = ETLInputAdapter.normalize(inputs)
        
        assert result["symbols"] == ["AAPL", "MSFT"]
    
    def test_normalize_passthrough_fields(self):
        """Test that optional fields are passed through."""
        inputs = {
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
            "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]],
            "target_return": 0.10,
            "risk_free_rate": 0.02,
            "max_weight": 0.40,
        }
        
        result = ETLInputAdapter.normalize(inputs)
        
        assert result["target_return"] == 0.10
        assert result["risk_free_rate"] == 0.02
        assert result["max_weight"] == 0.40
    
    def test_validate_success(self):
        """Test validation with valid inputs."""
        inputs = {
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
            "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]],
        }
        
        normalized = ETLInputAdapter.normalize(inputs)
        issues = ETLInputAdapter.validate(normalized)
        
        assert issues == []
    
    def test_validate_missing_expected_returns(self):
        """Test validation with missing expected_returns."""
        inputs = {
            "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]],
        }
        
        normalized = ETLInputAdapter.normalize(inputs)
        issues = ETLInputAdapter.validate(normalized)
        
        assert len(issues) == 1
        assert "expected_returns" in issues[0]
    
    def test_validate_missing_covariance(self):
        """Test validation with missing covariance_matrix."""
        inputs = {
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
        }
        
        normalized = ETLInputAdapter.normalize(inputs)
        issues = ETLInputAdapter.validate(normalized)
        
        assert len(issues) == 1
        assert "covariance_matrix" in issues[0]


class TestETLOutputFormatter:
    """Tests for ETL output formatter."""
    
    def test_format_result_success(self):
        """Test formatting successful result."""
        result = {
            "weights": {"AAPL": 0.4, "MSFT": 0.6},
            "portfolio_return": 0.11,
            "portfolio_volatility": 0.18,
            "sharpe_ratio": 0.5,
            "status": "optimal",
        }
        
        output = ETLOutputFormatter.format_result(
            result=result,
            job_id="test-001",
            objective="min_volatility",
            symbols=["AAPL", "MSFT"],
            solver="ipopt",
        )
        
        assert output["job_id"] == "test-001"
        assert output["optimization_type"] == "min_volatility"
        assert output["symbols"] == ["AAPL", "MSFT"]
        assert output["weights"] == {"AAPL": 0.4, "MSFT": 0.6}
        assert output["expected_return"] == 0.11
        assert output["volatility"] == 0.18
        assert output["sharpe_ratio"] == 0.5
        assert output["status"] == "optimal"
        assert output["parameters"]["solver"] == "ipopt"
        assert "run_at" in output["parameters"]
    
    def test_format_result_with_alternative_keys(self):
        """Test formatting result with alternative metric keys."""
        result = {
            "weights": {"AAPL": 0.5, "MSFT": 0.5},
            "expected_return": 0.10,  # Alternative key
            "volatility": 0.15,  # Alternative key
            "status": "optimal",
        }
        
        output = ETLOutputFormatter.format_result(
            result=result,
            job_id="test-002",
            objective="max_sharpe",
            solver="highs",
        )
        
        assert output["expected_return"] == 0.10
        assert output["volatility"] == 0.15
    
    def test_format_error(self):
        """Test formatting error result."""
        error = ValueError("Solver failed")
        
        output = ETLOutputFormatter.format_error(
            error=error,
            job_id="test-003",
            objective="min_volatility",
            symbols=["AAPL"],
            solver="ipopt",
        )
        
        assert output["job_id"] == "test-003"
        assert output["status"] == "error"
        assert output["weights"] == {}
        assert output["expected_return"] is None
        assert "Solver failed" in output["parameters"]["error"]


class TestOptimizeBatch:
    """Tests for optimize_batch function."""
    
    def test_optimize_batch_min_volatility(self):
        """Test batch optimization with min_volatility."""
        data = [{
            "job_id": "test-001",
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "covariance_matrix": {
                "matrix": [
                    [0.04, 0.01, 0.02],
                    [0.01, 0.05, 0.01],
                    [0.02, 0.01, 0.06]
                ],
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11, "GOOGL": 0.15},
        }]
        
        results = optimize_batch(data, objective="min_volatility", solver="ipopt")
        
        assert len(results) == 1
        result = results[0]
        assert result["job_id"] == "test-001"
        assert result["optimization_type"] == "min_volatility"
        assert "weights" in result
        assert result["status"] in ("optimal", "suboptimal")
        assert len(result["weights"]) == 3
        # Weights should sum to approximately 1
        total_weight = sum(result["weights"].values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_optimize_batch_multiple_records(self):
        """Test batch optimization with multiple records."""
        base_cov = {
            "matrix": [[0.04, 0.01], [0.01, 0.05]],
            "symbols": ["AAPL", "MSFT"]
        }
        
        data = [
            {
                "job_id": f"job-{i}",
                "symbols": ["AAPL", "MSFT"],
                "covariance_matrix": base_cov,
                "expected_returns": {"AAPL": 0.10 + i * 0.01, "MSFT": 0.12},
            }
            for i in range(3)
        ]
        
        results = optimize_batch(data, objective="min_volatility")
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["job_id"] == f"job-{i}"
            assert "weights" in result
    
    def test_optimize_batch_with_kwargs(self):
        """Test batch optimization with additional kwargs."""
        data = [{
            "symbols": ["AAPL", "MSFT"],
            "covariance_matrix": {
                "matrix": [[0.04, 0.01], [0.01, 0.05]],
                "symbols": ["AAPL", "MSFT"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
        }]
        
        results = optimize_batch(
            data,
            objective="min_volatility",
            max_weight=0.60,
        )
        
        assert len(results) == 1
        result = results[0]
        # Max weight constraint should be applied
        for weight in result["weights"].values():
            assert weight <= 0.61  # Small tolerance
    
    def test_optimize_batch_generates_job_ids(self):
        """Test that job IDs are generated if not provided."""
        data = [{
            "symbols": ["AAPL", "MSFT"],
            "covariance_matrix": {
                "matrix": [[0.04, 0.01], [0.01, 0.05]],
                "symbols": ["AAPL", "MSFT"]
            },
            "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
        }]
        
        results = optimize_batch(data, objective="min_volatility")
        
        assert results[0]["job_id"] == "opt-0"
    
    def test_optimize_batch_handles_errors_gracefully(self):
        """Test that errors are captured without stopping batch."""
        data = [
            {
                "job_id": "good-job",
                "symbols": ["AAPL", "MSFT"],
                "covariance_matrix": {
                    "matrix": [[0.04, 0.01], [0.01, 0.05]],
                    "symbols": ["AAPL", "MSFT"]
                },
                "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
            },
            {
                "job_id": "bad-job",
                # Missing required fields - will fail validation
                "expected_returns": {"AAPL": 0.12},
            },
        ]
        
        results = optimize_batch(data, objective="min_volatility")
        
        assert len(results) == 2
        assert results[0]["status"] in ("optimal", "suboptimal")
        assert results[1]["status"] == "error"
        assert "error" in results[1]["parameters"]
    
    def test_optimize_batch_unknown_objective_raises(self):
        """Test that unknown objective raises ValueError."""
        data = [{
            "expected_returns": {"AAPL": 0.12},
            "covariance_matrix": [[0.04]],
        }]
        
        with pytest.raises(ValueError, match="Unknown objective"):
            optimize_batch(data, objective="unknown_objective")
    
    def test_optimize_batch_empty_objective_raises(self):
        """Test that empty objective raises ValueError."""
        with pytest.raises(ValueError, match="objective.*required"):
            optimize_batch([], objective="")


class TestValidateInputs:
    """Tests for validate_inputs function."""
    
    def test_validate_inputs_all_valid(self):
        """Test validation with all valid records."""
        data = [
            {
                "job_id": "job-1",
                "expected_returns": {"AAPL": 0.12, "MSFT": 0.11},
                "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]],
            },
            {
                "job_id": "job-2",
                "expected_returns": {"GOOGL": 0.15},
                "covariance_matrix": [[0.06]],
            },
        ]
        
        issues = validate_inputs(data)
        
        assert issues == {}
    
    def test_validate_inputs_some_invalid(self):
        """Test validation with some invalid records."""
        data = [
            {
                "job_id": "good-job",
                "expected_returns": {"AAPL": 0.12},
                "covariance_matrix": [[0.04]],
            },
            {
                "job_id": "bad-job",
                # Missing covariance_matrix
                "expected_returns": {"AAPL": 0.12},
            },
        ]
        
        issues = validate_inputs(data)
        
        assert "good-job" not in issues
        assert "bad-job" in issues
        assert len(issues["bad-job"]) == 1


class TestSupportedObjectives:
    """Tests for supported objectives list."""
    
    def test_supported_objectives_not_empty(self):
        """Test that supported objectives list is populated."""
        assert len(SUPPORTED_OBJECTIVES) > 0
    
    def test_supported_objectives_includes_common(self):
        """Test that common objectives are included."""
        common = ["min_volatility", "max_sharpe", "max_return", "efficient_return"]
        for obj in common:
            assert obj in SUPPORTED_OBJECTIVES
    
    def test_supported_objectives_has_31_methods(self):
        """Test that all 31 portfolio methods are supported."""
        assert len(SUPPORTED_OBJECTIVES) == 31
