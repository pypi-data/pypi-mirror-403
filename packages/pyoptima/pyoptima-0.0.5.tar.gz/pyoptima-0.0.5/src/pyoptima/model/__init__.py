"""
Solver-agnostic model representation.

This module provides a universal model representation that can be translated
to various solver backends (Pyomo, OR-Tools, CVXPY, etc.).
"""

from pyoptima.model.core import (
    Variable,
    VariableType,
    Expression,
    Term,
    Constraint,
    ConstraintSense,
    Objective,
    OptimizationSense,
    AbstractModel,
    OptimizationResult,
    SolverStatus,
)
from pyoptima.model.sets import IndexSet, IndexedSet

__all__ = [
    "Variable",
    "VariableType",
    "Expression",
    "Term",
    "Constraint",
    "ConstraintSense",
    "Objective",
    "OptimizationSense",
    "AbstractModel",
    "OptimizationResult",
    "SolverStatus",
    "IndexSet",
    "IndexedSet",
]
