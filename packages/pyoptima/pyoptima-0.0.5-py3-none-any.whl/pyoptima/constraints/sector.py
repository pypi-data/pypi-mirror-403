"""
Sector and factor constraints.

Constraints for sector/factor exposure limits.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class FactorExposureLimits(BaseConstraint):
    """
    Min/max portfolio exposure to factors (e.g. beta, size, value).

    Requires factor loadings in solve() data (e.g. factor_data, factor loadings per asset).

    Example:
        >>> # Cap market beta between 0.8 and 1.2
        >>> constraint = FactorExposureLimits(limits={"beta": (0.8, 1.2)})
        >>> # Cap only
        >>> constraint = FactorExposureLimits(limits={"momentum": 0.5})
    """

    name = "factor_exposure_limits"

    def __init__(
        self,
        limits: Dict[str, Union[float, Tuple[float, float]]],
        asset_factors: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """
        Args:
            limits: Factor name -> max (float) or (min, max) tuple.
            asset_factors: Optional asset -> {factor_name: loading}; can also be in solve() data.
        """
        self.limits = limits
        self.asset_factors = asset_factors

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        data["_factor_exposure_limits"] = self.limits
        if self.asset_factors:
            data["_asset_factors"] = self.asset_factors


class SectorCaps(BaseConstraint):
    """
    Maximum sector exposure constraints.
    
    Example:
        >>> constraint = SectorCaps(
        ...     caps={"Technology": 0.4, "Finance": 0.3},
        ...     asset_sectors={"AAPL": "Technology", "JPM": "Finance", ...}
        ... )
    """
    
    name = "sector_caps"
    
    def __init__(
        self,
        caps: Dict[str, float],
        asset_sectors: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize sector caps.
        
        Args:
            caps: Dictionary mapping sector name to maximum exposure
            asset_sectors: Dictionary mapping asset symbol to sector
                          (can also be provided in solve() data)
        """
        self.caps = caps
        self.asset_sectors = asset_sectors
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply sector cap constraints."""
        data["_sector_caps"] = self.caps
        if self.asset_sectors:
            data["_asset_sectors"] = self.asset_sectors


class SectorMins(BaseConstraint):
    """
    Minimum sector exposure constraints.
    
    Example:
        >>> constraint = SectorMins(
        ...     mins={"Technology": 0.1, "Healthcare": 0.05},
        ...     asset_sectors={"AAPL": "Technology", "JNJ": "Healthcare", ...}
        ... )
    """
    
    name = "sector_mins"
    
    def __init__(
        self,
        mins: Dict[str, float],
        asset_sectors: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize sector minimums.
        
        Args:
            mins: Dictionary mapping sector name to minimum exposure
            asset_sectors: Dictionary mapping asset symbol to sector
        """
        self.mins = mins
        self.asset_sectors = asset_sectors
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply sector minimum constraints."""
        data["_sector_mins"] = self.mins
        if self.asset_sectors:
            data.setdefault("_asset_sectors", {}).update(self.asset_sectors)


class SectorConstraints(BaseConstraint):
    """
    Combined sector constraints (both caps and mins).
    
    Example:
        >>> constraint = SectorConstraints(
        ...     caps={"Technology": 0.4},
        ...     mins={"Healthcare": 0.1},
        ...     asset_sectors={...}
        ... )
    """
    
    name = "sector_constraints"
    
    def __init__(
        self,
        caps: Optional[Dict[str, float]] = None,
        mins: Optional[Dict[str, float]] = None,
        asset_sectors: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize sector constraints.
        
        Args:
            caps: Maximum sector exposures
            mins: Minimum sector exposures
            asset_sectors: Asset to sector mapping
        """
        self.caps = caps or {}
        self.mins = mins or {}
        self.asset_sectors = asset_sectors
    
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """Apply combined sector constraints."""
        if self.caps:
            data["_sector_caps"] = self.caps
        if self.mins:
            data["_sector_mins"] = self.mins
        if self.asset_sectors:
            data["_asset_sectors"] = self.asset_sectors
