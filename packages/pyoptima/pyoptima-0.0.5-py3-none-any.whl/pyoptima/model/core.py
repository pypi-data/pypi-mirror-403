"""
Core model classes for solver-agnostic optimization model representation.

These classes represent optimization problems in a way that can be translated
to various solver backends.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class VariableType(Enum):
    """Variable type enumeration."""
    CONTINUOUS = "continuous"
    BINARY = "binary"
    INTEGER = "integer"


class ConstraintSense(Enum):
    """Constraint sense enumeration."""
    LEQ = "<="  # Less than or equal
    GEQ = ">="  # Greater than or equal
    EQ = "=="   # Equal


class OptimizationSense(Enum):
    """Optimization direction."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class SolverStatus(Enum):
    """Solver termination status."""
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    TIME_LIMIT = "time_limit"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class Variable:
    """
    Optimization variable representation.
    
    Attributes:
        name: Variable name/identifier
        var_type: Variable type (continuous, binary, integer)
        lower_bound: Lower bound (None for unbounded)
        upper_bound: Upper bound (None for unbounded)
        indices: For indexed variables, the index tuple
        value: Solution value (set after solving)
    """
    name: str
    var_type: VariableType = VariableType.CONTINUOUS
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    indices: Optional[Tuple] = None
    value: Optional[float] = None
    
    def __hash__(self):
        return hash((self.name, self.indices))
    
    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        return self.name == other.name and self.indices == other.indices
    
    @property
    def full_name(self) -> str:
        """Return full name including indices."""
        if self.indices:
            idx_str = ",".join(str(i) for i in self.indices)
            return f"{self.name}[{idx_str}]"
        return self.name


@dataclass
class Term:
    """
    A term in a linear/quadratic expression.
    
    Represents: coefficient * variable (linear)
            or: coefficient * var1 * var2 (quadratic)
    """
    coefficient: float
    variable: Union[Variable, str]
    variable2: Optional[Union[Variable, str]] = None  # For quadratic terms
    
    @property
    def is_quadratic(self) -> bool:
        return self.variable2 is not None


@dataclass
class Expression:
    """
    Mathematical expression (linear or quadratic).
    
    Represents: constant + sum(terms)
    """
    terms: List[Term] = field(default_factory=list)
    constant: float = 0.0
    
    def add_term(self, coefficient: float, variable: Union[Variable, str], 
                 variable2: Optional[Union[Variable, str]] = None) -> "Expression":
        """Add a term to the expression."""
        self.terms.append(Term(coefficient, variable, variable2))
        return self
    
    def add_constant(self, value: float) -> "Expression":
        """Add a constant to the expression."""
        self.constant += value
        return self
    
    @property
    def is_linear(self) -> bool:
        """Check if expression is linear."""
        return all(not t.is_quadratic for t in self.terms)
    
    @property
    def is_quadratic(self) -> bool:
        """Check if expression has quadratic terms."""
        return any(t.is_quadratic for t in self.terms)
    
    @classmethod
    def from_dict(cls, var_coeffs: Dict[str, float], constant: float = 0.0) -> "Expression":
        """Create linear expression from variable-coefficient dictionary."""
        expr = cls(constant=constant)
        for var_name, coef in var_coeffs.items():
            expr.add_term(coef, var_name)
        return expr


@dataclass
class Constraint:
    """
    Optimization constraint representation.
    
    Represents: lhs sense rhs
    e.g., sum(x[i]) <= 100
    """
    name: str
    lhs: Expression
    sense: ConstraintSense
    rhs: float
    indices: Optional[Tuple] = None  # For indexed constraints
    
    @property
    def full_name(self) -> str:
        """Return full name including indices."""
        if self.indices:
            idx_str = ",".join(str(i) for i in self.indices)
            return f"{self.name}[{idx_str}]"
        return self.name
    
    @classmethod
    def leq(cls, name: str, lhs: Expression, rhs: float, indices: Optional[Tuple] = None) -> "Constraint":
        """Create a <= constraint."""
        return cls(name, lhs, ConstraintSense.LEQ, rhs, indices)
    
    @classmethod
    def geq(cls, name: str, lhs: Expression, rhs: float, indices: Optional[Tuple] = None) -> "Constraint":
        """Create a >= constraint."""
        return cls(name, lhs, ConstraintSense.GEQ, rhs, indices)
    
    @classmethod
    def eq(cls, name: str, lhs: Expression, rhs: float, indices: Optional[Tuple] = None) -> "Constraint":
        """Create an == constraint."""
        return cls(name, lhs, ConstraintSense.EQ, rhs, indices)


