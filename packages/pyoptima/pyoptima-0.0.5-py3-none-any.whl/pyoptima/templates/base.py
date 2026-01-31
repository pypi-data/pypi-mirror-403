"""
Base class for problem templates.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from pyoptima.model.core import AbstractModel, OptimizationResult
from pyoptima.solvers import SolverOptions, get_solver


@dataclass
class TemplateInfo:
    """Information about a problem template."""
    name: str
    description: str
    problem_type: str
    required_data: List[str]
    optional_data: List[str]
    default_solver: str


class ProblemTemplate(ABC):
    """
    Base class for problem templates.
    
    Templates provide a simple interface for solving common optimization problems.
    Subclasses implement:
    - validate_data(): Validate input data
    - build_model(): Create AbstractModel from data
    - format_solution(): Format results
    """
    
    @property
    @abstractmethod
    def info(self) -> TemplateInfo:
        """Return template information."""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> None:
        """Validate input data. Raises ValueError if invalid."""
        pass
    
    @abstractmethod
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        """Build optimization model from data."""
        pass
    
    @abstractmethod
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format solution into problem-specific output."""
        pass
    
    def solve(
        self,
        data: Dict[str, Any],
        solver: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Solve the problem.
        
        Args:
            data: Problem data dictionary
            solver: Solver name (uses default if not specified)
            options: Solver options (time_limit, verbose, etc.)
        
        Returns:
            Solution dictionary
        """
        self.validate_data(data)
        model = self.build_model(data)
        
        solver_name = solver or self.info.default_solver
        solver_instance = get_solver(solver_name)
        solver_options = SolverOptions(**(options or {}))
        
        result = solver_instance.solve(model, solver_options)
        return self.format_solution(model, result, data)
    
    def _require_keys(self, data: Dict[str, Any], keys: List[str]) -> None:
        """Validate that required keys are present."""
        missing = [k for k in keys if k not in data]
        if missing:
            available = list(data.keys())
            suggestions = []
            for key in missing:
                # Try to find similar keys
                similar = [k for k in available if key.lower() in k.lower() or k.lower() in key.lower()]
                if similar:
                    suggestions.append(f"  '{key}' - did you mean: {similar}")
            
            msg = f"Missing required data fields: {missing}"
            if suggestions:
                msg += "\n\nSuggestions:\n" + "\n".join(suggestions)
            msg += f"\n\nAvailable fields: {available if available else '(none)'}"
            msg += f"\nRequired fields: {keys}"
            raise ValueError(msg)


# Template registry
class TemplateRegistry:
    """Registry for problem templates."""
    
    _templates: Dict[str, Type[ProblemTemplate]] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a template."""
        def decorator(template_cls: Type[ProblemTemplate]):
            cls._templates[name.lower()] = template_cls
            return template_cls
        return decorator
    
    @classmethod
    def get(cls, name: str) -> ProblemTemplate:
        """Get a template instance by name."""
        name_lower = name.lower()
        if name_lower not in cls._templates:
            available = sorted(cls._templates.keys())
            
            # Find similar template names
            suggestions = []
            for template_name in available:
                if name_lower in template_name or template_name in name_lower:
                    suggestions.append(template_name)
                elif len(name_lower) >= 3 and any(name_lower[:i] in template_name for i in range(3, len(name_lower) + 1)):
                    suggestions.append(template_name)
            
            msg = f"Template '{name}' not found."
            if suggestions:
                msg += f"\n\nDid you mean one of these?\n  " + "\n  ".join(suggestions[:5])
            msg += f"\n\nAvailable templates: {', '.join(available)}"
            msg += "\n\nUse list_templates() to see all available templates."
            raise ValueError(msg)
        return cls._templates[name_lower]()
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """List all registered templates."""
        return sorted(cls._templates.keys())


def get_template(name: str) -> ProblemTemplate:
    """
    Get a problem template by name.
    
    Args:
        name: Template name (case-insensitive)
    
    Returns:
        ProblemTemplate instance
    
    Examples:
        >>> knapsack = get_template("knapsack")
        >>> lp = get_template("lp")
    """
    return TemplateRegistry.get(name)
