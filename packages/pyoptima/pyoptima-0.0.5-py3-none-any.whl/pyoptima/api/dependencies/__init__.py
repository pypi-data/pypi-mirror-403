"""
Dependency injection for PyOptima API.
"""

from pyoptima.api.dependencies.core import (
    get_job_manager,
    get_optimization_service,
)

__all__ = [
    "get_job_manager",
    "get_optimization_service",
]