@dataclass
class Objective:
    """
    Objective function representation.
    """
    expression: Expression
    sense: OptimizationSense
    
    @classmethod
    def minimize(cls, expression: Expression) -> "Objective":
        """Create minimization objective."""
        return cls(expression, OptimizationSense.MINIMIZE)
    
    @classmethod
    def maximize(cls, expression: Expression) -> "Objective":
        """Create maximization objective."""
        return cls(expression, OptimizationSense.MAXIMIZE)


@dataclass
class OptimizationResult:
    """
    Standardized optimization result.
    
    Provides a consistent result format across all problem types.
    """
    status: SolverStatus
    objective_value: Optional[float] = None
    solution: Dict[str, float] = field(default_factory=dict)
    message: str = ""
    solve_time: Optional[float] = None
    gap: Optional[float] = None  # MIP gap
    
    # Problem-specific results (populated by method implementations)
    weights: Optional[Dict[str, float]] = None  # Portfolio
    selected_items: Optional[Dict[str, Any]] = None  # Knapsack
    assignments: Optional[Dict[str, Any]] = None  # Assignment
    flows: Optional[Dict[str, float]] = None  # Network flow
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "status": self.status.value,
            "objective_value": self.objective_value,
            "solution": self.solution,
            "message": self.message,
        }
        if self.solve_time is not None:
            result["solve_time"] = self.solve_time
        if self.gap is not None:
            result["gap"] = self.gap
        
        # Add problem-specific results if present
        if self.weights is not None:
            result["weights"] = self.weights
        if self.selected_items is not None:
            result["selected_items"] = self.selected_items
        if self.assignments is not None:
            result["assignments"] = self.assignments
        if self.flows is not None:
            result["flows"] = self.flows
        
        return result
    
    @property
    def is_optimal(self) -> bool:
        return self.status == SolverStatus.OPTIMAL
    
    @property
    def is_feasible(self) -> bool:
        return self.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)


