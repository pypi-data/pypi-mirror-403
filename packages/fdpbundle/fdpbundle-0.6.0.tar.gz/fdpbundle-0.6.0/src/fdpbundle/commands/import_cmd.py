"""Import command - Import a bundle spec into the system."""

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


def display_import_result(data: dict):
    """Display import result in a formatted way."""
    console.print("\n[bold green]✓ Import Successful[/bold green]\n")

    # Create info table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Bundle ID", str(data.get("bundle_id", "-")))
    table.add_row("Bundle Name", data.get("bundle_name", "-"))
    table.add_row("Version ID", str(data.get("version_id", "-")))
    table.add_row("Version Number", str(data.get("version_number", "-")))
    table.add_row("Content Hash", data.get("content_hash", "-")[:16] + "..." if data.get("content_hash") else "-")

    # Status flags
    is_new_bundle = data.get("is_new_bundle", False)
    is_new_version = data.get("is_new_version", False)

    if is_new_bundle:
        table.add_row("Status", "[green]New bundle created[/green]")
    elif is_new_version:
        table.add_row("Status", "[yellow]New version created[/yellow]")
    else:
        table.add_row("Status", "[dim]No changes (same content)[/dim]")

    console.print(table)


@click.command("import")
@click.argument("bundle_file", type=click.Path(exists=True))
@click.option(
    "--no-set-current",
    is_flag=True,
    help="Don't set as current version after import",
)
@click.pass_context
def import_bundle(ctx, bundle_file: str, no_set_current: bool):
    """Import a bundle spec into the Workflow Engine.

    Creates a new version of the bundle in the system.

    \b
    Example:
      fdpbundle import bundles/etl-pipeline/bundle.json
    """
    config = ctx.obj
    require_api_config(config.api_url)

    console.print(f"\n[bold]Importing:[/bold] {bundle_file}")

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
    result = client.import_bundle(spec, set_as_current=not no_set_current)

    if not result.get("success"):
        console.print(f"\n[red]✗ Import Failed[/red]")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    data = result.get("data", {})
    display_import_result(data)
    raise SystemExit(0)
