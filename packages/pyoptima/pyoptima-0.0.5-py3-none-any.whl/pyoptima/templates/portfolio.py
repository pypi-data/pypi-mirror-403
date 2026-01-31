"""
Comprehensive Portfolio Optimization Template.

Provides a unified interface for all portfolio optimization objectives including:
- Efficient Frontier: min_volatility, max_sharpe, max_return, efficient_risk, efficient_return, max_utility
- Black-Litterman: black_litterman_max_sharpe, black_litterman_min_volatility, black_litterman_quadratic_utility
- CVaR: min_cvar, efficient_cvar_risk, efficient_cvar_return
- CDaR: min_cdar, efficient_cdar_risk, efficient_cdar_return
- Semivariance: min_semivariance, efficient_semivariance_risk, efficient_semivariance_return
- CLA: cla_min_volatility, cla_max_sharpe
- Hierarchical: hierarchical_min_volatility, hierarchical_max_sharpe
- Maximum Diversification: max_diversification, max_diversification_index
- Risk Parity: risk_parity, equal_risk_contribution
- Transaction Cost-Aware: max_sharpe_with_costs, min_volatility_with_costs
- Momentum-Filtered: momentum_filtered_max_sharpe, momentum_filtered_min_volatility
- Factor-Based: factor_based_selection

Supports advanced constraints:
- Cardinality constraints (max_assets) for watchlist selection
- Turnover constraints for rebalancing
- Transaction cost modeling
- Momentum-based filtering
- Factor-based selection
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

from pyoptima.model.core import OptimizationResult, SolverStatus as OptStatus
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry
from pyoptima.templates.portfolio_config import (
    PortfolioConfig,
    PortfolioData,
    Objective,
    WeightBounds,
    CardinalityConstraint,
    TurnoverConstraint,
    TransactionCosts,
    PerAssetBounds,
    SectorConstraints,
    BlackLittermanConfig,
    MomentumConfig,
    FactorConfig,
)


def _to_numpy(data: Union[pd.Series, pd.DataFrame, np.ndarray, list]) -> Tuple[np.ndarray, Optional[List[str]]]:
    """Convert data to numpy array and extract labels if available."""
    if isinstance(data, pd.Series):
        return data.values, list(data.index)
    elif isinstance(data, pd.DataFrame):
        return data.values, list(data.columns)
    elif isinstance(data, list):
        return np.array(data), None
    else:
        return np.array(data), None


def _get_solver_factory(solver_name: str):
    """Get Pyomo solver factory."""
    if solver_name == "ipopt":
        return pyo.SolverFactory("ipopt_v2")
    elif solver_name == "highs":
        return pyo.SolverFactory("appsi_highs")
    else:
        return pyo.SolverFactory(solver_name)


# =============================================================================
# Black-Litterman Helper Functions
# =============================================================================

def _market_implied_prior_returns(
    market_caps: np.ndarray,
    risk_aversion: float,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.0
) -> np.ndarray:
    """Compute market-implied prior returns."""
    mkt_weights = market_caps / market_caps.sum()
    prior_returns = risk_aversion * np.dot(cov_matrix, mkt_weights) + risk_free_rate
    return prior_returns


def _black_litterman_returns(
    prior_returns: np.ndarray,
    cov_matrix: np.ndarray,
    views: np.ndarray,
    view_cov: np.ndarray,
    tau: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Black-Litterman posterior returns and covariance."""
    if len(views.shape) == 1:
        views = views.reshape(1, -1)
    
    tau_sigma = tau * cov_matrix
    tau_sigma_inv = np.linalg.inv(tau_sigma)
    view_cov_inv = np.linalg.inv(view_cov)
    
    # Posterior covariance
    posterior_cov = np.linalg.inv(tau_sigma_inv + np.dot(views.T, np.dot(view_cov_inv, views)))
    
    # Posterior returns (simplified - assumes views are absolute returns)
    prior_term = np.dot(tau_sigma_inv, prior_returns)
    view_term = np.dot(views.T, np.dot(view_cov_inv, views))
    posterior_returns = np.dot(posterior_cov, prior_term + np.dot(view_term, prior_returns))
    
    return posterior_returns, posterior_cov


# =============================================================================
# CVaR Helper Functions
# =============================================================================

def _calculate_cvar(
    returns: np.ndarray,
    weights: np.ndarray,
    confidence_level: float = 0.05
) -> float:
    """Calculate CVaR for given weights and returns."""
    portfolio_returns = np.dot(returns, weights)
    var = np.percentile(portfolio_returns, confidence_level * 100)
    cvar = np.mean(portfolio_returns[portfolio_returns <= var])
    return -cvar  # Return negative for minimization


# =============================================================================
# CDaR Helper Functions
# =============================================================================

def _calculate_drawdowns(returns: np.ndarray) -> np.ndarray:
    """Calculate drawdowns from returns."""
    cumulative = np.cumprod(1 + returns, axis=0)
    running_max = np.maximum.accumulate(cumulative, axis=0)
    drawdowns = (cumulative - running_max) / running_max
    return drawdowns


def _calculate_cdar(
    returns: np.ndarray,
    weights: np.ndarray,
    confidence_level: float = 0.05
) -> float:
    """Calculate CDaR for given weights and returns."""
    portfolio_returns = np.dot(returns, weights)
    drawdowns = _calculate_drawdowns(portfolio_returns.reshape(-1, 1))
    drawdowns_flat = drawdowns.flatten()
    var = np.percentile(drawdowns_flat, confidence_level * 100)
    cdar = np.mean(drawdowns_flat[drawdowns_flat <= var])
    return -cdar  # Return negative for minimization


# =============================================================================
# Semivariance Helper Functions
# =============================================================================

def _calculate_semivariance(
    returns: np.ndarray,
    weights: np.ndarray,
    benchmark: float = 0.0
) -> float:
    """Calculate semivariance (downside deviation)."""
    portfolio_returns = np.dot(returns, weights)
    downside_returns = portfolio_returns[portfolio_returns < benchmark]
    if len(downside_returns) == 0:
        return 0.0
    semivariance = np.mean((downside_returns - benchmark) ** 2)
    return semivariance


# =============================================================================
# CLA Helper Functions (Simplified Implementation)
# =============================================================================

def _cla_optimize(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    weight_bounds: Tuple[float, float] = (0, 1),
    objective: str = "min_volatility",
    risk_free_rate: float = 0.0
) -> np.ndarray:
    """
    Simplified Critical Line Algorithm implementation.
    For full CLA, see PyPortfolioOpt or similar libraries.
    """
    n = len(expected_returns)
    lower, upper = weight_bounds
    
    # Initialize with equal weights
    weights = np.ones(n) / n
    
    # Simple iterative optimization
    max_iter = 1000
    tolerance = 1e-6
    learning_rate = 0.01
    
    for _ in range(max_iter):
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        
        if objective == "min_volatility":
            gradient = 2 * np.dot(cov_matrix, weights)
        elif objective == "max_sharpe":
            excess_return = portfolio_return - risk_free_rate
            if excess_return > 0:
                gradient = -excess_return / (portfolio_variance ** 1.5) * np.dot(cov_matrix, weights) + \
                           (1 / portfolio_variance ** 0.5) * expected_returns
            else:
                gradient = 2 * np.dot(cov_matrix, weights)
        else:
            gradient = 2 * np.dot(cov_matrix, weights)
        
        # Update weights
        new_weights = weights - learning_rate * gradient
        
        # Apply constraints
        new_weights = np.clip(new_weights, lower, upper)
        new_weights = new_weights / np.sum(new_weights)
        
        # Check convergence
        if np.max(np.abs(new_weights - weights)) < tolerance:
            break
        
        weights = new_weights
    
    return weights


# =============================================================================
# Hierarchical Risk Parity Helper Functions
# =============================================================================

