"""
Main CLI entry point for pyoptima commands.

Improved CLI with better formatting, more commands, and enhanced UX.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def status(self, *args, **kwargs): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass


def main():
    """Main CLI entry point."""
    console = Console() if RICH_AVAILABLE else Console()
    
    parser = argparse.ArgumentParser(
        description="PyOptima - Universal Optimization Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Solve from config file
  pyoptima solve config.yaml
  pyoptima solve config.json --output result.json --pretty
  
  # List templates
  pyoptima list
  pyoptima list --detailed
  
  # Get template information
  pyoptima info portfolio
  pyoptima info knapsack
  
  # Validate config without solving
  pyoptima validate config.yaml
  
  # Generate example config
  pyoptima example portfolio > portfolio_example.json
  
  # Start API server
  pyoptima api --port 8000
  
  # UI commands
  pyoptima ui dev
  pyoptima ui serve
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

    # solve subcommand
    solve_parser = subparsers.add_parser(
        "solve", help="Run optimization from configuration file or stdin"
    )
    solve_parser.add_argument(
        "config_file",
        nargs="?",
        type=str,
        help="Path to optimization configuration file (JSON or YAML), or '-' for stdin",
    )
    solve_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path for results (JSON format, default: stdout)",
    )
    solve_parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        default=True,
        help="Pretty print output (default: True)",
    )
    solve_parser.add_argument(
        "--no-pretty",
        dest="pretty",
        action="store_false",
        help="Disable pretty printing",
    )
    solve_parser.add_argument(
        "--solver",
        type=str,
        help="Override solver from config",
    )
    solve_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    # list subcommand
    list_parser = subparsers.add_parser(
        "list", help="List available templates"
    )
    list_parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Show detailed template information",
    )
    list_parser.add_argument(
        "--format",
        choices=["table", "json", "simple"],
        default="table",
        help="Output format (default: table)",
    )
    
    # info subcommand
    info_parser = subparsers.add_parser(
        "info", help="Show detailed information about a template"
    )
    info_parser.add_argument(
        "template",
        type=str,
        help="Template name",
    )
    info_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    
    # validate subcommand
    validate_parser = subparsers.add_parser(
        "validate", help="Validate configuration file without solving"
    )
    validate_parser.add_argument(
        "config_file",
        type=str,
        help="Path to configuration file (JSON or YAML), or '-' for stdin",
    )
    validate_parser.add_argument(
        "--template",
        type=str,
        help="Template name (auto-detected from config if not provided)",
    )
    
    # example subcommand
    example_parser = subparsers.add_parser(
        "example", help="Generate example configuration for a template"
    )
    example_parser.add_argument(
        "template",
        type=str,
        help="Template name",
    )
    example_parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    example_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file (default: stdout)",
    )

    # api subcommand
    api_parser = subparsers.add_parser("api", help="Start the API server")
    api_parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    api_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    api_parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload (default: True)",
    )
    api_parser.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )

    # ui subcommand
    ui_parser = subparsers.add_parser("ui", help="UI management commands")
    ui_subparsers = ui_parser.add_subparsers(dest="ui_command", help="UI command")

    # ui serve
    ui_serve_parser = ui_subparsers.add_parser(
        "serve", help="Serve the built UI (production mode)"
    )
    ui_serve_parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="URL of the PyOptima API (default: http://localhost:8000 or PYOPTIMA_API_URL env var)",
    )
    ui_serve_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    ui_serve_parser.add_argument(
        "--port", type=int, default=3000, help="Port to bind to (default: 3000)"
    )

    # ui dev
    ui_dev_parser = ui_subparsers.add_parser("dev", help="Run UI development server")
    ui_dev_parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="URL of the PyOptima API (default: http://localhost:8000 or PYOPTIMA_API_URL env var)",
    )
    ui_dev_parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to run dev server on (default: 3000)",
    )

    # ui build
    ui_build_parser = ui_subparsers.add_parser(
        "build", help="Build the UI for production"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "solve":
        return cmd_solve(
            config_file=args.config_file,
            output=args.output,
            pretty=args.pretty,
        )
    elif args.command == "list":
        return cmd_list()
    elif args.command == "api":
        return cmd_api(host=args.host, port=args.port, reload=args.reload)
    elif args.command == "ui":
        return cmd_ui(args, ui_parser)
    else:
        parser.print_help()
        return 1


def cmd_solve(
    config_file: Optional[str] = None,
    output: Optional[str] = None,
    pretty: bool = True,
    solver: Optional[str] = None,
    verbose: bool = False
) -> int:
    """
    Run optimization from configuration file or stdin.

    Args:
        config_file: Path to configuration file, '-' for stdin, or None for interactive
        output: Optional output file path
        pretty: Whether to pretty print output
        solver: Override solver from config
        verbose: Verbose output

    Returns:
        Exit code (0 for success, 1 for error)
    """
    console = Console() if RICH_AVAILABLE else Console()
    
    try:
        from pyoptima.config import load_config_file, run_from_config
        
        # Read config from file or stdin
        if config_file == "-" or config_file is None:
            if config_file is None:
                console.print("[yellow]Reading config from stdin...[/yellow]")
            config_data = json.load(sys.stdin)
        else:
            config = load_config_file(config_file)
            config_data = config.model_dump() if hasattr(config, 'model_dump') else config
        
        # Override solver if specified
        if solver:
            if "solver" not in config_data:
                config_data["solver"] = {}
            if isinstance(config_data["solver"], dict):
                config_data["solver"]["name"] = solver
            else:
                config_data["solver"] = {"name": solver}
        
        # Run optimization with progress indicator
        if RICH_AVAILABLE and verbose:
            with console.status("[bold green]Solving optimization problem...", spinner="dots"):
                result = run_from_config(config_data)
        else:
            if verbose:
                console.print("Solving optimization problem...")
            result = run_from_config(config_data)

        # Output results
        output_json = json.dumps(result, indent=2 if pretty else None)
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_json)
            if RICH_AVAILABLE:
                console.print(f"[green]✓[/green] Results written to [bold]{output}[/bold]")
            else:
                print(f"✓ Results written to {output}")
        else:
            print(output_json)

        # Return appropriate exit code
        status = result.get("status", "unknown")
        if status == "optimal":
            return 0
        else:
            if RICH_AVAILABLE:
                console.print(f"[yellow]⚠[/yellow] Warning: Optimization status: [bold]{status}[/bold]", style="yellow")
            else:
                print(f"⚠ Warning: Optimization status: {status}", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Validation Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        else:
            print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
            if verbose:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
            if verbose:
                import traceback
                traceback.print_exc()
        return 1


def cmd_list(detailed: bool = False, format: str = "table") -> int:
    """List available templates with optional details."""
    from pyoptima import list_templates, get_template
    
    console = Console() if RICH_AVAILABLE else Console()
    templates = list_templates()
    
    if format == "json":
        import json
        if detailed:
            template_data = []
            for name in templates:
                try:
                    template = get_template(name)
                    info = template.info
                    template_data.append({
                        "name": info.name,
                        "description": info.description,
                        "problem_type": info.problem_type,
                        "required_data": info.required_data,
                        "optional_data": info.optional_data,
                        "default_solver": info.default_solver,
                    })
                except Exception:
                    template_data.append({"name": name})
            print(json.dumps(template_data, indent=2))
        else:
            print(json.dumps(templates, indent=2))
        return 0
    
    if not detailed:
        if format == "simple":
            for name in templates:
                print(name)
        else:
            if RICH_AVAILABLE:
                console.print(f"[bold]Available templates ({len(templates)}):[/bold]")
                for name in templates:
                    console.print(f"  • [cyan]{name}[/cyan]")
            else:
                print(f"Available templates ({len(templates)}):")
                for name in templates:
                    print(f"  - {name}")
        return 0
    
    # Detailed view
    if RICH_AVAILABLE:
        table = Table(title="Available Templates", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Solver", style="green")
        
        for name in templates:
            try:
                template = get_template(name)
                info = template.info
                table.add_row(
                    info.name,
                    info.description[:60] + "..." if len(info.description) > 60 else info.description,
                    info.problem_type,
                    info.default_solver,
                )
            except Exception as e:
                table.add_row(name, f"Error: {e}", "?", "?")
        
        console.print(table)
    else:
        print("Available templates:")
        for name in templates:
            try:
                template = get_template(name)
                info = template.info
                print(f"\n{name}:")
                print(f"  Description: {info.description}")
                print(f"  Problem Type: {info.problem_type}")
                print(f"  Default Solver: {info.default_solver}")
                print(f"  Required Data: {', '.join(info.required_data)}")
            except Exception as e:
                print(f"\n{name}: Error loading - {e}")
    
    return 0


def cmd_info(template_name: str, format: str = "text") -> int:
    """Show detailed information about a template."""
    console = Console() if RICH_AVAILABLE else Console()
    
    try:
        from pyoptima import get_template
        
        template = get_template(template_name)
        info = template.info
        
        if format == "json":
            import json
            print(json.dumps({
                "name": info.name,
                "description": info.description,
                "problem_type": info.problem_type,
                "required_data": info.required_data,
                "optional_data": info.optional_data,
                "default_solver": info.default_solver,
            }, indent=2))
            return 0
        
        # Text format
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[bold cyan]{info.name}[/bold cyan]\n"
                f"[white]{info.description}[/white]",
                title="Template Information",
                border_style="cyan"
            ))
            
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Field", style="bold yellow", no_wrap=True)
            table.add_column("Value", style="white")
            
            table.add_row("Problem Type", info.problem_type)
            table.add_row("Default Solver", info.default_solver)
            table.add_row("Required Data", ", ".join(info.required_data) if info.required_data else "None")
            table.add_row("Optional Data", f"{len(info.optional_data)} fields" if info.optional_data else "None")
            
            console.print("\n")
            console.print(table)
            
            if info.optional_data:
                console.print("\n[bold]Optional Parameters:[/bold]")
                for param in info.optional_data[:20]:  # Show first 20
                    console.print(f"  • {param}")
                if len(info.optional_data) > 20:
                    console.print(f"  ... and {len(info.optional_data) - 20} more")
        else:
            print(f"Template: {info.name}")
            print(f"Description: {info.description}")
            print(f"Problem Type: {info.problem_type}")
            print(f"Default Solver: {info.default_solver}")
            print(f"Required Data: {', '.join(info.required_data)}")
            if info.optional_data:
                print(f"Optional Data ({len(info.optional_data)}): {', '.join(info.optional_data[:10])}...")
        
        return 0
    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_validate(config_file: str, template: Optional[str] = None) -> int:
    """Validate configuration file without solving."""
    console = Console() if RICH_AVAILABLE else Console()
    
    try:
        from pyoptima.config import load_config_file
        from pyoptima import get_template
        
        # Load config
        if config_file == "-":
            config_data = json.load(sys.stdin)
        else:
            config = load_config_file(config_file)
            config_data = config.model_dump() if hasattr(config, 'model_dump') else config
        
        # Get template
        template_name = template or config_data.get("template")
        if not template_name:
            if RICH_AVAILABLE:
                console.print("[red]❌ Error:[/red] Template name not found in config and not provided", style="red")
            else:
                print("❌ Error: Template name not found in config and not provided", file=sys.stderr)
            return 1
        
        template_obj = get_template(template_name)
        
        # Validate
        if RICH_AVAILABLE:
            with console.status(f"[bold green]Validating {template_name} configuration...", spinner="dots"):
                template_obj.validate_data(config_data.get("data", {}))
        else:
            console.print(f"Validating {template_name} configuration...")
            template_obj.validate_data(config_data.get("data", {}))
        
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Configuration is valid!")
        else:
            print("✓ Configuration is valid!")
        return 0
        
    except FileNotFoundError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Validation Error:[/red] {e}", style="red")
        else:
            print(f"❌ Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_example(template_name: str, format: str = "json", output: Optional[str] = None) -> int:
    """Generate example configuration for a template."""
    console = Console() if RICH_AVAILABLE else Console()
    
    try:
        from pyoptima import get_template
        
        template = get_template(template_name)
        info = template.info
        
        # Generate example config
        example_config = {
            "template": info.name,
            "data": {}
        }
        
        # Add required fields with example values
        for field in info.required_data:
            if field == "expected_returns":
                example_config["data"][field] = [0.1, 0.12, 0.08]
            elif field == "covariance_matrix":
                example_config["data"][field] = [
                    [0.04, 0.01, 0.02],
                    [0.01, 0.05, 0.01],
                    [0.02, 0.01, 0.03]
                ]
            elif field == "items":
                example_config["data"][field] = [
                    {"name": "item1", "value": 60, "weight": 10},
                    {"name": "item2", "value": 100, "weight": 20}
                ]
            elif field == "capacity":
                example_config["data"][field] = 50
            elif field == "c":
                example_config["data"][field] = [1, 2, 3]
            elif field == "Q":
                example_config["data"][field] = [[1, 0], [0, 2]]
            else:
                example_config["data"][field] = f"<{field}>"
        
        # Add some common optional fields
        if info.name == "portfolio":
            example_config["data"]["objective"] = "max_sharpe"
            example_config["data"]["risk_free_rate"] = 0.02
        
        # Output
        if format == "yaml":
            try:
                import yaml
                output_text = yaml.dump(example_config, default_flow_style=False, sort_keys=False)
            except ImportError:
                if RICH_AVAILABLE:
                    console.print("[yellow]Warning:[/yellow] PyYAML not installed, falling back to JSON")
                output_text = json.dumps(example_config, indent=2)
        else:
            output_text = json.dumps(example_config, indent=2)
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_text)
            if RICH_AVAILABLE:
                console.print(f"[green]✓[/green] Example config written to [bold]{output}[/bold]")
            else:
                print(f"✓ Example config written to {output}")
        else:
            if RICH_AVAILABLE:
                syntax = Syntax(output_text, format, theme="monokai", line_numbers=True)
                console.print(syntax)
            else:
                print(output_text)
        
        return 0
        
    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Error:[/red] {e}", style="red")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_api(host: str, port: int, reload: bool) -> int:
    """Start the API server."""
    try:
        import uvicorn  # type: ignore[import-not-found,import-untyped]
    except ImportError:
        print("❌ Error: uvicorn is required for API server.", file=sys.stderr)
        print("   Install with: pip install pyoptima[api]", file=sys.stderr)
        return 1

    # Try to import api module (pyoptima.api when installed)
    try:
        import pyoptima.api  # type: ignore[import-untyped]
    except ImportError:
        # Development mode: add project root to Python path (src layout)
        project_root = Path(__file__).parent.parent.parent.resolve()
        project_root_str = str(project_root)
        
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
        
        # Set PYTHONPATH for uvicorn subprocess (reload mode)
        pythonpath = os.environ.get("PYTHONPATH", "")
        if pythonpath:
            pythonpath = f"{project_root_str}{os.pathsep}{pythonpath}"
        else:
            pythonpath = project_root_str
        os.environ["PYTHONPATH"] = pythonpath

    uvicorn.run(
        "pyoptima.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )
    return 0


def cmd_ui(args, ui_parser) -> int:
    """Handle UI commands."""
    if not args.ui_command:
        ui_parser.print_help()
        return 1

    # Find UI directory
    ui_path = None
    possible_paths = []

    # Check installed package location first (src layout: __file__ parent is package dir)
    try:
        import pyoptima
        package_ui = Path(pyoptima.__file__).parent / "ui"
        possible_paths.append(package_ui)
    except (ImportError, AttributeError):
        pass

    # Check development locations (__file__ is src/pyoptima/cli.py)
    possible_paths.extend([
        Path(__file__).parent / "ui",  # src/pyoptima/ui
        Path.cwd() / "src" / "pyoptima" / "ui",
        Path.cwd() / "ui",
    ])

    for path in possible_paths:
        if path.exists() and (path / "package.json").exists():
            ui_path = path
            break

    if not ui_path:
        print("❌ Error: UI directory not found.", file=sys.stderr)
        print(
            "   If installed from pip: UI should be included in the package.",
            file=sys.stderr,
        )
        print(
            "   If in development: Make sure you're running from the PyOptima project root.",
            file=sys.stderr,
        )
        print(
            "   Or install the UI dependencies: cd ui && npm install",
            file=sys.stderr,
        )
        return 1

    # Add ui directory to Python path
    if str(ui_path) not in sys.path:
        sys.path.insert(0, str(ui_path))

    if args.ui_command == "serve":
        return _cmd_ui_serve(ui_path, args.api_url, args.host, args.port)
    elif args.ui_command == "dev":
        return _cmd_ui_dev(ui_path, args.api_url, args.port)
    elif args.ui_command == "build":
        return _cmd_ui_build(ui_path)
    else:
        ui_parser.print_help()
        return 1


def _cmd_ui_dev(ui_path: Path, api_url: str = None, port: int = 3000) -> int:
    """Run the UI development server."""
    import importlib.util

    dev_path = ui_path / "dev.py"
    if not dev_path.exists():
        print(f"❌ Error: dev.py not found at {dev_path}", file=sys.stderr)
        return 1

    spec = importlib.util.spec_from_file_location("dev", dev_path)
    if spec and spec.loader:
        dev_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dev_module)
        dev_module.run_dev_server(api_url=api_url, port=port)
    return 0


def _cmd_ui_serve(ui_path: Path, api_url: str = None, host: str = "127.0.0.1", port: int = 3000) -> int:
    """Serve the built UI in production mode."""
    import importlib.util

    server_path = ui_path / "server.py"
    if not server_path.exists():
        print(f"❌ Error: server.py not found at {server_path}", file=sys.stderr)
        print("   Creating server.py for production UI serving...", file=sys.stderr)
        # Fall back to dev server if server.py doesn't exist
        return _cmd_ui_dev(ui_path, api_url, port)

    spec = importlib.util.spec_from_file_location("server", server_path)
    if spec and spec.loader:
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)
        server_module.serve_ui(api_url=api_url, host=host, port=port)
    return 0


def _cmd_ui_build(ui_path: Path) -> int:
    """Build the UI for production."""
    import importlib.util

    build_path = ui_path / "build.py"
    if not build_path.exists():
        print(f"❌ Error: build.py not found at {build_path}", file=sys.stderr)
        return 1

    spec = importlib.util.spec_from_file_location("build", build_path)
    if spec and spec.loader:
        build_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_module)
        return build_module.build_ui()
    return 1


if __name__ == "__main__":
    sys.exit(main())
