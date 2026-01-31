"""
Weight bound constraints.

Constraints for limiting portfolio weights.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class WeightBounds(BaseConstraint):
    """
    Global weight bounds for all assets.
    
    Example:
        >>> # Weights between 0% and 40%
        >>> constraint = WeightBounds(min_weight=0.0, max_weight=0.4)
        >>> 
        >>> # Or shorthand
        >>> constraint = WeightBounds(0, 0.4)
    """
    
    name = "weight_bounds"
    
    def __init__(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
    ):
        """
        Initialize weight bounds.
        
        Args:
            min_weight: Minimum weight for each asset (default: 0.0)
            max_weight: Maximum weight for each asset (default: 1.0)
        """
        self.min_weight = min_weight
        self.max_weight = max_weight
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply weight bounds to all variables."""
        # Get weight variables
        weights = data.get("_weights_var")
        if weights is None:
            return
        
        n_assets = len(weights) if hasattr(weights, "__len__") else data.get("n_assets", 0)
        
        for i in range(n_assets):
            if hasattr(weights[i], "setlb"):
                weights[i].setlb(self.min_weight)
                weights[i].setub(self.max_weight)


class PerAssetBounds(BaseConstraint):
    """
    Per-asset weight bounds.
    
    Example:
        >>> constraint = PerAssetBounds({
        ...     "AAPL": (0.0, 0.3),
        ...     "GOOGL": (0.05, 0.25),
        ...     "MSFT": (0.0, 0.4),
        ... })
    """
    
    name = "per_asset_bounds"
    
    def __init__(self, bounds: Dict[str, Tuple[float, float]]):
        """
        Initialize per-asset bounds.
        
        Args:
            bounds: Dictionary mapping asset symbol to (min, max) tuple
        """
        self.bounds = bounds
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply per-asset bounds."""
        weights = data.get("_weights_var")
        symbols = data.get("symbols", [])
        
        if weights is None:
            return
        
        for i, symbol in enumerate(symbols):
            if symbol in self.bounds:
                min_w, max_w = self.bounds[symbol]
                if hasattr(weights[i], "setlb"):
                    weights[i].setlb(min_w)
                    weights[i].setub(max_w)


class LongOnly(BaseConstraint):
    """
    Long-only constraint (no short selling).
    
    Equivalent to WeightBounds(0, 1).
    
    Example:
        >>> constraint = LongOnly()
    """
    
    name = "long_only"
    
    def __init__(self):
        """Initialize long-only constraint."""
        pass
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply long-only constraint (weights >= 0)."""
        weights = data.get("_weights_var")
        if weights is None:
            return
        
        n_assets = len(weights) if hasattr(weights, "__len__") else data.get("n_assets", 0)
        
        for i in range(n_assets):
            if hasattr(weights[i], "setlb"):
                weights[i].setlb(0.0)


class GrossExposure(BaseConstraint):
    """
    Maximum gross exposure (sum of absolute weights).

    Common for long-short or 130/30 portfolios.

    Example:
        >>> # Max 150% gross (e.g. 100% long + 50% short)
        >>> constraint = GrossExposure(1.5)
    """

    name = "gross_exposure"

    def __init__(self, max_gross: float):
        """
        Args:
            max_gross: Maximum sum of |weights| (e.g. 1.0 = long-only, 1.5 = 130/30).
        """
        self.max_gross = max_gross

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        data["_max_gross_exposure"] = self.max_gross


class LongShort(BaseConstraint):
    """
    Long-short constraint allowing short positions.
    
    Example:
        >>> # Allow -50% to +100% positions
        >>> constraint = LongShort(min_weight=-0.5, max_weight=1.0)
    """
    
    name = "long_short"
    
    def __init__(
        self,
        min_weight: float = -1.0,
        max_weight: float = 1.0,
        gross_exposure: Optional[float] = None,
        net_exposure: Optional[Tuple[float, float]] = None,
    ):
        """
        Initialize long-short constraint.
        
        Args:
            min_weight: Minimum weight (can be negative for shorts)
            max_weight: Maximum weight
            gross_exposure: Maximum gross exposure (sum of |weights|)
            net_exposure: (min, max) net exposure range
        """
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.gross_exposure = gross_exposure
        self.net_exposure = net_exposure
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply long-short constraints."""
        weights = data.get("_weights_var")
        if weights is None:
            return
        
        n_assets = len(weights) if hasattr(weights, "__len__") else data.get("n_assets", 0)
        
        # Apply weight bounds
        for i in range(n_assets):
            if hasattr(weights[i], "setlb"):
                weights[i].setlb(self.min_weight)
                weights[i].setub(self.max_weight)
        
        # Gross/net exposure stored for template support
        if self.gross_exposure is not None:
            data["_max_gross_exposure"] = self.gross_exposure
        if self.net_exposure is not None:
            data["_net_exposure"] = self.net_exposure
