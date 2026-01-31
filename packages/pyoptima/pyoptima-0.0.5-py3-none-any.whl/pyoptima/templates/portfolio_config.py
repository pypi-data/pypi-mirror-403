"""
Portfolio optimization configuration structures.

Provides clean, type-safe configuration for portfolio optimization.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class Objective(Enum):
    """Portfolio optimization objectives."""
    # Efficient Frontier
    MIN_VOLATILITY = "min_volatility"
    MAX_SHARPE = "max_sharpe"
    MAX_RETURN = "max_return"
    EFFICIENT_RETURN = "efficient_return"
    EFFICIENT_RISK = "efficient_risk"
    MAX_UTILITY = "max_utility"
    
    # Black-Litterman
    BL_MAX_SHARPE = "black_litterman_max_sharpe"
    BL_MIN_VOLATILITY = "black_litterman_min_volatility"
    BL_QUADRATIC_UTILITY = "black_litterman_quadratic_utility"
    
    # CVaR
    MIN_CVAR = "min_cvar"
    EFFICIENT_CVAR_RISK = "efficient_cvar_risk"
    EFFICIENT_CVAR_RETURN = "efficient_cvar_return"
    
    # CDaR
    MIN_CDAR = "min_cdar"
    EFFICIENT_CDAR_RISK = "efficient_cdar_risk"
    EFFICIENT_CDAR_RETURN = "efficient_cdar_return"
    
    # Semivariance
    MIN_SEMIVARIANCE = "min_semivariance"
    EFFICIENT_SEMIVARIANCE_RISK = "efficient_semivariance_risk"
    EFFICIENT_SEMIVARIANCE_RETURN = "efficient_semivariance_return"
    
    # CLA
    CLA_MIN_VOLATILITY = "cla_min_volatility"
    CLA_MAX_SHARPE = "cla_max_sharpe"
    
    # Hierarchical
    HIERARCHICAL_MIN_VOLATILITY = "hierarchical_min_volatility"
    HIERARCHICAL_MAX_SHARPE = "hierarchical_max_sharpe"
    
    # Maximum Diversification
    MAX_DIVERSIFICATION = "max_diversification"
    MAX_DIVERSIFICATION_INDEX = "max_diversification_index"
    
    # Risk Parity
    RISK_PARITY = "risk_parity"
    EQUAL_RISK_CONTRIBUTION = "equal_risk_contribution"
    
    # Transaction Cost-Aware
    MAX_SHARPE_WITH_COSTS = "max_sharpe_with_costs"
    MIN_VOLATILITY_WITH_COSTS = "min_volatility_with_costs"
    
    # Momentum-Filtered
    MOMENTUM_FILTERED_MAX_SHARPE = "momentum_filtered_max_sharpe"
    MOMENTUM_FILTERED_MIN_VOLATILITY = "momentum_filtered_min_volatility"
    
    # Factor-Based
    FACTOR_BASED_SELECTION = "factor_based_selection"


@dataclass
class WeightBounds:
    """Weight bounds configuration."""
    min: float = 0.0
    max: float = 1.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeightBounds":
        """Create from dictionary."""
        if "weight_bounds" in data:
            bounds = data["weight_bounds"]
            return cls(min=bounds[0], max=bounds[1])
        return cls(
            min=data.get("min_weight", 0.0),
            max=data.get("max_weight", 1.0)
        )


@dataclass
class CardinalityConstraint:
    """Cardinality constraint configuration."""
    max_assets: int
    min_position_size: float = 0.0


@dataclass
class TurnoverConstraint:
    """Turnover constraint configuration."""
    current_weights: Union[Dict[str, float], np.ndarray, List[float]]
    max_turnover: float


@dataclass
class TransactionCosts:
    """Transaction cost configuration."""
    costs: Union[Dict[str, float], List[float], float]
    current_weights: Optional[Union[Dict[str, float], np.ndarray, List[float]]] = None


@dataclass
class BlackLittermanConfig:
    """Black-Litterman configuration."""
    market_caps: Optional[Union[List[float], np.ndarray]] = None
    views: Optional[Union[List[float], np.ndarray]] = None
    view_cov: Optional[Union[List[List[float]], np.ndarray]] = None
    tau: float = 1.0


@dataclass
class MomentumConfig:
    """Momentum filtering configuration."""
    returns: Union[List[List[float]], np.ndarray]
    period: int = 20
    top_pct: float = 0.2


@dataclass
class FactorConfig:
    """Factor-based selection configuration."""
    factor_data: Dict[str, Union[List[float], np.ndarray]]
    factor_weights: Optional[Dict[str, float]] = None


@dataclass
class PerAssetBounds:
    """Per-asset weight bounds configuration."""
    bounds: Dict[str, Tuple[float, float]]  # Asset symbol -> (min, max)


@dataclass
class SectorConstraints:
    """Sector constraint configuration."""
    sector_caps: Optional[Dict[str, float]] = None  # Sector -> max exposure
    sector_mins: Optional[Dict[str, float]] = None  # Sector -> min exposure
    asset_sectors: Dict[str, str] = field(default_factory=dict)  # Asset -> sector mapping


@dataclass
class PortfolioData:
    """Core portfolio data."""
    expected_returns: Union[List[float], np.ndarray, pd.Series]
    covariance_matrix: Union[List[List[float]], np.ndarray, pd.DataFrame]
    symbols: Optional[List[str]] = None
    returns: Optional[Union[List[List[float]], np.ndarray]] = None  # Historical returns for CVaR/CDaR/Semivariance


@dataclass
class PortfolioConfig:
    """Complete portfolio optimization configuration."""
    data: PortfolioData
    objective: Objective = Objective.MIN_VOLATILITY
    
    # Weight bounds
    weight_bounds: WeightBounds = field(default_factory=WeightBounds)
    
    # Objective parameters
    risk_free_rate: float = 0.0
    target_return: Optional[float] = None
    target_volatility: Optional[float] = None
    target_cvar: Optional[float] = None
    target_cdar: Optional[float] = None
    target_semivariance: Optional[float] = None
    risk_aversion: float = 1.0
    confidence_level: float = 0.05
    benchmark: float = 0.0
    min_net_return: float = 0.0
    max_volatility: Optional[float] = None
    
    # Constraints
    cardinality: Optional[CardinalityConstraint] = None
    turnover: Optional[TurnoverConstraint] = None
    transaction_costs: Optional[TransactionCosts] = None
    per_asset_bounds: Optional[PerAssetBounds] = None
    sector_constraints: Optional[SectorConstraints] = None
    
    # Method-specific configs
    black_litterman: Optional[BlackLittermanConfig] = None
    momentum: Optional[MomentumConfig] = None
    factors: Optional[FactorConfig] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioConfig":
        """Create from flat dictionary."""
        # Extract core data
        portfolio_data = PortfolioData(
            expected_returns=data["expected_returns"],
            covariance_matrix=data["covariance_matrix"],
            symbols=data.get("symbols"),
            returns=data.get("returns")
        )
        
        # Extract objective
        objective_str = data.get("objective", "min_volatility")
        try:
            objective = Objective(objective_str)
        except ValueError:
            # Fallback: try to find by value
            objective = next((obj for obj in Objective if obj.value == objective_str), Objective.MIN_VOLATILITY)
        
        # Extract weight bounds
        weight_bounds = WeightBounds.from_dict(data)
        
        # Extract constraints
        cardinality = None
        if "max_assets" in data:
            cardinality = CardinalityConstraint(
                max_assets=data["max_assets"],
                min_position_size=data.get("min_position_size", 0.0)
            )
        
        turnover = None
        if "max_turnover" in data and "current_weights" in data:
            turnover = TurnoverConstraint(
                current_weights=data["current_weights"],
                max_turnover=data["max_turnover"]
            )
        
        transaction_costs = None
        if "transaction_costs" in data:
            transaction_costs = TransactionCosts(
                costs=data["transaction_costs"],
                current_weights=data.get("current_weights")
            )
        
        # Extract method-specific configs
        bl_config = None
        if any(k in data for k in ["market_caps", "views", "view_cov"]):
            bl_config = BlackLittermanConfig(
                market_caps=data.get("market_caps"),
                views=data.get("views"),
                view_cov=data.get("view_cov"),
                tau=data.get("tau", 1.0)
            )
        
        momentum_config = None
        if "returns" in data and objective_str.startswith("momentum_filtered"):
            momentum_config = MomentumConfig(
                returns=data["returns"],
                period=data.get("momentum_period", 20),
                top_pct=data.get("momentum_top_pct", 0.2)
            )
        
        factor_config = None
        if "factor_data" in data:
            factor_config = FactorConfig(
                factor_data=data["factor_data"],
                factor_weights=data.get("factor_weights")
            )
        
        # Extract per-asset bounds
        per_asset_bounds = None
        if "per_asset_bounds" in data:
            bounds_dict = data["per_asset_bounds"]
            # Convert list format [min, max] to tuple if needed
            converted_bounds = {}
            for asset, bounds in bounds_dict.items():
                if isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                    converted_bounds[asset] = (float(bounds[0]), float(bounds[1]))
                else:
                    converted_bounds[asset] = bounds
            per_asset_bounds = PerAssetBounds(bounds=converted_bounds)
        
        # Extract sector constraints
        sector_constraints = None
        if any(k in data for k in ["sector_caps", "sector_mins", "asset_sectors"]):
            sector_constraints = SectorConstraints(
                sector_caps=data.get("sector_caps"),
                sector_mins=data.get("sector_mins"),
                asset_sectors=data.get("asset_sectors", {})
            )
        
        return cls(
            data=portfolio_data,
            objective=objective,
            weight_bounds=weight_bounds,
            risk_free_rate=data.get("risk_free_rate", 0.0),
            target_return=data.get("target_return"),
            target_volatility=data.get("target_volatility"),
            target_cvar=data.get("target_cvar"),
            target_cdar=data.get("target_cdar"),
            target_semivariance=data.get("target_semivariance"),
            risk_aversion=data.get("risk_aversion", 1.0),
            confidence_level=data.get("confidence_level", 0.05),
            benchmark=data.get("benchmark", 0.0),
            min_net_return=data.get("min_net_return", 0.0),
            max_volatility=data.get("max_volatility"),
            cardinality=cardinality,
            turnover=turnover,
            transaction_costs=transaction_costs,
            per_asset_bounds=per_asset_bounds,
            sector_constraints=sector_constraints,
            black_litterman=bl_config,
            momentum=momentum_config,
            factors=factor_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary."""
        result = {
            "expected_returns": self.data.expected_returns,
            "covariance_matrix": self.data.covariance_matrix,
            "objective": self.objective.value,
        }
        
        if self.data.symbols:
            result["symbols"] = self.data.symbols
        if self.data.returns is not None:
            result["returns"] = self.data.returns
        
        # Weight bounds
        if self.weight_bounds.min != 0.0 or self.weight_bounds.max != 1.0:
            result["weight_bounds"] = [self.weight_bounds.min, self.weight_bounds.max]
        
        # Objective parameters
        if self.risk_free_rate != 0.0:
            result["risk_free_rate"] = self.risk_free_rate
        if self.target_return is not None:
            result["target_return"] = self.target_return
        if self.target_volatility is not None:
            result["target_volatility"] = self.target_volatility
        if self.target_cvar is not None:
            result["target_cvar"] = self.target_cvar
        if self.target_cdar is not None:
            result["target_cdar"] = self.target_cdar
        if self.target_semivariance is not None:
            result["target_semivariance"] = self.target_semivariance
        if self.risk_aversion != 1.0:
            result["risk_aversion"] = self.risk_aversion
        if self.confidence_level != 0.05:
            result["confidence_level"] = self.confidence_level
        if self.benchmark != 0.0:
            result["benchmark"] = self.benchmark
        if self.min_net_return != 0.0:
            result["min_net_return"] = self.min_net_return
        if self.max_volatility is not None:
            result["max_volatility"] = self.max_volatility
        
        # Constraints
        if self.cardinality:
            result["max_assets"] = self.cardinality.max_assets
            if self.cardinality.min_position_size != 0.0:
                result["min_position_size"] = self.cardinality.min_position_size
        
        if self.turnover:
            result["current_weights"] = self.turnover.current_weights
            result["max_turnover"] = self.turnover.max_turnover
        
        if self.transaction_costs:
            result["transaction_costs"] = self.transaction_costs.costs
            if self.transaction_costs.current_weights:
                result["current_weights"] = self.transaction_costs.current_weights
        
        if self.per_asset_bounds:
            result["per_asset_bounds"] = self.per_asset_bounds.bounds
        
        if self.sector_constraints:
            if self.sector_constraints.sector_caps:
                result["sector_caps"] = self.sector_constraints.sector_caps
            if self.sector_constraints.sector_mins:
                result["sector_mins"] = self.sector_constraints.sector_mins
            if self.sector_constraints.asset_sectors:
                result["asset_sectors"] = self.sector_constraints.asset_sectors
        
        # Method-specific configs
        if self.black_litterman:
            if self.black_litterman.market_caps is not None:
                result["market_caps"] = self.black_litterman.market_caps
            if self.black_litterman.views is not None:
                result["views"] = self.black_litterman.views
            if self.black_litterman.view_cov is not None:
                result["view_cov"] = self.black_litterman.view_cov
            if self.black_litterman.tau != 1.0:
                result["tau"] = self.black_litterman.tau
        
        if self.momentum:
            result["returns"] = self.momentum.returns
            if self.momentum.period != 20:
                result["momentum_period"] = self.momentum.period
            if self.momentum.top_pct != 0.2:
                result["momentum_top_pct"] = self.momentum.top_pct
        
        if self.factors:
            result["factor_data"] = self.factors.factor_data
            if self.factors.factor_weights:
                result["factor_weights"] = self.factors.factor_weights
        
        return result
