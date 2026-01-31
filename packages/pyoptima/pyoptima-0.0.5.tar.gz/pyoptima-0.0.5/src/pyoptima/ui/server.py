"""
Standalone UI server for PyOptima.

Serves the built Next.js static files and proxies API requests to the PyOptima API.
Supports both installed package (pre-built static files) and development mode.
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import httpx
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    httpx = None
    FastAPI = None
    Request = None
    Response = None
    FileResponse = None
    StaticFiles = None
    uvicorn = None


def find_ui_static_files() -> Optional[Path]:
    """
    Find UI static files in multiple locations (package, source, etc.).
    
    Priority:
    1. Installed package location (pyoptima/ui/static/)
    2. Source location (ui/static/)
    3. Next.js out directory (ui/out/)
    
    Returns:
        Path to static directory if found, None otherwise
    """
    # Try to find static files in installed package (src layout: __file__ parent is package dir)
    try:
        import pyoptima
        pyoptima_path = Path(pyoptima.__file__).parent
        package_static = pyoptima_path / "ui" / "static"
        if package_static.exists() and (package_static / "index.html").exists():
            return package_static
    except (ImportError, AttributeError):
        pass
    
    # Try source locations (development; __file__ is pyoptima/ui/server.py)
    possible_paths = [
        Path(__file__).parent / "static",  # pyoptima/ui/static/
        Path(__file__).parent / "out",  # pyoptima/ui/out/ (Next.js export)
        Path.cwd() / "src" / "pyoptima" / "ui" / "static",
        Path.cwd() / "ui" / "static",
    ]
    
    for static_path in possible_paths:
        if static_path.exists() and (static_path / "index.html").exists():
            return static_path
    
    return None


def get_static_dir() -> Path:
    """Get the directory containing built static files."""
    static_dir = find_ui_static_files()
    
    if static_dir:
        return static_dir
    
    # Provide helpful error message
    raise FileNotFoundError(
        "No built UI found.\n\n"
        "If you installed from pip:\n"
        "  The UI static files should be included in the package.\n"
        "  If they're missing, please report this issue.\n\n"
        "If you're in development:\n"
        "  1. Build the UI: pyoptima ui build\n"
        "  2. Or run in dev mode: pyoptima ui dev\n\n"
        "Expected locations:\n"
        "  - Installed package: <site-packages>/ui/static/\n"
        "  - Source: ui/static/ or ui/out/"
    )


def create_app(api_url: str) -> "FastAPI":
    """Create FastAPI app for serving UI and proxying API requests."""
    if FastAPI is None:
        raise ImportError("FastAPI is required. Install with: pip install pyoptima[api]")
    
    app = FastAPI(title="PyOptima UI")
    
    static_dir = get_static_dir()
    
    # Mount _next static files (must be before catch-all route)
    _next_dir = static_dir / "_next"
    if _next_dir.exists():
        _next_dir_abs = _next_dir.resolve()
        app.mount("/_next", StaticFiles(directory=str(_next_dir_abs), html=False), name="next")
    
    # Mount other static assets if they exist
    static_assets_dir = static_dir / "static"
    if static_assets_dir.exists() and static_assets_dir != _next_dir:
        app.mount("/static", StaticFiles(directory=str(static_assets_dir), html=False), name="static")
    
    # Proxy API requests
    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def proxy_api(request: Request, path: str):
        """Proxy API requests to the PyOptima API."""
        url = f"{api_url.rstrip('/')}/api/{path}"
        
        if request.url.query:
            url = f"{url}?{request.url.query}"
        
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("connection", None)
        headers.pop("content-length", None)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    content=body,
                    timeout=30.0,
                )
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type"),
                )
            except httpx.RequestError as e:
                return Response(
                    content=f"API request failed: {str(e)}",
                    status_code=502,
                    media_type="text/plain",
                )
    
    # Also proxy /health endpoint
    @app.get("/health")
    async def proxy_health(request: Request):
        """Proxy health check to API."""
        url = f"{api_url.rstrip('/')}/health"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=5.0)
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    media_type="application/json",
                )
            except httpx.RequestError:
                return Response(
                    content='{"status": "api_unavailable"}',
                    status_code=503,
                    media_type="application/json",
                )
    
    # Serve index.html for all other routes (SPA routing)
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve the SPA index.html for all non-API, non-static routes."""
        if path.startswith("api/") or path.startswith("_next/") or path.startswith("static/"):
            return Response(content="Not found", status_code=404)
        
        file_path_obj = static_dir / path
        if file_path_obj.exists() and file_path_obj.is_file():
            return FileResponse(str(file_path_obj))
        
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return Response(
                content="UI not built. Please run 'pyoptima ui build' first.",
                status_code=404,
                media_type="text/plain",
            )
    
    return app


def serve_ui(
    api_url: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 3000,
) -> None:
    """
    Serve the PyOptima UI.
    
    Args:
        api_url: URL of the PyOptima API (defaults to http://localhost:8000)
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 3000)
    """
    if uvicorn is None:
        print("❌ Error: uvicorn is required for UI server.", file=sys.stderr)
        print("   Install with: pip install pyoptima[api]", file=sys.stderr)
        sys.exit(1)
    
    if api_url is None:
        api_url = os.getenv("PYOPTIMA_API_URL", "http://localhost:8000")
    
    try:
        static_dir = get_static_dir()
        print(f"✓ Found UI static files at: {static_dir}")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    app = create_app(api_url)
    
    print(f"PyOptima UI server starting...")
    print(f"  UI: http://{host}:{port}")
    print(f"  API: {api_url}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PyOptima UI Server")
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="URL of the PyOptima API (default: http://localhost:8000 or PYOPTIMA_API_URL env var)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind to (default: 3000)",
    )
    
    args = parser.parse_args()
    serve_ui(api_url=args.api_url, host=args.host, port=args.port)
