"""
Response models for PyOptima API.

Pydantic models for API responses with proper documentation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OptimizationStatus(str, Enum):
    """Optimization result status."""

    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    ERROR = "error"


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


class AsyncJobResponse(BaseModel):
    """Response model for async job submission."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "opt-001",
                "status": "queued",
                "message": "Job submitted successfully",
            }
        }
    }


class JobResponse(BaseModel):
    """Response model for job status and results."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    template: Optional[str] = Field(None, description="Template used")
    result: Optional[Dict[str, Any]] = Field(None, description="Optimization results (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    duration_ms: Optional[float] = Field(None, description="Job duration in milliseconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "opt-001",
                "status": "completed",
                "template": "knapsack",
                "result": {"status": "optimal", "objective_value": 130},
                "created_at": "2024-01-15T10:00:00Z",
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:00:01Z",
                "duration_ms": 15.2,
            }
        }
    }


class TemplateInfo(BaseModel):
    """Information about an optimization template."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    problem_type: str = Field(..., description="Problem type (LP, MIP, QP, etc.)")
    required_data: List[str] = Field(..., description="Required data fields")
    optional_data: List[str] = Field(default_factory=list, description="Optional data fields")
    default_solver: str = Field(..., description="Default solver for this template")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "knapsack",
                "description": "0-1 Knapsack Problem",
                "problem_type": "MIP",
                "required_data": ["items", "capacity"],
                "optional_data": [],
                "default_solver": "highs",
            }
        }
    }


class TemplatesListResponse(BaseModel):
    """Response model for templates list."""

    templates: List[str] = Field(..., description="List of template names")
    total: int = Field(..., description="Total number of templates")

    model_config = {
        "json_schema_extra": {
            "example": {
                "templates": ["knapsack", "lp", "portfolio", "tsp"],
                "total": 4,
            }
        }
    }


class SolverInfo(BaseModel):
    """Information about an available solver."""

    name: str = Field(..., description="Solver name")
    available: bool = Field(..., description="Whether solver is installed and available")
    supports: List[str] = Field(..., description="Problem types supported (LP, MIP, QP, NLP)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "highs",
                "available": True,
                "supports": ["LP", "MIP"],
            }
        }
    }


class SolversListResponse(BaseModel):
    """Response model for solvers list."""

    solvers: List[SolverInfo] = Field(..., description="List of available solvers")
    total: int = Field(..., description="Total number of solvers")

    model_config = {
        "json_schema_extra": {
            "example": {
                "solvers": [
                    {"name": "highs", "available": True, "supports": ["LP", "MIP"]},
                    {"name": "ipopt", "available": True, "supports": ["LP", "QP", "NLP"]},
                ],
                "total": 2,
            }
        }
    }


class ValidationResponse(BaseModel):
    """Response model for data validation."""

    valid: bool = Field(..., description="Whether the data is valid")
    template: str = Field(..., description="Template validated against")
    errors: List[str] = Field(default_factory=list, description="Validation errors (if any)")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings (if any)")

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


class BatchOptimizeResponse(BaseModel):
    """Response model for batch optimization."""

    total: int = Field(..., description="Total number of requests")
    completed: int = Field(..., description="Number of completed requests")
    failed: int = Field(..., description="Number of failed requests")
    results: List[OptimizeResponse] = Field(..., description="Individual results")
    duration_ms: float = Field(..., description="Total batch duration in milliseconds")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="PyOptima version")
    solvers_available: int = Field(..., description="Number of available solvers")
    templates_available: int = Field(..., description="Number of available templates")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "solvers_available": 5,
                "templates_available": 14,
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "Missing required field: items",
                "details": {"template": "knapsack", "missing_fields": ["items"]},
            }
        }
    }
