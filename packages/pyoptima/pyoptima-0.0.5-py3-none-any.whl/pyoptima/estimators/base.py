"""
Base optimizer class following sklearn conventions.

Provides the foundation for all domain-specific optimizers with:
- get_params() / set_params() for introspection
- solve() as the main execution method
- sklearn-style repr
- Clone support
"""

import copy
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Self, Type, TypeVar, Union

from pyoptima.core.protocols import Constraint, ConstraintSet
from pyoptima.core.result import OptimizationResult

T = TypeVar("T", bound="BaseOptimizer")


def clone(estimator: T, **params) -> T:
    """
    Clone an optimizer with optional parameter overrides.
    
    Similar to sklearn.base.clone().
    
    Args:
        estimator: Optimizer to clone
        **params: Parameters to override
        
    Returns:
        New optimizer instance with same/updated parameters
        
    Example:
        >>> opt = PortfolioOptimizer(objective="min_volatility")
        >>> opt2 = clone(opt, objective="max_sharpe")
    """
    klass = estimator.__class__
    new_params = estimator.get_params(deep=False)
    new_params.update(params)
    return klass(**new_params)


class BaseOptimizer(ABC):
    """
    Base class for all PyOptima optimizers.
    
    Follows sklearn conventions:
    - All parameters should be specified in __init__
    - get_params() returns all __init__ parameters
    - set_params() updates parameters and returns self
    - solve() is the main execution method
    
    Subclasses should:
    1. Define all parameters in __init__ with defaults
    2. Store parameters as attributes with same names
    3. Implement _solve() to do the actual optimization
    
    Example:
        >>> class MyOptimizer(BaseOptimizer):
        ...     def __init__(self, alpha=1.0, max_iter=100):
        ...         self.alpha = alpha
        ...         self.max_iter = max_iter
        ...     
        ...     def _solve(self, **data):
        ...         # Optimization logic here
        ...         return OptimizationResult(...)
        >>> 
        >>> opt = MyOptimizer(alpha=0.5)
        >>> opt.get_params()
        {'alpha': 0.5, 'max_iter': 100}
        >>> opt.set_params(max_iter=200)
        >>> result = opt.solve(x=[1, 2, 3])
    """
    
    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """
        Get parameters for this optimizer.
        
        Following sklearn convention, returns all parameters passed to __init__.
        
        Args:
            deep: If True, also return parameters of nested objects
            
        Returns:
            Dictionary of parameter names to values
        """
        # Get __init__ signature
        init_signature = inspect.signature(self.__init__)
        
        params = {}
        for name, param in init_signature.parameters.items():
            if name == "self":
                continue
            
            # Get value from attribute
            if hasattr(self, name):
                value = getattr(self, name)
            elif param.default is not inspect.Parameter.empty:
                value = param.default
            else:
                value = None
            
            params[name] = value
            
            # Handle nested objects with get_params
            if deep and hasattr(value, "get_params"):
                nested_params = value.get_params(deep=True)
                for key, val in nested_params.items():
                    params[f"{name}__{key}"] = val
        
        return params
    
    def set_params(self, **params) -> Self:
        """
        Set parameters for this optimizer.
        
        Following sklearn convention, returns self for method chaining.
        
        Args:
            **params: Parameter names and values to set
            
        Returns:
            self
            
        Raises:
            ValueError: If an invalid parameter name is provided
        """
        valid_params = self.get_params(deep=True)
        
        # Handle nested parameters (param__subparam)
        nested_params: Dict[str, Dict[str, Any]] = {}
        
        for key, value in params.items():
            if "__" in key:
                # Nested parameter
                param_name, sub_key = key.split("__", 1)
                if param_name not in nested_params:
                    nested_params[param_name] = {}
                nested_params[param_name][sub_key] = value
            else:
                # Direct parameter
                if key not in valid_params:
                    raise ValueError(
                        f"Invalid parameter '{key}' for {self.__class__.__name__}. "
                        f"Valid parameters: {list(valid_params.keys())}"
                    )
                setattr(self, key, value)
        
        # Set nested parameters
        for param_name, sub_params in nested_params.items():
            if hasattr(self, param_name):
                nested_obj = getattr(self, param_name)
                if hasattr(nested_obj, "set_params"):
                    nested_obj.set_params(**sub_params)
        
        return self
    
    def solve(self, **data) -> OptimizationResult:
        """
        Solve the optimization problem.
        
        This is the main entry point. It:
        1. Validates input data
        2. Calls _solve() to do the actual optimization
        3. Returns the result
        
        Args:
            **data: Problem data (varies by optimizer type)
            
        Returns:
            OptimizationResult with solution
        """
        # Validate data
        self._validate_data(data)
        
        # Call implementation
        return self._solve(**data)
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
        """
        Validate input data.
        
        Override in subclasses to add validation logic.
        
        Args:
            data: Input data dictionary
            
        Raises:
            ValueError: If data is invalid
        """
        pass
    
    @abstractmethod
    def _solve(self, **data) -> OptimizationResult:
        """
        Actual optimization implementation.
        
        Subclasses must implement this method.
        
        Args:
            **data: Problem data
            
        Returns:
            OptimizationResult with solution
        """
        ...
    
    def __repr__(self) -> str:
        """sklearn-style repr showing class and parameters."""
        params = self.get_params(deep=False)
        
        # Format parameters
        param_strs = []
        for name, value in params.items():
            if isinstance(value, str):
                param_strs.append(f"{name}={value!r}")
            elif isinstance(value, float):
                param_strs.append(f"{name}={value:.4g}")
            elif value is None:
                continue  # Skip None values for cleaner repr
            else:
                param_strs.append(f"{name}={value!r}")
        
        return f"{self.__class__.__name__}({', '.join(param_strs)})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on class and parameters."""
        if not isinstance(other, BaseOptimizer):
            return False
        if self.__class__ != other.__class__:
            return False
        return self.get_params() == other.get_params()
    
    def __hash__(self) -> int:
        """Hash based on class name (not params, as they're mutable)."""
        return hash(self.__class__.__name__)
