"""
API models package.

Exports request and response models for the PyOptima API.
"""

from pyoptima.api.models.optimization import (
    BatchOptimizeRequest,
    BatchOptimizeResponse,
    OptimizeRequest,
    OptimizeResponse,
    SolverOptions,
    ValidateRequest,
    ValidationResponse,
)
from pyoptima.api.models.jobs import (
    AsyncJobResponse,
    JobResponse,
    JobStatus,
)
from pyoptima.api.models.templates import (
    TemplateInfo,
    TemplatesListResponse,
)
from pyoptima.api.models.solvers import (
    SolverInfo,
    SolversListResponse,
)

__all__ = [
    # Optimization
    "OptimizeRequest",
    "OptimizeResponse",
    "BatchOptimizeRequest",
    "BatchOptimizeResponse",
    "ValidateRequest",
    "ValidationResponse",
    "SolverOptions",
    # Jobs
    "AsyncJobResponse",
    "JobResponse",
    "JobStatus",
    # Templates
    "TemplateInfo",
    "TemplatesListResponse",
    # Solvers
    "SolverInfo",
    "SolversListResponse",
]
