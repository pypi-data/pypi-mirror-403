"""
PyOptima ETL Integration.

Provides direct integration with pycharter ETL pipelines.
Use the `optimize_batch` function as a pycharter custom_function.

Example transform.yaml:
    custom_function:
      module: pyoptima.etl
      function: optimize_batch
      mode: batch
      kwargs:
        objective: min_volatility
        solver: ipopt

Example Python usage:
    from pyoptima.etl import optimize_batch
    
    results = optimize_batch(
        data=[{"expected_returns": {...}, "covariance_matrix": {...}}],
        objective="min_volatility",
        solver="ipopt"
    )
"""

import logging
from typing import Any, Dict, List, Optional

from pyoptima.etl.adapter import ETLInputAdapter
from pyoptima.etl.output import ETLOutputFormatter
from pyoptima.templates.portfolio import PortfolioTemplate
from pyoptima.templates.portfolio_config import Objective, PortfolioConfig

__all__ = [
    "optimize_batch",
    "optimize_single",
    "ETLInputAdapter",
    "ETLOutputFormatter",
    "SUPPORTED_OBJECTIVES",
]

logger = logging.getLogger(__name__)

# All supported portfolio optimization objectives
SUPPORTED_OBJECTIVES = [
    "min_volatility",
    "max_sharpe",
    "max_return",
    "efficient_return",
    "efficient_risk",
    "max_utility",
    "black_litterman_max_sharpe",
    "black_litterman_min_volatility",
    "black_litterman_quadratic_utility",
    "min_cvar",
    "efficient_cvar_risk",
    "efficient_cvar_return",
    "min_cdar",
    "efficient_cdar_risk",
    "efficient_cdar_return",
    "min_semivariance",
    "efficient_semivariance_risk",
    "efficient_semivariance_return",
    "cla_min_volatility",
    "cla_max_sharpe",
    "hierarchical_min_volatility",
    "hierarchical_max_sharpe",
    "max_diversification",
    "max_diversification_index",
    "risk_parity",
    "equal_risk_contribution",
    "max_sharpe_with_costs",
    "min_volatility_with_costs",
    "momentum_filtered_max_sharpe",
    "momentum_filtered_min_volatility",
    "factor_based_selection",
]


