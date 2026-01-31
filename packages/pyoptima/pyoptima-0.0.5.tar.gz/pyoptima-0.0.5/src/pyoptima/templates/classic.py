"""
Classic optimization problem templates.

Includes Knapsack, Transportation, and Assignment problems.
"""

from typing import Any, Dict, List, Optional

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("knapsack")
class KnapsackTemplate(ProblemTemplate):
    """
    Knapsack Problem template.
    
    Selects items to maximize value within a weight capacity.
    Supports 0-1, bounded, and unbounded variants.
    
    Data format:
        {
            "items": [
                {"name": "A", "value": 60, "weight": 10},
                {"name": "B", "value": 100, "weight": 20},
                ...
            ],
            # OR
            "values": [60, 100, 120, ...],
            "weights": [10, 20, 30, ...],
            
            "capacity": 50,
            
            # Optional
            "variant": "01",  # "01", "bounded", "unbounded"
            "quantities": [1, 2, 3, ...],  # For bounded variant
        }
    
    Result format:
        {
            "status": "optimal",
            "total_value": 220,
            "total_weight": 50,
            "selected_items": [
                {"name": "A", "quantity": 1, "value": 60, "weight": 10},
                {"name": "B", "quantity": 1, "value": 100, "weight": 20},
                ...
            ]
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="knapsack",
            description="Knapsack Problem (0-1, bounded, unbounded)",
            problem_type="MILP",
            required_data=["capacity"],
            optional_data=["items", "values", "weights", "variant", "quantities"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["capacity"])
        
        if "items" not in data and ("values" not in data or "weights" not in data):
            raise ValueError("Either 'items' or both 'values' and 'weights' must be provided")
        
        if data["capacity"] <= 0:
            raise ValueError("Capacity must be positive")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        capacity = data["capacity"]
        variant = data.get("variant", "01")
        
        # Get item data
        if "items" in data:
            items = data["items"]
            values = [item["value"] for item in items]
            weights = [item["weight"] for item in items]
        else:
            values = data["values"]
            weights = data["weights"]
            items = [{"name": f"item{i}"} for i in range(len(values))]
        
        n = len(values)
        quantities = data.get("quantities", [1] * n)
        
        model = AbstractModel("Knapsack")
        
        # Variables based on variant
        if variant == "01":
            for i in range(n):
                model.add_binary(f"x", indices=(i,))
        elif variant == "bounded":
            for i in range(n):
                model.add_integer(f"x", lb=0, ub=quantities[i], indices=(i,))
        else:  # unbounded
            max_qty = capacity // min(weights) + 1
            for i in range(n):
                model.add_integer(f"x", lb=0, ub=max_qty, indices=(i,))
        
        # Objective: maximize total value
        obj_expr = Expression()
        for i in range(n):
            obj_expr.add_term(values[i], f"x[{i}]")
        model.maximize(obj_expr)
        
        # Constraint: weight capacity
        weight_expr = Expression()
        for i in range(n):
            weight_expr.add_term(weights[i], f"x[{i}]")
        model.add_leq_constraint("capacity", weight_expr, capacity)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {
                "status": result.status.value,
                "message": result.message
            }
        
        # Get item data
        if "items" in data:
            items = data["items"]
            values = [item["value"] for item in items]
            weights = [item["weight"] for item in items]
        else:
            values = data["values"]
            weights = data["weights"]
            items = [{"name": f"item{i}"} for i in range(len(values))]
        
        n = len(values)
        
        # Extract selected items
        selected = []
        total_weight = 0
        
        for i in range(n):
            qty = result.solution.get(f"x[{i}]", 0)
            if qty > 0.5:
                qty = round(qty)
                name = items[i].get("name", f"item{i}")
                selected.append({
                    "name": name,
                    "quantity": qty,
                    "value": values[i] * qty,
                    "weight": weights[i] * qty
                })
                total_weight += weights[i] * qty
        
        return {
            "status": result.status.value,
            "total_value": result.objective_value,
            "total_weight": total_weight,
            "selected_items": selected,
            "solve_time": result.solve_time
        }


@TemplateRegistry.register("transportation")
class TransportationTemplate(ProblemTemplate):
    """
    Transportation Problem template.
    
    Finds minimum cost flow from sources to destinations.
    
    Data format:
        {
            "sources": ["S1", "S2", ...],
            "destinations": ["D1", "D2", ...],
            "supply": [100, 150, ...],
            "demand": [80, 120, ...],
            "costs": [
                [10, 20, 15],  # Costs from S1 to each destination
                [12, 8, 18],   # Costs from S2 to each destination
                ...
            ]
        }
    
    Result format:
        {
            "status": "optimal",
            "total_cost": 5000,
            "shipments": [
                {"from": "S1", "to": "D1", "quantity": 80},
                {"from": "S1", "to": "D2", "quantity": 20},
                ...
            ]
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="transportation",
            description="Transportation Problem",
            problem_type="LP",
            required_data=["sources", "destinations", "supply", "demand", "costs"],
            optional_data=[],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["sources", "destinations", "supply", "demand", "costs"])
        
        n_sources = len(data["sources"])
        n_dests = len(data["destinations"])
        
        if len(data["supply"]) != n_sources:
            raise ValueError("Supply must match number of sources")
        if len(data["demand"]) != n_dests:
            raise ValueError("Demand must match number of destinations")
        if len(data["costs"]) != n_sources:
            raise ValueError("Costs must have one row per source")
        
        for i, row in enumerate(data["costs"]):
            if len(row) != n_dests:
                raise ValueError(f"Cost row {i} must have {n_dests} entries")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        sources = data["sources"]
        destinations = data["destinations"]
        supply = data["supply"]
        demand = data["demand"]
        costs = data["costs"]
        
        n_sources = len(sources)
        n_dests = len(destinations)
        
        model = AbstractModel("Transportation")
        
        # Variables: x[i,j] = quantity shipped from source i to dest j
        for i in range(n_sources):
            for j in range(n_dests):
                model.add_continuous(f"x", lb=0, indices=(i, j))
        
        # Objective: minimize total cost
        obj_expr = Expression()
        for i in range(n_sources):
            for j in range(n_dests):
                obj_expr.add_term(costs[i][j], f"x[{i},{j}]")
        model.minimize(obj_expr)
        
        # Supply constraints
        for i in range(n_sources):
            expr = Expression()
            for j in range(n_dests):
                expr.add_term(1.0, f"x[{i},{j}]")
            model.add_leq_constraint(f"supply_{i}", expr, supply[i])
        
        # Demand constraints
        for j in range(n_dests):
            expr = Expression()
            for i in range(n_sources):
                expr.add_term(1.0, f"x[{i},{j}]")
            model.add_geq_constraint(f"demand_{j}", expr, demand[j])
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {
                "status": result.status.value,
                "message": result.message
            }
        
        sources = data["sources"]
        destinations = data["destinations"]
        
        n_sources = len(sources)
        n_dests = len(destinations)
        
        # Extract shipments
        shipments = []
        for i in range(n_sources):
            for j in range(n_dests):
                qty = result.solution.get(f"x[{i},{j}]", 0)
                if qty > 0.001:
                    shipments.append({
                        "from": sources[i],
                        "to": destinations[j],
                        "quantity": qty
                    })
        
        return {
            "status": result.status.value,
            "total_cost": result.objective_value,
            "shipments": shipments,
            "solve_time": result.solve_time
        }


