"""
Routing problem templates (TSP, VRP).

These templates solve vehicle routing and traveling salesman problems.
"""

from typing import Any, Dict, List, Optional

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    OptimizationSense,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("tsp")
class TSPTemplate(ProblemTemplate):
    """
    Traveling Salesman Problem template.
    
    Finds the shortest route visiting all cities exactly once and
    returning to the starting city.
    
    Data format:
        {
            "cities": ["A", "B", "C", ...],  # City names
            "distances": [[...], ...],       # Distance matrix (n x n)
            # OR
            "coordinates": [(x1, y1), ...],  # City coordinates (Euclidean)
        }
    
    Result format:
        {
            "status": "optimal",
            "tour": ["A", "B", "C", "D", "A"],  # Ordered tour
            "total_distance": 123.45,
            "edges": [("A", "B"), ("B", "C"), ...]  # Tour edges
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="tsp",
            description="Traveling Salesman Problem",
            problem_type="MILP",
            required_data=["cities"],
            optional_data=["distances", "coordinates"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["cities"])
        
        n = len(data["cities"])
        if n < 2:
            raise ValueError("TSP requires at least 2 cities")
        
        if "distances" not in data and "coordinates" not in data:
            raise ValueError("Either 'distances' or 'coordinates' must be provided")
        
        if "distances" in data:
            dist = data["distances"]
            if len(dist) != n or any(len(row) != n for row in dist):
                raise ValueError(f"Distance matrix must be {n}x{n}")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        cities = data["cities"]
        n = len(cities)
        
        # Get or compute distances
        if "distances" in data:
            distances = data["distances"]
        else:
            distances = self._compute_euclidean_distances(data["coordinates"])
        
        model = AbstractModel("TSP")
        
        # Binary variables: x[i,j] = 1 if edge (i,j) is in tour
        for i in range(n):
            for j in range(n):
                if i != j:
                    model.add_binary(f"x", indices=(i, j))
        
        # MTZ subtour elimination variables
        for i in range(1, n):
            model.add_continuous(f"u", lb=1, ub=n-1, indices=(i,))
        
        # Objective: minimize total distance
        obj_expr = Expression()
        for i in range(n):
            for j in range(n):
                if i != j:
                    obj_expr.add_term(distances[i][j], f"x[{i},{j}]")
        model.minimize(obj_expr)
        
        # Constraints: each city has exactly one outgoing edge
        for i in range(n):
            expr = Expression()
            for j in range(n):
                if i != j:
                    expr.add_term(1.0, f"x[{i},{j}]")
            model.add_eq_constraint(f"out_{i}", expr, 1.0)
        
        # Constraints: each city has exactly one incoming edge
        for j in range(n):
            expr = Expression()
            for i in range(n):
                if i != j:
                    expr.add_term(1.0, f"x[{i},{j}]")
            model.add_eq_constraint(f"in_{j}", expr, 1.0)
        
        # MTZ subtour elimination constraints
        for i in range(1, n):
            for j in range(1, n):
                if i != j:
                    expr = Expression()
                    expr.add_term(1.0, f"u[{i}]")
                    expr.add_term(-1.0, f"u[{j}]")
                    expr.add_term(n - 1, f"x[{i},{j}]")
                    model.add_leq_constraint(f"mtz_{i}_{j}", expr, n - 2)
        
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
        
        cities = data["cities"]
        n = len(cities)
        
        # Extract tour from solution
        edges = []
        for i in range(n):
            for j in range(n):
                if i != j:
                    val = result.solution.get(f"x[{i},{j}]", 0)
                    if val > 0.5:
                        edges.append((i, j))
        
        # Reconstruct tour order
        tour_indices = self._reconstruct_tour(edges, n)
        tour = [cities[i] for i in tour_indices]
        tour.append(tour[0])  # Return to start
        
        # Format edges with city names
        tour_edges = [(cities[i], cities[j]) for i, j in edges]
        
        return {
            "status": result.status.value,
            "tour": tour,
            "total_distance": result.objective_value,
            "edges": tour_edges,
            "solve_time": result.solve_time
        }
    
    def _compute_euclidean_distances(self, coordinates: List[tuple]) -> List[List[float]]:
        """Compute Euclidean distance matrix from coordinates."""
        import math
        n = len(coordinates)
        distances = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = coordinates[i][0] - coordinates[j][0]
                    dy = coordinates[i][1] - coordinates[j][1]
                    distances[i][j] = math.sqrt(dx*dx + dy*dy)
        return distances
    
    def _reconstruct_tour(self, edges: List[tuple], n: int) -> List[int]:
        """Reconstruct tour order from edges."""
        # Build adjacency
        next_city = {}
        for i, j in edges:
            next_city[i] = j
        
        # Start from city 0 and follow the tour
        tour = [0]
        current = 0
        while len(tour) < n:
            current = next_city.get(current, 0)
            if current == 0:
                break
            tour.append(current)
        
        return tour


@TemplateRegistry.register("vrp")
class VRPTemplate(ProblemTemplate):
    """
    Vehicle Routing Problem template.
    
    Finds optimal routes for multiple vehicles to serve customers
    while minimizing total distance.
    
    Data format:
        {
            "depot": 0,                    # Depot index
            "customers": [1, 2, 3, ...],   # Customer indices
            "distances": [[...], ...],     # Distance matrix
            "demands": [0, 10, 20, ...],   # Demand at each location
            "vehicle_capacity": 100,       # Vehicle capacity
            "num_vehicles": 3,             # Number of vehicles
        }
    
    Result format:
        {
            "status": "optimal",
            "routes": [[0, 1, 3, 0], [0, 2, 4, 0], ...],  # Routes per vehicle
            "total_distance": 456.78,
            "vehicle_loads": [80, 60, ...]  # Load per vehicle
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="vrp",
            description="Vehicle Routing Problem",
            problem_type="MILP",
            required_data=["distances", "demands", "vehicle_capacity", "num_vehicles"],
            optional_data=["depot", "customers"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["distances", "demands", "vehicle_capacity", "num_vehicles"])
        
        n = len(data["distances"])
        if len(data["demands"]) != n:
            raise ValueError("Demands must match number of locations")
        
        if data["vehicle_capacity"] <= 0:
            raise ValueError("Vehicle capacity must be positive")
        
        if data["num_vehicles"] <= 0:
            raise ValueError("Number of vehicles must be positive")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        distances = data["distances"]
        demands = data["demands"]
        capacity = data["vehicle_capacity"]
        num_vehicles = data["num_vehicles"]
        depot = data.get("depot", 0)
        
        n = len(distances)
        K = num_vehicles
        
        model = AbstractModel("VRP")
        
        # Binary variables: x[i,j,k] = 1 if vehicle k travels from i to j
        for k in range(K):
            for i in range(n):
                for j in range(n):
                    if i != j:
                        model.add_binary(f"x", indices=(i, j, k))
        
        # Load variables for subtour elimination
        for k in range(K):
            for i in range(n):
                if i != depot:
                    model.add_continuous(f"q", lb=0, ub=capacity, indices=(i, k))
        
        # Objective: minimize total distance
        obj_expr = Expression()
        for k in range(K):
            for i in range(n):
                for j in range(n):
                    if i != j:
                        obj_expr.add_term(distances[i][j], f"x[{i},{j},{k}]")
        model.minimize(obj_expr)
        
        # Each customer visited exactly once
        for i in range(n):
            if i != depot:
                expr = Expression()
                for k in range(K):
                    for j in range(n):
                        if i != j:
                            expr.add_term(1.0, f"x[{i},{j},{k}]")
                model.add_eq_constraint(f"visit_{i}", expr, 1.0)
        
        # Flow conservation for each vehicle
        for k in range(K):
            for i in range(n):
                expr = Expression()
                for j in range(n):
                    if i != j:
                        expr.add_term(1.0, f"x[{i},{j},{k}]")
                        expr.add_term(-1.0, f"x[{j},{i},{k}]")
                model.add_eq_constraint(f"flow_{i}_{k}", expr, 0.0)
        
        # Each vehicle leaves depot at most once
        for k in range(K):
            expr = Expression()
            for j in range(n):
                if j != depot:
                    expr.add_term(1.0, f"x[{depot},{j},{k}]")
            model.add_leq_constraint(f"depot_out_{k}", expr, 1.0)
        
        # Capacity constraints (load tracking)
        M = capacity + max(demands)
        for k in range(K):
            for i in range(n):
                if i != depot:
                    for j in range(n):
                        if j != depot and i != j:
                            expr = Expression()
                            expr.add_term(1.0, f"q[{i},{k}]")
                            expr.add_term(-1.0, f"q[{j},{k}]")
                            expr.add_term(M, f"x[{i},{j},{k}]")
                            expr.add_constant(-demands[j])
                            model.add_leq_constraint(f"load_{i}_{j}_{k}", expr, M)
        
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
        
        n = len(data["distances"])
        K = data["num_vehicles"]
        depot = data.get("depot", 0)
        demands = data["demands"]
        
        # Extract routes for each vehicle
        routes = []
        vehicle_loads = []
        
        for k in range(K):
            # Find edges for this vehicle
            edges = []
            for i in range(n):
                for j in range(n):
                    if i != j:
                        val = result.solution.get(f"x[{i},{j},{k}]", 0)
                        if val > 0.5:
                            edges.append((i, j))
            
            if edges:
                # Reconstruct route
                route = self._reconstruct_route(edges, depot, n)
                routes.append(route)
                
                # Calculate load
                load = sum(demands[i] for i in route if i != depot)
                vehicle_loads.append(load)
        
        return {
            "status": result.status.value,
            "routes": routes,
            "total_distance": result.objective_value,
            "vehicle_loads": vehicle_loads,
            "solve_time": result.solve_time
        }
    
    def _reconstruct_route(self, edges: List[tuple], depot: int, n: int) -> List[int]:
        """Reconstruct route from edges."""
        next_node = {}
        for i, j in edges:
            next_node[i] = j
        
        route = [depot]
        current = depot
        while True:
            current = next_node.get(current)
            if current is None or current == depot:
                break
            route.append(current)
        route.append(depot)
        
        return route
