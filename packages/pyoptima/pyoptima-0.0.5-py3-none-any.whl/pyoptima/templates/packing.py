"""
Packing problem templates.

Includes Bin Packing and Cutting Stock problems.
"""

from typing import Any, Dict, List, Optional

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("binpacking")
class BinPackingTemplate(ProblemTemplate):
    """
    Bin Packing Problem template.
    
    Packs items into the minimum number of bins.
    
    Data format:
        {
            "items": [
                {"name": "item1", "size": 10},
                {"name": "item2", "size": 20},
                ...
            ],
            # OR
            "item_sizes": [10, 20, 30, ...],
            
            "bin_capacity": 100,
            # Optional
            "max_bins": 10  # Maximum number of bins (computed if not provided)
        }
    
    Result format:
        {
            "status": "optimal",
            "num_bins_used": 3,
            "bins": [
                {"bin": 0, "items": ["item1", "item3"], "used_capacity": 40},
                {"bin": 1, "items": ["item2", "item4"], "used_capacity": 55},
                ...
            ],
            "item_assignments": {"item1": 0, "item2": 1, ...}
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="binpacking",
            description="Bin Packing Problem",
            problem_type="MILP",
            required_data=["bin_capacity"],
            optional_data=["items", "item_sizes", "max_bins"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["bin_capacity"])
        
        if "items" not in data and "item_sizes" not in data:
            raise ValueError("Either 'items' or 'item_sizes' must be provided")
        
        capacity = data["bin_capacity"]
        if capacity <= 0:
            raise ValueError("Bin capacity must be positive")
        
        # Get item sizes
        if "items" in data:
            sizes = [item["size"] for item in data["items"]]
        else:
            sizes = data["item_sizes"]
        
        for i, size in enumerate(sizes):
            if size > capacity:
                raise ValueError(f"Item {i} size ({size}) exceeds bin capacity ({capacity})")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        capacity = data["bin_capacity"]
        
        # Get items
        if "items" in data:
            items = data["items"]
            sizes = [item["size"] for item in items]
        else:
            sizes = data["item_sizes"]
            items = [{"name": f"item{i}", "size": s} for i, s in enumerate(sizes)]
        
        n_items = len(items)
        
        # Compute max bins needed (worst case: one item per bin)
        max_bins = data.get("max_bins", n_items)
        
        model = AbstractModel("BinPacking")
        
        # Binary variables: x[i,b] = 1 if item i is in bin b
        for i in range(n_items):
            for b in range(max_bins):
                model.add_binary(f"x", indices=(i, b))
        
        # Binary variables: y[b] = 1 if bin b is used
        for b in range(max_bins):
            model.add_binary(f"y", indices=(b,))
        
        # Objective: minimize number of bins used
        obj_expr = Expression()
        for b in range(max_bins):
            obj_expr.add_term(1.0, f"y[{b}]")
        model.minimize(obj_expr)
        
        # Constraint: each item in exactly one bin
        for i in range(n_items):
            expr = Expression()
            for b in range(max_bins):
                expr.add_term(1.0, f"x[{i},{b}]")
            model.add_eq_constraint(f"assign_{i}", expr, 1.0)
        
        # Constraint: bin capacity
        for b in range(max_bins):
            expr = Expression()
            for i in range(n_items):
                expr.add_term(sizes[i], f"x[{i},{b}]")
            model.add_leq_constraint(f"capacity_{b}", expr, capacity)
        
        # Constraint: link x and y (if any item in bin, bin is used)
        for b in range(max_bins):
            for i in range(n_items):
                expr = Expression()
                expr.add_term(1.0, f"x[{i},{b}]")
                expr.add_term(-1.0, f"y[{b}]")
                model.add_leq_constraint(f"link_{i}_{b}", expr, 0.0)
        
        # Symmetry breaking: use bins in order
        for b in range(max_bins - 1):
            expr = Expression()
            expr.add_term(1.0, f"y[{b + 1}]")
            expr.add_term(-1.0, f"y[{b}]")
            model.add_leq_constraint(f"symbreak_{b}", expr, 0.0)
        
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
        
        capacity = data["bin_capacity"]
        
        # Get items
        if "items" in data:
            items = data["items"]
            sizes = [item["size"] for item in items]
            names = [item.get("name", f"item{i}") for i, item in enumerate(items)]
        else:
            sizes = data["item_sizes"]
            names = [f"item{i}" for i in range(len(sizes))]
        
        n_items = len(items)
        max_bins = data.get("max_bins", n_items)
        
        # Extract bin assignments
        bins = []
        item_assignments = {}
        num_bins_used = 0
        
        for b in range(max_bins):
            bin_items = []
            used_capacity = 0
            
            for i in range(n_items):
                val = result.solution.get(f"x[{i},{b}]", 0)
                if val > 0.5:
                    bin_items.append(names[i])
                    item_assignments[names[i]] = b
                    used_capacity += sizes[i]
            
            if bin_items:
                bins.append({
                    "bin": b,
                    "items": bin_items,
                    "used_capacity": used_capacity,
                    "utilization": used_capacity / capacity
                })
                num_bins_used += 1
        
        return {
            "status": result.status.value,
            "num_bins_used": num_bins_used,
            "bins": bins,
            "item_assignments": item_assignments,
            "solve_time": result.solve_time
        }
