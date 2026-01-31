"""
Request/Response models for optimization endpoints.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class SolverOptions(BaseModel):
    """Solver configuration options."""

    name: str = Field(
        default="highs",
        description="Solver name (highs, ipopt, cbc, glpk, gurobi, cplex, scip)",
    )
    time_limit: Optional[float] = Field(
        default=None,
        description="Time limit in seconds",
        ge=0,
    )
    gap_tolerance: Optional[float] = Field(
        default=None,
        description="Relative MIP gap tolerance",
        ge=0,
        le=1,
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose solver output",
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional solver-specific options",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "highs",
                "time_limit": 60,
                "verbose": False,
            }
        }
    }


class OptimizeRequest(BaseModel):
    """
    Request model for optimization.

    Supports all PyOptima templates with a unified interface.
    """

    template: str = Field(
        ...,
        description="Template name (e.g., 'knapsack', 'lp', 'portfolio', 'tsp')",
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Problem data specific to the template",
    )
    solver: Optional[SolverOptions] = Field(
        default=None,
        description="Solver configuration (uses template default if not provided)",
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Custom job identifier (auto-generated if not provided)",
    )

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        """Normalize template name to lowercase."""
        return v.lower().strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Knapsack Problem",
                    "value": {
                        "template": "knapsack",
                        "data": {
                            "items": [
                                {"name": "gold", "value": 100, "weight": 5},
                                {"name": "silver", "value": 50, "weight": 3},
                                {"name": "bronze", "value": 30, "weight": 2},
                            ],
                            "capacity": 7,
                        },
                    },
                },
                {
                    "summary": "Linear Programming",
                    "value": {
                        "template": "lp",
                        "data": {
                            "c": [3, 2],
                            "A": [[1, 1], [2, 1]],
                            "b": [4, 5],
                            "sense": "maximize",
                        },
                        "solver": {"name": "highs"},
                    },
                },
                {
                    "summary": "Portfolio Optimization",
                    "value": {
                        "template": "portfolio",
                        "data": {
                            "expected_returns": [0.12, 0.10, 0.07],
                            "covariance_matrix": [
                                [0.04, 0.01, 0.02],
                                [0.01, 0.03, 0.01],
                                [0.02, 0.01, 0.02],
                            ],
                            "symbols": ["AAPL", "GOOGL", "MSFT"],
                            "objective": "min_volatility",
                            "max_weight": 0.5,
                        },
                        "solver": {"name": "ipopt"},
                    },
                },
            ]
        }
    }


class OptimizeResponse(BaseModel):
    """Response model for synchronous optimization."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Optimization status (optimal, feasible, infeasible, error)")
    result: Dict[str, Any] = Field(..., description="Optimization results")
    template: str = Field(..., description="Template used")
    solver: str = Field(..., description="Solver used")
    duration_ms: float = Field(..., description="Optimization duration in milliseconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "opt-001",
                "status": "optimal",
                "result": {
                    "objective_value": 130,
                    "selected_items": ["gold", "bronze"],
                    "total_value": 130,
                    "total_weight": 7,
                },
                "template": "knapsack",
                "solver": "highs",
                "duration_ms": 15.2,
            }
        }
    }


class ValidateRequest(BaseModel):
    """Request model for validating optimization data without solving."""

    template: str = Field(
        ...,
        description="Template name to validate against",
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Problem data to validate",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "template": "knapsack",
                "data": {
                    "items": [{"name": "A", "value": 10, "weight": 5}],
                    "capacity": 10,
                },
            }
        }
    }


class ValidationResponse(BaseModel):
    """Response model for data validation."""

    valid: bool = Field(..., description="Whether the data is valid")
    template: str = Field(..., description="Template validated against")
    errors: list[str] = Field(default_factory=list, description="Validation errors (if any)")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings (if any)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "valid": True,
                "template": "knapsack",
                "errors": [],
                "warnings": [],
            }
        }
    }


class BatchOptimizeRequest(BaseModel):
    """Request model for batch optimization (multiple problems)."""

    requests: list[OptimizeRequest] = Field(
        ...,
        description="List of optimization requests",
        min_length=1,
        max_length=100,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "requests": [
                    {
                        "template": "knapsack",
                        "data": {"items": [{"name": "A", "value": 10, "weight": 5}], "capacity": 10},
                        "job_id": "batch-1",
                    },
                    {
                        "template": "knapsack",
                        "data": {"items": [{"name": "B", "value": 20, "weight": 8}], "capacity": 15},
                        "job_id": "batch-2",
                    },
                ],
            }
        }
    }


class BatchOptimizeResponse(BaseModel):
    """Response model for batch optimization."""

    total: int = Field(..., description="Total number of requests")
    completed: int = Field(..., description="Number of completed requests")
    failed: int = Field(..., description="Number of failed requests")
    results: list[OptimizeResponse] = Field(..., description="Individual results")
    duration_ms: float = Field(..., description="Total batch duration in milliseconds")
