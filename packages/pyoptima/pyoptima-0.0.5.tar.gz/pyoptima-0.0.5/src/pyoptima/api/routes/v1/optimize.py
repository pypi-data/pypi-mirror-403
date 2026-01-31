"""
Route handlers for optimization operations.
"""

import time
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from pyoptima.api.dependencies import get_job_manager, get_optimization_service
from pyoptima.api.models.optimization import (
    BatchOptimizeRequest,
    BatchOptimizeResponse,
    OptimizeRequest,
    OptimizeResponse,
    ValidateRequest,
    ValidationResponse,
)
from pyoptima.api.models.jobs import AsyncJobResponse, JobStatus
from pyoptima.api.services.job_manager import JobManager
from pyoptima.api.services.optimization_service import OptimizationService

router = APIRouter()


@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronous optimization",
    description="Submit an optimization request and wait for the result. "
    "Best for problems that complete quickly (< 30 seconds).",
    responses={
        200: {"description": "Optimization completed successfully"},
        400: {"description": "Invalid request data"},
        422: {"description": "Validation error"},
        500: {"description": "Optimization failed"},
    },
)
async def optimize_sync(
    request: OptimizeRequest,
    service: Annotated[OptimizationService, Depends(get_optimization_service)],
) -> OptimizeResponse:
    """
    Execute optimization synchronously.
    
    Returns results immediately after optimization completes.
    For long-running optimizations, use the async endpoint instead.
    """
    job_id = request.job_id or str(uuid.uuid4())
    start_time = time.perf_counter()

    # Get solver name for response
    solver_name = request.solver.name if request.solver else "default"

    try:
        result = service.optimize_sync(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Determine solver actually used
        if solver_name == "default":
            from pyoptima import get_template
            try:
                template_obj = get_template(request.template)
                solver_name = template_obj.info.default_solver
            except Exception:
                solver_name = "unknown"

        return OptimizeResponse(
            job_id=job_id,
            status=result.get("status", "unknown"),
            result=result,
            template=request.template,
            solver=solver_name,
            duration_ms=duration_ms,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/optimize/async",
    response_model=AsyncJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Asynchronous optimization",
    description="Submit an optimization request and receive a job ID for status polling. "
    "Best for long-running optimizations.",
    responses={
        202: {"description": "Job submitted successfully"},
        400: {"description": "Invalid request data"},
        422: {"description": "Validation error"},
    },
)
async def optimize_async(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    service: Annotated[OptimizationService, Depends(get_optimization_service)],
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
) -> AsyncJobResponse:
    """
    Execute optimization asynchronously.
    
    Returns immediately with a job ID. Use GET /jobs/{job_id} to poll for results.
    """
    # Validate request data first
    errors = service.validate_data(request.template, request.data)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )

    # Submit job
    job_id = job_manager.submit_job(
        template=request.template,
        data=request.data,
        job_id=request.job_id,
    )

    # Start background task
    background_tasks.add_task(
        service.optimize_async,
        job_id=job_id,
        request=request,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="Job submitted successfully. Poll GET /jobs/{job_id} for results.",
    )


@router.post(
    "/optimize/batch",
    response_model=BatchOptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch optimization",
    description="Submit multiple optimization requests at once. "
    "Requests are processed sequentially.",
    responses={
        200: {"description": "Batch completed"},
        400: {"description": "Invalid request data"},
    },
)
async def optimize_batch(
    request: BatchOptimizeRequest,
    service: Annotated[OptimizationService, Depends(get_optimization_service)],
) -> BatchOptimizeResponse:
    """
    Execute multiple optimizations in a batch.
    
    All requests are processed and results returned together.
    """
    start_time = time.perf_counter()

    results = service.optimize_batch_sync(requests=request.requests)

    duration_ms = (time.perf_counter() - start_time) * 1000

    # Convert to response format
    responses = []
    completed = 0
    failed = 0

    for i, result in enumerate(results):
        req = request.requests[i]
        job_id = req.job_id or str(uuid.uuid4())

        if result.get("status") == "error":
            failed += 1
            status_str = "error"
        else:
            completed += 1
            status_str = result.get("status", "unknown")

        solver_name = req.solver.name if req.solver else "default"

        responses.append(
            OptimizeResponse(
                job_id=job_id,
                status=status_str,
                result=result,
                template=req.template,
                solver=solver_name,
                duration_ms=0,  # Individual timing not tracked in batch
            )
        )

    return BatchOptimizeResponse(
        total=len(request.requests),
        completed=completed,
        failed=failed,
        results=responses,
        duration_ms=duration_ms,
    )


@router.post(
    "/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate optimization data",
    description="Validate problem data against a template without running optimization.",
    responses={
        200: {"description": "Validation result"},
        404: {"description": "Template not found"},
    },
)
async def validate_data(
    request: ValidateRequest,
    service: Annotated[OptimizationService, Depends(get_optimization_service)],
) -> ValidationResponse:
    """
    Validate optimization data without solving.
    
    Useful for checking data format before submitting optimization jobs.
    """
    errors = service.validate_data(request.template, request.data)

    return ValidationResponse(
        valid=len(errors) == 0,
        template=request.template,
        errors=errors,
        warnings=[],
    )
