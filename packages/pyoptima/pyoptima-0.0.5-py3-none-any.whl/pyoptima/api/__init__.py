"""
PyOptima API Package

REST API for optimization operations using PyOptima.

Usage:
    # Run development server
    uvicorn pyoptima.api.main:app --reload

    # Access documentation
    http://localhost:8000/docs        # Swagger UI
    http://localhost:8000/redoc       # ReDoc
"""

from pyoptima.api.main import app, create_application

__all__ = ["app", "create_application"]
