"""
Request/Response models for job management endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
