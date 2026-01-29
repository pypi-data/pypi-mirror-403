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
    """Display validation result in a formatted way."""
    is_valid = data.get("is_valid", False)
    errors = data.get("errors", [])
    warnings = data.get("warnings", [])

    # Status
    if is_valid:
        console.print("\n[bold green]✓ Validation PASSED[/bold green]")
    else:
        console.print("\n[bold red]✗ Validation FAILED[/bold red]")

    # Errors table
    if errors:
        console.print()
        table = Table(
            title=f"[red]Errors ({len(errors)})[/red]",
            show_header=True,
            header_style="bold red",
        )
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Message", style="white")
        table.add_column("Severity", style="red")

        for error in errors:
            table.add_row(
                error.get("field", "-"),
                error.get("message", "-"),
                error.get("severity", "error"),
            )
        console.print(table)

    # Warnings table
    if warnings:
        console.print()
        table = Table(
            title=f"[yellow]Warnings ({len(warnings)})[/yellow]",
            show_header=True,
            header_style="bold yellow",
        )
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Message", style="white")
        table.add_column("Severity", style="yellow")

        for warning in warnings:
            table.add_row(
                warning.get("field", "-"),
                warning.get("message", "-"),
                warning.get("severity", "warning"),
            )
        console.print(table)

    # Summary
    if not errors and not warnings:
        console.print("[dim]No errors or warnings[/dim]")


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

    client = BundleClient(config.api_url, config.session)
    result = client.validate(spec)

    if not result.get("success"):
        console.print(f"\n[red]API Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    data = result.get("data", {})
    display_validation_result(data, config.verbose)

    if data.get("is_valid", False):
        raise SystemExit(0)
    else:
        raise SystemExit(1)
