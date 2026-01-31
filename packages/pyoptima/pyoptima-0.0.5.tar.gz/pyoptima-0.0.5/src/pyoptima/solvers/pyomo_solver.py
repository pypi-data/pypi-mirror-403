"""
Pyomo solver backend.

Translates AbstractModel to Pyomo and solves using various Pyomo-supported solvers.
"""

import time
from typing import Dict, List, Optional

import pyomo.environ as pyo

from pyoptima.model.core import (
    AbstractModel,
    Constraint,
    ConstraintSense,
    Expression,
    Objective,
    OptimizationResult,
    OptimizationSense,
    SolverStatus,
    Term,
    Variable,
    VariableType,
)
from pyoptima.solvers.base import (
    ProblemType,
    SolverCapabilities,
    SolverInterface,
    SolverOptions,
    register_solver,
)


# Mapping of solver names to Pyomo solver interfaces
PYOMO_SOLVER_MAP = {
    "ipopt": "ipopt_v2",      # Use cyipopt interface
    "highs": "appsi_highs",   # Use highspy interface
    "cbc": "cbc",
    "glpk": "glpk",
    "gurobi": "gurobi",
    "cplex": "cplex",
    "scip": "scip",
}

# Solver capabilities
SOLVER_CAPABILITIES = {
    "ipopt": SolverCapabilities(
        name="ipopt",
        supported_problem_types=[ProblemType.LP, ProblemType.QP, ProblemType.NLP],
        description="Interior Point Optimizer - nonlinear solver"
    ),
    "highs": SolverCapabilities(
        name="highs",
        supported_problem_types=[ProblemType.LP, ProblemType.MILP, ProblemType.QP, ProblemType.MIQP],
        description="HiGHS - high-performance LP/MIP solver"
    ),
    "cbc": SolverCapabilities(
        name="cbc",
        supported_problem_types=[ProblemType.LP, ProblemType.MILP],
        description="COIN-OR Branch and Cut - open-source MIP solver"
    ),
    "glpk": SolverCapabilities(
        name="glpk",
        supported_problem_types=[ProblemType.LP, ProblemType.MILP],
        description="GNU Linear Programming Kit"
    ),
    "gurobi": SolverCapabilities(
        name="gurobi",
        supported_problem_types=[ProblemType.LP, ProblemType.MILP, ProblemType.QP, ProblemType.MIQP],
        is_free=False,
        description="Gurobi Optimizer - commercial solver (requires license)"
    ),
    "cplex": SolverCapabilities(
        name="cplex",
        supported_problem_types=[ProblemType.LP, ProblemType.MILP, ProblemType.QP, ProblemType.MIQP],
        is_free=False,
        description="IBM CPLEX - commercial solver (requires license)"
    ),
}


