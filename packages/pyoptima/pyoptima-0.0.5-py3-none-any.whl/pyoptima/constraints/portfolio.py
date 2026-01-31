"""
Portfolio-specific constraints.

Common constraints for portfolio optimization.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class ExclusionList(BaseConstraint):
    """
    Exclude specific assets from the portfolio (weight forced to zero).

    Example:
        >>> constraint = ExclusionList(["AAPL", "TSLA"])
        >>> # Or from a set
        >>> constraint = ExclusionList({"sin_stocks", "tobacco_ticker"})
    """

    name = "exclusion_list"

    def __init__(self, symbols: Union[List[str], Set[str], tuple]):
        """
        Args:
            symbols: Asset symbols to exclude (weight will be 0).
        """
        self.symbols = list(symbols) if not isinstance(symbols, (list, tuple)) else list(symbols)

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        data["_excluded_assets"] = self.symbols


class InclusionList(BaseConstraint):
    """
    Restrict the portfolio to only the listed assets (all others forced to zero).

    Example:
        >>> constraint = InclusionList(["AAPL", "MSFT", "GOOGL"])
    """

    name = "inclusion_list"

    def __init__(self, symbols: Union[List[str], Set[str], tuple]):
        """
        Args:
            symbols: Only these assets may have non-zero weight.
        """
        self.symbols = list(symbols) if not isinstance(symbols, (list, tuple)) else list(symbols)

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        data["_inclusion_list"] = self.symbols


class SumToOne(BaseConstraint):
    """
    Sum of weights must equal one (fully invested).
    
    Example:
        >>> constraint = SumToOne()
    """
    
    name = "sum_to_one"
    
    def __init__(self):
        """Initialize sum-to-one constraint."""
        pass
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply sum-to-one constraint."""
        data["_sum_to_one"] = True


class MinReturn(BaseConstraint):
    """
    Minimum expected return constraint.
    
    Example:
        >>> # Minimum 10% expected return
        >>> constraint = MinReturn(0.10)
    """
    
    name = "min_return"
    
    def __init__(self, min_return: float):
        """
        Initialize minimum return constraint.
        
        Args:
            min_return: Minimum expected portfolio return
        """
        self.min_return = min_return
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply minimum return constraint."""
        data["_min_return"] = self.min_return


class MaxReturn(BaseConstraint):
    """
    Maximum expected return constraint.
    
    Rarely used directly, but available for efficient frontier exploration.
    
    Example:
        >>> constraint = MaxReturn(0.20)
    """
    
    name = "max_return"
    
    def __init__(self, max_return: float):
        """
        Initialize maximum return constraint.
        
        Args:
            max_return: Maximum expected portfolio return
        """
        self.max_return = max_return
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply maximum return constraint."""
        data["_max_return"] = self.max_return
