"""
Portfolio Optimizer - sklearn-style API for portfolio optimization.

Provides a clean, composable interface to all portfolio optimization objectives.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from pyoptima.core.result import OptimizationResult, SolverStatus
from pyoptima.core.protocols import Constraint, ConstraintSet
from pyoptima.estimators.base import BaseOptimizer


# All supported objectives
OBJECTIVES = [
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


class PortfolioOptimizer(BaseOptimizer):
    """
    sklearn-style portfolio optimizer.
    
    Provides a clean interface to all portfolio optimization objectives with
    composable constraints and get_params/set_params pattern.
    
    Example:
        >>> from pyoptima import PortfolioOptimizer, WeightBounds, SumToOne
        >>> 
        >>> # Create optimizer
        >>> opt = PortfolioOptimizer(
        ...     objective="min_volatility",
        ...     constraints=[WeightBounds(0, 0.4), SumToOne()]
        ... )
        >>> 
        >>> # Solve
        >>> result = opt.solve(
        ...     expected_returns=[0.1, 0.12, 0.08],
        ...     covariance_matrix=[[0.04, 0.01, 0.02], ...],
        ...     symbols=["AAPL", "GOOGL", "MSFT"]
        ... )
        >>> 
        >>> # Access results
        >>> print(result.weights)
        >>> print(result.sharpe_ratio)
        >>> df = result.weights_to_dataframe()
    
    All sklearn conventions are supported:
        >>> opt.get_params()  # Get all parameters
        >>> opt.set_params(risk_free_rate=0.02)  # Update parameters
        >>> clone(opt, objective="max_sharpe")  # Clone with different params
    
    Objectives:
        Efficient Frontier: min_volatility, max_sharpe, max_return, 
            efficient_return, efficient_risk, max_utility
        Black-Litterman: black_litterman_max_sharpe, black_litterman_min_volatility,
            black_litterman_quadratic_utility
        CVaR: min_cvar, efficient_cvar_risk, efficient_cvar_return
        CDaR: min_cdar, efficient_cdar_risk, efficient_cdar_return
        Semivariance: min_semivariance, efficient_semivariance_risk, 
            efficient_semivariance_return
        CLA: cla_min_volatility, cla_max_sharpe
        Hierarchical: hierarchical_min_volatility, hierarchical_max_sharpe
        Diversification: max_diversification, max_diversification_index
        Risk Parity: risk_parity, equal_risk_contribution
        Transaction Costs: max_sharpe_with_costs, min_volatility_with_costs
        Momentum: momentum_filtered_max_sharpe, momentum_filtered_min_volatility
        Factor: factor_based_selection
    """
    
    def __init__(
        self,
        objective: str = "min_volatility",
        constraints: Optional[List[Constraint]] = None,
        # Basic parameters
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        risk_free_rate: float = 0.0,
        # Target parameters
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None,
        target_cvar: Optional[float] = None,
        target_cdar: Optional[float] = None,
        target_semivariance: Optional[float] = None,
        # Risk parameters
        risk_aversion: float = 1.0,
        confidence_level: float = 0.05,
        benchmark: float = 0.0,
        # Cardinality
        max_assets: Optional[int] = None,
        min_position_size: float = 0.0,
        # Turnover
        max_turnover: Optional[float] = None,
        # Solver
        solver: str = "ipopt",
        solver_options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize portfolio optimizer.
        
        Args:
            objective: Optimization objective (see class docstring for options)
            constraints: List of constraint objects
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
            risk_free_rate: Risk-free rate for Sharpe calculations
            target_return: Target return for efficient_return objective
            target_volatility: Target volatility for efficient_risk objective
            target_cvar: Target CVaR for efficient_cvar_risk objective
            target_cdar: Target CDaR for efficient_cdar_risk objective
            target_semivariance: Target semivariance for efficient_semivariance_risk
            risk_aversion: Risk aversion for utility objectives
            confidence_level: Confidence level for CVaR/CDaR (default 0.05 = 95%)
            benchmark: Benchmark return for semivariance
            max_assets: Maximum number of assets (cardinality constraint)
            min_position_size: Minimum position size when using max_assets
            max_turnover: Maximum turnover constraint
            solver: Solver name (default: "ipopt")
            solver_options: Additional solver options
        """
        if objective not in OBJECTIVES:
            raise ValueError(
                f"Unknown objective '{objective}'. "
                f"Supported: {', '.join(OBJECTIVES)}"
            )
        
        self.objective = objective
        self.constraints = constraints or []
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.risk_free_rate = risk_free_rate
        self.target_return = target_return
        self.target_volatility = target_volatility
        self.target_cvar = target_cvar
        self.target_cdar = target_cdar
        self.target_semivariance = target_semivariance
        self.risk_aversion = risk_aversion
        self.confidence_level = confidence_level
        self.benchmark = benchmark
        self.max_assets = max_assets
        self.min_position_size = min_position_size
        self.max_turnover = max_turnover
        self.solver = solver
        self.solver_options = solver_options or {}
        self._config: Optional[Any] = None  # set by from_config for solve() with no args

    @classmethod
    def from_config(
        cls,
        config: Union["OptimizationConfig", Dict[str, Any], str, Path],
    ) -> "PortfolioOptimizer":
        """
        Build a PortfolioOptimizer from a config file or dict.

        Config must have template="portfolio" and data with objective,
        expected_returns, covariance_matrix (and optionally symbols, solver, etc.).
        After from_config, call opt.solve() with no args to run with config data.

        Args:
            config: Path to .json/.yaml, or dict, or OptimizationConfig.

        Returns:
            Configured PortfolioOptimizer.

        Example:
            opt = PortfolioOptimizer.from_config("min_volatility.json")
            result = opt.solve()
        """
        from pyoptima.config import OptimizationConfig, load_config, load_config_file

        if isinstance(config, (str, Path)):
            loaded = load_config_file(config)
        elif isinstance(config, dict):
            loaded = load_config(config)
        else:
            loaded = config

        if getattr(loaded, "template", None) != "portfolio":
            raise ValueError(
                "PortfolioOptimizer.from_config requires template='portfolio'. "
                f"Got template={getattr(loaded, 'template', None)}."
            )

        data = loaded.data
        solver_cfg = loaded.solver

        # Map config data to optimizer __init__ params
        objective = data.get("objective", "min_volatility")
        weight_bounds = data.get("weight_bounds")
        if weight_bounds is not None and len(weight_bounds) == 2:
            min_weight, max_weight = float(weight_bounds[0]), float(weight_bounds[1])
        else:
            min_weight = data.get("min_weight", 0.0)
            max_weight = data.get("max_weight", 1.0)

        solver_options = dict(solver_cfg.options)
        if solver_cfg.time_limit is not None:
            solver_options["time_limit"] = solver_cfg.time_limit
        solver_options["verbose"] = solver_cfg.verbose

        opt = cls(
            objective=objective,
            min_weight=min_weight,
            max_weight=max_weight,
            risk_free_rate=data.get("risk_free_rate", 0.0),
            target_return=data.get("target_return"),
            target_volatility=data.get("target_volatility"),
            target_cvar=data.get("target_cvar"),
            target_cdar=data.get("target_cdar"),
            target_semivariance=data.get("target_semivariance"),
            risk_aversion=data.get("risk_aversion", 1.0),
            confidence_level=data.get("confidence_level", 0.05),
            benchmark=data.get("benchmark", 0.0),
            max_assets=data.get("max_assets"),
            min_position_size=data.get("min_position_size", 0.0),
            max_turnover=data.get("max_turnover"),
            solver=solver_cfg.name,
            solver_options=solver_options,
        )
        opt._config = loaded
        return opt

    def solve(self, **data: Any) -> OptimizationResult:
        """Solve the portfolio problem. If no kwargs and this optimizer was built from_config, use config data."""
        if not data and getattr(self, "_config", None) is not None:
            data = dict(self._config.data)
        return super().solve(**data)

    def add_constraint(self, constraint: Constraint) -> "PortfolioOptimizer":
        """
        Add a constraint to the optimizer.
        
        Args:
            constraint: Constraint to add
            
        Returns:
            self for method chaining
        """
        self.constraints.append(constraint)
        return self
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
        """Validate input data."""
        if "expected_returns" not in data:
            raise ValueError("expected_returns required")
        if "covariance_matrix" not in data:
            raise ValueError("covariance_matrix required")
        
        # Validate dimensions
        er = data["expected_returns"]
        cov = data["covariance_matrix"]
        
        if hasattr(er, "__len__"):
            n = len(er)
        else:
            raise ValueError("expected_returns must be array-like")
        
        if hasattr(cov, "shape"):
            if cov.shape != (n, n):
                raise ValueError(f"covariance_matrix must be {n}x{n}")
        elif hasattr(cov, "__len__"):
            if len(cov) != n:
                raise ValueError(f"covariance_matrix must be {n}x{n}")
        
        # Validate objective-specific requirements
        if self.objective in ["efficient_return", "efficient_cvar_return", 
                              "efficient_cdar_return", "efficient_semivariance_return"]:
            if self.target_return is None:
                raise ValueError(f"target_return required for {self.objective}")
        
        if self.objective == "efficient_risk":
            if self.target_volatility is None:
                raise ValueError("target_volatility required for efficient_risk")
        
        if self.objective == "efficient_cvar_risk":
            if self.target_cvar is None:
                raise ValueError("target_cvar required for efficient_cvar_risk")
        
        if self.objective == "efficient_cdar_risk":
            if self.target_cdar is None:
                raise ValueError("target_cdar required for efficient_cdar_risk")
        
        if self.objective == "efficient_semivariance_risk":
            if self.target_semivariance is None:
                raise ValueError("target_semivariance required for efficient_semivariance_risk")
        
        # Methods requiring historical returns
        cvar_cdar_objectives = [
            "min_cvar", "efficient_cvar_risk", "efficient_cvar_return",
            "min_cdar", "efficient_cdar_risk", "efficient_cdar_return",
            "min_semivariance", "efficient_semivariance_risk", "efficient_semivariance_return",
        ]
        if self.objective in cvar_cdar_objectives:
            if "returns" not in data:
                raise ValueError(f"returns (historical returns) required for {self.objective}")
    
    def _solve(self, **data) -> OptimizationResult:
        """
        Solve the portfolio optimization problem.
        
        Args:
            **data: Problem data including:
                - expected_returns: Expected returns for each asset
                - covariance_matrix: Covariance matrix
                - symbols: Optional asset symbols
                - returns: Historical returns (for CVaR/CDaR/Semivariance)
                - current_weights: Current weights (for turnover)
                - sector_caps/mins: Sector constraints
                - asset_sectors: Asset to sector mapping
                
        Returns:
            OptimizationResult with solution
        """
        # Import template
        from pyoptima.templates.portfolio import PortfolioTemplate
        from pyoptima.templates.portfolio_config import PortfolioConfig
        
        # Build config dict
        config_dict = self._build_config_dict(data)
        
        # Apply constraints
        self._apply_constraints(config_dict, data)
        
        # Create template and solve
        template = PortfolioTemplate()
        
        try:
            result_dict = template.solve(
                config_dict,
                solver=self.solver,
                options=self.solver_options
            )
        except Exception as e:
            return OptimizationResult(
                status=SolverStatus.ERROR,
                solver_message=str(e),
            )
        
        # Convert to OptimizationResult
        return self._convert_result(result_dict, data)
    
    def _build_config_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build configuration dictionary for template."""
        config = {
            "expected_returns": data["expected_returns"],
            "covariance_matrix": data["covariance_matrix"],
            "objective": self.objective,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "risk_free_rate": self.risk_free_rate,
            "risk_aversion": self.risk_aversion,
            "confidence_level": self.confidence_level,
            "benchmark": self.benchmark,
        }
        
        # Optional fields
        if "symbols" in data:
            config["symbols"] = data["symbols"]
        
        if "returns" in data:
            config["returns"] = data["returns"]
        
        # Target parameters
        if self.target_return is not None:
            config["target_return"] = self.target_return
        if self.target_volatility is not None:
            config["target_volatility"] = self.target_volatility
        if self.target_cvar is not None:
            config["target_cvar"] = self.target_cvar
        if self.target_cdar is not None:
            config["target_cdar"] = self.target_cdar
        if self.target_semivariance is not None:
            config["target_semivariance"] = self.target_semivariance
        
        # Cardinality
        if self.max_assets is not None:
            config["max_assets"] = self.max_assets
            config["min_position_size"] = self.min_position_size
        
        # Turnover
        if self.max_turnover is not None and "current_weights" in data:
            config["max_turnover"] = self.max_turnover
            config["current_weights"] = data["current_weights"]
        
        # Transaction costs (from data)
        if "transaction_costs" in data:
            config["transaction_costs"] = data["transaction_costs"]
            if "current_weights" in data:
                config["current_weights"] = data["current_weights"]
        
        # Black-Litterman
        if "market_caps" in data:
            config["market_caps"] = data["market_caps"]
        if "views" in data:
            config["views"] = data["views"]
        if "view_cov" in data:
            config["view_cov"] = data["view_cov"]
        if "tau" in data:
            config["tau"] = data["tau"]
        
        # Momentum
        if "momentum_period" in data:
            config["momentum_period"] = data["momentum_period"]
        if "momentum_top_pct" in data:
            config["momentum_top_pct"] = data["momentum_top_pct"]
        
        # Factor
        if "factor_data" in data:
            config["factor_data"] = data["factor_data"]
        if "factor_weights" in data:
            config["factor_weights"] = data["factor_weights"]
        if "max_volatility" in data:
            config["max_volatility"] = data["max_volatility"]
        
        # Sector constraints (from data)
        if "sector_caps" in data:
            config["sector_caps"] = data["sector_caps"]
        if "sector_mins" in data:
            config["sector_mins"] = data["sector_mins"]
        if "asset_sectors" in data:
            config["asset_sectors"] = data["asset_sectors"]
        
        # Per-asset bounds (from data)
        if "per_asset_bounds" in data:
            config["per_asset_bounds"] = data["per_asset_bounds"]
        
        return config
    
    def _apply_constraints(self, config: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Apply constraints to config dictionary."""
        for constraint in self.constraints:
            # Apply constraint to a temporary data dict
            temp_data = dict(data)
            constraint.apply(None, temp_data)  # type: ignore
            
            # Extract constraint data into config
            if "_max_volatility" in temp_data:
                config["max_volatility"] = temp_data["_max_volatility"]
            if "_sector_caps" in temp_data:
                config["sector_caps"] = temp_data["_sector_caps"]
            if "_sector_mins" in temp_data:
                config["sector_mins"] = temp_data["_sector_mins"]
            if "_asset_sectors" in temp_data:
                config["asset_sectors"] = temp_data["_asset_sectors"]
            if "_max_assets" in temp_data:
                config["max_assets"] = temp_data["_max_assets"]
            if "_min_assets" in temp_data:
                config["min_assets"] = temp_data["_min_assets"]
            if "_min_position_size" in temp_data:
                config["min_position_size"] = temp_data["_min_position_size"]
            if "_max_turnover" in temp_data:
                config["max_turnover"] = temp_data["_max_turnover"]
            if "_current_weights" in temp_data:
                config["current_weights"] = temp_data["_current_weights"]
            if "_transaction_costs" in temp_data:
                config["transaction_costs"] = temp_data["_transaction_costs"]
            if "_max_transaction_cost" in temp_data:
                config["max_transaction_cost"] = temp_data["_max_transaction_cost"]
            if "_min_return" in temp_data:
                config["target_return"] = temp_data["_min_return"]
            if "_max_return" in temp_data:
                config["max_return"] = temp_data["_max_return"]
            if "_sum_to_one" in temp_data:
                pass
            # Exclusion/inclusion -> per_asset_bounds (0, 0)
            if "_excluded_assets" in temp_data:
                excluded = set(temp_data["_excluded_assets"])
                symbols = data.get("symbols") or []
                per_asset = dict(config.get("per_asset_bounds", {}))
                for sym in excluded:
                    if sym in symbols or not symbols:
                        per_asset[sym] = (0.0, 0.0)
                if per_asset:
                    config["per_asset_bounds"] = {**config.get("per_asset_bounds", {}), **per_asset}
            if "_inclusion_list" in temp_data:
                allowed = set(temp_data["_inclusion_list"])
                symbols = list(data.get("symbols") or [])
                if symbols:
                    per_asset = {sym: (0.0, 0.0) for sym in symbols if sym not in allowed}
                    if per_asset:
                        config["per_asset_bounds"] = {**config.get("per_asset_bounds", {}), **per_asset}
            if "_max_gross_exposure" in temp_data:
                config["max_gross_exposure"] = temp_data["_max_gross_exposure"]
            if "_net_exposure" in temp_data:
                config["net_exposure"] = temp_data["_net_exposure"]
            if "_max_concentration" in temp_data:
                config["max_concentration"] = temp_data["_max_concentration"]
            if "_factor_exposure_limits" in temp_data:
                config["factor_exposure_limits"] = temp_data["_factor_exposure_limits"]
                if "_asset_factors" in temp_data:
                    config["asset_factors"] = temp_data["_asset_factors"]
            if "_max_tracking_error" in temp_data:
                config["max_tracking_error"] = temp_data["_max_tracking_error"]
            if "_linear_constraints" in temp_data:
                config["linear_constraints"] = temp_data["_linear_constraints"]
    
    def _convert_result(self, result_dict: Dict[str, Any], data: Dict[str, Any]) -> OptimizationResult:
        """Convert template result to OptimizationResult."""
        status_str = result_dict.get("status", "unknown")
        
        if status_str == "optimal":
            status = SolverStatus.OPTIMAL
        elif status_str == "feasible":
            status = SolverStatus.FEASIBLE
        elif status_str == "infeasible":
            status = SolverStatus.INFEASIBLE
        elif status_str == "unbounded":
            status = SolverStatus.UNBOUNDED
        elif status_str == "error":
            status = SolverStatus.ERROR
        else:
            status = SolverStatus.UNKNOWN
        
        return OptimizationResult(
            status=status,
            objective_value=result_dict.get("objective_value"),
            solution=result_dict.get("weights", {}),
            solver_name=self.solver,
            solver_message=result_dict.get("message"),
            problem_type="QP",
            # Portfolio-specific
            weights=result_dict.get("weights"),
            portfolio_return=result_dict.get("portfolio_return"),
            portfolio_volatility=result_dict.get("portfolio_volatility"),
            sharpe_ratio=result_dict.get("sharpe_ratio"),
            metadata={
                "portfolio_variance": result_dict.get("portfolio_variance"),
                "objective": self.objective,
                **{k: v for k, v in result_dict.items() 
                   if k not in ["status", "objective_value", "weights", 
                               "portfolio_return", "portfolio_volatility", 
                               "sharpe_ratio", "portfolio_variance", "message"]},
            }
        )
    
    @staticmethod
    def list_objectives() -> List[str]:
        """List all supported objectives."""
        return list(OBJECTIVES)


