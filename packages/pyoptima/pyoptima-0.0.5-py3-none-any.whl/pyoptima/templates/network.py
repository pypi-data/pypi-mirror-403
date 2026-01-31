"""
Network flow optimization templates.

Covers Min Cost Flow and Max Flow problems.
"""

from typing import Any, Dict, List, Optional, Tuple

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("mincostflow")
@TemplateRegistry.register("min_cost_flow")
class MinCostFlowTemplate(ProblemTemplate):
    """
    Minimum Cost Flow template.
    
    Finds minimum cost flow through a network.
    
    Data format:
        {
            "nodes": ["S", "A", "B", "T"],
            "arcs": [
                {"from": "S", "to": "A", "capacity": 10, "cost": 2},
                {"from": "S", "to": "B", "capacity": 8, "cost": 3},
                {"from": "A", "to": "B", "capacity": 5, "cost": 1},
                {"from": "A", "to": "T", "capacity": 7, "cost": 4},
                {"from": "B", "to": "T", "capacity": 10, "cost": 2},
            ],
            "supply": {"S": 15},   # Positive = supply
            "demand": {"T": 15}    # Positive = demand
        }
    
    Result format:
        {
            "status": "optimal",
            "total_cost": 45.0,
            "flows": {"S->A": 7, "S->B": 8, ...}
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="mincostflow",
            description="Minimum Cost Flow",
            problem_type="LP",
            required_data=["nodes", "arcs"],
            optional_data=["supply", "demand"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["nodes", "arcs"])
        
        nodes = set(data["nodes"])
        for arc in data["arcs"]:
            if arc["from"] not in nodes:
                raise ValueError(f"Arc from unknown node: {arc['from']}")
            if arc["to"] not in nodes:
                raise ValueError(f"Arc to unknown node: {arc['to']}")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        nodes = data["nodes"]
        arcs = data["arcs"]
        supply = data.get("supply", {})
        demand = data.get("demand", {})
        
        model = AbstractModel("MinCostFlow")
        
        # Flow variables for each arc
        arc_names = []
        for arc in arcs:
            arc_name = f"{arc['from']}->{arc['to']}"
            arc_names.append(arc_name)
            capacity = arc.get("capacity")
            model.add_continuous(f"f_{arc_name}", lb=0, ub=capacity)
        
        # Objective: minimize total cost
        obj_expr = Expression()
        for arc, arc_name in zip(arcs, arc_names):
            cost = arc.get("cost", 0)
            obj_expr.add_term(cost, f"f_{arc_name}")
        model.minimize(obj_expr)
        
        # Flow conservation at each node
        for node in nodes:
            expr = Expression()
            
            # Outgoing flow
            for arc, arc_name in zip(arcs, arc_names):
                if arc["from"] == node:
                    expr.add_term(1.0, f"f_{arc_name}")
            
            # Incoming flow
            for arc, arc_name in zip(arcs, arc_names):
                if arc["to"] == node:
                    expr.add_term(-1.0, f"f_{arc_name}")
            
            # Net supply/demand
            net = supply.get(node, 0) - demand.get(node, 0)
            model.add_eq_constraint(f"balance_{node}", expr, net)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {"status": result.status.value, "message": result.message}
        
        arcs = data["arcs"]
        flows = {}
        for arc in arcs:
            arc_name = f"{arc['from']}->{arc['to']}"
            flow = result.solution.get(f"f_{arc_name}", 0)
            if flow > 0.001:
                flows[arc_name] = flow
        
        return {
            "status": result.status.value,
            "total_cost": result.objective_value,
            "flows": flows,
            "solve_time": result.solve_time
        }


@TemplateRegistry.register("maxflow")
@TemplateRegistry.register("max_flow")
class MaxFlowTemplate(ProblemTemplate):
    """
    Maximum Flow template.
    
    Finds maximum flow from source to sink.
    
    Data format:
        {
            "nodes": ["S", "A", "B", "T"],
            "arcs": [
                {"from": "S", "to": "A", "capacity": 10},
                {"from": "S", "to": "B", "capacity": 8},
                {"from": "A", "to": "B", "capacity": 5},
                {"from": "A", "to": "T", "capacity": 7},
                {"from": "B", "to": "T", "capacity": 10},
            ],
            "source": "S",
            "sink": "T"
        }
    
    Result format:
        {
            "status": "optimal",
            "max_flow": 15.0,
            "flows": {"S->A": 7, "S->B": 8, ...}
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="maxflow",
            description="Maximum Flow",
            problem_type="LP",
            required_data=["nodes", "arcs", "source", "sink"],
            optional_data=[],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["nodes", "arcs", "source", "sink"])
        
        nodes = set(data["nodes"])
        if data["source"] not in nodes:
            raise ValueError(f"Source not in nodes: {data['source']}")
        if data["sink"] not in nodes:
            raise ValueError(f"Sink not in nodes: {data['sink']}")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        nodes = data["nodes"]
        arcs = data["arcs"]
        source = data["source"]
        sink = data["sink"]
        
        model = AbstractModel("MaxFlow")
        
        # Total flow variable
        model.add_continuous("total_flow", lb=0)
        
        # Flow variables for each arc
        arc_names = []
        for arc in arcs:
            arc_name = f"{arc['from']}->{arc['to']}"
            arc_names.append(arc_name)
            capacity = arc.get("capacity", float('inf'))
            model.add_continuous(f"f_{arc_name}", lb=0, ub=capacity if capacity != float('inf') else None)
        
        # Objective: maximize total flow
        obj_expr = Expression()
        obj_expr.add_term(1.0, "total_flow")
        model.maximize(obj_expr)
        
        # Flow conservation at each node
        for node in nodes:
            expr = Expression()
            
            # Outgoing flow
            for arc, arc_name in zip(arcs, arc_names):
                if arc["from"] == node:
                    expr.add_term(1.0, f"f_{arc_name}")
            
            # Incoming flow
            for arc, arc_name in zip(arcs, arc_names):
                if arc["to"] == node:
                    expr.add_term(-1.0, f"f_{arc_name}")
            
            if node == source:
                # Source: outflow = total_flow
                expr.add_term(-1.0, "total_flow")
                model.add_eq_constraint(f"balance_{node}", expr, 0)
            elif node == sink:
                # Sink: inflow = total_flow
                expr.add_term(1.0, "total_flow")
                model.add_eq_constraint(f"balance_{node}", expr, 0)
            else:
                # Transit: inflow = outflow
                model.add_eq_constraint(f"balance_{node}", expr, 0)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {"status": result.status.value, "message": result.message}
        
        arcs = data["arcs"]
        flows = {}
        for arc in arcs:
            arc_name = f"{arc['from']}->{arc['to']}"
            flow = result.solution.get(f"f_{arc_name}", 0)
            if flow > 0.001:
                flows[arc_name] = flow
        
        return {
            "status": result.status.value,
            "max_flow": result.solution.get("total_flow", result.objective_value),
            "flows": flows,
            "solve_time": result.solve_time
        }
