"""Diff command - Show diff for a bundle."""

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


def get_action_style(action: str) -> tuple:
    """Get color and symbol for action type."""
    styles = {
        "create": ("green", "+"),
        "update": ("yellow", "~"),
        "delete": ("red", "-"),
        "unchanged": ("dim", "="),
        "unlinked": ("red", "⊘"),
    }
    return styles.get(action, ("white", "?"))


def display_diff_result(data: dict, verbose: bool = False):
    """
    Display diff result in a formatted way.
    
    Data structure (BundleDiff):
    - bundle_name: str
    - env: str
    - has_changes: bool
    - summary: {workflows_create, workflows_update, workflows_unchanged, 
                tasks_create, tasks_update, tasks_delete, tasks_unchanged}
    - workflows: List[WorkflowDiff]
      - workflow_name: str
      - workflow_id: Optional[int]
      - action: str (create, update, delete, unchanged)
      - changes: Optional[Dict] - {field: {old, new}}
      - tasks: List[TaskDiff]
        - task_id: str
        - task_name: str
        - action: str
        - changes: Optional[Dict]
    """
    bundle_name = data.get("bundle_name", "-")
    env = data.get("env", "-")
    has_changes = data.get("has_changes", False)
    summary = data.get("summary", {})
    workflows = data.get("workflows", [])

    # Header
    console.print()
    if has_changes:
        console.print(f"[bold yellow]⚡ Changes Detected[/bold yellow]")
    else:
        console.print(f"[bold green]✓ No Changes[/bold green]")

    console.print(f"[dim]Bundle: {bundle_name} | Environment: {env.upper()}[/dim]\n")

    # Summary table
    if summary:
        table = Table(title="Summary", show_header=True, header_style="bold")
        table.add_column("Category", style="cyan")
        table.add_column("Create", justify="right", style="green")
        table.add_column("Update", justify="right", style="yellow")
        table.add_column("Delete", justify="right", style="red")
        table.add_column("Unchanged", justify="right", style="dim")

        # Workflows row
        table.add_row(
            "Workflows",
            str(summary.get("workflows_create", 0)),
            str(summary.get("workflows_update", 0)),
            "-",  # workflows don't have delete in summary
            str(summary.get("workflows_unchanged", 0)),
        )

        # Tasks row
        table.add_row(
            "Tasks",
            str(summary.get("tasks_create", 0)),
            str(summary.get("tasks_update", 0)),
            str(summary.get("tasks_delete", 0)),
            str(summary.get("tasks_unchanged", 0)),
        )

        console.print(table)
        console.print()

    # Workflow details tree
    if workflows:
        tree = Tree("[bold]Workflow Changes[/bold]")

        for wf in workflows:
            wf_name = wf.get("workflow_name", "unknown")
            wf_id = wf.get("workflow_id")
            wf_action = wf.get("action", "unchanged")
            wf_changes = wf.get("changes") or {}
            tasks = wf.get("tasks", [])

            color, symbol = get_action_style(wf_action)
            wf_label = f"[{color}][{symbol}] {wf_name}[/{color}]"
            if wf_id:
                wf_label += f" [dim](id: {wf_id})[/dim]"
            wf_label += f" [{color}]{wf_action}[/{color}]"

            wf_branch = tree.add(wf_label)

            # Show workflow field changes
            if wf_changes:
                changes_branch = wf_branch.add("[dim]Field changes:[/dim]")
                for field, change in wf_changes.items():
                    if isinstance(change, dict) and "old" in change and "new" in change:
                        old_val = _format_value(change["old"])
                        new_val = _format_value(change["new"])
                        changes_branch.add(
                            f"[cyan]{field}[/cyan]: [red]{old_val}[/red] → [green]{new_val}[/green]"
                        )
                    else:
                        changes_branch.add(f"[cyan]{field}[/cyan]: {change}")

            # Show tasks
            if tasks:
                # Group tasks by action for cleaner display
                for task in tasks:
                    task_id = task.get("task_id", "unknown")
                    task_name = task.get("task_name", task_id)
                    task_action = task.get("action", "unchanged")
                    task_changes = task.get("changes") or {}

                    t_color, t_symbol = get_action_style(task_action)
                    
                    # Only show non-unchanged tasks by default, show all if verbose
                    if task_action == "unchanged" and not verbose:
                        continue
                    
                    task_label = f"[{t_color}][{t_symbol}] {task_name}[/{t_color}]"
                    if task_id != task_name:
                        task_label += f" [dim](id: {task_id})[/dim]"

                    task_branch = wf_branch.add(task_label)

                    # Show task field changes
                    if task_changes:
                        for field, change in task_changes.items():
                            if isinstance(change, dict) and "old" in change and "new" in change:
                                old_val = _format_value(change["old"])
                                new_val = _format_value(change["new"])
                                task_branch.add(
                                    f"[cyan]{field}[/cyan]: [red]{old_val}[/red] → [green]{new_val}[/green]"
                                )
                            else:
                                task_branch.add(f"[cyan]{field}[/cyan]: {change}")

                # Count unchanged tasks
                unchanged_count = sum(1 for t in tasks if t.get("action") == "unchanged")
                if unchanged_count > 0 and not verbose:
                    wf_branch.add(f"[dim]... and {unchanged_count} unchanged task(s)[/dim]")

        console.print(tree)
        console.print()

    # Legend
    console.print(
        "[dim]Legend: [green][+] create[/green] | "
        "[yellow][~] update[/yellow] | "
        "[red][-] delete[/red] | "
        "[=] unchanged[/dim]"
    )
    if not verbose:
        console.print("[dim]Use -v/--verbose to see all tasks and field changes[/dim]")


def _format_value(value) -> str:
    """Format a value for display."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)[:50]
    return str(value)


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
      fdpbundle diff bundles/etl-pipeline/bundle.json --env prod -v
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

    console.print(f"\n[bold]Computing diff...[/bold]")
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

    result = client.diff(bundle["id"], env)

    # Check for errors
    if not result.get("success") and not result.get("data"):
        console.print(f"\n[red]✗ Diff Failed[/red]")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    data = result.get("data", {})
    display_diff_result(data, config.verbose)
    raise SystemExit(0)
