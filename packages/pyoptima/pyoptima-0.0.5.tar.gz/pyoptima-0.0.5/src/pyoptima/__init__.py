"""
PyOptima - Portfolio optimization with sklearn-style and config-driven APIs.

Quick Start:
    from pyoptima import PortfolioOptimizer, WeightBounds, SumToOne

    opt = PortfolioOptimizer(
        objective="min_volatility",
        constraints=[WeightBounds(0, 0.4), SumToOne()],
    )
    result = opt.solve(
        expected_returns=[0.1, 0.12, 0.08],
        covariance_matrix=[[0.04, 0.01, 0.02], ...],
        symbols=["AAPL", "GOOGL", "MSFT"],
    )
    print(result.weights)
    df = result.weights_to_dataframe()

Config-driven:
    opt = PortfolioOptimizer.from_config("config.yaml")
    result = opt.solve()

Templates (solve, get_template, list_templates) and model building
(Problem, AbstractModel, get_solver) are available for other problem types.
"""

try:
    from importlib.metadata import version
    __version__ = version("pyoptima")
except Exception:
    __version__ = "0.2.0"

# Core types (single result type: core.result.OptimizationResult)
from pyoptima.core.result import OptimizationResult, SolverStatus
from pyoptima.core.protocols import Objective as ObjectiveProtocol, Constraint as ConstraintProtocol, ConstraintSet
from pyoptima.core.problem import Problem, Minimize, Maximize
Result = OptimizationResult  # alias

# Estimators
from pyoptima.estimators import BaseOptimizer, clone, PortfolioOptimizer

# Constraints (composable)
from pyoptima.constraints import (
    BaseConstraint,
    WeightBounds,
    PerAssetBounds,
    LongOnly,
    LongShort,
    GrossExposure,
    MaxAssets,
    MinAssets,
    MinPositionSize,
    SectorCaps,
    SectorMins,
    SectorConstraints,
    FactorExposureLimits,
    MaxTurnover,
    TransactionCosts,
    MaxVolatility,
    MaxCVaR,
    MaxDrawdown,
    MaxConcentration,
    TrackingErrorLimit,
    SumToOne,
    MinReturn,
    MaxReturn,
    ExclusionList,
    InclusionList,
    LinearInequality,
)

# Objectives
from pyoptima.objectives import (
    BaseObjective,
    MinVolatility,
    MaxSharpe,
    MaxReturn as MaxReturnObjective,
    EfficientReturn,
    EfficientRisk,
    MaxUtility,
    MinCVaR,
    MinCDaR,
    MinSemivariance,
    RiskParity,
    MaxDiversification,
)

# IO (pandas-style)
from pyoptima.io import (
    read_portfolio_csv,
    read_portfolio_json,
    read_portfolio_sql,
    read_portfolio_excel,
    PortfolioData,
)

# ETL
from pyoptima.etl import (
    optimize_batch,
    optimize_single,
    ETLInputAdapter,
    ETLOutputFormatter,
    SUPPORTED_OBJECTIVES,
    validate_inputs,
)

from pyoptima.templates import solve, get_template, list_templates
from pyoptima.config import (
    OptimizationConfig,
    load_config,
    load_config_file,
    run_from_config,
)

# Model (templates/solvers)
from pyoptima.model import (
    AbstractModel,
    Variable,
    VariableType,
    Expression,
    Constraint,
    Objective,
)

# Solver interface
from pyoptima.solvers import (
    get_solver,
    list_available_solvers,
    SolverInterface,
    SolverOptions,
)

# Expression
from pyoptima.expression import (
    parse_expression,
    evaluate_expression,
)

from pyoptima.templates import ProblemTemplate, TemplateRegistry, PortfolioTemplate

# Exceptions
from pyoptima.exceptions import (
    OptimizationError,
    SolverError,
    ValidationError,
)


__all__ = [
    # Core
    "Result",
    "OptimizationResult",
    "SolverStatus",
    "ObjectiveProtocol",
    "ConstraintProtocol",
    "ConstraintSet",
    "Problem",
    "Minimize",
    "Maximize",
    # Estimators
    "BaseOptimizer",
    "clone",
    "PortfolioOptimizer",
    # Constraints
    "BaseConstraint",
    "WeightBounds",
    "PerAssetBounds",
    "LongOnly",
    "LongShort",
    "GrossExposure",
    "MaxAssets",
    "MinAssets",
    "MinPositionSize",
    "SectorCaps",
    "SectorMins",
    "SectorConstraints",
    "FactorExposureLimits",
    "MaxTurnover",
    "TransactionCosts",
    "MaxVolatility",
    "MaxCVaR",
    "MaxDrawdown",
    "MaxConcentration",
    "TrackingErrorLimit",
    "SumToOne",
    "MinReturn",
    "MaxReturn",
    "ExclusionList",
    "InclusionList",
    "LinearInequality",
    # Objectives
    "BaseObjective",
    "MinVolatility",
    "MaxSharpe",
    "MaxReturnObjective",
    "EfficientReturn",
    "EfficientRisk",
    "MaxUtility",
    "MinCVaR",
    "MinCDaR",
    "MinSemivariance",
    "RiskParity",
    "MaxDiversification",
    # IO
    "read_portfolio_csv",
    "read_portfolio_json",
    "read_portfolio_sql",
    "read_portfolio_excel",
    "PortfolioData",
    # ETL Integration
    "optimize_batch",
    "optimize_single",
    "ETLInputAdapter",
    "ETLOutputFormatter",
    "SUPPORTED_OBJECTIVES",
    "validate_inputs",
    "solve",
    "get_template",
    "list_templates",
    "OptimizationConfig",
    "load_config",
    "load_config_file",
    "run_from_config",
    # Model (advanced)
    "AbstractModel",
    "Variable",
    "VariableType",
    "Expression",
    "Constraint",
    "Objective",
    # Solvers
    "get_solver",
    "list_available_solvers",
    "SolverInterface",
    "SolverOptions",
    # Expression
    "parse_expression",
    "evaluate_expression",
    # Templates
    "ProblemTemplate",
    "TemplateRegistry",
    "PortfolioTemplate",
    # Exceptions
    "OptimizationError",
    "SolverError",
    "ValidationError",
]
