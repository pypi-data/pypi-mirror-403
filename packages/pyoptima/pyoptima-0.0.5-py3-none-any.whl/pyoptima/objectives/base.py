"""
Base objective class.

Provides the foundation for optimization objectives.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from pyoptima.model.core import AbstractModel


class BaseObjective(ABC):
    """
    Base class for optimization objectives.
    
    Example:
        >>> class MyObjective(BaseObjective):
        ...     name = "my_objective"
        ...     sense = "minimize"
        ...     
        ...     def build(self, model, data):
        ...         # Build objective expression
        ...         expr = sum(...)
        ...         model.minimize(expr)
    """
    
    name: str = "base_objective"
    sense: str = "minimize"  # "minimize" or "maximize"
    
    def build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Build the objective on the model.
        
        Args:
            model: The optimization model
            data: Problem data dictionary
        """
        self._build(model, data)
    
    @abstractmethod
    def _build(self, model: "AbstractModel", data: Dict[str, Any]) -> None:
        """
        Implementation of objective building.
        
        Subclasses must implement this method.
        
        Args:
            model: The optimization model
            data: Problem data dictionary
        """
        ...
    
    def __repr__(self) -> str:
        """sklearn-style repr."""
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
