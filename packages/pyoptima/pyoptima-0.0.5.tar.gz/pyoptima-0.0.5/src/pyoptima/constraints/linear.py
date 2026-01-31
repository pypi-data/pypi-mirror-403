"""
Generalized linear constraints.

Constraints of the form A @ x <= b, A @ x >= b, or A @ x == b
for use with templates/solvers that accept linear constraints.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from pyoptima.constraints.base import BaseConstraint

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel

Sense = Literal["<=", ">=", "=="]


class LinearInequality(BaseConstraint):
    """
    Generic linear constraint: A @ x <= b, >= b, or == b.

    Use with solvers or templates that accept extra linear constraints.
    A is a matrix (list of lists or 2d array), b is a vector.

    Example:
        >>> # Single constraint: 2*w0 + 3*w1 <= 0.5
        >>> constraint = LinearInequality(A=[[2, 3]], b=[0.5], sense="<=")
        >>> # Multiple constraints
        >>> constraint = LinearInequality(
        ...     A=[[1, 1, 0], [0, 1, 1]],
        ...     b=[0.4, 0.6],
        ...     sense="<=",
        ... )
    """

    name = "linear_inequality"

    def __init__(
        self,
        A: Union[List[List[float]], Any],
        b: Union[List[float], Any],
        sense: Sense = "<=",
    ):
        """
        Args:
            A: Coefficient matrix (n_constraints x n_vars).
            b: Right-hand side (length n_constraints).
            sense: "<=", ">=", or "==".
        """
        self.A = A
        self.b = b
        self.sense = sense

    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        key = "_linear_constraints"
        if key not in data:
            data[key] = []
        data[key].append({"A": self.A, "b": self.b, "sense": self.sense})
