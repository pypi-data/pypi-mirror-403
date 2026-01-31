"""
Route handlers for solver information.
"""

from fastapi import APIRouter

from pyoptima import list_available_solvers

from pyoptima.api.models.solvers import SolverInfo, SolversListResponse

router = APIRouter()


# Solver capabilities mapping
SOLVER_CAPABILITIES = {
    "highs": ["LP", "MIP"],
    "ipopt": ["LP", "QP", "NLP"],
    "cbc": ["LP", "MIP"],
    "glpk": ["LP", "MIP"],
    "gurobi": ["LP", "MIP", "QP", "MIQP"],
    "cplex": ["LP", "MIP", "QP", "MIQP"],
    "scip": ["LP", "MIP", "MINLP"],
}


@router.get(
    "/solvers",
    response_model=SolversListResponse,
    summary="List solvers",
    description="List all available optimization solvers and their capabilities.",
    responses={
        200: {"description": "List of solvers"},
    },
)
async def list_solvers() -> SolversListResponse:
    """
    List all available optimization solvers.

    Returns information about each solver including:
    - Whether it's installed and available
    - What problem types it supports (LP, MIP, QP, NLP)
    """
    available = list_available_solvers()
    available_set = set(available)

    solvers = []
    for solver_name, capabilities in SOLVER_CAPABILITIES.items():
        solvers.append(
            SolverInfo(
                name=solver_name,
                available=solver_name in available_set,
                supports=capabilities,
            )
        )

    # Sort: available solvers first, then alphabetically
    solvers.sort(key=lambda s: (not s.available, s.name))

    return SolversListResponse(
        solvers=solvers,
        total=len(solvers),
    )


@router.get(
    "/solvers/{solver_name}",
    response_model=SolverInfo,
    summary="Get solver info",
    description="Get detailed information about a specific solver.",
    responses={
        200: {"description": "Solver information"},
        404: {"description": "Solver not found"},
    },
)
async def get_solver_info(solver_name: str) -> SolverInfo:
    """
    Get information about a specific solver.

    Returns the solver's availability and supported problem types.
    """
    from fastapi import HTTPException, status

    solver_name = solver_name.lower()
    capabilities = SOLVER_CAPABILITIES.get(solver_name)

    if capabilities is None:
        available_solvers = ", ".join(sorted(SOLVER_CAPABILITIES.keys()))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown solver '{solver_name}'. "
            f"Available solvers: {available_solvers}",
        )

    available = list_available_solvers()

    return SolverInfo(
        name=solver_name,
        available=solver_name in available,
        supports=capabilities,
    )
