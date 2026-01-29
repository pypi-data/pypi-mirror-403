"""Import command - Import a bundle spec into the system."""

import json

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

    console.print(f"\n[bold]Importing:[/bold] {bundle_file}\n")

    try:
        spec = load_bundle_file(bundle_file)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise SystemExit(1)

    client = BundleClient(config.api_url, config.session)
    result = client.import_bundle(spec, set_as_current=not no_set_current)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="API Response"))

    if result.get("success"):
        data = result.get("data", {})
        bundle_id = data.get("bundle_id")
        bundle_name = data.get("bundle_name")
        version_number = data.get("version_number")
        is_new_bundle = data.get("is_new_bundle", False)
        is_new_version = data.get("is_new_version", False)

        console.print("[green]✓ Import successful[/green]")
        console.print(f"  Bundle ID: [cyan]{bundle_id}[/cyan]")
        console.print(f"  Bundle Name: [cyan]{bundle_name}[/cyan]")
        console.print(f"  Version: [cyan]{version_number}[/cyan]")
        console.print(f"  New bundle: [cyan]{is_new_bundle}[/cyan]")
        console.print(f"  New version: [cyan]{is_new_version}[/cyan]")

        raise SystemExit(0)
    else:
        console.print("[red]✗ Import failed[/red]")
        console.print(f"\n[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)
