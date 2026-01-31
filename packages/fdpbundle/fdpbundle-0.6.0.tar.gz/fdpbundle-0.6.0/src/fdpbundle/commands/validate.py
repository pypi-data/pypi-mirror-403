"""Validate command - Validate a bundle spec."""

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..client import BundleClient, load_bundle_file

console = Console()


def require_api_config(api_url: str) -> None:
    """Check that API URL is configured."""
    if not api_url:
        console.print(
            "[red]Error:[/red] API URL required. "
            "Use --api-url or set WORKFLOW_ENGINE_URL environment variable."
        )
        raise SystemExit(1)


def display_validation_result(data: dict, verbose: bool = False):
    """
    Display validation result in a formatted way.
    
    Data structure:
    - is_valid: bool
    - errors: List[{field, message, severity}]
    - warnings: List[{field, message, severity}]
    """
    is_valid = data.get("is_valid", False)
    errors = data.get("errors", [])
    warnings = data.get("warnings", [])

    # Status
    if is_valid:
        console.print("\n[bold green]✓ Validation PASSED[/bold green]")
    else:
        console.print("\n[bold red]✗ Validation FAILED[/bold red]")

    # Summary line
    console.print(f"[dim]Errors: {len(errors)} | Warnings: {len(warnings)}[/dim]\n")

    # Errors table
    if errors:
        table = Table(
            title=f"[red]Errors ({len(errors)})[/red]",
            show_header=True,
            header_style="bold red",
            expand=True,
        )
        table.add_column("Field", style="cyan", no_wrap=False, width=30)
        table.add_column("Message", style="white")
        table.add_column("Severity", style="red", width=10)

        for error in errors:
            field = error.get("field", "-")
            message = error.get("message", "-")
            severity = error.get("severity", "error")
            table.add_row(field, message, severity)
        
        console.print(table)
        console.print()

    # Warnings table
    if warnings:
        table = Table(
            title=f"[yellow]Warnings ({len(warnings)})[/yellow]",
            show_header=True,
            header_style="bold yellow",
            expand=True,
        )
        table.add_column("Field", style="cyan", no_wrap=False, width=30)
        table.add_column("Message", style="white")
        table.add_column("Severity", style="yellow", width=10)

        for warning in warnings:
            field = warning.get("field", "-")
            message = warning.get("message", "-")
            severity = warning.get("severity", "warning")
            table.add_row(field, message, severity)
        
        console.print(table)
        console.print()

    # No issues
    if not errors and not warnings:
        console.print("[dim]No errors or warnings found.[/dim]")


@click.command()
@click.argument("bundle_file", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, bundle_file: str):
    """Validate a bundle JSON file.

    Validates the bundle spec against the Workflow Engine API.

    \b
    Example:
      fdpbundle validate bundles/etl-pipeline/bundle.json
    """
    config = ctx.obj
    require_api_config(config.api_url)

    console.print(f"\n[bold]Validating:[/bold] {bundle_file}")

    try:
        spec = load_bundle_file(bundle_file)
        bundle_name = spec.get("bundle", {}).get("name", "unknown")
        console.print(f"[bold]Bundle:[/bold] {bundle_name}")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise SystemExit(1)

    client = BundleClient(config.api_url, config.username, config.password)
    result = client.validate(spec)

    # Even if HTTP 400, we may have validation data to display
    data = result.get("data", {})
    
    if not data and not result.get("success"):
        # No data at all, just an error
        console.print(f"\n[red]API Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    # Display validation results (works even for 400 responses with data)
    display_validation_result(data, config.verbose)

    if data.get("is_valid", False):
        raise SystemExit(0)
    else:
        raise SystemExit(1)
