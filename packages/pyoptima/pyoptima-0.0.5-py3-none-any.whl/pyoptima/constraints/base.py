"""
Base constraint class.

Provides the foundation for composable constraints with + operator support.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

from pyoptima.core.protocols import ConstraintSet

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class BaseConstraint(ABC):
    """
    Base class for all constraints.
    
    Provides:
    - + operator for combining constraints
    - Consistent interface via apply() method
    - sklearn-style repr
    
    Example:
        >>> class MyConstraint(BaseConstraint):
        ...     name = "my_constraint"
        ...     
        ...     def __init__(self, limit: float):
        ...         self.limit = limit
        ...     
        ...     def apply(self, model, data):
        ...         # Add constraints to model
        ...         pass
        >>> 
        >>> # Combine with +
        >>> constraints = MyConstraint(10) + AnotherConstraint()
    """
    
    name: str = "base_constraint"
    
    def apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Apply the constraint to the model.
        
        Args:
            model: The optimization model to add constraints to
            data: Problem data dictionary
        """
        self._apply(model, data)
    
    @abstractmethod
    def _apply(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Implementation of constraint application.
        
        Subclasses must implement this method.
        
        Args:
            model: The optimization model
            data: Problem data dictionary
        """
        ...
    
    def __add__(self, other: "BaseConstraint | ConstraintSet") -> ConstraintSet:
        """
        Combine constraints with + operator.
        
        Args:
            other: Another constraint or constraint set
            
        Returns:
            ConstraintSet containing both constraints
        """
        if isinstance(other, ConstraintSet):
            return ConstraintSet([self] + list(other))
        return ConstraintSet([self, other])
    
    def __radd__(self, other: "BaseConstraint | ConstraintSet") -> ConstraintSet:
        """Support other + self."""
        if isinstance(other, ConstraintSet):
            return other + self
        return ConstraintSet([other, self])
    
    def __repr__(self) -> str:
        """sklearn-style repr."""
        # Get __init__ parameters
        import inspect
        
        try:
            init_sig = inspect.signature(self.__init__)
            params = []
            for name, param in init_sig.parameters.items():
                if name == "self":
                    continue
                if hasattr(self, name):
                    value = getattr(self, name)
                    if isinstance(value, str):
                        params.append(f"{name}={value!r}")
                    elif isinstance(value, float):
                        params.append(f"{name}={value:.4g}")
                    elif value is not None:
                        params.append(f"{name}={value!r}")
            return f"{self.__class__.__name__}({', '.join(params)})"
        except (ValueError, TypeError):
            return f"{self.__class__.__name__}()"