class AbstractModel:
    """
    Solver-agnostic optimization model.
    
    This class represents an optimization problem that can be translated
    to various solver backends (Pyomo, OR-Tools, CVXPY).
    """
    
    def __init__(self, name: str = "model"):
        """
        Initialize abstract model.
        
        Args:
            name: Model name/identifier
        """
        self.name = name
        self._variables: Dict[str, Variable] = {}
        self._constraints: Dict[str, Constraint] = {}
        self._objective: Optional[Objective] = None
        self._sets: Dict[str, List] = {}
        self._parameters: Dict[str, Any] = {}
    
    # Variable management
    def add_variable(
        self,
        name: str,
        var_type: VariableType = VariableType.CONTINUOUS,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
        indices: Optional[Tuple] = None
    ) -> Variable:
        """Add a variable to the model."""
        var = Variable(name, var_type, lower_bound, upper_bound, indices)
        key = var.full_name
        self._variables[key] = var
        return var
    
    def add_continuous(self, name: str, lb: Optional[float] = None, 
                       ub: Optional[float] = None, indices: Optional[Tuple] = None) -> Variable:
        """Add a continuous variable."""
        return self.add_variable(name, VariableType.CONTINUOUS, lb, ub, indices)
    
    def add_binary(self, name: str, indices: Optional[Tuple] = None) -> Variable:
        """Add a binary variable."""
        return self.add_variable(name, VariableType.BINARY, 0, 1, indices)
    
    def add_integer(self, name: str, lb: Optional[float] = None,
                    ub: Optional[float] = None, indices: Optional[Tuple] = None) -> Variable:
        """Add an integer variable."""
        return self.add_variable(name, VariableType.INTEGER, lb, ub, indices)
    
    def get_variable(self, name: str) -> Optional[Variable]:
        """Get variable by name."""
        return self._variables.get(name)
    
    @property
    def variables(self) -> Dict[str, Variable]:
        """Get all variables."""
        return self._variables
    
    # Constraint management
    def add_constraint(self, constraint: Constraint) -> Constraint:
        """Add a constraint to the model."""
        self._constraints[constraint.full_name] = constraint
        return constraint
    
    def add_leq_constraint(self, name: str, lhs: Expression, rhs: float,
                           indices: Optional[Tuple] = None) -> Constraint:
        """Add a <= constraint."""
        return self.add_constraint(Constraint.leq(name, lhs, rhs, indices))
    
    def add_geq_constraint(self, name: str, lhs: Expression, rhs: float,
                           indices: Optional[Tuple] = None) -> Constraint:
        """Add a >= constraint."""
        return self.add_constraint(Constraint.geq(name, lhs, rhs, indices))
    
    def add_eq_constraint(self, name: str, lhs: Expression, rhs: float,
                          indices: Optional[Tuple] = None) -> Constraint:
        """Add an == constraint."""
        return self.add_constraint(Constraint.eq(name, lhs, rhs, indices))
    
    @property
    def constraints(self) -> Dict[str, Constraint]:
        """Get all constraints."""
        return self._constraints
    
    # Objective management
    def set_objective(self, expression: Expression, sense: OptimizationSense) -> Objective:
        """Set the objective function."""
        self._objective = Objective(expression, sense)
        return self._objective
    
    def minimize(self, expression: Expression) -> Objective:
        """Set minimization objective."""
        return self.set_objective(expression, OptimizationSense.MINIMIZE)
    
    def maximize(self, expression: Expression) -> Objective:
        """Set maximization objective."""
        return self.set_objective(expression, OptimizationSense.MAXIMIZE)
    
    @property
    def objective(self) -> Optional[Objective]:
        """Get objective function."""
        return self._objective
    
    # Set and parameter management
    def add_set(self, name: str, elements: List) -> None:
        """Add an index set."""
        self._sets[name] = list(elements)
    
    def get_set(self, name: str) -> Optional[List]:
        """Get set by name."""
        return self._sets.get(name)
    
    def add_parameter(self, name: str, value: Any) -> None:
        """Add a parameter."""
        self._parameters[name] = value
    
    def get_parameter(self, name: str) -> Any:
        """Get parameter by name."""
        return self._parameters.get(name)
    
    @property
    def sets(self) -> Dict[str, List]:
        """Get all sets."""
        return self._sets
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get all parameters."""
        return self._parameters
    
    # Model properties
    @property
    def num_variables(self) -> int:
        """Get number of variables."""
        return len(self._variables)
    
    @property
    def num_constraints(self) -> int:
        """Get number of constraints."""
        return len(self._constraints)
    
    @property
    def is_linear(self) -> bool:
        """Check if model is linear."""
        if self._objective is None:
            return True
        if not self._objective.expression.is_linear:
            return False
        return all(c.lhs.is_linear for c in self._constraints.values())
    
    @property
    def has_integer_variables(self) -> bool:
        """Check if model has integer/binary variables."""
        return any(v.var_type in (VariableType.BINARY, VariableType.INTEGER)
                   for v in self._variables.values())
    
    @property
    def problem_type(self) -> str:
        """Determine problem type (LP, MILP, QP, MIQP)."""
        is_linear = self.is_linear
        has_integers = self.has_integer_variables
        
        if is_linear and not has_integers:
            return "LP"
        elif is_linear and has_integers:
            return "MILP"
        elif not is_linear and not has_integers:
            return "QP"
        else:
            return "MIQP"
    
    def __repr__(self) -> str:
        return (f"AbstractModel(name={self.name}, vars={self.num_variables}, "
                f"constraints={self.num_constraints}, type={self.problem_type})")
