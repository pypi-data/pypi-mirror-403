"""Diff command - Show diff for a bundle."""

import json

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table

from ..client import BundleClient, get_bundle_name_from_file

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
@click.option(
    "--env",
    type=click.Choice(["dev", "stg", "prod"]),
    default="dev",
    help="Target environment (default: dev)",
)
@click.pass_context
def diff(ctx, bundle_file: str, env: str):
    """Show diff for a bundle against current state.

    Compares the bundle spec with what's currently deployed.

    \b
    Example:
      fdpbundle diff bundles/etl-pipeline/bundle.json --env dev
    """
    config = ctx.obj
    require_api_config(config.api_url)

    try:
        bundle_name = get_bundle_name_from_file(bundle_file)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise SystemExit(1)

    console.print(f"\n[bold]Computing diff for:[/bold] {bundle_name}")
    console.print(f"[bold]Environment:[/bold] {env}\n")

    client = BundleClient(config.api_url, config.session)

    # Find bundle by name
    bundle = client.get_bundle_by_name(bundle_name)
    if not bundle:
        console.print(
            f"[red]Error:[/red] Bundle '{bundle_name}' not found. Import it first."
        )
        raise SystemExit(1)

    result = client.diff(bundle["id"], env)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="API Response"))

    if result.get("success"):
        data = result.get("data", {})
        has_changes = data.get("has_changes", False)
        summary = data.get("summary", {})

        if has_changes:
            console.print("[yellow]⚡ Changes detected[/yellow]\n")

            # Create summary table
            table = Table(title="Change Summary")
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right")

            for change_type, count in summary.items():
                if count > 0:
                    table.add_row(change_type.replace("_", " ").title(), str(count))

            console.print(table)

            # Show detailed changes if available
            changes = data.get("changes", {})
            if changes and config.verbose:
                console.print("\n[bold]Detailed changes:[/bold]")
                console.print(JSON(json.dumps(changes, default=str)))
        else:
            console.print("[green]✓ No changes detected[/green]")

        raise SystemExit(0)
    else:
        console.print("[red]✗ Diff failed[/red]")
        console.print(f"\n[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)
