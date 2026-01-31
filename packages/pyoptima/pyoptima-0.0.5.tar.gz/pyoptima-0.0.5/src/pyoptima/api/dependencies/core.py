"""
Dependency injection for PyOptima API.

Provides singleton services and dependency injection for FastAPI routes.
"""

from functools import lru_cache
from typing import Generator

from pyoptima.api.services.job_manager import JobManager
from pyoptima.api.services.optimization_service import OptimizationService


@lru_cache()
def get_job_manager() -> JobManager:
    """
    Get JobManager singleton instance.

    Returns:
        JobManager: Singleton job manager instance
    """
    return JobManager()


def get_optimization_service() -> Generator[OptimizationService, None, None]:
    """
    Get OptimizationService instance (dependency).

    Yields:
        OptimizationService: Service instance with job manager
    """
    job_manager = get_job_manager()
    yield OptimizationService(job_manager)
