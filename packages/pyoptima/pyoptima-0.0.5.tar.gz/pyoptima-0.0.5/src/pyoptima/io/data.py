"""
Data classes for optimization problems.

Provides structured data containers with validation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


@dataclass
class PortfolioData:
    """
    Container for portfolio optimization data.
    
    Provides a structured way to pass data to portfolio optimizers
    with validation and conversion methods.
    
    Example:
        >>> data = PortfolioData(
        ...     expected_returns=[0.1, 0.12, 0.08],
        ...     covariance_matrix=[[0.04, 0.01, 0.02], ...],
        ...     symbols=["AAPL", "GOOGL", "MSFT"]
        ... )
        >>> 
        >>> # Or from DataFrame
        >>> data = PortfolioData.from_returns(returns_df)
    """
    
    expected_returns: Union[List[float], "np.ndarray", "pd.Series"]
    covariance_matrix: Union[List[List[float]], "np.ndarray", "pd.DataFrame"]
    symbols: Optional[List[str]] = None
    
    # Optional historical returns for CVaR/CDaR/Semivariance
    returns: Optional[Union[List[List[float]], "np.ndarray", "pd.DataFrame"]] = None
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        self._validate()
        self._normalize()
    
    def _validate(self) -> None:
        """Validate data consistency."""
        n_expected = len(self.expected_returns) if hasattr(self.expected_returns, "__len__") else 0
        
        # Check covariance matrix shape
        cov = self.covariance_matrix
        if hasattr(cov, "shape"):
            n_cov = cov.shape[0]
        elif hasattr(cov, "__len__"):
            n_cov = len(cov)
        else:
            n_cov = 0
        
        if n_expected != n_cov:
            raise ValueError(
                f"Dimension mismatch: expected_returns has {n_expected} elements, "
                f"but covariance_matrix has {n_cov} rows"
            )
        
        # Check symbols if provided
        if self.symbols is not None and len(self.symbols) != n_expected:
            raise ValueError(
                f"Dimension mismatch: symbols has {len(self.symbols)} elements, "
                f"but expected_returns has {n_expected}"
            )
    
    def _normalize(self) -> None:
        """Convert data to numpy arrays if available."""
        if not HAS_NUMPY:
            return
        
        # Convert expected returns
        if not isinstance(self.expected_returns, np.ndarray):
            if HAS_PANDAS and isinstance(self.expected_returns, pd.Series):
                if self.symbols is None:
                    self.symbols = list(self.expected_returns.index)
                self.expected_returns = self.expected_returns.values
            else:
                self.expected_returns = np.array(self.expected_returns)
        
        # Convert covariance matrix
        if not isinstance(self.covariance_matrix, np.ndarray):
            if HAS_PANDAS and isinstance(self.covariance_matrix, pd.DataFrame):
                if self.symbols is None:
                    self.symbols = list(self.covariance_matrix.index)
                self.covariance_matrix = self.covariance_matrix.values
            else:
                self.covariance_matrix = np.array(self.covariance_matrix)
        
        # Convert returns if present
        if self.returns is not None and not isinstance(self.returns, np.ndarray):
            if HAS_PANDAS and isinstance(self.returns, pd.DataFrame):
                self.returns = self.returns.values
            else:
                self.returns = np.array(self.returns)
    
    @property
    def n_assets(self) -> int:
        """Number of assets."""
        return len(self.expected_returns)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for optimizer input.
        
        Returns:
            Dictionary with all data fields
        """
        result = {
            "expected_returns": self.expected_returns,
            "covariance_matrix": self.covariance_matrix,
        }
        
        if self.symbols is not None:
            result["symbols"] = self.symbols
        
        if self.returns is not None:
            result["returns"] = self.returns
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_returns(
        cls,
        returns: Union["pd.DataFrame", "np.ndarray"],
        frequency: int = 252,
        method: str = "mean",
        cov_method: str = "sample",
    ) -> "PortfolioData":
        """
        Create PortfolioData from historical returns.
        
        Args:
            returns: Historical returns (rows=dates, columns=assets)
            frequency: Annualization factor (252 for daily, 12 for monthly)
            method: Expected returns method ("mean", "ewma", "capm")
            cov_method: Covariance method ("sample", "shrinkage", "ledoit_wolf")
            
        Returns:
            PortfolioData instance
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required for from_returns()")
        
        if HAS_PANDAS and isinstance(returns, pd.DataFrame):
            symbols = list(returns.columns)
            returns_array = returns.values
        else:
            symbols = None
            returns_array = np.array(returns)
        
        # Calculate expected returns
        if method == "mean":
            expected_returns = np.mean(returns_array, axis=0) * frequency
        elif method == "ewma":
            # Exponentially weighted moving average
            span = min(len(returns_array), 60)
            weights = np.exp(np.linspace(0, 1, len(returns_array)))
            weights /= weights.sum()
            expected_returns = np.average(returns_array, axis=0, weights=weights) * frequency
        else:
            expected_returns = np.mean(returns_array, axis=0) * frequency
        
        # Calculate covariance matrix
        if cov_method == "sample":
            covariance_matrix = np.cov(returns_array.T) * frequency
        elif cov_method == "shrinkage":
            # Simple shrinkage toward diagonal
            sample_cov = np.cov(returns_array.T) * frequency
            n = sample_cov.shape[0]
            shrinkage = 0.1
            target = np.diag(np.diag(sample_cov))
            covariance_matrix = (1 - shrinkage) * sample_cov + shrinkage * target
        else:
            covariance_matrix = np.cov(returns_array.T) * frequency
        
        return cls(
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            symbols=symbols,
            returns=returns_array,
            metadata={
                "frequency": frequency,
                "expected_returns_method": method,
                "covariance_method": cov_method,
            }
        )
