"""
Portfolio optimization objectives.

Common objectives for portfolio optimization problems.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from pyoptima.objectives.base import BaseObjective

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class MinVolatility(BaseObjective):
    """
    Minimize portfolio volatility (variance).
    
    Example:
        >>> objective = MinVolatility()
    """
    
    name = "min_volatility"
    sense = "minimize"
    
    def __init__(self):
        pass
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build minimum volatility objective."""
        data["_objective"] = "min_volatility"


class MaxSharpe(BaseObjective):
    """
    Maximize Sharpe ratio.
    
    Example:
        >>> objective = MaxSharpe(risk_free_rate=0.02)
    """
    
    name = "max_sharpe"
    sense = "maximize"
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize max Sharpe objective.
        
        Args:
            risk_free_rate: Risk-free rate (default: 0)
        """
        self.risk_free_rate = risk_free_rate
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build max Sharpe objective."""
        data["_objective"] = "max_sharpe"
        data["_risk_free_rate"] = self.risk_free_rate


class MaxReturn(BaseObjective):
    """
    Maximize expected return.
    
    Example:
        >>> objective = MaxReturn()
    """
    
    name = "max_return"
    sense = "maximize"
    
    def __init__(self):
        pass
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build max return objective."""
        data["_objective"] = "max_return"


class EfficientReturn(BaseObjective):
    """
    Minimize volatility for a target return.
    
    Example:
        >>> objective = EfficientReturn(target_return=0.10)
    """
    
    name = "efficient_return"
    sense = "minimize"
    
    def __init__(self, target_return: float):
        """
        Initialize efficient return objective.
        
        Args:
            target_return: Target expected return
        """
        self.target_return = target_return
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build efficient return objective."""
        data["_objective"] = "efficient_return"
        data["_target_return"] = self.target_return


class EfficientRisk(BaseObjective):
    """
    Maximize return for a target volatility.
    
    Example:
        >>> objective = EfficientRisk(target_volatility=0.15)
    """
    
    name = "efficient_risk"
    sense = "maximize"
    
    def __init__(self, target_volatility: float):
        """
        Initialize efficient risk objective.
        
        Args:
            target_volatility: Target portfolio volatility
        """
        self.target_volatility = target_volatility
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build efficient risk objective."""
        data["_objective"] = "efficient_risk"
        data["_target_volatility"] = self.target_volatility


class MaxUtility(BaseObjective):
    """
    Maximize quadratic utility (return - 0.5 * risk_aversion * variance).
    
    Example:
        >>> objective = MaxUtility(risk_aversion=1.0)
    """
    
    name = "max_utility"
    sense = "maximize"
    
    def __init__(self, risk_aversion: float = 1.0):
        """
        Initialize max utility objective.
        
        Args:
            risk_aversion: Risk aversion parameter (default: 1.0)
        """
        self.risk_aversion = risk_aversion
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build max utility objective."""
        data["_objective"] = "max_utility"
        data["_risk_aversion"] = self.risk_aversion


class MinCVaR(BaseObjective):
    """
    Minimize Conditional Value at Risk (CVaR).
    
    Example:
        >>> objective = MinCVaR(confidence=0.95)
    """
    
    name = "min_cvar"
    sense = "minimize"
    
    def __init__(self, confidence: float = 0.95):
        """
        Initialize min CVaR objective.
        
        Args:
            confidence: Confidence level (default: 0.95)
        """
        self.confidence = confidence
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build min CVaR objective."""
        data["_objective"] = "min_cvar"
        data["_confidence"] = self.confidence


class MinCDaR(BaseObjective):
    """
    Minimize Conditional Drawdown at Risk (CDaR).
    
    Example:
        >>> objective = MinCDaR(confidence=0.95)
    """
    
    name = "min_cdar"
    sense = "minimize"
    
    def __init__(self, confidence: float = 0.95):
        """
        Initialize min CDaR objective.
        
        Args:
            confidence: Confidence level (default: 0.95)
        """
        self.confidence = confidence
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build min CDaR objective."""
        data["_objective"] = "min_cdar"
        data["_confidence"] = self.confidence


class MinSemivariance(BaseObjective):
    """
    Minimize semivariance (downside deviation).
    
    Example:
        >>> objective = MinSemivariance(benchmark=0.0)
    """
    
    name = "min_semivariance"
    sense = "minimize"
    
    def __init__(self, benchmark: float = 0.0):
        """
        Initialize min semivariance objective.
        
        Args:
            benchmark: Benchmark return (default: 0)
        """
        self.benchmark = benchmark
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build min semivariance objective."""
        data["_objective"] = "min_semivariance"
        data["_benchmark"] = self.benchmark


class RiskParity(BaseObjective):
    """
    Risk parity (equal risk contribution).
    
    Example:
        >>> objective = RiskParity()
    """
    
    name = "risk_parity"
    sense = "minimize"  # Minimizes risk contribution deviation
    
    def __init__(self):
        pass
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build risk parity objective."""
        data["_objective"] = "risk_parity"


class MaxDiversification(BaseObjective):
    """
    Maximize diversification ratio.
    
    Example:
        >>> objective = MaxDiversification()
    """
    
    name = "max_diversification"
    sense = "maximize"
    
    def __init__(self):
        pass
    
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Build max diversification objective."""
        data["_objective"] = "max_diversification"