def _hrp_optimize(
    cov_matrix: np.ndarray
) -> np.ndarray:
    """
    Hierarchical Risk Parity optimization.
    Simplified implementation - for full HRP see original papers.
    """
    n = cov_matrix.shape[0]
    
    # Calculate correlation matrix
    std = np.sqrt(np.diag(cov_matrix))
    corr = cov_matrix / np.outer(std, std)
    
    # Distance matrix
    dist = np.sqrt((1 - corr) / 2)
    np.fill_diagonal(dist, 0.0)
    
    # Simple inverse-variance weighting as approximation
    inv_var = 1.0 / np.diag(cov_matrix)
    weights = inv_var / np.sum(inv_var)
    
    return weights


# =============================================================================
# Maximum Diversification Helper Functions
# =============================================================================

def _calculate_diversification_ratio(
    weights: np.ndarray,
    cov_matrix: np.ndarray
) -> float:
    """Calculate diversification ratio."""
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
    weighted_avg_vol = np.sum(weights * np.sqrt(np.diag(cov_matrix)))
    if weighted_avg_vol == 0:
        return 0.0
    return weighted_avg_vol / portfolio_vol


def _calculate_diversification_index(
    weights: np.ndarray,
    cov_matrix: np.ndarray
) -> float:
    """Calculate maximum diversification index."""
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
    individual_vols = np.sqrt(np.diag(cov_matrix))
    weighted_vol_sum = np.sum(weights * individual_vols)
    if portfolio_vol == 0:
        return 0.0
    return weighted_vol_sum / portfolio_vol


# =============================================================================
# Risk Parity Helper Functions
# =============================================================================

def _calculate_risk_contribution(
    weights: np.ndarray,
    cov_matrix: np.ndarray
) -> np.ndarray:
    """Calculate risk contribution of each asset."""
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
    if portfolio_vol == 0:
        return np.zeros(len(weights))
    marginal_contrib = cov_matrix @ weights / portfolio_vol
    risk_contrib = weights * marginal_contrib
    return risk_contrib


# =============================================================================
# Momentum Filtering Helper Functions
# =============================================================================

def _filter_by_momentum(
    returns: np.ndarray,
    symbols: List[str],
    momentum_period: int = 20,
    top_pct: float = 0.2
) -> Tuple[np.ndarray, List[str], np.ndarray]:
    """
    Filter assets by momentum (recent returns).
    
    Returns:
        Filtered returns, filtered symbols, mask array
    """
    if returns.ndim == 1:
        returns = returns.reshape(1, -1)
    
    # Calculate momentum (average of last N periods)
    if returns.shape[0] < momentum_period:
        momentum_period = returns.shape[0]
    
    recent_returns = returns[-momentum_period:, :]
    momentum_scores = np.mean(recent_returns, axis=0)
    
    # Select top percentage
    n_select = max(1, int(len(symbols) * top_pct))
    top_indices = np.argsort(momentum_scores)[-n_select:]
    
    mask = np.zeros(len(symbols), dtype=bool)
    mask[top_indices] = True
    
    filtered_returns = returns[:, mask]
    filtered_symbols = [symbols[i] for i in top_indices]
    
    return filtered_returns, filtered_symbols, mask


# =============================================================================
# Factor-Based Selection Helper Functions
# =============================================================================

def _calculate_factor_scores(
    factor_data: Dict[str, np.ndarray],
    factor_weights: Optional[Dict[str, float]] = None
) -> np.ndarray:
    """
    Calculate composite factor scores from multiple factors.
    
    Args:
        factor_data: Dict of factor_name -> factor_values array
        factor_weights: Optional weights for each factor (default: equal weights)
    
    Returns:
        Composite factor scores
    """
    if not factor_data:
        raise ValueError("factor_data cannot be empty")
    
    n_assets = len(next(iter(factor_data.values())))
    
    if factor_weights is None:
        factor_weights = {k: 1.0 / len(factor_data) for k in factor_data.keys()}
    
    # Normalize each factor to [0, 1] range
    normalized_factors = {}
    for factor_name, factor_values in factor_data.items():
        f_min, f_max = factor_values.min(), factor_values.max()
        if f_max > f_min:
            normalized = (factor_values - f_min) / (f_max - f_min)
        else:
            normalized = np.ones_like(factor_values)
        normalized_factors[factor_name] = normalized
    
    # Weighted sum
    composite_scores = np.zeros(n_assets)
    for factor_name, normalized_values in normalized_factors.items():
        weight = factor_weights.get(factor_name, 0.0)
        composite_scores += weight * normalized_values
    
    return composite_scores


