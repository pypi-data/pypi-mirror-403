"""
Request/Response models for template endpoints.
"""

from typing import List

from pydantic import BaseModel, Field


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
