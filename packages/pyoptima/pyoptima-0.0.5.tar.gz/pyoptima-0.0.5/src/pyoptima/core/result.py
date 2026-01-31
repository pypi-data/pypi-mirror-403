"""
Optimization result classes with IO methods.

Provides a standardized result format with pandas-style export methods.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class SolverStatus(Enum):
    """Solver termination status."""
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    TIME_LIMIT = "time_limit"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class OptimizationResult:
    """
    Standardized optimization result with IO methods.
    
    Provides pandas-style methods for exporting results:
    - to_dict(): Export as dictionary
    - to_dataframe(): Export as pandas DataFrame
    - to_json(): Export as JSON string
    - to_sql(): Write to SQL database
    
    Example:
        >>> result = optimizer.solve(data)
        >>> print(result.status)
        SolverStatus.OPTIMAL
        >>> df = result.to_dataframe()
        >>> result.to_json("result.json")
    """
    
    # Core result fields
    status: SolverStatus
    objective_value: Optional[float] = None
    solution: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    solve_time: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Solver info
    solver_name: Optional[str] = None
    solver_message: Optional[str] = None
    gap: Optional[float] = None  # MIP gap
    
    # Problem info
    problem_type: Optional[str] = None
    num_variables: Optional[int] = None
    num_constraints: Optional[int] = None
    
    # Domain-specific results (e.g., portfolio)
    weights: Optional[Dict[str, float]] = None
    portfolio_return: Optional[float] = None
    portfolio_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    
    # Extra metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_optimal(self) -> bool:
        """Check if solution is optimal."""
        return self.status == SolverStatus.OPTIMAL
    
    @property
    def is_feasible(self) -> bool:
        """Check if solution is feasible (optimal or feasible)."""
        return self.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    
    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Export result as dictionary.
        
        Args:
            include_metadata: Whether to include metadata field
            
        Returns:
            Dictionary representation of the result
        """
        result = {
            "status": self.status.value,
            "objective_value": self.objective_value,
            "solution": self.solution,
            "solve_time": self.solve_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "solver_name": self.solver_name,
            "solver_message": self.solver_message,
        }
        
        # Add optional fields if present
        if self.gap is not None:
            result["gap"] = self.gap
        if self.problem_type:
            result["problem_type"] = self.problem_type
        if self.num_variables is not None:
            result["num_variables"] = self.num_variables
        if self.num_constraints is not None:
            result["num_constraints"] = self.num_constraints
        
        # Add domain-specific fields
        if self.weights is not None:
            result["weights"] = self.weights
        if self.portfolio_return is not None:
            result["portfolio_return"] = self.portfolio_return
        if self.portfolio_volatility is not None:
            result["portfolio_volatility"] = self.portfolio_volatility
        if self.sharpe_ratio is not None:
            result["sharpe_ratio"] = self.sharpe_ratio
        
        if include_metadata and self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    def to_dataframe(self, orient: str = "index") -> "pd.DataFrame":
        """
        Export result as pandas DataFrame.
        
        Args:
            orient: DataFrame orientation ("index" or "columns")
            
        Returns:
            pandas DataFrame
            
        Raises:
            ImportError: If pandas is not installed
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for to_dataframe(). Install with: pip install pandas")
        
        data = self.to_dict(include_metadata=False)
        
        if orient == "index":
            # Each field as a row
            return pd.DataFrame.from_dict(data, orient="index", columns=["value"])
        else:
            # Single row with fields as columns
            return pd.DataFrame([data])
    
    def weights_to_dataframe(self) -> "pd.DataFrame":
        """
        Export portfolio weights as DataFrame.
        
        Returns:
            DataFrame with columns [symbol, weight]
            
        Raises:
            ImportError: If pandas is not installed
            ValueError: If no weights available
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for weights_to_dataframe(). Install with: pip install pandas")
        
        if self.weights is None:
            raise ValueError("No weights available in result")
        
        return pd.DataFrame([
            {"symbol": k, "weight": v}
            for k, v in self.weights.items()
        ]).sort_values("weight", ascending=False).reset_index(drop=True)
    
    def to_json(self, path: Optional[str] = None, indent: int = 2) -> str:
        """
        Export result as JSON.
        
        Args:
            path: Optional file path to write to
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        import json
        
        data = self.to_dict()
        json_str = json.dumps(data, indent=indent, default=str)
        
        if path:
            with open(path, "w") as f:
                f.write(json_str)
        
        return json_str
    
    def to_sql(
        self,
        table: str,
        connection: Any,
        schema: Optional[str] = None,
        if_exists: str = "append",
    ) -> None:
        """
        Write result to SQL database.
        
        Args:
            table: Table name
            connection: SQLAlchemy connection or engine
            schema: Database schema
            if_exists: How to handle existing table ("append", "replace", "fail")
            
        Raises:
            ImportError: If pandas is not installed
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for to_sql(). Install with: pip install pandas")
        
        df = self.to_dataframe(orient="columns")
        df.to_sql(table, connection, schema=schema, if_exists=if_exists, index=False)
    
    def __repr__(self) -> str:
        parts = [f"OptimizationResult(status={self.status.value}"]
        if self.objective_value is not None:
            parts.append(f", objective={self.objective_value:.6f}")
        if self.solve_time is not None:
            parts.append(f", time={self.solve_time:.3f}s")
        parts.append(")")
        return "".join(parts)
