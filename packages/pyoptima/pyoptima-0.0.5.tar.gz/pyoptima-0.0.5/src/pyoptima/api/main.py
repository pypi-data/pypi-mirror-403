"""
PyOptima API - FastAPI Application

REST API for optimization operations using PyOptima.

Usage:
    # Development server
    uvicorn pyoptima.api.main:app --reload

    # Production server
    uvicorn pyoptima.api.main:app --host 0.0.0.0 --port 8000 --workers 4

    # With gunicorn
    gunicorn pyoptima.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pyoptima import __version__ as pyoptima_version, list_templates, list_available_solvers

from pyoptima.api.routes.v1 import jobs, optimize, solvers, templates

# API configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events.
    """
    # Startup: Initialize resources if needed
    # Pre-load templates registry
    _ = list_templates()
    yield
    # Shutdown: Cleanup resources if needed


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="PyOptima API",
        description="REST API for PyOptima optimization operations",
        version=pyoptima_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    import os
    # Get CORS origins from environment variable
    cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()] if cors_origins_env else []
    
    # Default behavior: In development (or when ENVIRONMENT not set), allow localhost origins
    # This makes development easier without requiring environment variables
    is_development = os.getenv("ENVIRONMENT") == "development"
    is_production = os.getenv("ENVIRONMENT") == "production"
    
    # If no explicit CORS origins set and not in production, allow localhost for development
    if not cors_origins and not is_production:
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]
    
    # Configure CORS middleware
    # Note: Can't use allow_credentials=True with allow_origins=["*"]
    # So we use specific origins for development, or "*" without credentials for production
    use_credentials = bool(cors_origins and "*" not in cors_origins)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],  # Fallback to "*" if explicitly empty
        allow_credentials=use_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Include routers from v1 with automatic /api/v1 prefix
    # All routers in routes/v1/ are automatically included with the /api/v1 prefix
    app.include_router(
        optimize.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Optimization"],
    )
    app.include_router(
        jobs.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Jobs"],
    )
    app.include_router(
        templates.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Templates"],
    )
    app.include_router(
        solvers.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Solvers"],
    )

    # Root endpoint
    @app.get(
        "/",
        summary="API Information",
        description="Get API information and version",
        tags=["General"],
    )
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": "PyOptima API",
            "version": pyoptima_version,
            "api_version": API_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
        }
    
    # Health check endpoint
    @app.get(
        "/health",
        summary="Health Check",
        description="Check API health status",
        tags=["General"],
    )
    async def health_check() -> dict:
        """Health check endpoint."""
        available_solvers = list_available_solvers()
        available_templates = list_templates()
        
        return {
            "status": "healthy",
            "version": pyoptima_version,
            "solvers_available": len(available_solvers),
            "templates_available": len(available_templates),
        }

    # Request validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        # Convert errors to JSON-serializable format
        def serialize_error(error: dict) -> dict:
            """Recursively serialize error dict, converting exceptions to strings."""
            serialized = {}
            for key, value in error.items():
                if isinstance(value, Exception):
                    serialized[key] = str(value)
                elif isinstance(value, dict):
                    serialized[key] = serialize_error(value)
                elif isinstance(value, (list, tuple)):
                    serialized[key] = [
                        serialize_error(item) if isinstance(item, dict) else str(item) if isinstance(item, Exception) else item
                        for item in value
                    ]
                else:
                    serialized[key] = value
            return serialized
        
        errors = [serialize_error(err) for err in exc.errors()]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": errors,
            },
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler for unhandled errors."""
        import logging
        import os
        
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # In production, don't expose internal error details
        is_development = os.getenv("ENVIRONMENT") == "development"
        
        error_detail = {
            "error": "Internal server error",
        }
        
        if is_development:
            error_detail.update({
                "message": str(exc),
                "type": type(exc).__name__,
            })
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_detail,
        )
    
    # Override openapi() method to handle schema generation errors gracefully
    # This is a workaround for a Pydantic v2 issue with unhashable types in schema generation
    original_openapi = app.openapi
    
    def openapi_with_error_handling():
        """OpenAPI schema with error handling for unhashable types."""
        try:
            return original_openapi()
        except TypeError as e:
            if "unhashable type" in str(e):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"OpenAPI schema generation encountered an issue: {e}. "
                    "Returning minimal schema."
                )
                # Return a minimal valid OpenAPI schema as fallback
                return {
                    "openapi": "3.1.0",
                    "info": {
                        "title": app.title,
                        "version": app.version,
                        "description": app.description,
                    },
                    "paths": {},
                    "components": {"schemas": {}},
                }
            raise
    
    app.openapi = openapi_with_error_handling

    return app


# Create application instance
app = create_application()


def main():
    """Main entry point for running the API server."""
    import uvicorn
    
    uvicorn.run(
        "pyoptima.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
    )


if __name__ == "__main__":
    main()
