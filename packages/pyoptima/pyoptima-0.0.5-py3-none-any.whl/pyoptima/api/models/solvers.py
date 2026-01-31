"""
Request/Response models for solver endpoints.
"""

from typing import List

from pydantic import BaseModel, Field


class SolverInfo(BaseModel):
    """Information about an available solver."""

    name: str = Field(..., description="Solver name")
    available: bool = Field(..., description="Whether solver is installed and available")
    supports: List[str] = Field(..., description="Problem types supported (LP, MIP, QP, NLP)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "highs",
                "available": True,
                "supports": ["LP", "MIP"],
            }
        }
    }


class SolversListResponse(BaseModel):
    """Response model for solvers list."""

    solvers: List[SolverInfo] = Field(..., description="List of available solvers")
    total: int = Field(..., description="Total number of solvers")

    model_config = {
        "json_schema_extra": {
            "example": {
                "solvers": [
                    {"name": "highs", "available": True, "supports": ["LP", "MIP"]},
                    {"name": "ipopt", "available": True, "supports": ["LP", "QP", "NLP"]},
                ],
                "total": 2,
            }
        }
    }