@TemplateRegistry.register("assignment")
class AssignmentTemplate(ProblemTemplate):
    """
    Assignment Problem template.
    
    Assigns workers to tasks to minimize/maximize total cost/profit.
    
    Data format:
        {
            "workers": ["W1", "W2", ...],
            "tasks": ["T1", "T2", ...],
            "costs": [
                [10, 20, 15],  # Costs of W1 doing each task
                [12, 8, 18],   # Costs of W2 doing each task
                ...
            ],
            # Optional
            "maximize": False  # If True, maximize (profit instead of cost)
        }
    
    Result format:
        {
            "status": "optimal",
            "total_cost": 35,
            "assignments": {"W1": "T3", "W2": "T2", ...}
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="assignment",
            description="Assignment Problem",
            problem_type="MILP",
            required_data=["workers", "tasks", "costs"],
            optional_data=["maximize"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["workers", "tasks", "costs"])
        
        n_workers = len(data["workers"])
        n_tasks = len(data["tasks"])
        
        if len(data["costs"]) != n_workers:
            raise ValueError("Costs must have one row per worker")
        
        for i, row in enumerate(data["costs"]):
            if len(row) != n_tasks:
                raise ValueError(f"Cost row {i} must have {n_tasks} entries")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        workers = data["workers"]
        tasks = data["tasks"]
        costs = data["costs"]
        maximize = data.get("maximize", False)
        
        n_workers = len(workers)
        n_tasks = len(tasks)
        
        model = AbstractModel("Assignment")
        
        # Binary variables: x[i,j] = 1 if worker i assigned to task j
        for i in range(n_workers):
            for j in range(n_tasks):
                model.add_binary(f"x", indices=(i, j))
        
        # Objective
        obj_expr = Expression()
        for i in range(n_workers):
            for j in range(n_tasks):
                obj_expr.add_term(costs[i][j], f"x[{i},{j}]")
        
        if maximize:
            model.maximize(obj_expr)
        else:
            model.minimize(obj_expr)
        
        # Each worker assigned to at most one task
        for i in range(n_workers):
            expr = Expression()
            for j in range(n_tasks):
                expr.add_term(1.0, f"x[{i},{j}]")
            model.add_leq_constraint(f"worker_{i}", expr, 1.0)
        
        # Each task assigned to exactly one worker
        for j in range(n_tasks):
            expr = Expression()
            for i in range(n_workers):
                expr.add_term(1.0, f"x[{i},{j}]")
            model.add_eq_constraint(f"task_{j}", expr, 1.0)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {
                "status": result.status.value,
                "message": result.message
            }
        
        workers = data["workers"]
        tasks = data["tasks"]
        maximize = data.get("maximize", False)
        
        n_workers = len(workers)
        n_tasks = len(tasks)
        
        # Extract assignments
        assignments = {}
        for i in range(n_workers):
            for j in range(n_tasks):
                val = result.solution.get(f"x[{i},{j}]", 0)
                if val > 0.5:
                    assignments[workers[i]] = tasks[j]
        
        return {
            "status": result.status.value,
            "total_cost" if not maximize else "total_profit": result.objective_value,
            "assignments": assignments,
            "solve_time": result.solve_time
        }
