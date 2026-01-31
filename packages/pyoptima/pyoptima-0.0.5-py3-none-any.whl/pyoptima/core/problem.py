"""
CVXPY-style problem definition.

Provides a clean interface for defining optimization problems.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pyoptima.core.protocols import Constraint, ConstraintSet, Objective
from pyoptima.core.result import OptimizationResult, SolverStatus

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel, Expression


class Minimize:
    """
    Minimize objective wrapper.
    
    Example:
        >>> prob = Problem(
        ...     objective=Minimize(portfolio_variance),
        ...     constraints=[SumToOne(), WeightBounds(0, 1)]
        ... )
    """
    
    def __init__(self, expression: Union["Expression", "Objective"]):
        """
        Initialize minimization objective.
        
        Args:
            expression: Expression to minimize or Objective object
        """
        self.expression = expression
        self.sense = "minimize"
    
    def __repr__(self) -> str:
        return f"Minimize({self.expression})"


class Maximize:
    """
    Maximize objective wrapper.
    
    Example:
        >>> prob = Problem(
        ...     objective=Maximize(expected_return),
        ...     constraints=[SumToOne(), MaxVolatility(0.2)]
        ... )
    """
    
    def __init__(self, expression: Union["Expression", "Objective"]):
        """
        Initialize maximization objective.
        
        Args:
            expression: Expression to maximize or Objective object
        """
        self.expression = expression
        self.sense = "maximize"
    
    def __repr__(self) -> str:
        return f"Maximize({self.expression})"


class Problem:
    """
    CVXPY-style optimization problem definition.
    
    Provides a clean, declarative interface for defining and solving
    optimization problems.
    
    Example:
        >>> from pyoptima import Problem, Minimize, Variable
        >>> from pyoptima.constraints import WeightBounds, SumToOne
        >>> 
        >>> # Define problem
        >>> prob = Problem(
        ...     objective=Minimize(portfolio_variance),
        ...     constraints=[
        ...         SumToOne(),
        ...         WeightBounds(0, 0.4),
        ...     ]
        ... )
        >>> 
        >>> # Solve
        >>> result = prob.solve(
        ...     expected_returns=[0.1, 0.12, 0.08],
        ...     covariance_matrix=[[0.04, 0.01, 0.02], ...]
        ... )
    """
    
    def __init__(
        self,
        objective: Union[Minimize, Maximize, Objective],
        constraints: Optional[List[Union[Constraint, ConstraintSet]]] = None,
    ):
        """
        Initialize optimization problem.
        
        Args:
            objective: Objective to optimize (Minimize, Maximize, or Objective)
            constraints: List of constraints or constraint sets
        """
        self.objective = objective
        self._constraints: List[Constraint] = []
        
        # Flatten constraints
        if constraints:
            for c in constraints:
                if isinstance(c, ConstraintSet):
                    self._constraints.extend(c)
                else:
                    self._constraints.append(c)
    
    @property
    def constraints(self) -> List[Constraint]:
        """Get list of constraints."""
        return self._constraints
    
    def add_constraint(self, constraint: Union[Constraint, ConstraintSet]) -> "Problem":
        """
        Add a constraint to the problem.
        
        Args:
            constraint: Constraint or ConstraintSet to add
            
        Returns:
            self for method chaining
        """
        if isinstance(constraint, ConstraintSet):
            self._constraints.extend(constraint)
        else:
            self._constraints.append(constraint)
        return self
    
    def solve(
        self,
        solver: str = "auto",
        options: Optional[Dict[str, Any]] = None,
        **data,
    ) -> OptimizationResult:
        """
        Solve the optimization problem.
        
        Args:
            solver: Solver name ("auto", "ipopt", "highs", etc.)
            options: Solver options (time_limit, verbose, etc.)
            **data: Problem data (expected_returns, covariance_matrix, etc.)
            
        Returns:
            OptimizationResult with solution
        """
        from pyoptima.model.core import AbstractModel
        from pyoptima.solvers import get_solver
        
        # Build model
        model = AbstractModel(name="problem")
        
        # Build objective
        if isinstance(self.objective, (Minimize, Maximize)):
            obj = self.objective.expression
            if hasattr(obj, "build"):
                obj.build(model, data)
            else:
                # Direct expression
                if self.objective.sense == "minimize":
                    model.minimize(obj)
                else:
                    model.maximize(obj)
        elif hasattr(self.objective, "build"):
            self.objective.build(model, data)
        
        # Apply constraints
        for constraint in self._constraints:
            constraint.apply(model, data)
        
        # Get solver
        if solver == "auto":
            solver = "ipopt"  # Default to IPOPT
        
        solver_instance = get_solver(solver)
        
        # Solve
        result = solver_instance.solve(model, options)
        
        return result
    
    def __repr__(self) -> str:
        return f"Problem(objective={self.objective}, constraints={len(self._constraints)})"
