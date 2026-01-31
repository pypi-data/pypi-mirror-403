"""
PyOptima Core Module.

Contains core abstractions: protocols, problem definitions, and results.
"""

from pyoptima.core.protocols import (
    Objective,
    Constraint,
    Solver,
)
from pyoptima.core.result import OptimizationResult
from pyoptima.core.problem import (
    Problem,
    Minimize,
    Maximize,
)

__all__ = [
    # Protocols
    "Objective",
    "Constraint", 
    "Solver",
    # Results
    "OptimizationResult",
    # Problem definition
    "Problem",
    "Minimize",
    "Maximize",
]
