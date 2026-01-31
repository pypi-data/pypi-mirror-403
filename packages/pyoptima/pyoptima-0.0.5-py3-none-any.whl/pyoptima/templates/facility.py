"""
Facility location problem templates.
"""

from typing import Any, Dict, List, Optional

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("facility")
@TemplateRegistry.register("facility_location")
class FacilityLocationTemplate(ProblemTemplate):
    """
    Facility Location Problem template.
    
    Determines which facilities to open and how to assign customers
    to facilities to minimize total cost (fixed + transportation).
    
    Data format:
        {
            "facilities": [
                {"name": "F1", "fixed_cost": 1000, "capacity": 500},
                {"name": "F2", "fixed_cost": 1500, "capacity": 800},
                ...
            ],
            "customers": [
                {"name": "C1", "demand": 100},
                {"name": "C2", "demand": 150},
                ...
            ],
            "transport_costs": [
                [10, 20, 15],  # Costs from customer 0 to each facility
                [25, 5, 30],   # Costs from customer 1 to each facility
                ...
            ],
            # Optional
            "uncapacitated": False  # If True, ignore capacity constraints
        }
    
    Result format:
        {
            "status": "optimal",
            "total_cost": 5000,
            "fixed_cost": 2500,
            "transport_cost": 2500,
            "facilities_opened": ["F1", "F3"],
            "assignments": {"C1": "F1", "C2": "F3", ...},
            "facility_loads": {"F1": 250, "F3": 300}
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="facility_location",
            description="Facility Location Problem",
            problem_type="MILP",
            required_data=["facilities", "customers", "transport_costs"],
            optional_data=["uncapacitated"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["facilities", "customers", "transport_costs"])
        
        n_facilities = len(data["facilities"])
        n_customers = len(data["customers"])
        
        if len(data["transport_costs"]) != n_customers:
            raise ValueError("Transport costs must have one row per customer")
        
        for i, row in enumerate(data["transport_costs"]):
            if len(row) != n_facilities:
                raise ValueError(f"Transport cost row {i} must have {n_facilities} entries")
        
        for i, f in enumerate(data["facilities"]):
            if "fixed_cost" not in f:
                raise ValueError(f"Facility {i} missing 'fixed_cost'")
            if not data.get("uncapacitated", False) and "capacity" not in f:
                raise ValueError(f"Facility {i} missing 'capacity' (or set uncapacitated=True)")
        
        for i, c in enumerate(data["customers"]):
            if "demand" not in c:
                raise ValueError(f"Customer {i} missing 'demand'")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        facilities = data["facilities"]
        customers = data["customers"]
        transport_costs = data["transport_costs"]
        uncapacitated = data.get("uncapacitated", False)
        
        n_facilities = len(facilities)
        n_customers = len(customers)
        
        model = AbstractModel("FacilityLocation")
        
        # Binary variables: y[j] = 1 if facility j is opened
        for j in range(n_facilities):
            model.add_binary(f"y", indices=(j,))
        
        # Continuous variables: x[i,j] = fraction of customer i served by facility j
        for i in range(n_customers):
            for j in range(n_facilities):
                model.add_continuous(f"x", lb=0, ub=1, indices=(i, j))
        
        # Objective: minimize total cost
        obj_expr = Expression()
        
        # Fixed costs
        for j in range(n_facilities):
            obj_expr.add_term(facilities[j]["fixed_cost"], f"y[{j}]")
        
        # Transportation costs
        for i in range(n_customers):
            for j in range(n_facilities):
                cost = transport_costs[i][j] * customers[i]["demand"]
                obj_expr.add_term(cost, f"x[{i},{j}]")
        
        model.minimize(obj_expr)
        
        # Constraint: each customer fully served
        for i in range(n_customers):
            expr = Expression()
            for j in range(n_facilities):
                expr.add_term(1.0, f"x[{i},{j}]")
            model.add_eq_constraint(f"serve_{i}", expr, 1.0)
        
        # Constraint: can only assign to open facilities
        for i in range(n_customers):
            for j in range(n_facilities):
                expr = Expression()
                expr.add_term(1.0, f"x[{i},{j}]")
                expr.add_term(-1.0, f"y[{j}]")
                model.add_leq_constraint(f"open_{i}_{j}", expr, 0.0)
        
        # Capacity constraints (if not uncapacitated)
        if not uncapacitated:
            for j in range(n_facilities):
                expr = Expression()
                for i in range(n_customers):
                    expr.add_term(customers[i]["demand"], f"x[{i},{j}]")
                model.add_leq_constraint(f"cap_{j}", expr, facilities[j]["capacity"])
        
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
        
        facilities = data["facilities"]
        customers = data["customers"]
        transport_costs = data["transport_costs"]
        
        n_facilities = len(facilities)
        n_customers = len(customers)
        
        # Extract opened facilities
        facilities_opened = []
        fixed_cost = 0
        
        for j in range(n_facilities):
            val = result.solution.get(f"y[{j}]", 0)
            if val > 0.5:
                name = facilities[j].get("name", f"F{j}")
                facilities_opened.append(name)
                fixed_cost += facilities[j]["fixed_cost"]
        
        # Extract assignments
        assignments = {}
        facility_loads = {f.get("name", f"F{j}"): 0 for j, f in enumerate(facilities)}
        transport_cost = 0
        
        for i in range(n_customers):
            customer_name = customers[i].get("name", f"C{i}")
            demand = customers[i]["demand"]
            
            for j in range(n_facilities):
                val = result.solution.get(f"x[{i},{j}]", 0)
                if val > 0.5:
                    facility_name = facilities[j].get("name", f"F{j}")
                    assignments[customer_name] = facility_name
                    facility_loads[facility_name] += demand
                    transport_cost += transport_costs[i][j] * demand
        
        return {
            "status": result.status.value,
            "total_cost": result.objective_value,
            "fixed_cost": fixed_cost,
            "transport_cost": transport_cost,
            "facilities_opened": facilities_opened,
            "assignments": assignments,
            "facility_loads": {k: v for k, v in facility_loads.items() if v > 0},
            "solve_time": result.solve_time
        }
