"""
Risk constraints.

Constraints for limiting portfolio risk measures.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class MaxConcentration(BaseConstraint):
    """
    Maximum combined weight in the top K assets (concentration limit).

    Example:
        >>> # No more than 60% in top 3 assets
        >>> constraint = MaxConcentration(max_weight=0.60, top_k=3)
    """

    name = "max_concentration"

    def __init__(self, max_weight: float, top_k: int = 1):
        """
        Args:
            max_weight: Maximum total weight allowed in top K assets.
            top_k: Number of largest positions to limit.
        """
        self.max_weight = max_weight
        self.top_k = top_k

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        data["_max_concentration"] = (self.max_weight, self.top_k)


class TrackingErrorLimit(BaseConstraint):
    """
    Maximum tracking error versus a benchmark.

    Requires benchmark returns in solve() data when the template supports it.

    Example:
        >>> constraint = TrackingErrorLimit(max_tracking_error=0.02)
    """

    name = "tracking_error_limit"

    def __init__(self, max_tracking_error: float):
        """
        Args:
            max_tracking_error: Maximum allowed tracking error (e.g. 0.02 = 2%).
        """
        self.max_tracking_error = max_tracking_error

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        data["_max_tracking_error"] = self.max_tracking_error


class MaxVolatility(BaseConstraint):
    """
    Maximum volatility constraint.
    
    Example:
        >>> # Maximum 20% annualized volatility
        >>> constraint = MaxVolatility(0.2)
    """
    
    name = "max_volatility"
    
    def __init__(self, max_volatility: float):
        """
        Initialize max volatility constraint.
        
        Args:
            max_volatility: Maximum portfolio volatility (standard deviation)
        """
        self.max_volatility = max_volatility
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply volatility constraint."""
        data["_max_volatility"] = self.max_volatility


class MaxCVaR(BaseConstraint):
    """
    Maximum Conditional Value at Risk (CVaR) constraint.
    
    Example:
        >>> # Maximum 5% CVaR at 95% confidence
        >>> constraint = MaxCVaR(max_cvar=0.05, confidence=0.95)
    """
    
    name = "max_cvar"
    
    def __init__(
        self,
        max_cvar: float,
        confidence: float = 0.95,
    ):
        """
        Initialize max CVaR constraint.
        
        Args:
            max_cvar: Maximum CVaR
            confidence: Confidence level (default: 0.95)
        """
        self.max_cvar = max_cvar
        self.confidence = confidence
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply CVaR constraint."""
        data["_max_cvar"] = self.max_cvar
        data["_cvar_confidence"] = self.confidence


class MaxDrawdown(BaseConstraint):
    """
    Maximum drawdown constraint.
    
    Example:
        >>> # Maximum 15% drawdown
        >>> constraint = MaxDrawdown(0.15)
    """
    
    name = "max_drawdown"
    
    def __init__(self, max_drawdown: float):
        """
        Initialize max drawdown constraint.
        
        Args:
            max_drawdown: Maximum allowed drawdown
        """
        self.max_drawdown = max_drawdown
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply drawdown constraint."""
        data["_max_drawdown"] = self.max_drawdown
