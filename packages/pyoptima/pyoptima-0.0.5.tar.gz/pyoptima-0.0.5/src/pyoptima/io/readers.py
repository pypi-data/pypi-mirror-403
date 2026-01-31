"""
Data readers for portfolio optimization.

pandas-style functions for reading portfolio data from various sources.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pyoptima.io.data import PortfolioData

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


def read_portfolio_json(
    path_or_dict: Union[str, Path, Dict[str, Any]],
    expected_returns_key: str = "expected_returns",
    covariance_key: str = "covariance_matrix",
    symbols_key: str = "symbols",
    returns_key: str = "returns",
) -> PortfolioData:
    """
    Read portfolio data from JSON file or dictionary.
    
    Args:
        path_or_dict: Path to JSON file or dictionary
        expected_returns_key: Key for expected returns in JSON
        covariance_key: Key for covariance matrix in JSON
        symbols_key: Key for symbols in JSON
        returns_key: Key for historical returns in JSON
        
    Returns:
        PortfolioData instance
        
    Example:
        >>> data = read_portfolio_json("portfolio.json")
        >>> data = read_portfolio_json({
        ...     "expected_returns": [0.1, 0.12],
        ...     "covariance_matrix": [[0.04, 0.01], [0.01, 0.05]]
        ... })
    """
    if isinstance(path_or_dict, (str, Path)):
        with open(path_or_dict, "r") as f:
            data = json.load(f)
    else:
        data = path_or_dict
    
    # Handle nested structure (e.g., {"data": {...}})
    if "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    
    expected_returns = data.get(expected_returns_key)
    covariance_matrix = data.get(covariance_key)
    
    if expected_returns is None:
        raise ValueError(f"Missing required field: {expected_returns_key}")
    if covariance_matrix is None:
        raise ValueError(f"Missing required field: {covariance_key}")
    
    # Handle covariance matrix nested format
    if isinstance(covariance_matrix, dict):
        if "matrix" in covariance_matrix:
            covariance_matrix = covariance_matrix["matrix"]
    
    symbols = data.get(symbols_key)
    returns = data.get(returns_key)
    
    # Collect remaining fields as metadata
    metadata = {k: v for k, v in data.items() 
                if k not in {expected_returns_key, covariance_key, symbols_key, returns_key}}
    
    return PortfolioData(
        expected_returns=expected_returns,
        covariance_matrix=covariance_matrix,
        symbols=symbols,
        returns=returns,
        metadata=metadata,
    )


def read_portfolio_csv(
    prices_path: Union[str, Path],
    frequency: int = 252,
    method: str = "mean",
    cov_method: str = "sample",
    **read_csv_kwargs,
) -> PortfolioData:
    """
    Read portfolio data from CSV of historical prices.
    
    Calculates returns, expected returns, and covariance from prices.
    
    Args:
        prices_path: Path to CSV file with prices (columns=assets, rows=dates)
        frequency: Annualization factor (252 for daily, 12 for monthly)
        method: Expected returns method ("mean", "ewma")
        cov_method: Covariance method ("sample", "shrinkage")
        **read_csv_kwargs: Additional arguments for pandas.read_csv
        
    Returns:
        PortfolioData instance
        
    Example:
        >>> data = read_portfolio_csv("prices.csv", index_col=0, parse_dates=True)
    """
    if not HAS_PANDAS:
        raise ImportError("pandas is required for read_portfolio_csv(). Install with: pip install pandas")
    
    # Read prices
    prices = pd.read_csv(prices_path, **read_csv_kwargs)
    
    # Calculate returns
    returns = prices.pct_change().dropna()
    
    return PortfolioData.from_returns(
        returns=returns,
        frequency=frequency,
        method=method,
        cov_method=cov_method,
    )


def read_portfolio_sql(
    connection: Any,
    query: str,
    expected_returns_col: Optional[str] = None,
    covariance_query: Optional[str] = None,
    frequency: int = 252,
    method: str = "mean",
    cov_method: str = "sample",
) -> PortfolioData:
    """
    Read portfolio data from SQL database.
    
    Can either:
    1. Read pre-calculated expected returns and covariance
    2. Read historical returns and calculate stats
    
    Args:
        connection: SQLAlchemy connection or engine
        query: SQL query for returns data
        expected_returns_col: Column name for expected returns (if pre-calculated)
        covariance_query: Separate query for covariance matrix
        frequency: Annualization factor for calculations
        method: Expected returns calculation method
        cov_method: Covariance calculation method
        
    Returns:
        PortfolioData instance
    """
    if not HAS_PANDAS:
        raise ImportError("pandas is required for read_portfolio_sql()")
    
    # Read returns data
    returns = pd.read_sql(query, connection)
    
    return PortfolioData.from_returns(
        returns=returns,
        frequency=frequency,
        method=method,
        cov_method=cov_method,
    )


def read_portfolio_excel(
    path: Union[str, Path],
    sheet_name: Union[str, int] = 0,
    frequency: int = 252,
    method: str = "mean",
    cov_method: str = "sample",
    **read_excel_kwargs,
) -> PortfolioData:
    """
    Read portfolio data from Excel file.
    
    Args:
        path: Path to Excel file
        sheet_name: Sheet name or index
        frequency: Annualization factor
        method: Expected returns method
        cov_method: Covariance method
        **read_excel_kwargs: Additional arguments for pandas.read_excel
        
    Returns:
        PortfolioData instance
    """
    if not HAS_PANDAS:
        raise ImportError("pandas is required for read_portfolio_excel()")
    
    prices = pd.read_excel(path, sheet_name=sheet_name, **read_excel_kwargs)
    returns = prices.pct_change().dropna()
    
    return PortfolioData.from_returns(
        returns=returns,
        frequency=frequency,
        method=method,
        cov_method=cov_method,
    )
