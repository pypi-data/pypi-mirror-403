"""Apply command - Apply a bundle to an environment."""

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from ..client import BundleClient, get_bundle_name_from_file
from .diff import display_diff_result

console = Console()


def require_api_config(api_url: str) -> None:
    """Check that API URL is configured."""
    if not api_url:
        console.print(
            "[red]Error:[/red] API URL required. "
            "Use --api-url or set WORKFLOW_ENGINE_URL environment variable."
        )
        raise SystemExit(1)


def display_apply_result(data: dict, dry_run: bool = False, verbose: bool = False):
    """
    Display apply result in a formatted way.
    
    Data structure (ApplyResult):
    - bundle_id: int
    - bundle_name: str
    - version_id: int
    - version_number: int
    - content_hash: str
    - env: str
    - diff: Optional[BundleDiff] (only for dry_run)
    - created_workflows: List[Dict] - {workflow_id, workflow_name, action, created_tasks, updated_tasks, deleted_tasks}
    - updated_workflows: List[Dict] - same structure
    - unlinked_workflows: List[Dict] - {workflow_id, workflow_name, action: "unlinked"}
    - created_tasks: List[Dict] - {spec_task_id, db_task_id, task_name, action}
    - updated_tasks: List[Dict] - same structure
    - deleted_tasks: List[Dict] - {db_task_id, task_name}
    """
    bundle_name = data.get("bundle_name", "-")
    env = data.get("env", "-")
    version_number = data.get("version_number", "-")

    # Header
    console.print()
    if dry_run:
        console.print("[bold cyan]Dry Run Result[/bold cyan]")
    else:
        console.print("[bold green]✓ Apply Successful[/bold green]")

    # Basic info table
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Property", style="bold cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Bundle", bundle_name)
    info_table.add_row("Environment", env.upper())
    info_table.add_row("Version", str(version_number))
    info_table.add_row("Bundle ID", str(data.get("bundle_id", "-")))
    info_table.add_row("Version ID", str(data.get("version_id", "-")))

    content_hash = data.get("content_hash", "")
    if content_hash:
        info_table.add_row("Content Hash", content_hash[:20] + "...")

    console.print(info_table)
    console.print()

    # For dry run, show the diff
    if dry_run and data.get("diff"):
        console.print("[bold]Diff Preview:[/bold]")
        display_diff_result(data["diff"], verbose)
        return

    # Get changes
    created_workflows = data.get("created_workflows", [])
    updated_workflows = data.get("updated_workflows", [])
    unlinked_workflows = data.get("unlinked_workflows", [])
    created_tasks = data.get("created_tasks", [])
    updated_tasks = data.get("updated_tasks", [])
    deleted_tasks = data.get("deleted_tasks", [])

    # Summary table
    summary_table = Table(title="Changes Applied", show_header=True, header_style="bold")
    summary_table.add_column("Type", style="cyan")
    summary_table.add_column("Action", style="white")
    summary_table.add_column("Count", justify="right")

    has_changes = False

    if created_workflows:
        summary_table.add_row("Workflows", "[green]Created[/green]", f"[green]{len(created_workflows)}[/green]")
        has_changes = True
    if updated_workflows:
        summary_table.add_row("Workflows", "[yellow]Updated[/yellow]", f"[yellow]{len(updated_workflows)}[/yellow]")
        has_changes = True
    if unlinked_workflows:
        summary_table.add_row("Workflows", "[red]Unlinked[/red]", f"[red]{len(unlinked_workflows)}[/red]")
        has_changes = True
    if created_tasks:
        summary_table.add_row("Tasks", "[green]Created[/green]", f"[green]{len(created_tasks)}[/green]")
        has_changes = True
    if updated_tasks:
        summary_table.add_row("Tasks", "[yellow]Updated[/yellow]", f"[yellow]{len(updated_tasks)}[/yellow]")
        has_changes = True
    if deleted_tasks:
        summary_table.add_row("Tasks", "[red]Deleted[/red]", f"[red]{len(deleted_tasks)}[/red]")
        has_changes = True

    if has_changes:
        console.print(summary_table)
        console.print()

        # Detailed tree view
        tree = Tree("[bold]Applied Changes[/bold]")

        # Created workflows
        if created_workflows:
            created_branch = tree.add("[green]Created Workflows[/green]")
            for wf in created_workflows:
                wf_name = wf.get("workflow_name", wf.get("name", "-"))
                wf_id = wf.get("workflow_id", wf.get("id", "-"))
                wf_branch = created_branch.add(f"[green]+[/green] {wf_name} [dim](id: {wf_id})[/dim]")
                
                # Show tasks within this workflow
                for task in wf.get("created_tasks", []):
                    task_name = task.get("task_name", "-")
                    task_id = task.get("db_task_id", task.get("spec_task_id", "-"))
                    wf_branch.add(f"[green]+[/green] {task_name} [dim](id: {task_id})[/dim]")

        # Updated workflows
        if updated_workflows:
            updated_branch = tree.add("[yellow]Updated Workflows[/yellow]")
            for wf in updated_workflows:
                wf_name = wf.get("workflow_name", wf.get("name", "-"))
                wf_id = wf.get("workflow_id", wf.get("id", "-"))
                wf_branch = updated_branch.add(f"[yellow]~[/yellow] {wf_name} [dim](id: {wf_id})[/dim]")
                
                # Show tasks within this workflow
                for task in wf.get("created_tasks", []):
                    task_name = task.get("task_name", "-")
                    task_id = task.get("db_task_id", "-")
                    wf_branch.add(f"[green]+[/green] {task_name} [dim](id: {task_id})[/dim]")
                
                for task in wf.get("updated_tasks", []):
                    task_name = task.get("task_name", "-")
                    task_id = task.get("db_task_id", "-")
                    wf_branch.add(f"[yellow]~[/yellow] {task_name} [dim](id: {task_id})[/dim]")
                
                for task in wf.get("deleted_tasks", []):
                    task_name = task.get("task_name", "-")
                    task_id = task.get("db_task_id", "-")
                    wf_branch.add(f"[red]-[/red] {task_name} [dim](id: {task_id})[/dim]")

        # Unlinked workflows
        if unlinked_workflows:
            unlinked_branch = tree.add("[red]Unlinked Workflows[/red]")
            for wf in unlinked_workflows:
                wf_name = wf.get("workflow_name", wf.get("name", "-"))
                wf_id = wf.get("workflow_id", wf.get("id", "-"))
                unlinked_branch.add(f"[red]⊘[/red] {wf_name} [dim](id: {wf_id})[/dim]")

        # Standalone tasks (if any not grouped by workflow)
        standalone_created = [t for t in created_tasks if not any(
            t in wf.get("created_tasks", []) for wf in created_workflows + updated_workflows
        )]
        standalone_updated = [t for t in updated_tasks if not any(
            t in wf.get("updated_tasks", []) for wf in updated_workflows
        )]
        standalone_deleted = [t for t in deleted_tasks if not any(
            t in wf.get("deleted_tasks", []) for wf in updated_workflows
        )]

        if standalone_created or standalone_updated or standalone_deleted:
            tasks_branch = tree.add("[bold]Tasks[/bold]")
            
            for task in standalone_created:
                task_name = task.get("task_name", "-")
                task_id = task.get("db_task_id", task.get("spec_task_id", "-"))
                tasks_branch.add(f"[green]+[/green] {task_name} [dim](id: {task_id})[/dim]")
            
            for task in standalone_updated:
                task_name = task.get("task_name", "-")
                task_id = task.get("db_task_id", "-")
                tasks_branch.add(f"[yellow]~[/yellow] {task_name} [dim](id: {task_id})[/dim]")
            
            for task in standalone_deleted:
                task_name = task.get("task_name", "-")
                task_id = task.get("db_task_id", "-")
                tasks_branch.add(f"[red]-[/red] {task_name} [dim](id: {task_id})[/dim]")

        console.print(tree)
        console.print()
        
        # Legend
        console.print(
            "[dim]Legend: [green][+] created[/green] | "
            "[yellow][~] updated[/yellow] | "
            "[red][-] deleted[/red] | "
            "[red][⊘] unlinked[/red][/dim]"
        )
    else:
        console.print("[dim]No changes were applied (bundle already up to date)[/dim]")



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
    console.print(f"[dim]Bundle: {bundle_name} | Environment: {env.upper()}[/dim]")

    client = BundleClient(config.api_url, config.username, config.password)

    # Find bundle by name
    bundle = client.get_bundle_by_name(bundle_name)
    if not bundle:
        console.print(
            f"\n[red]Error:[/red] Bundle '{bundle_name}' not found. "
            f"Run [cyan]fdpbundle import[/cyan] first."
        )
        raise SystemExit(1)

    result = client.apply(bundle["id"], env, dry_run)

    # Check for errors
    if not result.get("success") and not result.get("data"):
        console.print(f"\n[red]✗ Apply Failed[/red]")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    data = result.get("data", {})
    display_apply_result(data, dry_run, config.verbose)
    raise SystemExit(0)
