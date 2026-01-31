"""
Base solver interface and options.

Provides abstract interface for solver implementations and common options.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pyoptima.model.core import AbstractModel, OptimizationResult


@dataclass
class SolverOptions:
    """
    Common solver options that can be passed to any solver.
    
    Not all options are supported by all solvers - they will be
    translated or ignored as appropriate.
    """
    time_limit: Optional[float] = None  # Time limit in seconds
    mip_gap: Optional[float] = None  # MIP optimality gap tolerance
    threads: Optional[int] = None  # Number of threads to use
    verbose: bool = False  # Print solver output
    
    # Solver-specific options (passed through to backend)
    extra_options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.time_limit is not None:
            result["time_limit"] = self.time_limit
        if self.mip_gap is not None:
            result["mip_gap"] = self.mip_gap
        if self.threads is not None:
            result["threads"] = self.threads
        result["verbose"] = self.verbose
        result.update(self.extra_options)
        return result


class ProblemType(Enum):
    """Problem type classification."""
    LP = "LP"           # Linear Programming
    MILP = "MILP"       # Mixed Integer Linear Programming
    QP = "QP"           # Quadratic Programming
    MIQP = "MIQP"       # Mixed Integer Quadratic Programming
    NLP = "NLP"         # Nonlinear Programming
    MINLP = "MINLP"     # Mixed Integer Nonlinear Programming
    CP = "CP"           # Constraint Programming
    SOCP = "SOCP"       # Second-Order Cone Programming


@dataclass
class SolverCapabilities:
    """
    Describes the capabilities of a solver.
    """
    name: str
    supported_problem_types: List[ProblemType]
    supports_callbacks: bool = False
    supports_lazy_constraints: bool = False
    supports_indicator_constraints: bool = False
    is_free: bool = True
    description: str = ""
    
    def supports(self, problem_type: ProblemType) -> bool:
        """Check if solver supports a problem type."""
        return problem_type in self.supported_problem_types


class SolverInterface(ABC):
    """
    Abstract base class for solver implementations.
    
    All solver backends must implement this interface to be usable
    with the optimization engine.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return solver name."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> SolverCapabilities:
        """Return solver capabilities."""
        pass
    
    @abstractmethod
    def solve(self, model: AbstractModel, options: Optional[SolverOptions] = None) -> OptimizationResult:
        """
        Solve an optimization model.
        
        Args:
            model: AbstractModel to solve
            options: Solver options
            
        Returns:
            OptimizationResult with solution
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if solver is available on this system.
        
        Returns:
            True if solver can be used
        """
        pass
    
    def validate_model(self, model: AbstractModel) -> None:
        """
        Validate that model can be solved by this solver.
        
        Args:
            model: Model to validate
            
        Raises:
            ValueError: If model is not supported
        """
        problem_type = ProblemType(model.problem_type)
        if not self.capabilities.supports(problem_type):
            supported = [pt.value for pt in self.capabilities.supported_problem_types]
            
            # Suggest alternative solvers
            suggestions = []
            try:
                from pyoptima.solvers.pyomo_solver import SOLVER_CAPABILITIES
                for solver_name, caps in SOLVER_CAPABILITIES.items():
                    if problem_type in caps.supported_problem_types:
                        suggestions.append(solver_name)
            except ImportError:
                pass
            
            msg = (
                f"Solver '{self.name}' does not support {problem_type.value} problems.\n"
                f"Supported problem types for this solver: {supported}"
            )
            
            if suggestions:
                msg += f"\n\nSuggested solvers for {problem_type.value}:\n  " + "\n  ".join(suggestions)
                msg += "\n\nTry: solve(..., solver='<solver_name>')"
            
            raise ValueError(msg)


# Global solver registry
_SOLVER_REGISTRY: Dict[str, Type[SolverInterface]] = {}


def register_solver(name: str):
    """Decorator to register a solver class."""
    def decorator(cls: Type[SolverInterface]):
        _SOLVER_REGISTRY[name.lower()] = cls
        return cls
    return decorator


def get_solver(name: str, **kwargs) -> SolverInterface:
    """
    Get a solver instance by name.
    
    Args:
        name: Solver name (case-insensitive)
        **kwargs: Arguments to pass to solver constructor
        
    Returns:
        SolverInterface instance
        
    Raises:
        ValueError: If solver not found
    """
    name_lower = name.lower()
    
    # Check registry
    if name_lower in _SOLVER_REGISTRY:
        return _SOLVER_REGISTRY[name_lower](**kwargs)
    
    # Try to create PyomoSolver with the name as backend
    try:
        from pyoptima.solvers.pyomo_solver import PyomoSolver
        solver = PyomoSolver(solver_name=name, **kwargs)
        if solver.is_available():
            return solver
    except Exception:
        pass
    
    available = list_available_solvers()
    
    # Find similar solver names
    suggestions = []
    name_lower = name.lower()
    for solver_name in available:
        if name_lower in solver_name.lower() or solver_name.lower() in name_lower:
            suggestions.append(solver_name)
    
    msg = f"Solver '{name}' not found or not available."
    if suggestions:
        msg += f"\n\nDid you mean one of these?\n  " + "\n  ".join(suggestions)
    msg += f"\n\nAvailable solvers: {', '.join(available) if available else '(none)'}"
    msg += "\n\nUse list_available_solvers() to check which solvers are installed."
    
    # Installation hints
    if not available:
        msg += "\n\nNo solvers are currently available. Install one of:"
        msg += "\n  - HiGHS: pip install highspy"
        msg += "\n  - IPOPT: pip install cyipopt (requires IPOPT libraries)"
        msg += "\n  - CBC: pip install pulp"
        msg += "\n  - GLPK: pip install pulp"
    
    raise ValueError(msg)


def list_available_solvers() -> List[str]:
    """
    List all available solvers.
    
    Returns:
        List of solver names that are available on this system
    """
    available = []
    
    # Check registered solvers
    for name, cls in _SOLVER_REGISTRY.items():
        try:
            instance = cls()
            if instance.is_available():
                available.append(name)
        except Exception:
            pass
    
    # Check Pyomo solvers
    try:
        from pyoptima.solvers.pyomo_solver import PyomoSolver
        for solver_name in ["highs", "ipopt", "cbc", "glpk"]:
            try:
                solver = PyomoSolver(solver_name=solver_name)
                if solver.is_available():
                    if solver_name not in available:
                        available.append(solver_name)
            except Exception:
                pass
    except ImportError:
        pass
    
    return sorted(available)
