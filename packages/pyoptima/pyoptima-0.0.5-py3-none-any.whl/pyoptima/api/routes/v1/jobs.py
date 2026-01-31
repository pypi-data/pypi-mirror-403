"""
Route handlers for job management operations.
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from pyoptima.api.dependencies import get_job_manager
from pyoptima.api.models.jobs import JobResponse, JobStatus
from pyoptima.api.services.job_manager import JobManager

router = APIRouter()


@router.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="List jobs",
    description="List optimization jobs with optional filtering and pagination.",
    responses={
        200: {"description": "List of jobs"},
    },
)
async def list_jobs(
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
    status: Optional[JobStatus] = Query(
        None,
        description="Filter by job status",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of jobs to return",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of jobs to skip",
    ),
) -> List[JobResponse]:
    """
    List optimization jobs.

    Returns jobs sorted by creation time (newest first).
    Use status filter to find specific job states.
    """
    return job_manager.list_jobs(status=status, limit=limit, offset=offset)


@router.get(
    "/jobs/stats",
    summary="Get job statistics",
    description="Get counts of jobs by status.",
    responses={
        200: {"description": "Job statistics"},
    },
)
async def get_job_stats(
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
) -> dict:
    """
    Get job statistics.

    Returns counts of jobs in each status (queued, running, completed, failed, cancelled).
    """
    return job_manager.get_stats()


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get job status",
    description="Get the status and results of an optimization job.",
    responses={
        200: {"description": "Job details"},
        404: {"description": "Job not found"},
    },
)
async def get_job(
    job_id: str,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
) -> JobResponse:
    """
    Get job status and results.

    For completed jobs, the result field contains the optimization solution.
    For failed jobs, the error field contains the error message.
    """
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    return job


@router.post(
    "/jobs/{job_id}/cancel",
    summary="Cancel job",
    description="Cancel a queued or running optimization job.",
    responses={
        200: {"description": "Job cancelled"},
        400: {"description": "Job cannot be cancelled"},
        404: {"description": "Job not found"},
    },
)
async def cancel_job(
    job_id: str,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
) -> dict:
    """
    Cancel an optimization job.

    Only queued or running jobs can be cancelled.
    Completed, failed, or already cancelled jobs cannot be cancelled.
    """
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    success = job_manager.cancel_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' cannot be cancelled (status: {job.status.value})",
        )

    return {
        "message": f"Job '{job_id}' cancelled successfully",
        "job_id": job_id,
        "status": "cancelled",
    }


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job",
    description="Delete a job from the job store.",
    responses={
        204: {"description": "Job deleted"},
        404: {"description": "Job not found"},
    },
)
async def delete_job(
    job_id: str,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
) -> None:
    """
    Delete a job from storage.

    This permanently removes the job and its results.
    """
    success = job_manager.delete_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )
