"""Apply command - Apply a bundle to an environment."""

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

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


def display_apply_result(data: dict, dry_run: bool = False):
    """Display apply result in a formatted way."""
    bundle_name = data.get("bundle_name", "-")
    env = data.get("env", "-")
    version_number = data.get("version_number", "-")

    # Header
    console.print()
    if dry_run:
        console.print("[bold cyan]🔍 Dry Run Result[/bold cyan]")
    else:
        console.print("[bold green]✓ Apply Successful[/bold green]")

    # Basic info
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Property", style="bold cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Bundle", bundle_name)
    info_table.add_row("Environment", env.upper())
    info_table.add_row("Version", str(version_number))
    info_table.add_row("Bundle ID", str(data.get("bundle_id", "-")))

    content_hash = data.get("content_hash", "")
    if content_hash:
        info_table.add_row("Content Hash", content_hash[:16] + "...")

    console.print(info_table)
    console.print()

    # Changes summary
    created_workflows = data.get("created_workflows", [])
    updated_workflows = data.get("updated_workflows", [])
    unlinked_workflows = data.get("unlinked_workflows", [])
    created_tasks = data.get("created_tasks", [])
    updated_tasks = data.get("updated_tasks", [])
    deleted_tasks = data.get("deleted_tasks", [])

    # Summary table
    summary_table = Table(title="Changes Summary", show_header=True, header_style="bold")
    summary_table.add_column("Type", style="cyan")
    summary_table.add_column("Count", justify="right")

    if created_workflows:
        summary_table.add_row("Workflows Created", f"[green]{len(created_workflows)}[/green]")
    if updated_workflows:
        summary_table.add_row("Workflows Updated", f"[yellow]{len(updated_workflows)}[/yellow]")
    if unlinked_workflows:
        summary_table.add_row("Workflows Unlinked", f"[red]{len(unlinked_workflows)}[/red]")
    if created_tasks:
        summary_table.add_row("Tasks Created", f"[green]{len(created_tasks)}[/green]")
    if updated_tasks:
        summary_table.add_row("Tasks Updated", f"[yellow]{len(updated_tasks)}[/yellow]")
    if deleted_tasks:
        summary_table.add_row("Tasks Deleted", f"[red]{len(deleted_tasks)}[/red]")

    total_changes = (
        len(created_workflows) + len(updated_workflows) + len(unlinked_workflows) +
        len(created_tasks) + len(updated_tasks) + len(deleted_tasks)
    )

    if total_changes > 0:
        console.print(summary_table)
        console.print()

        # Detailed changes
        if created_workflows:
            console.print("[bold green]Created Workflows:[/bold green]")
            for wf in created_workflows:
                wf_name = wf.get("name", wf.get("workflow_name", "-"))
                wf_id = wf.get("id", wf.get("workflow_id", "-"))
                console.print(f"  [green]+[/green] {wf_name} [dim](id: {wf_id})[/dim]")
            console.print()

        if updated_workflows:
            console.print("[bold yellow]Updated Workflows:[/bold yellow]")
            for wf in updated_workflows:
                wf_name = wf.get("name", wf.get("workflow_name", "-"))
                wf_id = wf.get("id", wf.get("workflow_id", "-"))
                console.print(f"  [yellow]~[/yellow] {wf_name} [dim](id: {wf_id})[/dim]")
            console.print()

        if unlinked_workflows:
            console.print("[bold red]Unlinked Workflows:[/bold red]")
            for wf in unlinked_workflows:
                wf_name = wf.get("name", wf.get("workflow_name", "-"))
                wf_id = wf.get("id", wf.get("workflow_id", "-"))
                console.print(f"  [red]-[/red] {wf_name} [dim](id: {wf_id})[/dim]")
            console.print()

        if created_tasks:
            console.print("[bold green]Created Tasks:[/bold green]")
            for task in created_tasks:
                task_name = task.get("task_display_name", task.get("name", "-"))
                task_id = task.get("id", task.get("task_id", "-"))
                console.print(f"  [green]+[/green] {task_name} [dim](id: {task_id})[/dim]")
            console.print()

        if updated_tasks:
            console.print("[bold yellow]Updated Tasks:[/bold yellow]")
            for task in updated_tasks:
                task_name = task.get("task_display_name", task.get("name", "-"))
                task_id = task.get("id", task.get("task_id", "-"))
                console.print(f"  [yellow]~[/yellow] {task_name} [dim](id: {task_id})[/dim]")
            console.print()

        if deleted_tasks:
            console.print("[bold red]Deleted Tasks:[/bold red]")
            for task in deleted_tasks:
                task_name = task.get("task_display_name", task.get("name", "-"))
                task_id = task.get("id", task.get("task_id", "-"))
                console.print(f"  [red]-[/red] {task_name} [dim](id: {task_id})[/dim]")
            console.print()
    else:
        console.print("[dim]No changes applied[/dim]\n")


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
    console.print(f"\n[bold]{action}...[/bold]")
    console.print(f"[dim]Bundle: {bundle_name} | Environment: {env}[/dim]")

    client = BundleClient(config.api_url, config.session)

    # Find bundle by name
    bundle = client.get_bundle_by_name(bundle_name)
    if not bundle:
        console.print(
            f"\n[red]Error:[/red] Bundle '{bundle_name}' not found. Run [cyan]fdpbundle import[/cyan] first."
        )
        raise SystemExit(1)

    result = client.apply(bundle["id"], env, dry_run)

    if not result.get("success"):
        console.print(f"\n[red]✗ Apply Failed[/red]")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    data = result.get("data", {})
    display_apply_result(data, dry_run)
    raise SystemExit(0)
