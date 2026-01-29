"""Validate command - Validate a bundle spec."""

import json
import sys

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

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

    console.print(f"\n[bold]Validating:[/bold] {bundle_file}\n")

    try:
        spec = load_bundle_file(bundle_file)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise SystemExit(1)

    client = BundleClient(config.api_url, config.session)
    result = client.validate(spec)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="API Response"))

    if result.get("success") and result.get("data", {}).get("is_valid", False):
        console.print("[green]✓ Validation passed[/green]")

        warnings = result.get("data", {}).get("warnings", [])
        if warnings:
            console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
            for warning in warnings:
                console.print(f"  [yellow]![/yellow] {warning}")

        raise SystemExit(0)
    else:
        console.print("[red]✗ Validation failed[/red]")

        errors = result.get("data", {}).get("errors", [])
        if errors:
            console.print(f"\n[red]Errors ({len(errors)}):[/red]")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
        elif result.get("error"):
            console.print(f"\n[red]Error:[/red] {result.get('error')}")

        raise SystemExit(1)
