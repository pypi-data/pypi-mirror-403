"""
Custom exceptions for PyOptima.
"""


class OptimizationError(Exception):
    """Base exception for optimization errors."""
    pass


class ConstraintError(OptimizationError):
    """Exception raised for constraint-related errors."""
    pass


class DataFormatError(OptimizationError):
    """Exception raised for data format issues."""
    pass


class SolverError(OptimizationError):
    """Exception raised for solver failures."""
    pass


class MethodNotFoundError(OptimizationError):
    """Exception raised when optimization method is not found."""
    pass


class ValidationError(OptimizationError):
    """Exception raised for input validation errors."""
    pass
