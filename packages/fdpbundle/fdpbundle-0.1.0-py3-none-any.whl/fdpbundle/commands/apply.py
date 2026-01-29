"""Apply command - Apply a bundle to an environment."""

import json

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

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
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.pass_context
def apply(ctx, bundle_file: str, env: str, dry_run: bool):
    """Apply a bundle to an environment.

    Applies the bundle changes to create/update/delete workflows.

    \b
    Example:
      fdpbundle apply bundles/etl-pipeline/bundle.json --env dev
      fdpbundle apply bundles/etl-pipeline/bundle.json --env prod --dry-run
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

    action = "Dry run" if dry_run else "Applying"
    console.print(f"\n[bold]{action}:[/bold] {bundle_name}")
    console.print(f"[bold]Environment:[/bold] {env}\n")

    client = BundleClient(config.api_url, config.session)

    # Find bundle by name
    bundle = client.get_bundle_by_name(bundle_name)
    if not bundle:
        console.print(
            f"[red]Error:[/red] Bundle '{bundle_name}' not found. Import it first."
        )
        raise SystemExit(1)

    result = client.apply(bundle["id"], env, dry_run)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="API Response"))

    if result.get("success"):
        data = result.get("data", {})

        if dry_run:
            console.print("[cyan]🔍 Dry run results:[/cyan]")
            console.print(Panel(JSON(json.dumps(data, default=str)), title="Would apply"))
        else:
            created = data.get("created_workflows", [])
            updated = data.get("updated_workflows", [])
            deleted = data.get("deleted_workflows", [])

            console.print("[green]✓ Apply successful[/green]")
            console.print(f"  Created workflows: [cyan]{len(created)}[/cyan]")
            console.print(f"  Updated workflows: [cyan]{len(updated)}[/cyan]")
            console.print(f"  Deleted workflows: [cyan]{len(deleted)}[/cyan]")

            if created:
                console.print("\n[bold]Created:[/bold]")
                for wf in created:
                    console.print(f"  [green]+[/green] {wf}")

            if updated:
                console.print("\n[bold]Updated:[/bold]")
                for wf in updated:
                    console.print(f"  [yellow]~[/yellow] {wf}")

            if deleted:
                console.print("\n[bold]Deleted:[/bold]")
                for wf in deleted:
                    console.print(f"  [red]-[/red] {wf}")

        raise SystemExit(0)
    else:
        console.print("[red]✗ Apply failed[/red]")
        console.print(f"\n[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)
