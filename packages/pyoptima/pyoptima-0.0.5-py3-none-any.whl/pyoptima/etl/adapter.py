"""
ETL Input Adapter.

Normalizes various input formats to pyoptima's expected format.
Supports formats from pycharter ETL pipelines and direct API calls.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class ETLInputAdapter:
    """
    Adapter for normalizing ETL pipeline inputs to pyoptima format.
    
    Handles various input formats:
    - ETL consolidated format (nested covariance with matrix/symbols)
    - Flat dicts
    - NumPy arrays
    - Pandas DataFrames/Series
    """
    
    @classmethod
    def normalize(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize an input record to pyoptima's expected format.
        
        Args:
            record: Input record from ETL pipeline or API.
            
        Returns:
            Normalized dict with expected_returns, covariance_matrix, symbols, etc.
        """
        normalized = {}
        
        # Extract symbols first (needed for matrix conversions)
        symbols = cls._extract_symbols(record)
        if symbols:
            normalized["symbols"] = symbols
        
        # Normalize expected returns
        if "expected_returns" in record:
            normalized["expected_returns"] = cls._normalize_expected_returns(
                record["expected_returns"], symbols
            )
        
        # Normalize covariance matrix
        if "covariance_matrix" in record:
            normalized["covariance_matrix"] = cls._normalize_covariance(
                record["covariance_matrix"], symbols
            )
        
        # Normalize returns matrix (for CVaR, CDaR, Semivariance, Momentum)
        if "returns" in record:
            normalized["returns"] = cls._normalize_returns(record["returns"])
        
        # Copy through other fields directly
        passthrough_fields = [
            "job_id", "objective", "solver",
            # Target parameters
            "target_return", "target_volatility", "target_cvar", 
            "target_cdar", "target_semivariance",
            # Risk parameters
            "risk_free_rate", "risk_aversion", "confidence_level",
            # Bounds
            "min_weight", "max_weight", "weight_bounds", "per_asset_bounds",
            # Cardinality
            "max_assets", "min_position_size",
            # Turnover
            "current_weights", "max_turnover", "transaction_costs",
            # Sector constraints
            "sector_caps", "sector_mins", "asset_sectors",
            # Black-Litterman
            "market_caps", "views", "view_cov", "tau",
            # Momentum
            "momentum_period", "momentum_top_pct",
            # Factor
            "factor_data", "factor_weights", "max_volatility",
            # Other
            "benchmark", "min_net_return",
        ]
        
        for field in passthrough_fields:
            if field in record and record[field] is not None:
                normalized[field] = record[field]
        
        return normalized
    
    @classmethod
    def _extract_symbols(cls, record: Dict[str, Any]) -> Optional[List[str]]:
        """Extract symbols from various locations in the record."""
        # Direct symbols field
        if "symbols" in record and record["symbols"]:
            return list(record["symbols"])
        
        # From covariance_matrix nested format
        cov = record.get("covariance_matrix")
        if isinstance(cov, dict) and "symbols" in cov:
            return list(cov["symbols"])
        
        # From expected_returns dict keys
        er = record.get("expected_returns")
        if isinstance(er, dict) and not any(k in er for k in ["values", "symbols"]):
            return list(er.keys())
        
        # From expected_returns nested format
        if isinstance(er, dict) and "symbols" in er:
            return list(er["symbols"])
        
        return None
    
    @classmethod
    def _normalize_expected_returns(
        cls, 
        data: Any, 
        symbols: Optional[List[str]] = None
    ) -> List[float]:
        """
        Normalize expected returns to list format (numpy-compatible).
        
        PortfolioTemplate's _to_numpy() doesn't handle dicts well,
        so we convert to list format with symbols preserved separately.
        
        Supported formats:
        - Dict[str, float]: {"AAPL": 0.12, "MSFT": 0.11}
        - Nested dict: {"values": [...], "symbols": [...]}
        - List[float]: [0.12, 0.11]
        - np.ndarray
        - pd.Series
        """
        # Nested dict format
        if isinstance(data, dict) and any(k in data for k in ["values", "expected_returns"]):
            values = data.get("values") or data.get("expected_returns")
            return list(values) if isinstance(values, (list, np.ndarray)) else values
        
        # Flat dict - convert to list in symbols order
        if isinstance(data, dict):
            if symbols:
                # Order by symbols
                return [data[s] for s in symbols if s in data]
            else:
                # Just return values in dict order
                return list(data.values())
        
        # Pandas Series
        if HAS_PANDAS and isinstance(data, pd.Series):
            return data.tolist()
        
        # NumPy array
        if isinstance(data, np.ndarray):
            return data.tolist()
        
        # Already a list
        if isinstance(data, list):
            return data
        
        return data
    
    @classmethod
    def _normalize_covariance(
        cls, 
        data: Any, 
        symbols: Optional[List[str]] = None
    ) -> Union[List[List[float]], Dict[str, Dict[str, float]]]:
        """
        Normalize covariance matrix to list-of-lists or dict-of-dicts format.
        
        Supported formats:
        - List[List[float]]: [[0.04, 0.01], [0.01, 0.05]]
        - Nested dict: {"matrix": [[...]], "symbols": [...]}
        - Dict[str, Dict[str, float]]: {"AAPL": {"AAPL": 0.04, ...}}
        - np.ndarray
        - pd.DataFrame
        """
        # Nested dict format (ETL consolidated)
        if isinstance(data, dict) and "matrix" in data:
            matrix = data["matrix"]
            syms = data.get("symbols") or symbols
            if syms and isinstance(matrix, (list, np.ndarray)):
                # Return as list-of-lists for pyoptima
                return [list(row) for row in matrix]
            return matrix
        
        # Dict-of-dicts format
        if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
            return data
        
        # Pandas DataFrame
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            return data.values.tolist()
        
        # NumPy array
        if isinstance(data, np.ndarray):
            return data.tolist()
        
        # Already list-of-lists
        if isinstance(data, list):
            return data
        
        return data
    
    @classmethod
    def _normalize_returns(cls, data: Any) -> List[List[float]]:
        """
        Normalize returns matrix to list-of-lists format.
        
        Args:
            data: Returns data (T x N matrix of historical returns).
            
        Returns:
            List of lists format.
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            return data.values.tolist()
        
        if isinstance(data, np.ndarray):
            return data.tolist()
        
        return data
    
    @classmethod
    def validate(cls, record: Dict[str, Any]) -> List[str]:
        """
        Validate an input record and return list of issues.
        
        Args:
            record: Normalized input record.
            
        Returns:
            List of validation error messages (empty if valid).
        """
        issues = []
        
        if "expected_returns" not in record:
            issues.append("Missing required field: expected_returns")
        
        if "covariance_matrix" not in record:
            issues.append("Missing required field: covariance_matrix")
        
        # Check dimensions match
        er = record.get("expected_returns")
        cov = record.get("covariance_matrix")
        
        if er and cov:
            n_assets = len(er) if isinstance(er, (list, dict)) else 0
            if isinstance(cov, list) and len(cov) > 0:
                n_cov = len(cov)
                if n_cov != n_assets:
                    issues.append(
                        f"Dimension mismatch: expected_returns has {n_assets} assets, "
                        f"covariance_matrix has {n_cov} rows"
                    )
        
        return issues