@register_solver("pyomo")
class PyomoSolver(SolverInterface):
    """
    Pyomo-based solver implementation.
    
    Uses Pyomo as the modeling interface and supports various solver backends
    including HiGHS, IPOPT, CBC, GLPK, Gurobi, and CPLEX.
    """
    
    def __init__(self, solver_name: str = "highs"):
        """
        Initialize Pyomo solver.
        
        Args:
            solver_name: Name of the underlying solver to use
        """
        self._solver_name = solver_name.lower()
        self._pyomo_solver_name = PYOMO_SOLVER_MAP.get(self._solver_name, self._solver_name)
    
    @property
    def name(self) -> str:
        return f"pyomo:{self._solver_name}"
    
    @property
    def capabilities(self) -> SolverCapabilities:
        return SOLVER_CAPABILITIES.get(
            self._solver_name,
            SolverCapabilities(
                name=self._solver_name,
                supported_problem_types=[ProblemType.LP, ProblemType.MILP]
            )
        )
    
    def is_available(self) -> bool:
        """Check if solver is available."""
        try:
            solver = pyo.SolverFactory(self._pyomo_solver_name)
            return solver.available()
        except Exception:
            return False
    
    def solve(self, model: AbstractModel, options: Optional[SolverOptions] = None) -> OptimizationResult:
        """
        Solve model using Pyomo.
        
        Args:
            model: AbstractModel to solve
            options: Solver options
            
        Returns:
            OptimizationResult with solution
        """
        options = options or SolverOptions()
        
        # Validate model
        self.validate_model(model)
        
        # Convert to Pyomo model
        pyomo_model = self._build_pyomo_model(model)
        
        # Create solver
        solver = self._create_solver(options)
        
        # Solve
        start_time = time.time()
        try:
            results = solver.solve(pyomo_model, tee=options.verbose)
            solve_time = time.time() - start_time
        except Exception as e:
            return OptimizationResult(
                status=SolverStatus.ERROR,
                message=f"Solver error: {str(e)}"
            )
        
        # Extract results
        return self._extract_results(model, pyomo_model, results, solve_time)
    
    def _build_pyomo_model(self, model: AbstractModel) -> pyo.ConcreteModel:
        """Convert AbstractModel to Pyomo ConcreteModel."""
        pyo_model = pyo.ConcreteModel(model.name)
        
        # Store variable mapping for expression building
        var_map: Dict[str, pyo.Var] = {}
        
        # Create variables
        for var_name, var in model.variables.items():
            domain = self._get_pyomo_domain(var.var_type)
            bounds = (var.lower_bound, var.upper_bound)
            pyo_var = pyo.Var(domain=domain, bounds=bounds)
            setattr(pyo_model, f"v_{var_name.replace('[', '_').replace(']', '').replace(',', '_')}", pyo_var)
            var_map[var_name] = pyo_var
        
        # Store var_map on model for expression building
        pyo_model._var_map = var_map
        
        # Create objective
        if model.objective is not None:
            obj_expr = self._build_pyomo_expression(model.objective.expression, var_map)
            sense = pyo.minimize if model.objective.sense == OptimizationSense.MINIMIZE else pyo.maximize
            pyo_model.objective = pyo.Objective(expr=obj_expr, sense=sense)
        
        # Create constraints
        pyo_model.constraints = pyo.ConstraintList()
        for const_name, const in model.constraints.items():
            lhs_expr = self._build_pyomo_expression(const.lhs, var_map)
            
            if const.sense == ConstraintSense.LEQ:
                pyo_model.constraints.add(lhs_expr <= const.rhs)
            elif const.sense == ConstraintSense.GEQ:
                pyo_model.constraints.add(lhs_expr >= const.rhs)
            else:  # EQ
                pyo_model.constraints.add(lhs_expr == const.rhs)
        
        return pyo_model
    
    def _get_pyomo_domain(self, var_type: VariableType):
        """Convert VariableType to Pyomo domain."""
        if var_type == VariableType.BINARY:
            return pyo.Binary
        elif var_type == VariableType.INTEGER:
            return pyo.Integers
        else:
            return pyo.Reals
    
    def _build_pyomo_expression(self, expr: Expression, var_map: Dict[str, pyo.Var]):
        """Convert Expression to Pyomo expression."""
        result = expr.constant
        
        for term in expr.terms:
            # Get variable(s)
            var_name = term.variable if isinstance(term.variable, str) else term.variable.full_name
            var = var_map.get(var_name)
            
            if var is None:
                available_vars = list(var_map.keys())
                suggestions = [v for v in available_vars if var_name.lower() in v.lower() or v.lower() in var_name.lower()]
                msg = f"Variable '{var_name}' not found in model."
                if suggestions:
                    msg += f"\n\nDid you mean one of these?\n  " + "\n  ".join(suggestions[:5])
                msg += f"\n\nAvailable variables: {', '.join(available_vars[:10])}"
                if len(available_vars) > 10:
                    msg += f" ... and {len(available_vars) - 10} more"
                raise ValueError(msg)
            
            if term.is_quadratic:
                # Quadratic term
                var2_name = term.variable2 if isinstance(term.variable2, str) else term.variable2.full_name
                var2 = var_map.get(var2_name)
                if var2 is None:
                    available_vars = list(var_map.keys())
                    suggestions = [v for v in available_vars if var2_name.lower() in v.lower() or v.lower() in var2_name.lower()]
                    msg = f"Variable '{var2_name}' not found in model."
                    if suggestions:
                        msg += f"\n\nDid you mean one of these?\n  " + "\n  ".join(suggestions[:5])
                    msg += f"\n\nAvailable variables: {', '.join(available_vars[:10])}"
                    if len(available_vars) > 10:
                        msg += f" ... and {len(available_vars) - 10} more"
                    raise ValueError(msg)
                result += term.coefficient * var * var2
            else:
                # Linear term
                result += term.coefficient * var
        
        return result
    
    def _create_solver(self, options: SolverOptions):
        """Create Pyomo solver with options."""
        solver = pyo.SolverFactory(self._pyomo_solver_name)
        
        # Apply common options (solver-specific translation)
        if options.time_limit is not None:
            if self._solver_name == "ipopt":
                solver.options["max_cpu_time"] = options.time_limit
            elif self._solver_name == "highs":
                solver.options["time_limit"] = options.time_limit
            elif self._solver_name in ("cbc", "glpk"):
                solver.options["sec"] = options.time_limit
            elif self._solver_name == "gurobi":
                solver.options["TimeLimit"] = options.time_limit
            elif self._solver_name == "cplex":
                solver.options["timelimit"] = options.time_limit
        
        if options.mip_gap is not None:
            if self._solver_name == "highs":
                solver.options["mip_rel_gap"] = options.mip_gap
            elif self._solver_name == "cbc":
                solver.options["ratioGap"] = options.mip_gap
            elif self._solver_name == "gurobi":
                solver.options["MIPGap"] = options.mip_gap
            elif self._solver_name == "cplex":
                solver.options["mipgap"] = options.mip_gap
        
        if options.threads is not None:
            if self._solver_name == "highs":
                solver.options["threads"] = options.threads
            elif self._solver_name == "gurobi":
                solver.options["Threads"] = options.threads
            elif self._solver_name == "cplex":
                solver.options["threads"] = options.threads
        
        # Apply extra options
        for key, value in options.extra_options.items():
            solver.options[key] = value
        
        return solver
    
    def _extract_results(
        self,
        abstract_model: AbstractModel,
        pyomo_model: pyo.ConcreteModel,
        results,
        solve_time: float
    ) -> OptimizationResult:
        """Extract results from solved Pyomo model."""
        # Determine status
        status = self._get_solver_status(results)
        
        # Extract objective value
        obj_value = None
        if hasattr(pyomo_model, 'objective') and status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            try:
                obj_value = pyo.value(pyomo_model.objective)
            except Exception:
                pass
        
        # Extract solution
        solution = {}
        if status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            var_map = pyomo_model._var_map
            for var_name, pyo_var in var_map.items():
                try:
                    val = pyo.value(pyo_var)
                    if val is not None:
                        solution[var_name] = val
                        # Update value in abstract model
                        if var_name in abstract_model.variables:
                            abstract_model.variables[var_name].value = val
                except Exception:
                    pass
        
        # Get message
        message = str(results.solver.termination_condition) if hasattr(results, 'solver') else ""
        
        # Get MIP gap if available
        gap = None
        if hasattr(results, 'solver') and hasattr(results.solver, 'gap'):
            gap = results.solver.gap
        
        return OptimizationResult(
            status=status,
            objective_value=obj_value,
            solution=solution,
            message=message,
            solve_time=solve_time,
            gap=gap
        )
    
    def _get_solver_status(self, results) -> SolverStatus:
        """Convert Pyomo solver status to SolverStatus."""
        if not hasattr(results, 'solver'):
            return SolverStatus.UNKNOWN
        
        from pyomo.opt import SolverStatus as PyomoStatus
        from pyomo.opt import TerminationCondition
        
        solver_status = results.solver.status
        termination = results.solver.termination_condition
        
        if solver_status == PyomoStatus.ok:
            if termination == TerminationCondition.optimal:
                return SolverStatus.OPTIMAL
            elif termination in (TerminationCondition.feasible, TerminationCondition.maxIterations):
                return SolverStatus.FEASIBLE
            elif termination == TerminationCondition.infeasible:
                return SolverStatus.INFEASIBLE
            elif termination == TerminationCondition.unbounded:
                return SolverStatus.UNBOUNDED
            elif termination == TerminationCondition.maxTimeLimit:
                return SolverStatus.TIME_LIMIT
        elif solver_status == PyomoStatus.error:
            return SolverStatus.ERROR
        
        return SolverStatus.UNKNOWN
