"""
Turnover and transaction cost constraints.

Constraints for limiting portfolio changes.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class MaxTurnover(BaseConstraint):
    """
    Maximum turnover constraint.
    
    Limits the total change from current portfolio weights.
    
    Example:
        >>> # Maximum 20% turnover
        >>> constraint = MaxTurnover(
        ...     max_turnover=0.2,
        ...     current_weights={"AAPL": 0.3, "GOOGL": 0.4, "MSFT": 0.3}
        ... )
    """
    
    name = "max_turnover"
    
    def __init__(
        self,
        max_turnover: float,
        current_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize max turnover constraint.
        
        Args:
            max_turnover: Maximum allowed turnover (sum of |new - old|)
            current_weights: Current portfolio weights
                            (can also be provided in solve() data)
        """
        self.max_turnover = max_turnover
        self.current_weights = current_weights
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply turnover constraint."""
        data["_max_turnover"] = self.max_turnover
        if self.current_weights:
            data["_current_weights"] = self.current_weights


class TransactionCosts(BaseConstraint):
    """
    Transaction cost constraint.
    
    Can be used with cost-aware objectives or as a constraint
    on total transaction costs.
    
    Example:
        >>> # Per-asset transaction costs
        >>> constraint = TransactionCosts(
        ...     costs={"AAPL": 0.001, "GOOGL": 0.0015},  # 0.1% and 0.15%
        ...     current_weights={"AAPL": 0.3, "GOOGL": 0.4},
        ...     max_cost=0.005  # Max 0.5% total cost
        ... )
    """
    
    name = "transaction_costs"
    
    def __init__(
        self,
        costs: Union[float, Dict[str, float]],
        current_weights: Optional[Dict[str, float]] = None,
        max_cost: Optional[float] = None,
    ):
        """
        Initialize transaction costs.
        
        Args:
            costs: Transaction cost per unit traded.
                   Can be single value or per-asset dict.
            current_weights: Current portfolio weights
            max_cost: Maximum total transaction cost (optional constraint)
        """
        self.costs = costs
        self.current_weights = current_weights
        self.max_cost = max_cost
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply transaction cost constraint."""
        data["_transaction_costs"] = self.costs
        if self.current_weights:
            data["_current_weights"] = self.current_weights
        if self.max_cost is not None:
            data["_max_transaction_cost"] = self.max_cost