def optimize_batch(
    data: List[Dict[str, Any]],
    objective: str,
    solver: str = "ipopt",
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Run portfolio optimization on a batch of records.
    
    This function is designed to be used directly as a pycharter custom_function.
    It handles input normalization, optimization, and output formatting automatically.
    
    Args:
        data: List of input records. Each record should contain:
            - expected_returns: Dict[symbol, return] or list of returns
            - covariance_matrix: Nested dict with 'matrix'/'symbols', or list-of-lists
            - symbols (optional): List of asset symbols
            - job_id (optional): Unique identifier for tracking
            - Additional method-specific fields (see pyoptima docs)
        objective: Optimization objective name (e.g., "min_volatility", "max_sharpe").
            See SUPPORTED_OBJECTIVES for full list.
        solver: Solver to use (default: "ipopt"). Options: "ipopt", "highs", etc.
        **kwargs: Additional parameters passed to config:
            - target_return: Target return for efficient_return
            - target_volatility: Target risk for efficient_risk
            - risk_free_rate: Risk-free rate for Sharpe calculations
            - risk_aversion: Risk aversion parameter
            - max_weight: Maximum weight per asset
            - min_weight: Minimum weight per asset
            - max_assets: Maximum number of assets (cardinality)
            - sector_caps: Dict of sector -> max weight
            - And more (see PortfolioConfig documentation)
    
    Returns:
        List of ETL-ready output records with:
            - job_id: Unique identifier
            - optimization_type: Objective name
            - symbols: List of asset symbols
            - weights: Dict of symbol -> weight
            - expected_return: Portfolio expected return
            - volatility: Portfolio volatility
            - sharpe_ratio: Sharpe ratio (if applicable)
            - status: "optimal", "suboptimal", or "error"
            - parameters: Additional metadata and solver info
    
    Example:
        >>> from pyoptima.etl import optimize_batch
        >>> 
        >>> data = [{
        ...     "job_id": "job-001",
        ...     "symbols": ["AAPL", "GOOGL", "MSFT"],
        ...     "expected_returns": {"AAPL": 0.12, "GOOGL": 0.10, "MSFT": 0.08},
        ...     "covariance_matrix": {
        ...         "matrix": [[0.04, 0.01, 0.02], [0.01, 0.03, 0.015], [0.02, 0.015, 0.025]],
        ...         "symbols": ["AAPL", "GOOGL", "MSFT"]
        ...     }
        ... }]
        >>> 
        >>> results = optimize_batch(data, objective="min_volatility")
        >>> print(results[0]["weights"])
        {'AAPL': 0.25, 'GOOGL': 0.40, 'MSFT': 0.35}
    """
    if not objective:
        raise ValueError("'objective' is required")
    
    if objective not in SUPPORTED_OBJECTIVES:
        # Try to find by value (in case enum name was used)
        try:
            obj_enum = Objective(objective)
            objective = obj_enum.value
        except ValueError:
            raise ValueError(
                f"Unknown objective: '{objective}'. "
                f"Supported: {', '.join(SUPPORTED_OBJECTIVES[:5])}... "
                f"(total: {len(SUPPORTED_OBJECTIVES)})"
            )
    
    template = PortfolioTemplate()
    results: List[Dict[str, Any]] = []
    
    for idx, record in enumerate(data):
        job_id = record.get("job_id") or f"opt-{idx}"
        symbols = record.get("symbols")
        
        try:
            result = optimize_single(
                record=record,
                objective=objective,
                solver=solver,
                **kwargs
            )
            
            # Format for ETL output
            output = ETLOutputFormatter.format_result(
                result=result,
                job_id=job_id,
                objective=objective,
                symbols=symbols,
                solver=solver,
            )
            results.append(output)
            logger.debug("Optimization %s completed: status=%s", job_id, output["status"])
            
        except Exception as e:
            logger.warning("Optimization failed job_id=%s: %s", job_id, e)
            output = ETLOutputFormatter.format_error(
                error=e,
                job_id=job_id,
                objective=objective,
                symbols=symbols or [],
                solver=solver,
            )
            results.append(output)
    
    logger.info(
        "optimize_batch completed: objective=%s, records=%d, success=%d",
        objective,
        len(results),
        sum(1 for r in results if r["status"] != "error")
    )
    
    return results


def optimize_single(
    record: Dict[str, Any],
    objective: str,
    solver: str = "ipopt",
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Run optimization on a single input record.
    
    Args:
        record: Input record with expected_returns, covariance_matrix, etc.
        objective: Optimization objective name.
        solver: Solver to use.
        **kwargs: Additional config parameters.
        
    Returns:
        Raw optimization result dict.
        
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Normalize input
    normalized = ETLInputAdapter.normalize(record)
    
    # Validate
    issues = ETLInputAdapter.validate(normalized)
    if issues:
        raise ValueError(f"Input validation failed: {'; '.join(issues)}")
    
    # Build config dict
    config_dict = _build_config_dict(normalized, objective, kwargs)
    
    # Create config and solve
    config = PortfolioConfig.from_dict(config_dict)
    template = PortfolioTemplate()
    result = template.solve(config, solver=solver)
    
    # Convert result to dict if needed
    if not isinstance(result, dict):
        result = getattr(result, "to_dict", lambda: {})() or {"status": "error"}
    
    return result


def _build_config_dict(
    normalized: Dict[str, Any],
    objective: str,
    kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build configuration dict for PortfolioConfig.from_dict().
    
    Merges normalized input with kwargs, handling priority correctly.
    """
    config: Dict[str, Any] = {
        "objective": objective,
    }
    
    # Required fields
    config["expected_returns"] = normalized["expected_returns"]
    config["covariance_matrix"] = normalized["covariance_matrix"]
    
    # Optional fields from normalized input
    optional_fields = [
        "symbols", "returns",
        # Target parameters
        "target_return", "target_volatility", "target_cvar",
        "target_cdar", "target_semivariance",
        # Risk parameters
        "risk_free_rate", "risk_aversion", "confidence_level",
        # Bounds
        "min_weight", "max_weight", "weight_bounds", "per_asset_bounds",
        # Cardinality
        "max_assets", "min_position_size",
        # Turnover
        "current_weights", "max_turnover", "transaction_costs",
        # Sector constraints
        "sector_caps", "sector_mins", "asset_sectors",
        # Black-Litterman
        "market_caps", "views", "view_cov", "tau",
        # Momentum
        "momentum_period", "momentum_top_pct",
        # Factor
        "factor_data", "factor_weights", "max_volatility",
        # Other
        "benchmark", "min_net_return",
    ]
    
    for field in optional_fields:
        if field in normalized and normalized[field] is not None:
            config[field] = normalized[field]
    
    # Override with kwargs (kwargs take precedence)
    for key, value in kwargs.items():
        if value is not None and key not in ("objective", "solver"):
            config[key] = value
    
    return config


# Convenience function for validation
def validate_inputs(data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Validate a batch of input records without running optimization.
    
    Args:
        data: List of input records.
        
    Returns:
        Dict mapping job_id to list of validation issues.
        Empty dict if all records are valid.
    """
    issues_by_job: Dict[str, List[str]] = {}
    
    for idx, record in enumerate(data):
        job_id = record.get("job_id") or f"record-{idx}"
        normalized = ETLInputAdapter.normalize(record)
        issues = ETLInputAdapter.validate(normalized)
        if issues:
            issues_by_job[job_id] = issues
    
    return issues_by_job
