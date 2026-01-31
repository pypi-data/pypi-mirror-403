"""
Optimization execution service.

Handles the execution of optimization jobs using the PyOptima solve API.
"""

import asyncio
from typing import Any, Dict, List, Optional
import uuid

from pyoptima import solve, get_template, list_templates

from pyoptima.api.models.optimization import OptimizeRequest
from pyoptima.api.models.jobs import JobStatus
from pyoptima.api.services.job_manager import JobManager


class OptimizationService:
    """
    Service for executing optimization jobs.

    Provides both synchronous and asynchronous optimization execution
    using the PyOptima solve API.
    """

    def __init__(self, job_manager: JobManager):
        """
        Initialize optimization service.

        Args:
            job_manager: JobManager instance for managing job state
        """
        self.job_manager = job_manager

    def optimize_sync(self, request: OptimizeRequest) -> Dict[str, Any]:
        """
        Execute optimization synchronously.

        Args:
            request: Optimization request

        Returns:
            Optimization result dictionary

        Raises:
            ValueError: If template or data is invalid
            RuntimeError: If optimization fails
        """
        # Get solver configuration
        solver_name = None
        solver_options = {}

        if request.solver:
            solver_name = request.solver.name
            if request.solver.time_limit:
                solver_options["time_limit"] = request.solver.time_limit
            if request.solver.gap_tolerance:
                solver_options["mip_gap"] = request.solver.gap_tolerance
            if request.solver.verbose:
                solver_options["verbose"] = request.solver.verbose
            solver_options.update(request.solver.options)

        try:
            # Use PyOptima solve function
            result = solve(
                template_name=request.template,
                data=request.data,
                solver=solver_name,
                **solver_options,
            )
            return result

        except Exception as e:
            raise RuntimeError(f"Optimization failed: {str(e)}") from e

    async def optimize_async(
        self,
        job_id: str,
        request: OptimizeRequest,
    ) -> None:
        """
        Execute optimization asynchronously.

        Updates job status in job_manager as optimization progresses.

        Args:
            job_id: Job identifier
            request: Optimization request
        """
        # Update status to running
        self.job_manager.update_job_status(job_id, JobStatus.RUNNING)

        try:
            # Run optimization in thread to avoid blocking event loop
            result = await asyncio.to_thread(self.optimize_sync, request)

            # Update status to completed
            self.job_manager.update_job_status(
                job_id, JobStatus.COMPLETED, result=result
            )

        except Exception as e:
            # Update status to failed
            self.job_manager.update_job_status(
                job_id, JobStatus.FAILED, error=str(e)
            )

    def optimize_batch_sync(
        self,
        requests: List[OptimizeRequest],
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple optimizations sequentially.

        Args:
            requests: List of optimization requests

        Returns:
            List of optimization results
        """
        results = []
        for req in requests:
            try:
                result = self.optimize_sync(req)
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "error": str(e),
                    "job_id": req.job_id or str(uuid.uuid4()),
                })
        return results

    @staticmethod
    def validate_data(template: str, data: Dict[str, Any]) -> List[str]:
        """
        Validate optimization data without solving.

        Args:
            template: Template name
            data: Problem data

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            template_obj = get_template(template)
            template_obj.validate_data(data)
        except KeyError as e:
            errors.append(f"Unknown template: {template}")
        except ValueError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return errors

    @staticmethod
    def get_template_info(template: str) -> Dict[str, Any]:
        """
        Get information about a template.

        Args:
            template: Template name

        Returns:
            Template information dictionary

        Raises:
            KeyError: If template not found
        """
        template_obj = get_template(template)
        info = template_obj.info

        return {
            "name": info.name,
            "description": info.description,
            "problem_type": info.problem_type,
            "required_data": info.required_data,
            "optional_data": info.optional_data,
            "default_solver": info.default_solver,
        }

    @staticmethod
    def list_templates() -> List[str]:
        """
        List all available templates.

        Returns:
            List of template names
        """
        return list_templates()
