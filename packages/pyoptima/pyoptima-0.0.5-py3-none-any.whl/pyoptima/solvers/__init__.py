"""
Solver abstraction layer.

This module provides a unified interface for various optimization solvers,
allowing easy swapping between backends (Pyomo, OR-Tools, CVXPY).
"""

from pyoptima.solvers.base import (
    SolverInterface,
    SolverOptions,
    SolverCapabilities,
    get_solver,
    list_available_solvers,
)
from pyoptima.solvers.pyomo_solver import PyomoSolver

__all__ = [
    "SolverInterface",
    "SolverOptions",
    "SolverCapabilities",
    "PyomoSolver",
    "get_solver",
    "list_available_solvers",
]
