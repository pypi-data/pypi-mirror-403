"""
Job queue management service.

Manages optimization jobs with an in-memory store.
Thread-safe implementation suitable for single-instance deployments.
Can be extended to use Redis or database for distributed deployments.
"""

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pyoptima.api.models.jobs import JobResponse, JobStatus


class JobState:
    """Internal job state representation."""

    __slots__ = [
        "job_id",
        "template",
        "data",
        "status",
        "result",
        "error",
        "created_at",
        "started_at",
        "completed_at",
    ]

    def __init__(
        self,
        job_id: str,
        template: str,
        data: Dict[str, Any],
        status: JobStatus = JobStatus.QUEUED,
    ):
        """Initialize job state."""
        self.job_id = job_id
        self.template = template
        self.data = data
        self.status = status
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_response(self) -> JobResponse:
        """Convert to JobResponse model."""
        duration_ms = None
        if self.completed_at and self.started_at:
            duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        elif self.completed_at and self.created_at:
            duration_ms = (self.completed_at - self.created_at).total_seconds() * 1000

        return JobResponse(
            job_id=self.job_id,
            status=self.status,
            template=self.template,
            result=self.result,
            error=self.error,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            duration_ms=duration_ms,
        )


class JobManager:
    """
    Thread-safe in-memory job manager.

    Manages optimization job lifecycle: creation, status updates, and queries.

    For production distributed deployments, this can be replaced with a
    Redis-backed or database-backed implementation.
    """

    def __init__(self, max_jobs: int = 10000):
        """
        Initialize job manager.

        Args:
            max_jobs: Maximum number of jobs to retain in memory
        """
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.RLock()
        self._max_jobs = max_jobs

    def submit_job(
        self,
        template: str,
        data: Dict[str, Any],
        job_id: Optional[str] = None,
    ) -> str:
        """
        Submit a new optimization job.

        Args:
            template: Template name
            data: Problem data
            job_id: Optional custom job ID

        Returns:
            Job ID (generated if not provided)
        """
        with self._lock:
            # Generate job ID if not provided
            if job_id is None:
                job_id = str(uuid.uuid4())

            # Ensure uniqueness
            while job_id in self._jobs:
                job_id = str(uuid.uuid4())

            # Cleanup old jobs if at capacity
            self._cleanup_if_needed()

            # Create job
            job = JobState(
                job_id=job_id,
                template=template,
                data=data,
                status=JobStatus.QUEUED,
            )
            self._jobs[job_id] = job

            return job_id

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        """
        Get job status and results.

        Args:
            job_id: Job identifier

        Returns:
            JobResponse if found, None otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return job.to_response()

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            result: Optimization result (if completed)
            error: Error message (if failed)

        Returns:
            True if updated, False if job not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False

            job.status = status

            if status == JobStatus.RUNNING and job.started_at is None:
                job.started_at = datetime.now(timezone.utc)

            elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                job.completed_at = datetime.now(timezone.utc)
                if result is not None:
                    job.result = result
                if error is not None:
                    job.error = error

            return True

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[JobResponse]:
        """
        List jobs with optional filtering and pagination.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to return (optional)
            offset: Number of jobs to skip (default 0)

        Returns:
            List of JobResponse objects
        """
        with self._lock:
            jobs = list(self._jobs.values())

            # Filter by status
            if status is not None:
                jobs = [j for j in jobs if j.status == status]

            # Sort by creation time (newest first)
            jobs.sort(key=lambda j: j.created_at, reverse=True)

            # Apply pagination
            if offset > 0:
                jobs = jobs[offset:]
            if limit is not None:
                jobs = jobs[:limit]

            return [job.to_response() for job in jobs]

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or running job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False if job not found or cannot be cancelled
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False

            # Can only cancel queued or running jobs
            if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING):
                return False

            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)

            return True

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the store.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if job not found
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    def get_stats(self) -> Dict[str, int]:
        """
        Get job statistics.

        Returns:
            Dictionary with job counts by status
        """
        with self._lock:
            stats = {status.value: 0 for status in JobStatus}
            stats["total"] = len(self._jobs)

            for job in self._jobs.values():
                stats[job.status.value] += 1

            return stats

    def _cleanup_if_needed(self) -> None:
        """Remove oldest completed jobs if at capacity."""
        if len(self._jobs) < self._max_jobs:
            return

        # Find completed jobs sorted by completion time
        completed = [
            j for j in self._jobs.values()
            if j.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
        ]
        completed.sort(key=lambda j: j.completed_at or j.created_at)

        # Remove oldest 10% of completed jobs
        to_remove = max(1, len(completed) // 10)
        for job in completed[:to_remove]:
            del self._jobs[job.job_id]
