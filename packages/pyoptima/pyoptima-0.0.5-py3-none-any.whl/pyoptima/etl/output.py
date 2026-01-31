"""
ETL Output Formatter.

Formats pyoptima optimization results into ETL-ready output records.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


class ETLOutputFormatter:
    """
    Formatter for converting pyoptima results to ETL-compatible output.
    
    Output format matches standard ETL load table schema:
    - job_id: Unique identifier
    - optimization_type: Objective name
    - symbols: List of asset symbols
    - weights: Dict of symbol -> weight
    - expected_return: Portfolio expected return
    - volatility: Portfolio volatility
    - sharpe_ratio: Sharpe ratio
    - status: Optimization status
    - parameters: Additional metadata
    """
    
    @classmethod
    def format_result(
        cls,
        result: Union[Dict[str, Any], Any],
        job_id: str,
        objective: str,
        symbols: Optional[List[str]] = None,
        solver: str = "ipopt",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format a single optimization result for ETL loading.
        
        Args:
            result: Optimization result (dict or OptimizationResult object).
            job_id: Unique job identifier.
            objective: Optimization objective name.
            symbols: List of asset symbols.
            solver: Solver used.
            extra_params: Additional parameters to include.
            
        Returns:
            ETL-ready output record.
        """
        run_at = datetime.now(timezone.utc).isoformat()
        
        # Convert result object to dict if needed
        if not isinstance(result, dict):
            result = getattr(result, "to_dict", lambda: {})() or {}
        
        # Normalize error message key
        if "message" in result and "error" not in result:
            result["error"] = result.pop("message")
        
        # Extract weights
        weights = result.get("weights") or {}
        
        # Determine symbols from various sources
        if symbols is None:
            if isinstance(weights, dict):
                symbols = list(weights.keys())
            else:
                symbols = []
        
        # Extract portfolio metrics
        portfolio_return = (
            result.get("portfolio_return") or 
            result.get("expected_return") or
            result.get("return")
        )
        portfolio_volatility = (
            result.get("portfolio_volatility") or 
            result.get("volatility") or
            result.get("risk")
        )
        sharpe_ratio = result.get("sharpe_ratio")
        status = str(result.get("status", "unknown"))
        
        # Build parameters dict with metadata
        parameters: Dict[str, Any] = {
            "solver": solver,
            "run_at": run_at,
        }
        
        # Include method-specific metrics
        for key in ["objective_value", "cvar", "cdar", "semivariance", "diversification_ratio"]:
            if key in result and result[key] is not None:
                parameters[key] = result[key]
        
        # Include any error message
        if "error" in result:
            parameters["error"] = result["error"]
        
        # Merge extra parameters
        if extra_params:
            parameters.update(extra_params)
        
        return {
            "job_id": job_id,
            "optimization_type": objective,
            "symbols": symbols,
            "weights": weights,
            "expected_return": float(portfolio_return) if portfolio_return is not None else None,
            "volatility": float(portfolio_volatility) if portfolio_volatility is not None else None,
            "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio is not None else None,
            "status": status,
            "parameters": parameters,
        }
    
    @classmethod
    def format_error(
        cls,
        error: Exception,
        job_id: str,
        objective: str,
        symbols: Optional[List[str]] = None,
        solver: str = "ipopt",
    ) -> Dict[str, Any]:
        """
        Format an error result for ETL loading.
        
        Args:
            error: The exception that occurred.
            job_id: Unique job identifier.
            objective: Optimization objective name.
            symbols: List of asset symbols.
            solver: Solver used.
            
        Returns:
            ETL-ready error record.
        """
        run_at = datetime.now(timezone.utc).isoformat()
        
        return {
            "job_id": job_id,
            "optimization_type": objective,
            "symbols": symbols or [],
            "weights": {},
            "expected_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "status": "error",
            "parameters": {
                "solver": solver,
                "run_at": run_at,
                "error": str(error),
            },
        }
    
    @classmethod
    def format_batch(
        cls,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Ensure batch results have consistent structure.
        
        Args:
            results: List of formatted results.
            
        Returns:
            List with consistent structure (all keys present).
        """
        required_keys = [
            "job_id", "optimization_type", "symbols", "weights",
            "expected_return", "volatility", "sharpe_ratio", "status", "parameters"
        ]
        
        normalized = []
        for result in results:
            record = {}
            for key in required_keys:
                if key in result:
                    record[key] = result[key]
                elif key in ("symbols",):
                    record[key] = []
                elif key in ("weights", "parameters"):
                    record[key] = {}
                else:
                    record[key] = None
            normalized.append(record)
        
        return normalized
