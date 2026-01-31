"""
Protocol definitions for PyOptima.

Defines the interfaces that objectives, constraints, and solvers must implement.
Uses Python's Protocol for structural subtyping (duck typing with type hints).
"""

from typing import TYPE_CHECKING, Any, Dict, List, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


@runtime_checkable
class Objective(Protocol):
    """
    Protocol for optimization objectives.
    
    Objectives define what to optimize (minimize or maximize).
    They build the objective function on an AbstractModel.
    
    Example:
        >>> class MinVolatility:
        ...     name = "min_volatility"
        ...     def build(self, model, data):
        ...         # Add objective to model
        ...         model.minimize(variance_expression)
    """
    
    name: str
    
    def build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Build the objective on the model.
        
        Args:
            model: The optimization model to add the objective to
            data: Problem data dictionary
        """
        ...


@runtime_checkable
class Constraint(Protocol):
    """
    Protocol for optimization constraints.
    
    Constraints limit the feasible region of the optimization problem.
    They add constraints to an AbstractModel.
    
    Example:
        >>> class WeightBounds:
        ...     name = "weight_bounds"
        ...     def apply(self, model, data):
        ...         # Add constraints to model
        ...         for var in model.variables:
        ...             model.add_constraint(var >= 0)
        ...             model.add_constraint(var <= 1)
    """
    
    name: str
    
    def apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Apply the constraint to the model.
        
        Args:
            model: The optimization model to add constraints to
            data: Problem data dictionary
        """
        ...


@runtime_checkable
class Solver(Protocol):
    """
    Protocol for optimization solvers.
    
    Solvers take an AbstractModel and find the optimal solution.
    
    Example:
        >>> class IPOPTSolver:
        ...     name = "ipopt"
        ...     def solve(self, model, options=None):
        ...         # Solve and return result
        ...         return OptimizationResult(...)
    """
    
    name: str
    
    def solve(
        self, 
        model: "AbstractModel", 
        options: Dict[str, Any] | None = None
    ) -> "OptimizationResult":
        """
        Solve the optimization model.
        
        Args:
            model: The optimization model to solve
            options: Solver-specific options
            
        Returns:
            OptimizationResult with solution
        """
        ...
    
    def is_available(self) -> bool:
        """Check if the solver is available on this system."""
        ...


class ConstraintSet:
    """
    A collection of constraints that can be combined with + operator.
    
    Follows sklearn's FeatureUnion pattern for composability.
    
    Example:
        >>> constraints = ConstraintSet([
        ...     WeightBounds(0, 1),
        ...     SectorCaps({"Tech": 0.5}),
        ... ])
        >>> # Or combine with +
        >>> constraints = WeightBounds(0, 1) + SectorCaps({"Tech": 0.5})
    """
    
    def __init__(self, constraints: List[Constraint] | None = None):
        """
        Initialize with a list of constraints.
        
        Args:
            constraints: List of Constraint objects
        """
        self._constraints: List[Constraint] = list(constraints) if constraints else []
    
    def add(self, constraint: Constraint) -> "ConstraintSet":
        """
        Add a constraint to the set.
        
        Args:
            constraint: Constraint to add
            
        Returns:
            self for method chaining
        """
        self._constraints.append(constraint)
        return self
    
    def __add__(self, other: "Constraint | ConstraintSet") -> "ConstraintSet":
        """
        Combine constraint sets with + operator.
        
        Args:
            other: Another constraint or constraint set
            
        Returns:
            New ConstraintSet with all constraints
        """
        if isinstance(other, ConstraintSet):
            return ConstraintSet(self._constraints + other._constraints)
        else:
            return ConstraintSet(self._constraints + [other])
    
    def __radd__(self, other: Constraint) -> "ConstraintSet":
        """Support constraint + constraint_set."""
        if isinstance(other, ConstraintSet):
            return other + self
        return ConstraintSet([other] + self._constraints)
    
    def __iter__(self):
        """Iterate over constraints."""
        return iter(self._constraints)
    
    def __len__(self) -> int:
        """Number of constraints."""
        return len(self._constraints)
    
    def __repr__(self) -> str:
        constraint_names = [c.name for c in self._constraints]
        return f"ConstraintSet({constraint_names})"
    
    def apply_all(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Apply all constraints to the model.
        
        Args:
            model: The optimization model
            data: Problem data dictionary
        """
        for constraint in self._constraints:
            constraint.apply(model, data)
