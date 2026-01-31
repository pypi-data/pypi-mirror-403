"""
Problem templates for common optimization problems.

Templates provide a simple, unified interface for solving optimization problems.
You provide data, the template builds the model and solves it.

Usage:
    from pyoptima import solve, get_template
    
    # Quick solve
    result = solve("knapsack", {
        "items": [{"name": "A", "value": 60, "weight": 10}, ...],
        "capacity": 50
    })
    
    # Or use template directly
    template = get_template("knapsack")
    result = template.solve(data)

Available templates:
    Mathematical:
        - lp / linear: Linear Programming
        - qp / quadratic: Quadratic Programming
        - mip / milp: Mixed Integer Programming
    
    Combinatorial:
        - knapsack: 0-1, bounded, unbounded knapsack
        - assignment: Assignment problem
        - transportation: Transportation problem
        - binpacking: Bin packing
        - tsp: Traveling Salesman Problem
        - vrp: Vehicle Routing Problem
    
    Network:
        - mincostflow / min_cost_flow: Minimum cost network flow
        - maxflow / max_flow: Maximum flow
    
    Scheduling:
        - jobshop: Job shop scheduling
    
    Facility:
        - facility / facility_location: Facility location
    
    Finance:
        - portfolio: Portfolio optimization (multiple objectives)
"""

from pyoptima.templates.base import (
    ProblemTemplate,
    TemplateInfo,
    TemplateRegistry,
    get_template,
)

# Import all templates to register them
from pyoptima.templates.mathematical import (
    LinearProgrammingTemplate,
    QuadraticProgrammingTemplate,
    MixedIntegerTemplate,
)
from pyoptima.templates.classic import (
    KnapsackTemplate,
    TransportationTemplate,
    AssignmentTemplate,
)
from pyoptima.templates.routing import (
    TSPTemplate,
    VRPTemplate,
)
from pyoptima.templates.network import (
    MinCostFlowTemplate,
    MaxFlowTemplate,
)
from pyoptima.templates.scheduling import (
    JobShopTemplate,
)
from pyoptima.templates.packing import (
    BinPackingTemplate,
)
from pyoptima.templates.facility import (
    FacilityLocationTemplate,
)
from pyoptima.templates.portfolio import (
    PortfolioTemplate,
)


def solve(template_name: str, data: dict, solver: str = None, **options) -> dict:
    """
    Solve an optimization problem using a template.
    
    This is the simplest way to use PyOptima.
    
    Args:
        template_name: Name of the template (e.g., "knapsack", "lp", "portfolio")
        data: Problem data dictionary (template-specific)
        solver: Optional solver name (uses template default if not specified)
        **options: Solver options
    
    Returns:
        Solution dictionary with status, objective value, and solution
    
    Examples:
        >>> result = solve("knapsack", {
        ...     "items": [{"name": "A", "value": 60, "weight": 10}],
        ...     "capacity": 50
        ... })
        
        >>> result = solve("lp", {
        ...     "c": [1, 2, 3],
        ...     "A": [[1, 1, 1]],
        ...     "b": [10],
        ...     "sense": "maximize"
        ... })
    """
    template = get_template(template_name)
    return template.solve(data, solver=solver, options=options if options else None)


def list_templates() -> list:
    """List all available template names."""
    return TemplateRegistry.list_templates()


__all__ = [
    # Main API
    "solve",
    "get_template",
    "list_templates",
    # Base classes
    "ProblemTemplate",
    "TemplateInfo",
    "TemplateRegistry",
    # Mathematical
    "LinearProgrammingTemplate",
    "QuadraticProgrammingTemplate",
    "MixedIntegerTemplate",
    # Classic
    "KnapsackTemplate",
    "TransportationTemplate",
    "AssignmentTemplate",
    # Routing
    "TSPTemplate",
    "VRPTemplate",
    # Network
    "MinCostFlowTemplate",
    "MaxFlowTemplate",
    # Scheduling
    "JobShopTemplate",
    # Packing
    "BinPackingTemplate",
    # Facility
    "FacilityLocationTemplate",
    # Finance
    "PortfolioTemplate",
]
