"""
Optimization configuration (Pydantic v2).

Unified config format: template + data + solver.
Portfolio: template="portfolio", data includes objective, expected_returns, covariance_matrix.
"""

from pathlib import Path
from typing import Any, Dict, Union

from pydantic import BaseModel, ConfigDict, Field


class SolverConfig(BaseModel):
    """Solver configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="highs", description="Solver name")
    time_limit: float | None = Field(None, description="Time limit in seconds")
    verbose: bool = Field(default=False, description="Print solver output")
    options: Dict[str, Any] = Field(default_factory=dict, description="Solver-specific options")


class OptimizationConfig(BaseModel):
    """
    Configuration for an optimization problem.

    Schema: template, data, solver. For portfolio, data must include
    objective, expected_returns, covariance_matrix (and optionally symbols).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "template": "portfolio",
                    "data": {
                        "objective": "min_volatility",
                        "expected_returns": [0.12, 0.10, 0.08],
                        "covariance_matrix": [[0.04, 0.01, 0.02], [0.01, 0.03, 0.015], [0.02, 0.015, 0.025]],
                        "symbols": ["AAPL", "GOOGL", "MSFT"],
                    },
                    "solver": {"name": "ipopt"},
                },
            ]
        },
    )

    template: str = Field(..., description="Template: portfolio, lp, knapsack, etc.")
    data: Dict[str, Any] = Field(..., description="Problem data (template-specific)")
    solver: SolverConfig = Field(default_factory=SolverConfig, description="Solver config")
    job_id: str | None = Field(None, description="Optional job id")


def load_config(config_dict: Dict[str, Any]) -> OptimizationConfig:
    """Load configuration from a dictionary."""
    return OptimizationConfig(**config_dict)


def load_config_file(path: str | Path) -> OptimizationConfig:
    """
    Load configuration from a JSON or YAML file.

    Args:
        path: Path to .json, .yaml, or .yml file.

    Returns:
        OptimizationConfig
    """
    import json

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(p.read_text())
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as e:
            raise ImportError("PyYAML required for YAML: pip install pyyaml") from e
        data = yaml.safe_load(p.read_text())
    else:
        raise ValueError(f"Unsupported format: {suffix}. Use .json, .yaml, or .yml")

    return load_config(data)


def run_from_config(config: OptimizationConfig | Dict[str, Any] | str | Path) -> Dict[str, Any]:
    """
    Run optimization from configuration.
    
    Args:
        config: OptimizationConfig, dict, or path to config file
    
    Returns:
        Solution dictionary
    """
    from pyoptima.templates import solve

    if isinstance(config, (str, Path)):
        config = load_config_file(config)
    elif isinstance(config, dict):
        config = load_config(config)

    solver_options = config.solver.options.copy()
    if config.solver.time_limit:
        solver_options["time_limit"] = config.solver.time_limit
    solver_options["verbose"] = config.solver.verbose
    
    return solve(
        config.template,
        config.data,
        solver=config.solver.name,
        **solver_options
    )
