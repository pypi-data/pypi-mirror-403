"""
Cardinality constraints.

Constraints for limiting the number of assets in a portfolio.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class MaxAssets(BaseConstraint):
    """
    Maximum number of assets constraint.
    
    Example:
        >>> # At most 10 assets in portfolio
        >>> constraint = MaxAssets(10)
    """
    
    name = "max_assets"
    
    def __init__(self, max_assets: int):
        """
        Initialize max assets constraint.
        
        Args:
            max_assets: Maximum number of assets with non-zero weight
        """
        self.max_assets = max_assets
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply max assets constraint using indicator variables."""
        # Store for the optimizer to handle
        data["_max_assets"] = self.max_assets


class MinAssets(BaseConstraint):
    """
    Minimum number of assets constraint.
    
    Example:
        >>> # At least 5 assets in portfolio
        >>> constraint = MinAssets(5)
    """
    
    name = "min_assets"
    
    def __init__(self, min_assets: int):
        """
        Initialize min assets constraint.
        
        Args:
            min_assets: Minimum number of assets with non-zero weight
        """
        self.min_assets = min_assets
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply min assets constraint."""
        data["_min_assets"] = self.min_assets


class MinPositionSize(BaseConstraint):
    """
    Minimum position size constraint.
    
    If an asset is held, it must have at least this weight.
    Often used with MaxAssets to avoid tiny positions.
    
    Example:
        >>> # Each position must be at least 2%
        >>> constraint = MinPositionSize(0.02)
    """
    
    name = "min_position_size"
    
    def __init__(self, min_size: float):
        """
        Initialize min position size constraint.
        
        Args:
            min_size: Minimum weight for any held position
        """
        self.min_size = min_size
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply min position size constraint."""
        data["_min_position_size"] = self.min_size
