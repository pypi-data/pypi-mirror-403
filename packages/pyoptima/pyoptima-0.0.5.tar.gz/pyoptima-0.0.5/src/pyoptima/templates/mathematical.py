"""
Mathematical programming templates.

Covers Linear Programming (LP), Quadratic Programming (QP),
and Mixed Integer Programming (MIP).
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("lp")
@TemplateRegistry.register("linear")
class LinearProgrammingTemplate(ProblemTemplate):
    """
    Linear Programming template.
    
    Solves: minimize/maximize c'x subject to Ax <= b, A_eq x = b_eq, lb <= x <= ub
    
    Data format:
        {
            "c": [1, 2, 3],              # Objective coefficients
            "sense": "minimize",          # or "maximize"
            
            # Inequality constraints (optional)
            "A": [[1, 2, 3], [4, 5, 6]], # Constraint matrix
            "b": [10, 20],               # RHS
            
            # Equality constraints (optional)
            "A_eq": [[1, 1, 1]],
            "b_eq": [5],
            
            # Bounds (optional)
            "lb": [0, 0, 0],             # Lower bounds (default: 0)
            "ub": [None, None, None],    # Upper bounds (default: None = unbounded)
            
            # Variable names (optional)
            "var_names": ["x1", "x2", "x3"]
        }
    
    Result format:
        {
            "status": "optimal",
            "objective_value": 15.5,
            "solution": {"x1": 2.5, "x2": 3.0, "x3": 0.0}
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="lp",
            description="Linear Programming",
            problem_type="LP",
            required_data=["c"],
            optional_data=["A", "b", "A_eq", "b_eq", "lb", "ub", "sense", "var_names"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["c"])
        
        n = len(data["c"])
        
        if "A" in data and "b" in data:
            if len(data["b"]) != len(data["A"]):
                raise ValueError(
                    f"Constraint matrix A has {len(data['A'])} rows but b has {len(data['b'])} elements. "
                    f"They must have the same length.\n"
                    f"Hint: Each row of A corresponds to one constraint, so len(A) == len(b)"
                )
            for i, row in enumerate(data["A"]):
                if len(row) != n:
                    raise ValueError(
                        f"Row {i} of A has length {len(row)} but expected {n} (number of variables).\n"
                        f"Hint: Each row of A must have the same length as the objective vector c"
                    )
        
        if "A_eq" in data and "b_eq" in data:
            if len(data["b_eq"]) != len(data["A_eq"]):
                raise ValueError(
                    f"Equality constraint matrix A_eq has {len(data['A_eq'])} rows but b_eq has {len(data['b_eq'])} elements. "
                    f"They must have the same length.\n"
                    f"Hint: Each row of A_eq corresponds to one equality constraint"
                )
            for i, row in enumerate(data["A_eq"]):
                if len(row) != n:
                    raise ValueError(
                        f"Row {i} of A_eq has length {len(row)} but expected {n} (number of variables).\n"
                        f"Hint: Each row of A_eq must have the same length as the objective vector c"
                    )
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        c = data["c"]
        n = len(c)
        sense = data.get("sense", "minimize")
        
        lb = data.get("lb", [0] * n)
        ub = data.get("ub", [None] * n)
        var_names = data.get("var_names", [f"x{i}" for i in range(n)])
        
        model = AbstractModel("LP")
        
        # Variables
        for i in range(n):
            model.add_continuous(
                var_names[i],
                lb=lb[i] if lb[i] is not None else None,
                ub=ub[i] if i < len(ub) and ub[i] is not None else None
            )
        
        # Objective
        obj_expr = Expression()
        for i in range(n):
            obj_expr.add_term(c[i], var_names[i])
        
        if sense == "maximize":
            model.maximize(obj_expr)
        else:
            model.minimize(obj_expr)
        
        # Inequality constraints: Ax <= b
        if "A" in data and "b" in data:
            for j, (row, rhs) in enumerate(zip(data["A"], data["b"])):
                expr = Expression()
                for i in range(n):
                    if row[i] != 0:
                        expr.add_term(row[i], var_names[i])
                model.add_leq_constraint(f"ineq_{j}", expr, rhs)
        
        # Equality constraints: A_eq x = b_eq
        if "A_eq" in data and "b_eq" in data:
            for j, (row, rhs) in enumerate(zip(data["A_eq"], data["b_eq"])):
                expr = Expression()
                for i in range(n):
                    if row[i] != 0:
                        expr.add_term(row[i], var_names[i])
                model.add_eq_constraint(f"eq_{j}", expr, rhs)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {"status": result.status.value, "message": result.message}
        
        return {
            "status": result.status.value,
            "objective_value": result.objective_value,
            "solution": result.solution,
            "solve_time": result.solve_time
        }


@TemplateRegistry.register("qp")
@TemplateRegistry.register("quadratic")
class QuadraticProgrammingTemplate(ProblemTemplate):
    """
    Quadratic Programming template.
    
    Solves: minimize/maximize (1/2)x'Qx + c'x subject to Ax <= b, A_eq x = b_eq
    
    Data format:
        {
            "Q": [[1, 0], [0, 2]],        # Quadratic term (symmetric)
            "c": [1, 2],                   # Linear term (optional)
            "sense": "minimize",
            
            # Constraints (optional)
            "A": [[1, 1]],
            "b": [10],
            "A_eq": [...],
            "b_eq": [...],
            
            # Bounds (optional)
            "lb": [0, 0],
            "ub": [None, None]
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="qp",
            description="Quadratic Programming",
            problem_type="QP",
            required_data=["Q"],
            optional_data=["c", "A", "b", "A_eq", "b_eq", "lb", "ub", "sense"],
            default_solver="ipopt"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["Q"])
        
        Q = data["Q"]
        n = len(Q)
        
        for row in Q:
            if len(row) != n:
                raise ValueError("Q must be square")
        
        if "c" in data and len(data["c"]) != n:
            raise ValueError("c length must match Q dimensions")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        Q = data["Q"]
        n = len(Q)
        c = data.get("c", [0] * n)
        sense = data.get("sense", "minimize")
        
        lb = data.get("lb", [0] * n)
        ub = data.get("ub", [None] * n)
        var_names = data.get("var_names", [f"x{i}" for i in range(n)])
        
        model = AbstractModel("QP")
        
        # Variables
        for i in range(n):
            model.add_continuous(
                var_names[i],
                lb=lb[i] if lb[i] is not None else None,
                ub=ub[i] if i < len(ub) and ub[i] is not None else None
            )
        
        # Objective: (1/2)x'Qx + c'x
        obj_expr = Expression()
        
        # Linear terms
        for i in range(n):
            if c[i] != 0:
                obj_expr.add_term(c[i], var_names[i])
        
        # Quadratic terms
        for i in range(n):
            for j in range(n):
                if Q[i][j] != 0:
                    coef = 0.5 * Q[i][j]
                    obj_expr.add_term(coef, var_names[i], var_names[j])
        
        if sense == "maximize":
            model.maximize(obj_expr)
        else:
            model.minimize(obj_expr)
        
        # Constraints
        if "A" in data and "b" in data:
            for j, (row, rhs) in enumerate(zip(data["A"], data["b"])):
                expr = Expression()
                for i in range(n):
                    if row[i] != 0:
                        expr.add_term(row[i], var_names[i])
                model.add_leq_constraint(f"ineq_{j}", expr, rhs)
        
        if "A_eq" in data and "b_eq" in data:
            for j, (row, rhs) in enumerate(zip(data["A_eq"], data["b_eq"])):
                expr = Expression()
                for i in range(n):
                    if row[i] != 0:
                        expr.add_term(row[i], var_names[i])
                model.add_eq_constraint(f"eq_{j}", expr, rhs)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {"status": result.status.value, "message": result.message}
        
        return {
            "status": result.status.value,
            "objective_value": result.objective_value,
            "solution": result.solution,
            "solve_time": result.solve_time
        }


@TemplateRegistry.register("mip")
@TemplateRegistry.register("milp")
class MixedIntegerTemplate(ProblemTemplate):
    """
    Mixed Integer Programming template.
    
    Solves: minimize/maximize c'x subject to Ax <= b with some variables integer/binary
    
    Data format:
        {
            "c": [1, 2, 3],
            "sense": "minimize",
            
            # Variable types: "continuous", "integer", "binary"
            "var_types": ["continuous", "integer", "binary"],
            
            # Constraints
            "A": [[1, 2, 3]],
            "b": [10],
            
            # Bounds
            "lb": [0, 0, 0],
            "ub": [None, 10, 1]  # Binary vars automatically bounded
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="mip",
            description="Mixed Integer Programming",
            problem_type="MILP",
            required_data=["c", "var_types"],
            optional_data=["A", "b", "A_eq", "b_eq", "lb", "ub", "sense"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["c", "var_types"])
        
        n = len(data["c"])
        if len(data["var_types"]) != n:
            raise ValueError("var_types length must match c")
        
        for vt in data["var_types"]:
            if vt not in ("continuous", "integer", "binary"):
                raise ValueError(f"Invalid var_type: {vt}")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        c = data["c"]
        n = len(c)
        var_types = data["var_types"]
        sense = data.get("sense", "minimize")
        
        lb = data.get("lb", [0] * n)
        ub = data.get("ub", [None] * n)
        var_names = data.get("var_names", [f"x{i}" for i in range(n)])
        
        model = AbstractModel("MIP")
        
        # Variables with types
        for i in range(n):
            vt = var_types[i]
            if vt == "binary":
                model.add_binary(var_names[i])
            elif vt == "integer":
                model.add_integer(
                    var_names[i],
                    lb=lb[i] if lb[i] is not None else None,
                    ub=ub[i] if i < len(ub) and ub[i] is not None else None
                )
            else:
                model.add_continuous(
                    var_names[i],
                    lb=lb[i] if lb[i] is not None else None,
                    ub=ub[i] if i < len(ub) and ub[i] is not None else None
                )
        
        # Objective
        obj_expr = Expression()
        for i in range(n):
            obj_expr.add_term(c[i], var_names[i])
        
        if sense == "maximize":
            model.maximize(obj_expr)
        else:
            model.minimize(obj_expr)
        
        # Constraints
        if "A" in data and "b" in data:
            for j, (row, rhs) in enumerate(zip(data["A"], data["b"])):
                expr = Expression()
                for i in range(n):
                    if row[i] != 0:
                        expr.add_term(row[i], var_names[i])
                model.add_leq_constraint(f"ineq_{j}", expr, rhs)
        
        if "A_eq" in data and "b_eq" in data:
            for j, (row, rhs) in enumerate(zip(data["A_eq"], data["b_eq"])):
                expr = Expression()
                for i in range(n):
                    if row[i] != 0:
                        expr.add_term(row[i], var_names[i])
                model.add_eq_constraint(f"eq_{j}", expr, rhs)
        
        return model
    
    def format_solution(
        self,
        model: AbstractModel,
        result: OptimizationResult,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result.is_feasible:
            return {"status": result.status.value, "message": result.message}
        
        return {
            "status": result.status.value,
            "objective_value": result.objective_value,
            "solution": result.solution,
            "solve_time": result.solve_time,
            "gap": result.gap
        }
