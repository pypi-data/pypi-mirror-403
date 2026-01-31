"""
PyOptima Constraints Module.

Composable, chainable constraints that can be combined with + operator.
"""

from pyoptima.constraints.base import BaseConstraint
from pyoptima.core.protocols import ConstraintSet

# Import all constraint types for convenience
from pyoptima.constraints.bounds import (
    WeightBounds,
    PerAssetBounds,
    LongOnly,
    LongShort,
    GrossExposure,
)
from pyoptima.constraints.cardinality import (
    MaxAssets,
    MinAssets,
    MinPositionSize,
)
from pyoptima.constraints.sector import (
    SectorCaps,
    SectorMins,
    SectorConstraints,
    FactorExposureLimits,
)
from pyoptima.constraints.turnover import (
    MaxTurnover,
    TransactionCosts,
)
from pyoptima.constraints.risk import (
    MaxVolatility,
    MaxCVaR,
    MaxDrawdown,
    MaxConcentration,
    TrackingErrorLimit,
)
from pyoptima.constraints.portfolio import (
    SumToOne,
    MinReturn,
    MaxReturn,
    ExclusionList,
    InclusionList,
)
from pyoptima.constraints.linear import LinearInequality

__all__ = [
    # Base
    "BaseConstraint",
    "ConstraintSet",
    # Bounds
    "WeightBounds",
    "PerAssetBounds",
    "LongOnly",
    "LongShort",
    "GrossExposure",
    # Cardinality
    "MaxAssets",
    "MinAssets", 
    "MinPositionSize",
    # Sector
    "SectorCaps",
    "SectorMins",
    "SectorConstraints",
    "FactorExposureLimits",
    # Turnover
    "MaxTurnover",
    "TransactionCosts",
    # Risk
    "MaxVolatility",
    "MaxCVaR",
    "MaxDrawdown",
    "MaxConcentration",
    "TrackingErrorLimit",
    # Portfolio
    "SumToOne",
    "MinReturn",
    "MaxReturn",
    "ExclusionList",
    "InclusionList",
    "LinearInequality",
]