@TemplateRegistry.register("portfolio")
class PortfolioTemplate(ProblemTemplate):
    """
    Comprehensive Portfolio Optimization Template.
    
    Supports multiple optimization objectives via the 'objective' parameter.
    
    Data format:
        {
            "expected_returns": [0.1, 0.12, 0.08, ...],  # Or pd.Series
            "covariance_matrix": [[...], ...],          # Or pd.DataFrame
            "symbols": ["AAPL", "GOOGL", ...],          # Asset names (optional if using pandas)
            
            # For methods requiring historical returns (CVaR, CDaR, Semivariance)
            "returns": [[...], ...],                    # Historical returns matrix (optional)
            
            # Optimization objective
            "objective": "min_volatility",  # See supported objectives below
            
            # Objective-specific parameters
            "risk_free_rate": 0.02,         # For max_sharpe, cla_max_sharpe
            "target_return": 0.15,          # For efficient_return, efficient_cvar_return, etc.
            "target_volatility": 0.20,      # For efficient_risk
            "target_cvar": 0.05,            # For efficient_cvar_risk
            "target_cdar": 0.10,            # For efficient_cdar_risk
            "target_semivariance": 0.02,    # For efficient_semivariance_risk
            "risk_aversion": 1.0,           # For max_utility, black_litterman
            "confidence_level": 0.05,       # For CVaR/CDaR methods (default 0.05 = 5%)
            "benchmark": 0.0,               # For semivariance (default 0.0)
            
            # Black-Litterman specific
            "market_caps": [100e9, 200e9, ...],  # Market capitalizations
            "views": [0.12, 0.15, ...],         # Investor views on returns
            "view_cov": [[...], ...],           # View covariance matrix
            "tau": 1.0,                         # BL scaling factor
            
            # Constraints (optional)
            "weight_bounds": [0, 1],        # Per-asset weight bounds
            "min_weight": 0.0,              # Minimum weight (alternative to bounds)
            "max_weight": 1.0,              # Maximum weight
            "max_assets": null,             # Maximum number of assets (cardinality)
            "min_position_size": 0.0,       # Minimum weight if asset is held (for cardinality)
            "current_weights": {...},       # Current portfolio weights (for turnover)
            "max_turnover": null,           # Maximum turnover (0.0 to 1.0)
            "transaction_costs": {...},     # Transaction costs per asset (dict or array)
            "momentum_period": 20,          # Period for momentum calculation
            "momentum_top_pct": 0.2,        # Top percentage to select by momentum
            "factor_data": {...},           # Factor data dict (factor_name -> values)
            "factor_weights": {...},         # Weights for factors (optional)
            "min_net_return": 0.0,          # Minimum net return (for cost-aware methods)
            "max_volatility": null,         # Maximum volatility (for factor-based)
        }
    
    Supported objectives:
        Efficient Frontier:
            - "min_volatility": Minimize portfolio variance
            - "max_sharpe": Maximize Sharpe ratio
            - "max_return": Maximize expected return
            - "efficient_return": Minimize volatility for target return
            - "efficient_risk": Maximize return for target volatility
            - "max_utility": Maximize quadratic utility
        
        Black-Litterman:
            - "black_litterman_max_sharpe": BL optimization for max Sharpe
            - "black_litterman_min_volatility": BL optimization for min volatility
            - "black_litterman_quadratic_utility": BL optimization with utility function
        
        CVaR (Conditional Value at Risk):
            - "min_cvar": Minimize CVaR
            - "efficient_cvar_risk": Maximize return for target CVaR
            - "efficient_cvar_return": Minimize CVaR for target return
        
        CDaR (Conditional Drawdown at Risk):
            - "min_cdar": Minimize CDaR
            - "efficient_cdar_risk": Maximize return for target CDaR
            - "efficient_cdar_return": Minimize CDaR for target return
        
        Semivariance:
            - "min_semivariance": Minimize semivariance (downside deviation)
            - "efficient_semivariance_risk": Maximize return for target semivariance
            - "efficient_semivariance_return": Minimize semivariance for target return
        
        CLA (Critical Line Algorithm):
            - "cla_min_volatility": CLA for minimum volatility
            - "cla_max_sharpe": CLA for maximum Sharpe
        
        Hierarchical:
            - "hierarchical_min_volatility": HRP for minimum volatility
            - "hierarchical_max_sharpe": HRP for maximum Sharpe
        
        Maximum Diversification:
            - "max_diversification": Maximize diversification ratio
            - "max_diversification_index": Maximize diversification index
        
        Risk Parity:
            - "risk_parity": Equal risk contribution (risk parity)
            - "equal_risk_contribution": Alias for risk_parity
        
        Transaction Cost-Aware:
            - "max_sharpe_with_costs": Maximize Sharpe ratio accounting for transaction costs
            - "min_volatility_with_costs": Minimize volatility accounting for transaction costs
        
        Momentum-Filtered:
            - "momentum_filtered_max_sharpe": Filter by momentum, then maximize Sharpe
            - "momentum_filtered_min_volatility": Filter by momentum, then minimize volatility
        
        Factor-Based:
            - "factor_based_selection": Select assets based on factor scores
    
    Result format:
        {
            "status": "optimal",
            "weights": {"AAPL": 0.25, "GOOGL": 0.35, ...},
            "portfolio_return": 0.12,
            "portfolio_volatility": 0.15,
            "sharpe_ratio": 0.67,
            "portfolio_variance": 0.0225,
            "objective_value": 0.0225
        }
    """
    
    SUPPORTED_OBJECTIVES = [
        # Efficient Frontier
        "min_volatility",
        "max_sharpe", 
        "max_return",
        "efficient_return",
        "efficient_risk",
        "max_utility",
        # Black-Litterman
        "black_litterman_max_sharpe",
        "black_litterman_min_volatility",
        "black_litterman_quadratic_utility",
        # CVaR
        "min_cvar",
        "efficient_cvar_risk",
        "efficient_cvar_return",
        # CDaR
        "min_cdar",
        "efficient_cdar_risk",
        "efficient_cdar_return",
        # Semivariance
        "min_semivariance",
        "efficient_semivariance_risk",
        "efficient_semivariance_return",
        # CLA
        "cla_min_volatility",
        "cla_max_sharpe",
        # Hierarchical
        "hierarchical_min_volatility",
        "hierarchical_max_sharpe",
        # Maximum Diversification
        "max_diversification",
        "max_diversification_index",
        # Risk Parity
        "risk_parity",
        "equal_risk_contribution",
        # Transaction Cost-Aware
        "max_sharpe_with_costs",
        "min_volatility_with_costs",
        # Momentum-Filtered
        "momentum_filtered_max_sharpe",
        "momentum_filtered_min_volatility",
        # Factor-Based
        "factor_based_selection",
    ]
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="portfolio",
            description="Comprehensive Portfolio Optimization",
            problem_type="QP",
            required_data=["expected_returns", "covariance_matrix"],
            optional_data=[
                "symbols", "objective", "weight_bounds", "min_weight", "max_weight",
                "risk_free_rate", "target_return", "target_volatility", "target_cvar",
                "target_cdar", "target_semivariance", "risk_aversion", "confidence_level",
                "benchmark", "returns", "market_caps", "views", "view_cov", "tau",
                "max_assets", "current_weights", "max_turnover", "transaction_costs",
                "momentum_period", "momentum_top_pct", "factor_data", "factor_weights",
                "min_position_size"
            ],
            default_solver="ipopt"
        )
    
    def validate_data(self, data: Union[Dict[str, Any], PortfolioConfig]) -> None:
        """Validate portfolio optimization data."""
        # Convert dict to PortfolioConfig if needed
        if isinstance(data, dict):
            config = PortfolioConfig.from_dict(data)
        else:
            config = data
        
        # Validate core data
        er, _ = _to_numpy(config.data.expected_returns)
        cov, _ = _to_numpy(config.data.covariance_matrix)
        
        n = len(er)
        if cov.shape != (n, n):
            raise ValueError(f"Covariance matrix must be {n}x{n}")
        
        objective = config.objective
        
        # Validate objective-specific requirements
        if objective in [Objective.EFFICIENT_RETURN, Objective.EFFICIENT_CVAR_RETURN, 
                         Objective.EFFICIENT_CDAR_RETURN, Objective.EFFICIENT_SEMIVARIANCE_RETURN]:
            if config.target_return is None:
                raise ValueError(f"target_return required for {objective.value} objective")
        
        if objective == Objective.EFFICIENT_RISK:
            if config.target_volatility is None:
                raise ValueError("target_volatility required for efficient_risk objective")
        
        if objective == Objective.EFFICIENT_CVAR_RISK:
            if config.target_cvar is None:
                raise ValueError("target_cvar required for efficient_cvar_risk objective")
        elif objective == Objective.EFFICIENT_CDAR_RISK:
            if config.target_cdar is None:
                raise ValueError("target_cdar required for efficient_cdar_risk objective")
        elif objective == Objective.EFFICIENT_SEMIVARIANCE_RISK:
            if config.target_semivariance is None:
                raise ValueError("target_semivariance required for efficient_semivariance_risk objective")
        
        # Methods requiring historical returns
        if objective in [Objective.MIN_CVAR, Objective.EFFICIENT_CVAR_RISK, Objective.EFFICIENT_CVAR_RETURN,
                         Objective.MIN_CDAR, Objective.EFFICIENT_CDAR_RISK, Objective.EFFICIENT_CDAR_RETURN,
                         Objective.MIN_SEMIVARIANCE, Objective.EFFICIENT_SEMIVARIANCE_RISK, Objective.EFFICIENT_SEMIVARIANCE_RETURN]:
            if config.data.returns is None:
                raise ValueError(f"returns (historical returns matrix) required for {objective.value} objective")
        
        # Black-Litterman requirements
        if objective in [Objective.BL_MAX_SHARPE, Objective.BL_MIN_VOLATILITY, Objective.BL_QUADRATIC_UTILITY]:
            if config.black_litterman is None:
                raise ValueError("black_litterman configuration required for Black-Litterman objectives")
        
        # Turnover constraint requirements
        if config.turnover is not None:
            if config.turnover.current_weights is None:
                raise ValueError("current_weights required when turnover constraint is specified")
        
        # Momentum-filtered requirements
        if objective in [Objective.MOMENTUM_FILTERED_MAX_SHARPE, Objective.MOMENTUM_FILTERED_MIN_VOLATILITY]:
            if config.momentum is None:
                raise ValueError("momentum configuration required for momentum_filtered objectives")
        
        # Factor-based requirements
        if objective == Objective.FACTOR_BASED_SELECTION:
            if config.factors is None:
                raise ValueError("factors configuration required for factor_based_selection objective")
    
    def build_model(self, config: Union[Dict[str, Any], PortfolioConfig]):
        """Build Pyomo model for portfolio optimization."""
        # Convert dict to PortfolioConfig if needed
        if isinstance(config, dict):
            config = PortfolioConfig.from_dict(config)
        
        # Parse and validate input data
        er, symbols = _to_numpy(config.data.expected_returns)
        cov, _ = _to_numpy(config.data.covariance_matrix)
        
        if symbols is None:
            symbols = config.data.symbols or [f"Asset{i}" for i in range(len(er))]
        
        n = len(er)
        objective = config.objective.value if isinstance(config.objective, Objective) else config.objective
        
        # Extract weight bounds
        min_weight = config.weight_bounds.min
        max_weight = config.weight_bounds.max
        
        # Build base model structure
        model = self._build_base_model(n, min_weight, max_weight, symbols, er, cov, objective)
        
        # Add constraints
        self._add_cardinality_constraint(model, config, n, max_weight, symbols)
        self._add_turnover_constraint(model, config, n, symbols, objective)
        self._add_per_asset_bounds_constraint(model, config, n, symbols)
        self._add_sector_constraints(model, config, n, symbols)
        
        # Build portfolio expressions
        portfolio_return = self._portfolio_return_expr(model, er)
        portfolio_variance = self._portfolio_variance_expr(model, cov)
        
        # Build objective based on type
        self._build_objective(model, config, er, cov, portfolio_return, portfolio_variance, n, symbols)
        
        return model
    
    def _build_base_model(
        self,
        n: int,
        min_weight: float,
        max_weight: float,
        symbols: List[str],
        er: np.ndarray,
        cov: np.ndarray,
        objective: str
    ) -> pyo.ConcreteModel:
        """Build base Pyomo model with variables and basic constraints."""
        model = pyo.ConcreteModel("Portfolio")
        model.assets = pyo.Set(initialize=range(n))
        
        # Weight variables
        model.weights = pyo.Var(
            model.assets,
            domain=pyo.Reals,
            bounds=(min_weight, max_weight)
        )
        
        # Weights sum to 1
        model.sum_weights = pyo.Constraint(
            expr=sum(model.weights[i] for i in model.assets) == 1
        )
        
        # Store metadata
        model._symbols = symbols
        model._expected_returns = er
        model._covariance = cov
        model._n_assets = n
        model._objective = objective
        
        return model
    
    def _add_cardinality_constraint(
        self,
        model: pyo.ConcreteModel,
        config: PortfolioConfig,
        n: int,
        max_weight: float,
        symbols: List[str]
    ) -> None:
        """Add cardinality constraint if specified."""
        if config.cardinality is None or config.cardinality.max_assets >= n:
            model._has_cardinality = False
            return
        
        cardinality = config.cardinality
        
        # Binary variables for asset selection
        model.z = pyo.Var(model.assets, domain=pyo.Binary)
        
        # Link binary variables to weights
        for i in model.assets:
            model.add_component(
                f"cardinality_lower_{i}",
                pyo.Constraint(expr=model.weights[i] >= cardinality.min_position_size * model.z[i])
            )
            model.add_component(
                f"cardinality_upper_{i}",
                pyo.Constraint(expr=model.weights[i] <= max_weight * model.z[i])
            )
        
        # Limit number of selected assets
        model.cardinality_constraint = pyo.Constraint(
            expr=sum(model.z[i] for i in model.assets) <= cardinality.max_assets
        )
        model._has_cardinality = True
    
    def _add_turnover_constraint(
        self,
        model: pyo.ConcreteModel,
        config: PortfolioConfig,
        n: int,
        symbols: List[str],
        objective: str
    ) -> None:
        """Add turnover constraint and buy/sell variables if needed."""
        has_transaction_costs = (
            config.transaction_costs is not None and 
            objective in ["max_sharpe_with_costs", "min_volatility_with_costs"]
        )
        
        # Determine if we need turnover variables
        needs_turnover = (
            config.turnover is not None or
            (has_transaction_costs and config.transaction_costs.current_weights is not None)
        )
        
        if not needs_turnover:
            model._has_turnover = False
            model._current_weights = None
            return
        
        # Get current weights from turnover or transaction costs
        current_weights = (
            config.turnover.current_weights if config.turnover 
            else config.transaction_costs.current_weights
        )
        
        # Convert current_weights to array
        if isinstance(current_weights, dict):
            current_weights_array = np.array([current_weights.get(symbols[i], 0.0) for i in range(n)])
        else:
            current_weights_array, _ = _to_numpy(current_weights)
            if len(current_weights_array) != n:
                raise ValueError(f"current_weights length ({len(current_weights_array)}) must match number of assets ({n})")
        
        # Turnover variables
        model.buy = pyo.Var(model.assets, domain=pyo.NonNegativeReals)
        model.sell = pyo.Var(model.assets, domain=pyo.NonNegativeReals)
        
        # Turnover constraints: w_new = w_old + buy - sell
        for i in model.assets:
            model.add_component(
                f"turnover_balance_{i}",
                pyo.Constraint(expr=model.weights[i] == current_weights_array[i] + model.buy[i] - model.sell[i])
            )
        
        # Total turnover constraint (if specified)
        if config.turnover is not None:
            total_turnover = sum(model.buy[i] + model.sell[i] for i in model.assets)
            model.turnover_constraint = pyo.Constraint(expr=total_turnover <= config.turnover.max_turnover)
            model._has_turnover = True
        else:
            model._has_turnover = False
        
        model._current_weights = current_weights_array
    
    def _add_per_asset_bounds_constraint(
        self,
        model: pyo.ConcreteModel,
        config: PortfolioConfig,
        n: int,
        symbols: List[str]
    ) -> None:
        """Add per-asset weight bounds if specified."""
        if config.per_asset_bounds is None or not config.per_asset_bounds.bounds:
            return
        
        bounds = config.per_asset_bounds.bounds
        
        # Override base bounds with per-asset bounds
        for i in model.assets:
            symbol = symbols[i]
            if symbol in bounds:
                min_bound, max_bound = bounds[symbol]
                # Update variable bounds
                model.weights[i].setlb(min_bound)
                model.weights[i].setub(max_bound)
    
    def _add_sector_constraints(
        self,
        model: pyo.ConcreteModel,
        config: PortfolioConfig,
        n: int,
        symbols: List[str]
    ) -> None:
        """Add sector exposure constraints if specified."""
        if config.sector_constraints is None:
            return
        
        sector_config = config.sector_constraints
        
        # Need asset_sectors mapping to apply constraints
        if not sector_config.asset_sectors:
            return
        
        # Group assets by sector
        sector_assets: Dict[str, List[int]] = {}
        for i, symbol in enumerate(symbols):
            if symbol in sector_config.asset_sectors:
                sector = sector_config.asset_sectors[symbol]
                if sector not in sector_assets:
                    sector_assets[sector] = []
                sector_assets[sector].append(i)
        
        # Add sector cap constraints
        if sector_config.sector_caps:
            for sector, max_exposure in sector_config.sector_caps.items():
                if sector in sector_assets:
                    sector_weight = sum(model.weights[i] for i in sector_assets[sector])
                    model.add_component(
                        f"sector_cap_{sector}",
                        pyo.Constraint(expr=sector_weight <= max_exposure)
                    )
        
        # Add sector minimum constraints
        if sector_config.sector_mins:
            for sector, min_exposure in sector_config.sector_mins.items():
                if sector in sector_assets:
                    sector_weight = sum(model.weights[i] for i in sector_assets[sector])
                    model.add_component(
                        f"sector_min_{sector}",
                        pyo.Constraint(expr=sector_weight >= min_exposure)
                    )
    
    def _portfolio_return_expr(self, model: pyo.ConcreteModel, er: np.ndarray) -> pyo.Expression:
        """Create portfolio return expression."""
        return sum(model.weights[i] * er[i] for i in model.assets)
    
    def _portfolio_variance_expr(self, model: pyo.ConcreteModel, cov: np.ndarray) -> pyo.Expression:
        """Create portfolio variance expression."""
        return sum(
            model.weights[i] * model.weights[j] * cov[i, j]
            for i in model.assets for j in model.assets
        )
    
    def _build_sharpe_objective(
        self,
        model: pyo.ConcreteModel,
        er: np.ndarray,
        cov: np.ndarray,
        risk_free_rate: float,
        prefix: str = ""
    ) -> None:
        """Build Sharpe ratio maximization objective (reusable helper)."""
        model.scale = pyo.Var(domain=pyo.NonNegativeReals)
        model.y = pyo.Var(model.assets, domain=pyo.NonNegativeReals)
        
        for i in model.assets:
            model.add_component(
                f"scale_link_{prefix}_{i}" if prefix else f"scale_link_{i}",
                pyo.Constraint(expr=model.y[i] == model.scale * model.weights[i])
            )
        
        excess_return = sum((er[i] - risk_free_rate) * model.weights[i] for i in model.assets)
        constraint_name = f"sharpe_normalize_{prefix}" if prefix else "sharpe_normalize"
        model.add_component(
            constraint_name,
            pyo.Constraint(expr=excess_return * model.scale == 1)
        )
        
        scaled_variance = sum(
            model.y[i] * model.y[j] * cov[i, j]
            for i in model.assets for j in model.assets
        )
        model.objective = pyo.Objective(expr=scaled_variance, sense=pyo.minimize)
    
    def _build_objective(
        self,
        model: pyo.ConcreteModel,
        config: PortfolioConfig,
        er: np.ndarray,
        cov: np.ndarray,
        portfolio_return: pyo.Expression,
        portfolio_variance: pyo.Expression,
        n: int,
        symbols: List[str]
    ) -> None:
        """Route to appropriate objective builder method."""
        objective = config.objective
        
        if objective in [Objective.MIN_VOLATILITY, Objective.MAX_RETURN, Objective.EFFICIENT_RETURN, 
                         Objective.EFFICIENT_RISK, Objective.MAX_UTILITY, Objective.MAX_SHARPE]:
            self._build_efficient_frontier_objective(model, objective, config, portfolio_return, portfolio_variance, er, cov)
        elif objective in [Objective.BL_MAX_SHARPE, Objective.BL_MIN_VOLATILITY, Objective.BL_QUADRATIC_UTILITY]:
            self._build_black_litterman_objective(model, objective, config, er, cov)
        elif objective in [Objective.MIN_CVAR, Objective.EFFICIENT_CVAR_RISK, Objective.EFFICIENT_CVAR_RETURN]:
            self._build_cvar_objective(model, objective, config, er)
        elif objective in [Objective.MIN_CDAR, Objective.EFFICIENT_CDAR_RISK, Objective.EFFICIENT_CDAR_RETURN]:
            self._build_cdar_objective(model, objective, config, er)
        elif objective in [Objective.MIN_SEMIVARIANCE, Objective.EFFICIENT_SEMIVARIANCE_RISK, Objective.EFFICIENT_SEMIVARIANCE_RETURN]:
            self._build_semivariance_objective(model, objective, config, er)
        elif objective in [Objective.MAX_DIVERSIFICATION, Objective.MAX_DIVERSIFICATION_INDEX]:
            self._build_diversification_objective(model, objective, portfolio_variance, cov)
        elif objective in [Objective.RISK_PARITY, Objective.EQUAL_RISK_CONTRIBUTION]:
            self._build_risk_parity_objective(model, portfolio_variance, cov, n)
        elif objective in [Objective.MAX_SHARPE_WITH_COSTS, Objective.MIN_VOLATILITY_WITH_COSTS]:
            self._build_transaction_cost_objective(model, objective, config, portfolio_return, portfolio_variance, er, cov, n, symbols)
        elif objective in [Objective.MOMENTUM_FILTERED_MAX_SHARPE, Objective.MOMENTUM_FILTERED_MIN_VOLATILITY]:
            self._build_momentum_filtered_objective(model, objective, config, portfolio_return, portfolio_variance, er, cov, symbols)
        elif objective == Objective.FACTOR_BASED_SELECTION:
            self._build_factor_objective(model, objective, config, portfolio_variance, n)
    
    def _build_black_litterman_returns(
        self,
        config: PortfolioConfig,
        er: np.ndarray,
        cov: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Build Black-Litterman posterior returns and covariance."""
        bl_config = config.black_litterman
        
        # Calculate prior returns
        if bl_config.market_caps is not None:
            market_caps, _ = _to_numpy(bl_config.market_caps)
            prior_returns = _market_implied_prior_returns(
                market_caps, config.risk_aversion, cov, config.risk_free_rate
            )
        else:
            prior_returns = er
        
        # Apply views if provided
        if bl_config.views is not None and bl_config.view_cov is not None:
            views, _ = _to_numpy(bl_config.views)
            view_cov, _ = _to_numpy(bl_config.view_cov)
            posterior_returns, posterior_cov = _black_litterman_returns(
                prior_returns, cov, views, view_cov, bl_config.tau
            )
        else:
            # No views - use prior
            posterior_returns = prior_returns
            posterior_cov = cov
        
        return posterior_returns, posterior_cov
    
    def _build_efficient_frontier_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        portfolio_return: pyo.Expression,
        portfolio_variance: pyo.Expression,
        er: np.ndarray,
        cov: np.ndarray
    ) -> None:
        """Build efficient frontier objectives."""
        if objective == Objective.MIN_VOLATILITY:
            model.objective = pyo.Objective(expr=portfolio_variance, sense=pyo.minimize)
        elif objective == Objective.MAX_RETURN:
            model.objective = pyo.Objective(expr=portfolio_return, sense=pyo.maximize)
        elif objective == Objective.MAX_SHARPE:
            self._build_sharpe_objective(model, er, cov, config.risk_free_rate)
        elif objective == Objective.EFFICIENT_RETURN:
            if config.target_return is None:
                raise ValueError("target_return required for efficient_return objective")
            model.return_constraint = pyo.Constraint(expr=portfolio_return >= config.target_return)
            model.objective = pyo.Objective(expr=portfolio_variance, sense=pyo.minimize)
        elif objective == Objective.EFFICIENT_RISK:
            if config.target_volatility is None:
                raise ValueError("target_volatility required for efficient_risk objective")
            target_var = config.target_volatility ** 2
            model.risk_constraint = pyo.Constraint(expr=portfolio_variance <= target_var)
            model.objective = pyo.Objective(expr=portfolio_return, sense=pyo.maximize)
        elif objective == Objective.MAX_UTILITY:
            utility = portfolio_return - config.risk_aversion * portfolio_variance
            model.objective = pyo.Objective(expr=utility, sense=pyo.maximize)
    
    def _build_black_litterman_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        er: np.ndarray,
        cov: np.ndarray
    ) -> None:
        """Build Black-Litterman objectives."""
        if config.black_litterman is None:
            raise ValueError("black_litterman configuration required for Black-Litterman objectives")
        
        bl_er, bl_cov = self._build_black_litterman_returns(config, er, cov)
        
        def bl_portfolio_return():
            return sum(model.weights[i] * bl_er[i] for i in model.assets)
        
        def bl_portfolio_variance():
            return sum(
                model.weights[i] * model.weights[j] * bl_cov[i, j]
                for i in model.assets for j in model.assets
            )
        
        if objective == Objective.BL_MAX_SHARPE:
            self._build_sharpe_objective(model, bl_er, bl_cov, config.risk_free_rate, prefix="bl")
        elif objective == Objective.BL_MIN_VOLATILITY:
            model.objective = pyo.Objective(expr=bl_portfolio_variance(), sense=pyo.minimize)
        elif objective == Objective.BL_QUADRATIC_UTILITY:
            utility = bl_portfolio_return() - config.risk_aversion * bl_portfolio_variance()
            model.objective = pyo.Objective(expr=utility, sense=pyo.maximize)
        
        # Store BL returns/cov for solution formatting
        model._bl_expected_returns = bl_er
        model._bl_covariance = bl_cov
    
    def _build_cvar_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        er: np.ndarray
    ) -> None:
        """Build CVaR objectives."""
        if config.data.returns is None:
            raise ValueError("returns (historical returns matrix) required for CVaR objectives")
        
        returns_array = self._get_returns_array(config.data.returns)
        n_scenarios = returns_array.shape[0]
        confidence_level = config.confidence_level
        
        model.alpha = pyo.Var(domain=pyo.Reals)  # VaR
        model.u = pyo.Var(range(n_scenarios), domain=pyo.NonNegativeReals)
        
        # CVaR constraints
        for s in range(n_scenarios):
            portfolio_return_scenario = sum(model.weights[i] * returns_array[s, i] for i in model.assets)
            model.add_component(
                f"cvar_constraint_{s}",
                pyo.Constraint(expr=model.u[s] >= model.alpha - portfolio_return_scenario)
            )
        
        # CVaR expression
        cvar_expr = model.alpha + (1.0 / confidence_level) * (1.0 / n_scenarios) * sum(
            model.u[s] for s in range(n_scenarios)
        )
        
        def cvar_portfolio_return():
            return sum(model.weights[i] * er[i] for i in model.assets)
        
        if objective == Objective.MIN_CVAR:
            model.objective = pyo.Objective(expr=cvar_expr, sense=pyo.minimize)
        elif objective == Objective.EFFICIENT_CVAR_RISK:
            if config.target_cvar is None:
                raise ValueError("target_cvar required for efficient_cvar_risk objective")
            model.cvar_constraint = pyo.Constraint(expr=cvar_expr <= config.target_cvar)
            model.objective = pyo.Objective(expr=cvar_portfolio_return(), sense=pyo.maximize)
        elif objective == Objective.EFFICIENT_CVAR_RETURN:
            if config.target_return is None:
                raise ValueError("target_return required for efficient_cvar_return objective")
            model.return_constraint = pyo.Constraint(expr=cvar_portfolio_return() >= config.target_return)
            model.objective = pyo.Objective(expr=cvar_expr, sense=pyo.minimize)
        
        model._returns = returns_array
        model._confidence_level = confidence_level
    
    def _build_cdar_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        er: np.ndarray
    ) -> None:
        """Build CDaR objectives."""
        if config.data.returns is None:
            raise ValueError("returns (historical returns matrix) required for CDaR objectives")
        
        returns_array = self._get_returns_array(config.data.returns)
        n_scenarios = returns_array.shape[0]
        confidence_level = config.confidence_level
        
        model.alpha = pyo.Var(domain=pyo.Reals)  # VaR for drawdowns
        model.u = pyo.Var(range(n_scenarios), domain=pyo.NonNegativeReals)
        
        # CDaR constraints
        for s in range(n_scenarios):
            portfolio_return_scenario = sum(model.weights[i] * returns_array[s, i] for i in model.assets)
            model.add_component(
                f"cdar_constraint_{s}",
                pyo.Constraint(expr=model.u[s] >= model.alpha - portfolio_return_scenario)
            )
        
        cdar_expr = model.alpha + (1.0 / confidence_level) * (1.0 / n_scenarios) * sum(
            model.u[s] for s in range(n_scenarios)
        )
        
        def cdar_portfolio_return():
            return sum(model.weights[i] * er[i] for i in model.assets)
        
        if objective == Objective.MIN_CDAR:
            model.objective = pyo.Objective(expr=cdar_expr, sense=pyo.minimize)
        elif objective == Objective.EFFICIENT_CDAR_RISK:
            if config.target_cdar is None:
                raise ValueError("target_cdar required for efficient_cdar_risk objective")
            model.cdar_constraint = pyo.Constraint(expr=cdar_expr <= config.target_cdar)
            model.objective = pyo.Objective(expr=cdar_portfolio_return(), sense=pyo.maximize)
        elif objective == Objective.EFFICIENT_CDAR_RETURN:
            if config.target_return is None:
                raise ValueError("target_return required for efficient_cdar_return objective")
            model.return_constraint = pyo.Constraint(expr=cdar_portfolio_return() >= config.target_return)
            model.objective = pyo.Objective(expr=cdar_expr, sense=pyo.minimize)
        
        model._returns = returns_array
        model._confidence_level = confidence_level
    
    def _build_semivariance_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        er: np.ndarray
    ) -> None:
        """Build semivariance objectives."""
        if config.data.returns is None:
            raise ValueError("returns (historical returns matrix) required for semivariance objectives")
        
        returns_array = self._get_returns_array(config.data.returns)
        n_scenarios = returns_array.shape[0]
        benchmark = config.benchmark
        
        model.d = pyo.Var(range(n_scenarios), domain=pyo.NonNegativeReals)
        
        # Semivariance constraints
        for s in range(n_scenarios):
            portfolio_return_scenario = sum(model.weights[i] * returns_array[s, i] for i in model.assets)
            model.add_component(
                f"semivariance_constraint_{s}",
                pyo.Constraint(expr=model.d[s] >= benchmark - portfolio_return_scenario)
            )
        
        semivariance_expr = (1.0 / n_scenarios) * sum(model.d[s] ** 2 for s in range(n_scenarios))
        
        def semivariance_portfolio_return():
            return sum(model.weights[i] * er[i] for i in model.assets)
        
        if objective == Objective.MIN_SEMIVARIANCE:
            model.objective = pyo.Objective(expr=semivariance_expr, sense=pyo.minimize)
        elif objective == Objective.EFFICIENT_SEMIVARIANCE_RISK:
            if config.target_semivariance is None:
                raise ValueError("target_semivariance required for efficient_semivariance_risk objective")
            model.semivariance_constraint = pyo.Constraint(expr=semivariance_expr <= config.target_semivariance)
            model.objective = pyo.Objective(expr=semivariance_portfolio_return(), sense=pyo.maximize)
        elif objective == Objective.EFFICIENT_SEMIVARIANCE_RETURN:
            if config.target_return is None:
                raise ValueError("target_return required for efficient_semivariance_return objective")
            model.return_constraint = pyo.Constraint(expr=semivariance_portfolio_return() >= config.target_return)
            model.objective = pyo.Objective(expr=semivariance_expr, sense=pyo.minimize)
        
        model._returns = returns_array
        model._benchmark = benchmark
    
    def _build_diversification_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        portfolio_variance: pyo.Expression,
        cov: np.ndarray
    ) -> None:
        """Build maximum diversification objectives."""
        individual_vols = np.sqrt(np.diag(cov))
        portfolio_vol = pyo.sqrt(portfolio_variance)
        
        if objective == Objective.MAX_DIVERSIFICATION:
            weighted_avg_vol = sum(model.weights[i] * individual_vols[i] for i in model.assets)
            model.objective = pyo.Objective(expr=-weighted_avg_vol / (portfolio_vol + 1e-8), sense=pyo.minimize)
        else:  # MAX_DIVERSIFICATION_INDEX
            weighted_vol_sum = sum(model.weights[i] * individual_vols[i] for i in model.assets)
            model.objective = pyo.Objective(expr=-weighted_vol_sum / (portfolio_vol + 1e-8), sense=pyo.minimize)
    
    def _build_risk_parity_objective(
        self,
        model: pyo.ConcreteModel,
        portfolio_variance: pyo.Expression,
        cov: np.ndarray,
        n: int
    ) -> None:
        """Build risk parity objective."""
        portfolio_vol = pyo.sqrt(portfolio_variance)
        target_risk_contrib = 1.0 / n
        
        risk_contrib_diff = sum(
            (model.weights[i] * sum(cov[i, j] * model.weights[j] for j in model.assets) / (portfolio_vol + 1e-8) - target_risk_contrib) ** 2
            for i in model.assets
        )
        model.objective = pyo.Objective(expr=risk_contrib_diff, sense=pyo.minimize)
    
    def _build_transaction_cost_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        portfolio_return: pyo.Expression,
        portfolio_variance: pyo.Expression,
        er: np.ndarray,
        cov: np.ndarray,
        n: int,
        symbols: List[str]
    ) -> None:
        """Build transaction cost-aware objectives."""
        if config.transaction_costs is None:
            raise ValueError("transaction_costs configuration required for transaction cost-aware objectives")
        
        tc = config.transaction_costs
        if isinstance(tc.costs, dict):
            cost_array = np.array([tc.costs.get(symbols[i], 0.0) for i in range(n)])
        else:
            cost_array, _ = _to_numpy(tc.costs)
            if len(cost_array) != n:
                cost_array = np.full(n, float(tc.costs) if isinstance(tc.costs, (int, float)) else 0.0)
        
        # Calculate transaction costs
        if hasattr(model, 'buy') and hasattr(model, 'sell'):
            total_costs = sum(
                (model.buy[i] + model.sell[i]) * cost_array[i] for i in model.assets
            )
        elif tc.current_weights is not None:
            if isinstance(tc.current_weights, dict):
                current_weights_array = np.array([tc.current_weights.get(symbols[i], 0.0) for i in range(n)])
            else:
                current_weights_array, _ = _to_numpy(tc.current_weights)
                if len(current_weights_array) != n:
                    current_weights_array = np.zeros(n)
            
            # Create buy/sell variables
            model.buy = pyo.Var(model.assets, domain=pyo.NonNegativeReals)
            model.sell = pyo.Var(model.assets, domain=pyo.NonNegativeReals)
            
            for i in model.assets:
                model.add_component(
                    f"cost_turnover_balance_{i}",
                    pyo.Constraint(expr=model.weights[i] == current_weights_array[i] + model.buy[i] - model.sell[i])
                )
            
            total_costs = sum(
                (model.buy[i] + model.sell[i]) * cost_array[i] for i in model.assets
            )
        else:
            total_costs = sum(model.weights[i] * cost_array[i] for i in model.assets)
        
        if objective == Objective.MAX_SHARPE_WITH_COSTS:
            net_return = portfolio_return - total_costs
            excess_return = net_return - config.risk_free_rate
            
            # Build Sharpe objective with net return
            model.scale = pyo.Var(domain=pyo.NonNegativeReals)
            model.y = pyo.Var(model.assets, domain=pyo.NonNegativeReals)
            
            for i in model.assets:
                model.add_component(
                    f"scale_link_costs_{i}",
                    pyo.Constraint(expr=model.y[i] == model.scale * model.weights[i])
                )
            
            model.add_component(
                "sharpe_normalize_costs",
                pyo.Constraint(expr=excess_return * model.scale == 1)
            )
            
            scaled_variance = sum(
                model.y[i] * model.y[j] * cov[i, j]
                for i in model.assets for j in model.assets
            )
            model.objective = pyo.Objective(expr=scaled_variance, sense=pyo.minimize)
        else:  # MIN_VOLATILITY_WITH_COSTS
            model.net_return_constraint = pyo.Constraint(expr=portfolio_return - total_costs >= config.min_net_return)
            model.objective = pyo.Objective(expr=portfolio_variance, sense=pyo.minimize)
    
    def _build_momentum_filtered_objective(
        self,
        model: pyo.ConcreteModel,
        objective: str,
        data: Dict[str, Any],
        portfolio_return: pyo.Expression,
        portfolio_variance: pyo.Expression,
        er: np.ndarray,
        cov: np.ndarray,
        symbols: List[str]
    ) -> None:
        """Build momentum-filtered objectives."""
        returns_array = self._get_returns_array(data)
        momentum_period = data.get("momentum_period", 20)
        momentum_top_pct = data.get("momentum_top_pct", 0.2)
        
        _, filtered_symbols, momentum_mask = _filter_by_momentum(
            returns_array, symbols, momentum_period, momentum_top_pct
        )
        
        model._momentum_mask = momentum_mask
        
        # Add momentum filter constraints
        for i in model.assets:
            if not momentum_mask[i]:
                model.add_component(
                    f"momentum_filter_{i}",
                    pyo.Constraint(expr=model.weights[i] == 0)
                )
        
        # Build underlying objective
        if objective == "momentum_filtered_max_sharpe":
            rf = data.get("risk_free_rate", 0.0)
            self._build_sharpe_objective(model, er, cov, rf, prefix="momentum")
        else:  # momentum_filtered_min_volatility
            model.objective = pyo.Objective(expr=portfolio_variance, sense=pyo.minimize)
    
    def _build_factor_objective(
        self,
        model: pyo.ConcreteModel,
        objective: Objective,
        config: PortfolioConfig,
        portfolio_variance: pyo.Expression,
        n: int
    ) -> None:
        """Build factor-based selection objective."""
        if config.factors is None:
            raise ValueError("factors configuration required for factor-based selection objective")
        
        factors = config.factors
        factor_scores = _calculate_factor_scores(factors.factor_data, factors.factor_weights)
        
        # Normalize factor scores
        f_min, f_max = factor_scores.min(), factor_scores.max()
        if f_max > f_min:
            normalized_scores = (factor_scores - f_min) / (f_max - f_min)
        else:
            normalized_scores = np.ones_like(factor_scores)
        
        factor_objective = sum(model.weights[i] * normalized_scores[i] for i in model.assets)
        
        if config.max_volatility is not None:
            max_variance = config.max_volatility ** 2
            model.risk_constraint = pyo.Constraint(expr=portfolio_variance <= max_variance)
        
        model.objective = pyo.Objective(expr=-factor_objective, sense=pyo.minimize)
        model._factor_scores = normalized_scores
    
    def _get_returns_array(self, returns: Union[List[List[float]], np.ndarray]) -> np.ndarray:
        """Get historical returns array."""
        returns_array, _ = _to_numpy(returns)
        
        # Ensure 2D array
        if returns_array.ndim == 1:
            returns_array = returns_array.reshape(1, -1)
        
        return returns_array
    
    def solve(
        self,
        data: Union[Dict[str, Any], PortfolioConfig],
        solver: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Solve portfolio optimization."""
        self.validate_data(data)
        
        # Convert dict to PortfolioConfig if needed
        if isinstance(data, dict):
            config = PortfolioConfig.from_dict(data)
        else:
            config = data
        
        objective = config.objective
        
        # Handle non-Pyomo methods (CLA, Hierarchical)
        if objective in [Objective.CLA_MIN_VOLATILITY, Objective.CLA_MAX_SHARPE]:
            return self._solve_cla(config, solver, options)
        elif objective in [Objective.HIERARCHICAL_MIN_VOLATILITY, Objective.HIERARCHICAL_MAX_SHARPE]:
            return self._solve_hierarchical(config, solver, options)
        
        # Build and solve Pyomo model
        model = self.build_model(config)
        solver_name = solver or self.info.default_solver
        opt = _get_solver_factory(solver_name)
        
        options = options or {}
        
        # Set default solver options for complex objectives
        if objective in [Objective.MIN_CVAR, Objective.EFFICIENT_CVAR_RISK, Objective.EFFICIENT_CVAR_RETURN,
                         Objective.MIN_CDAR, Objective.EFFICIENT_CDAR_RISK, Objective.EFFICIENT_CDAR_RETURN,
                         Objective.MIN_SEMIVARIANCE, Objective.EFFICIENT_SEMIVARIANCE_RISK, Objective.EFFICIENT_SEMIVARIANCE_RETURN]:
            # CVaR/CDaR/Semivariance methods may need more iterations
            if solver_name == "ipopt" and "max_iter" not in options:
                opt.options["max_iter"] = 5000
            if solver_name == "ipopt" and "tol" not in options:
                opt.options["tol"] = 1e-6
        
        for key, value in options.items():
            if hasattr(opt, "options"):
                opt.options[key] = value
        
        try:
            results = opt.solve(model, tee=options.get("verbose", False))
            
            if results.solver.status == SolverStatus.ok:
                if results.solver.termination_condition == TerminationCondition.optimal:
                    status = "optimal"
                else:
                    status = "feasible"
            else:
                return {
                    "status": "infeasible",
                    "message": str(results.solver.termination_condition)
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
        
        return self.format_solution(model, None, config)
    
    def _solve_cla(
        self,
        config: PortfolioConfig,
        solver: Optional[str],
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Solve using Critical Line Algorithm."""
        er, symbols = _to_numpy(config.data.expected_returns)
        cov, _ = _to_numpy(config.data.covariance_matrix)
        
        if symbols is None:
            symbols = config.data.symbols or [f"Asset{i}" for i in range(len(er))]
        
        weight_bounds = (config.weight_bounds.min, config.weight_bounds.max)
        objective = config.objective
        
        if objective == Objective.CLA_MAX_SHARPE:
            weights = _cla_optimize(er, cov, weight_bounds, "max_sharpe", config.risk_free_rate)
        else:
            weights = _cla_optimize(er, cov, weight_bounds, "min_volatility")
        
        # Format solution
        weights_dict = {symbols[i]: float(weights[i]) for i in range(len(symbols))}
        weight_array = weights
        
        portfolio_return = float(weight_array @ er)
        portfolio_variance = float(weight_array @ cov @ weight_array)
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        sharpe_ratio = (portfolio_return - config.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        return {
            "status": "optimal",
            "weights": weights_dict,
            "portfolio_return": portfolio_return,
            "portfolio_volatility": portfolio_volatility,
            "portfolio_variance": portfolio_variance,
            "sharpe_ratio": sharpe_ratio,
            "objective_value": portfolio_variance if objective == Objective.CLA_MIN_VOLATILITY else -sharpe_ratio
        }
    
    def _solve_hierarchical(
        self,
        config: PortfolioConfig,
        solver: Optional[str],
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Solve using Hierarchical Risk Parity."""
        er, symbols = _to_numpy(config.data.expected_returns)
        cov, _ = _to_numpy(config.data.covariance_matrix)
        
        if symbols is None:
            symbols = config.data.symbols or [f"Asset{i}" for i in range(len(er))]
        
        # Get HRP weights
        weights = _hrp_optimize(cov)
        
        # Format solution
        weights_dict = {symbols[i]: float(weights[i]) for i in range(len(symbols))}
        weight_array = weights
        
        portfolio_return = float(weight_array @ er)
        portfolio_variance = float(weight_array @ cov @ weight_array)
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        sharpe_ratio = (portfolio_return - config.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        return {
            "status": "optimal",
            "weights": weights_dict,
            "portfolio_return": portfolio_return,
            "portfolio_volatility": portfolio_volatility,
            "portfolio_variance": portfolio_variance,
            "sharpe_ratio": sharpe_ratio,
            "objective_value": portfolio_variance
        }
    
    def format_solution(
        self,
        model,
        result: Optional[OptimizationResult],
        config: Union[Dict[str, Any], PortfolioConfig]
    ) -> Dict[str, Any]:
        """Format portfolio solution."""
        # Convert dict to PortfolioConfig if needed
        if isinstance(config, dict):
            config_obj = PortfolioConfig.from_dict(config)
        else:
            config_obj = config
        
        symbols = model._symbols
        n = model._n_assets
        objective_str = model._objective
        
        # Extract weights
        weights = {}
        weight_array = np.zeros(n)
        for i in range(n):
            w = pyo.value(model.weights[i])
            weights[symbols[i]] = w
            weight_array[i] = w
        
        # Calculate portfolio metrics
        objective = Objective(objective_str) if objective_str in [obj.value for obj in Objective] else None
        
        if objective in [Objective.BL_MAX_SHARPE, Objective.BL_MIN_VOLATILITY, Objective.BL_QUADRATIC_UTILITY]:
            er = model._bl_expected_returns
            cov = model._bl_covariance
        else:
            er = model._expected_returns
            cov = model._covariance
        
        # For methods that use historical returns, calculate expected return from mean
        if objective in [Objective.MIN_CVAR, Objective.EFFICIENT_CVAR_RISK, Objective.EFFICIENT_CVAR_RETURN,
                         Objective.MIN_CDAR, Objective.EFFICIENT_CDAR_RISK, Objective.EFFICIENT_CDAR_RETURN,
                         Objective.MIN_SEMIVARIANCE, Objective.EFFICIENT_SEMIVARIANCE_RISK, Objective.EFFICIENT_SEMIVARIANCE_RETURN]:
            # Use expected returns if available, otherwise calculate from historical returns
            if hasattr(model, '_returns'):
                returns_array = model._returns
                # Calculate expected returns as mean of historical returns
                er_from_returns = np.mean(returns_array, axis=0)
                portfolio_return = float(weight_array @ er_from_returns)
            else:
                portfolio_return = float(weight_array @ er)
        else:
            portfolio_return = float(weight_array @ er)
        
        portfolio_variance = float(weight_array @ cov @ weight_array)
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        sharpe_ratio = (portfolio_return - config_obj.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        result_dict = {
            "status": "optimal",
            "weights": weights,
            "portfolio_return": portfolio_return,
            "portfolio_volatility": portfolio_volatility,
            "portfolio_variance": portfolio_variance,
            "sharpe_ratio": sharpe_ratio,
            "objective_value": float(pyo.value(model.objective))
        }
        
        # Add method-specific metrics
        if objective in [Objective.MIN_CVAR, Objective.EFFICIENT_CVAR_RISK, Objective.EFFICIENT_CVAR_RETURN]:
            returns_array = model._returns
            confidence_level = model._confidence_level
            cvar = _calculate_cvar(returns_array, weight_array, confidence_level)
            result_dict["cvar"] = -cvar  # Return positive CVaR
        
        if objective in [Objective.MIN_CDAR, Objective.EFFICIENT_CDAR_RISK, Objective.EFFICIENT_CDAR_RETURN]:
            returns_array = model._returns
            confidence_level = model._confidence_level
            cdar = _calculate_cdar(returns_array, weight_array, confidence_level)
            result_dict["cdar"] = -cdar  # Return positive CDaR
        
        if objective in [Objective.MIN_SEMIVARIANCE, Objective.EFFICIENT_SEMIVARIANCE_RISK, Objective.EFFICIENT_SEMIVARIANCE_RETURN]:
            returns_array = model._returns
            benchmark = model._benchmark
            semivariance = _calculate_semivariance(returns_array, weight_array, benchmark)
            result_dict["semivariance"] = semivariance
            result_dict["sortino_ratio"] = (portfolio_return - config_obj.risk_free_rate) / np.sqrt(semivariance) if semivariance > 0 else 0
        
        # Maximum Diversification metrics
        if objective in [Objective.MAX_DIVERSIFICATION, Objective.MAX_DIVERSIFICATION_INDEX]:
            diversification_ratio = _calculate_diversification_ratio(weight_array, cov)
            diversification_index = _calculate_diversification_index(weight_array, cov)
            result_dict["diversification_ratio"] = diversification_ratio
            result_dict["diversification_index"] = diversification_index
        
        # Risk Parity metrics
        if objective in [Objective.RISK_PARITY, Objective.EQUAL_RISK_CONTRIBUTION]:
            risk_contributions = _calculate_risk_contribution(weight_array, cov)
            result_dict["risk_contributions"] = {symbols[i]: float(risk_contributions[i]) for i in range(n)}
            result_dict["risk_contribution_std"] = float(np.std(risk_contributions))
        
        # Transaction cost metrics
        if objective in [Objective.MAX_SHARPE_WITH_COSTS, Objective.MIN_VOLATILITY_WITH_COSTS]:
            if config_obj.transaction_costs is None:
                transaction_costs = {}
            else:
                transaction_costs = config_obj.transaction_costs.costs
            
            if isinstance(transaction_costs, dict):
                cost_array = np.array([transaction_costs.get(symbols[i], 0.0) for i in range(n)])
            else:
                cost_array, _ = _to_numpy(transaction_costs)
                if len(cost_array) != n:
                    cost_array = np.full(n, float(transaction_costs) if isinstance(transaction_costs, (int, float)) else 0.0)
            
            if model._has_turnover:
                buy_weights = np.array([pyo.value(model.buy[i]) for i in range(n)])
                sell_weights = np.array([pyo.value(model.sell[i]) for i in range(n)])
                total_costs = float(np.sum((buy_weights + sell_weights) * cost_array))
            else:
                if config_obj.transaction_costs and config_obj.transaction_costs.current_weights:
                    current_weights = config_obj.transaction_costs.current_weights
                    if isinstance(current_weights, dict):
                        current_weights_array = np.array([current_weights.get(symbols[i], 0.0) for i in range(n)])
                    else:
                        current_weights_array, _ = _to_numpy(current_weights)
                    total_costs = float(np.sum(np.abs(weight_array - current_weights_array) * cost_array))
                else:
                    total_costs = float(np.sum(weight_array * cost_array))
            
            result_dict["transaction_costs"] = total_costs
            result_dict["net_return"] = portfolio_return - total_costs
            result_dict["net_sharpe_ratio"] = (result_dict["net_return"] - config_obj.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Cardinality metrics
        if hasattr(model, '_has_cardinality') and model._has_cardinality:
            selected_assets = sum(1 for i in range(n) if weight_array[i] > 1e-6)
            result_dict["num_assets"] = selected_assets
            result_dict["cardinality"] = selected_assets
        
        # Turnover metrics
        if hasattr(model, '_has_turnover') and model._has_turnover:
            buy_weights = np.array([pyo.value(model.buy[i]) for i in range(n)])
            sell_weights = np.array([pyo.value(model.sell[i]) for i in range(n)])
            total_turnover = float(np.sum(buy_weights + sell_weights))
            result_dict["turnover"] = total_turnover
        
        # Factor-based metrics
        if objective == Objective.FACTOR_BASED_SELECTION and hasattr(model, '_factor_scores'):
            factor_scores = model._factor_scores
            weighted_factor_score = float(np.sum(weight_array * factor_scores))
            result_dict["weighted_factor_score"] = weighted_factor_score
            result_dict["factor_scores"] = {symbols[i]: float(factor_scores[i]) for i in range(n)}
        
        return result_dict
