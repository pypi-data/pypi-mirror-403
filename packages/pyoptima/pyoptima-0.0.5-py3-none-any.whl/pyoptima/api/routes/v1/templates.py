"""
Route handlers for template information.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from pyoptima.api.dependencies import get_optimization_service
from pyoptima.api.models.templates import TemplateInfo, TemplatesListResponse
from pyoptima.api.services.optimization_service import OptimizationService

router = APIRouter()


@router.get(
    "/templates",
    response_model=TemplatesListResponse,
    summary="List templates",
    description="List all available optimization templates.",
    responses={
        200: {"description": "List of templates"},
    },
)
async def list_templates(
    service: Annotated[OptimizationService, Depends(get_optimization_service)],
) -> TemplatesListResponse:
    """
    List all available optimization templates.

    Templates provide pre-built solutions for common optimization problems
    like knapsack, linear programming, portfolio optimization, etc.
    """
    templates = service.list_templates()

    return TemplatesListResponse(
        templates=sorted(templates),
        total=len(templates),
    )


@router.get(
    "/templates/{template_name}",
    response_model=TemplateInfo,
    summary="Get template info",
    description="Get detailed information about a specific optimization template.",
    responses={
        200: {"description": "Template information"},
        404: {"description": "Template not found"},
    },
)
async def get_template_info(
    template_name: str,
    service: Annotated[OptimizationService, Depends(get_optimization_service)],
) -> TemplateInfo:
    """
    Get detailed information about an optimization template.

    Returns the template's description, required/optional data fields,
    problem type, and default solver.
    """
    try:
        info = service.get_template_info(template_name.lower())

        return TemplateInfo(
            name=info["name"],
            description=info["description"],
            problem_type=info["problem_type"],
            required_data=info["required_data"],
            optional_data=info.get("optional_data", []),
            default_solver=info["default_solver"],
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found. "
            f"Use GET /templates to see available templates.",
        )
