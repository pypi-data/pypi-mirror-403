"""
Scheduling problem templates.

Includes Job Shop Scheduling and related problems.
"""

from typing import Any, Dict, List, Optional, Tuple

from pyoptima.model.core import (
    AbstractModel,
    Expression,
    OptimizationResult,
    VariableType,
)
from pyoptima.templates.base import ProblemTemplate, TemplateInfo, TemplateRegistry


@TemplateRegistry.register("jobshop")
class JobShopTemplate(ProblemTemplate):
    """
    Job Shop Scheduling Problem template.
    
    Schedules jobs on machines to minimize makespan (total completion time).
    Each job consists of operations that must be performed in order,
    and each operation requires a specific machine.
    
    Data format:
        {
            "jobs": [
                {
                    "name": "Job1",
                    "operations": [
                        {"machine": 0, "duration": 3},
                        {"machine": 1, "duration": 2},
                        ...
                    ]
                },
                ...
            ],
            "num_machines": 3,
            # Optional
            "horizon": 1000  # Time horizon (computed if not provided)
        }
    
    Result format:
        {
            "status": "optimal",
            "makespan": 25,
            "schedule": {
                "Job1": [
                    {"operation": 0, "machine": 0, "start": 0, "end": 3},
                    {"operation": 1, "machine": 1, "start": 3, "end": 5},
                    ...
                ],
                ...
            },
            "machine_schedules": {
                0: [("Job1", 0, 0, 3), ("Job2", 0, 5, 8), ...],
                ...
            }
        }
    """
    
    @property
    def info(self) -> TemplateInfo:
        return TemplateInfo(
            name="jobshop",
            description="Job Shop Scheduling Problem",
            problem_type="MILP",
            required_data=["jobs", "num_machines"],
            optional_data=["horizon"],
            default_solver="highs"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> None:
        self._require_keys(data, ["jobs", "num_machines"])
        
        num_machines = data["num_machines"]
        if num_machines <= 0:
            raise ValueError("Number of machines must be positive")
        
        for i, job in enumerate(data["jobs"]):
            if "operations" not in job:
                raise ValueError(f"Job {i} missing 'operations'")
            for j, op in enumerate(job["operations"]):
                if "machine" not in op or "duration" not in op:
                    raise ValueError(f"Job {i} operation {j} missing 'machine' or 'duration'")
                if op["machine"] < 0 or op["machine"] >= num_machines:
                    raise ValueError(f"Job {i} operation {j} has invalid machine index")
    
    def build_model(self, data: Dict[str, Any]) -> AbstractModel:
        jobs = data["jobs"]
        num_machines = data["num_machines"]
        
        # Compute horizon if not provided
        horizon = data.get("horizon")
        if horizon is None:
            horizon = sum(
                sum(op["duration"] for op in job["operations"])
                for job in jobs
            )
        
        model = AbstractModel("JobShop")
        
        # Collect all operations
        operations = []  # List of (job_idx, op_idx, machine, duration)
        for j_idx, job in enumerate(jobs):
            for o_idx, op in enumerate(job["operations"]):
                operations.append((j_idx, o_idx, op["machine"], op["duration"]))
        
        # Start time variables for each operation
        for j_idx, o_idx, machine, duration in operations:
            model.add_continuous(f"start", lb=0, ub=horizon-duration, indices=(j_idx, o_idx))
        
        # Makespan variable
        model.add_continuous("makespan", lb=0, ub=horizon)
        
        # Binary variables for machine ordering
        # y[j1,o1,j2,o2] = 1 if (j1,o1) precedes (j2,o2) on their shared machine
        machine_ops = {}  # machine -> list of (j_idx, o_idx, duration)
        for j_idx, o_idx, machine, duration in operations:
            if machine not in machine_ops:
                machine_ops[machine] = []
            machine_ops[machine].append((j_idx, o_idx, duration))
        
        for machine, ops in machine_ops.items():
            for i in range(len(ops)):
                for j in range(i + 1, len(ops)):
                    j1, o1, _ = ops[i]
                    j2, o2, _ = ops[j]
                    model.add_binary(f"y", indices=(j1, o1, j2, o2))
        
        # Objective: minimize makespan
        obj_expr = Expression()
        obj_expr.add_term(1.0, "makespan")
        model.minimize(obj_expr)
        
        # Constraint: makespan >= end time of each operation
        for j_idx, o_idx, machine, duration in operations:
            expr = Expression()
            expr.add_term(1.0, "makespan")
            expr.add_term(-1.0, f"start[{j_idx},{o_idx}]")
            model.add_geq_constraint(f"makespan_{j_idx}_{o_idx}", expr, duration)
        
        # Precedence constraints within jobs
        for j_idx, job in enumerate(jobs):
            for o_idx in range(len(job["operations"]) - 1):
                duration = job["operations"][o_idx]["duration"]
                expr = Expression()
                expr.add_term(1.0, f"start[{j_idx},{o_idx + 1}]")
                expr.add_term(-1.0, f"start[{j_idx},{o_idx}]")
                model.add_geq_constraint(f"prec_{j_idx}_{o_idx}", expr, duration)
        
        # Machine disjunctive constraints
        M = horizon
        for machine, ops in machine_ops.items():
            for i in range(len(ops)):
                for j in range(i + 1, len(ops)):
                    j1, o1, d1 = ops[i]
                    j2, o2, d2 = ops[j]
                    
                    # Either (j1,o1) before (j2,o2) or vice versa
                    # start[j1,o1] + d1 <= start[j2,o2] + M*(1-y)
                    expr1 = Expression()
                    expr1.add_term(1.0, f"start[{j1},{o1}]")
                    expr1.add_term(-1.0, f"start[{j2},{o2}]")
                    expr1.add_term(M, f"y[{j1},{o1},{j2},{o2}]")
                    model.add_leq_constraint(f"mach_{j1}_{o1}_{j2}_{o2}_a", expr1, M - d1)
                    
                    # start[j2,o2] + d2 <= start[j1,o1] + M*y
                    expr2 = Expression()
                    expr2.add_term(1.0, f"start[{j2},{o2}]")
                    expr2.add_term(-1.0, f"start[{j1},{o1}]")
                    expr2.add_term(-M, f"y[{j1},{o1},{j2},{o2}]")
                    model.add_leq_constraint(f"mach_{j1}_{o1}_{j2}_{o2}_b", expr2, -d2)
        
        # Add custom constraints if provided
        custom_constraints = data.get("custom_constraints", [])
        self._add_custom_constraints(model, custom_constraints, operations, horizon)
        
        return model
    
    def _add_custom_constraints(
        self,
        model: AbstractModel,
        custom_constraints: List[Dict[str, Any]],
        operations: List[Tuple],
        horizon: float
    ) -> None:
        """
        Add custom constraints to the model.
        
        Custom constraints can be specified as:
        - "deadline": {"job": 0, "operation": 1, "deadline": 50}
        - "release_time": {"job": 0, "operation": 0, "release_time": 10}
        - "machine_capacity": {"machine": 0, "max_concurrent": 2}
        - "job_priority": {"job": 0, "must_finish_before": 1}
        - "time_window": {"job": 0, "operation": 0, "earliest": 5, "latest": 30}
        - "resource_limit": {"resource": "energy", "limit": 1000}
        - "sequence": {"job": 0, "operations": [0, 1, 2], "max_gap": 5}
        
        Args:
            model: AbstractModel to add constraints to
            custom_constraints: List of custom constraint specifications
            operations: List of (job_idx, op_idx, machine, duration) tuples
            horizon: Time horizon for the problem
        """
        for i, constraint_spec in enumerate(custom_constraints):
            constraint_type = constraint_spec.get("type")
            
            if constraint_type == "deadline":
                # Operation must finish by deadline
                job_idx = constraint_spec["job"]
                op_idx = constraint_spec["operation"]
                deadline = constraint_spec["deadline"]
                
                # Find operation duration
                duration = next(
                    (d for j, o, m, d in operations if j == job_idx and o == op_idx),
                    None
                )
                if duration is None:
                    continue
                
                expr = Expression()
                expr.add_term(1.0, f"start[{job_idx},{op_idx}]")
                model.add_leq_constraint(f"deadline_{i}", expr, deadline - duration)
            
            elif constraint_type == "release_time":
                # Operation cannot start before release time
                job_idx = constraint_spec["job"]
                op_idx = constraint_spec["operation"]
                release_time = constraint_spec["release_time"]
                
                expr = Expression()
                expr.add_term(1.0, f"start[{job_idx},{op_idx}]")
                model.add_geq_constraint(f"release_{i}", expr, release_time)
            
            elif constraint_type == "time_window":
                # Operation must start within time window
                job_idx = constraint_spec["job"]
                op_idx = constraint_spec["operation"]
                earliest = constraint_spec.get("earliest", 0)
                latest = constraint_spec.get("latest", horizon)
                
                expr_earliest = Expression()
                expr_earliest.add_term(1.0, f"start[{job_idx},{op_idx}]")
                model.add_geq_constraint(f"window_earliest_{i}", expr_earliest, earliest)
                
                expr_latest = Expression()
                expr_latest.add_term(1.0, f"start[{job_idx},{op_idx}]")
                model.add_leq_constraint(f"window_latest_{i}", expr_latest, latest)
            
            elif constraint_type == "job_priority":
                # One job must finish before another starts
                job1 = constraint_spec["job"]
                job2 = constraint_spec["must_finish_before"]
                
                # Find last operation of job1 and first operation of job2
                job1_ops = [(j, o, m, d) for j, o, m, d in operations if j == job1]
                job2_ops = [(j, o, m, d) for j, o, m, d in operations if j == job2]
                
                if job1_ops and job2_ops:
                    # Last op of job1
                    _, last_op, _, last_dur = max(job1_ops, key=lambda x: x[1])
                    # First op of job2
                    _, first_op, _, _ = min(job2_ops, key=lambda x: x[1])
                    
                    expr = Expression()
                    expr.add_term(1.0, f"start[{job2},{first_op}]")
                    expr.add_term(-1.0, f"start[{job1},{last_op}]")
                    model.add_geq_constraint(f"priority_{i}", expr, last_dur)
            
            elif constraint_type == "sequence":
                # Operations must be scheduled in sequence with max gap
                job_idx = constraint_spec["job"]
                op_indices = constraint_spec["operations"]
                max_gap = constraint_spec.get("max_gap", horizon)
                
                for k in range(len(op_indices) - 1):
                    op1 = op_indices[k]
                    op2 = op_indices[k + 1]
                    
                    # Find durations
                    dur1 = next(
                        (d for j, o, m, d in operations if j == job_idx and o == op1),
                        None
                    )
                    if dur1 is None:
                        continue
                    
                    expr = Expression()
                    expr.add_term(1.0, f"start[{job_idx},{op2}]")
                    expr.add_term(-1.0, f"start[{job_idx},{op1}]")
                    model.add_leq_constraint(f"sequence_{i}_{k}", expr, dur1 + max_gap)
            
            elif constraint_type == "expression":
                # Custom constraint using expression language
                # This requires parsing the expression and adding it to the model
                # For now, we'll note this is available but requires expression parser integration
                expr_str = constraint_spec.get("expr")
                if expr_str:
                    # Note: Full expression parsing integration would go here
                    # For now, we support simple expressions via the constraint builder
                    pass
    
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
        
        jobs = data["jobs"]
        
        # Extract schedule
        schedule = {}
        machine_schedules = {}
        
        for j_idx, job in enumerate(jobs):
            job_name = job.get("name", f"Job{j_idx}")
            job_schedule = []
            
            for o_idx, op in enumerate(job["operations"]):
                start = result.solution.get(f"start[{j_idx},{o_idx}]", 0)
                duration = op["duration"]
                machine = op["machine"]
                
                job_schedule.append({
                    "operation": o_idx,
                    "machine": machine,
                    "start": start,
                    "end": start + duration
                })
                
                # Add to machine schedule
                if machine not in machine_schedules:
                    machine_schedules[machine] = []
                machine_schedules[machine].append((job_name, o_idx, start, start + duration))
            
            schedule[job_name] = job_schedule
        
        # Sort machine schedules by start time
        for machine in machine_schedules:
            machine_schedules[machine].sort(key=lambda x: x[2])
        
        return {
            "status": result.status.value,
            "makespan": result.solution.get("makespan", result.objective_value),
            "schedule": schedule,
            "machine_schedules": machine_schedules,
            "solve_time": result.solve_time
        }