# Convenience aliases
def min_volatility(**kwargs) -> PortfolioOptimizer:
    """Create optimizer for minimum volatility."""
    return PortfolioOptimizer(objective="min_volatility", **kwargs)


def max_sharpe(**kwargs) -> PortfolioOptimizer:
    """Create optimizer for maximum Sharpe ratio."""
    return PortfolioOptimizer(objective="max_sharpe", **kwargs)


def max_return(**kwargs) -> PortfolioOptimizer:
    """Create optimizer for maximum return."""
    return PortfolioOptimizer(objective="max_return", **kwargs)


def efficient_frontier(
    expected_returns,
    covariance_matrix,
    n_points: int = 50,
    symbols: Optional[List[str]] = None,
    **kwargs,
) -> List[OptimizationResult]:
    """
    Generate efficient frontier points.
    
    Args:
        expected_returns: Expected returns
        covariance_matrix: Covariance matrix
        n_points: Number of points on frontier
        symbols: Asset symbols
        **kwargs: Additional optimizer parameters
        
    Returns:
        List of OptimizationResult for each frontier point
    """
    if not HAS_NUMPY:
        raise ImportError("numpy required for efficient_frontier")
    
    # Get return range
    er = np.array(expected_returns)
    min_ret = er.min()
    max_ret = er.max()
    
    results = []
    
    for target in np.linspace(min_ret, max_ret, n_points):
        opt = PortfolioOptimizer(
            objective="efficient_return",
            target_return=float(target),
            **kwargs
        )
        
        data = {
            "expected_returns": expected_returns,
            "covariance_matrix": covariance_matrix,
        }
        if symbols:
            data["symbols"] = symbols
        
        result = opt.solve(**data)
        if result.is_feasible:
            results.append(result)
    
    return results
