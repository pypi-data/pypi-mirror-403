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
    }
    return styles.get(action, ("white", "?"))


def display_diff_result(data: dict, verbose: bool = False):
    """Display diff result in a formatted way."""
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

    console.print(f"[dim]Bundle: {bundle_name} | Environment: {env}[/dim]\n")

    # Summary table
    if summary:
        table = Table(title="Summary", show_header=True, header_style="bold")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")

        for key, value in summary.items():
            if value > 0:
                color, _ = get_action_style(key.replace("_workflows", "").replace("_tasks", ""))
                table.add_row(key.replace("_", " ").title(), f"[{color}]{value}[/{color}]")

        console.print(table)
        console.print()

    # Workflow details
    if workflows:
        tree = Tree("[bold]Workflow Changes[/bold]")

        for wf in workflows:
            wf_name = wf.get("workflow_name", "unknown")
            wf_id = wf.get("workflow_id")
            wf_action = wf.get("action", "unchanged")
            wf_changes = wf.get("changes", {})
            tasks = wf.get("tasks", [])

            color, symbol = get_action_style(wf_action)
            wf_label = f"[{color}][{symbol}] {wf_name}[/{color}]"
            if wf_id:
                wf_label += f" [dim](id: {wf_id})[/dim]"

            wf_branch = tree.add(wf_label)

            # Show workflow field changes
            if wf_changes and verbose:
                changes_branch = wf_branch.add("[dim]Field changes:[/dim]")
                for field, change in wf_changes.items():
                    if isinstance(change, dict) and "old" in change and "new" in change:
                        changes_branch.add(
                            f"[cyan]{field}[/cyan]: "
                            f"[red]{change['old']}[/red] → [green]{change['new']}[/green]"
                        )
                    else:
                        changes_branch.add(f"[cyan]{field}[/cyan]: {change}")

            # Show tasks
            if tasks:
                for task in tasks:
                    task_id = task.get("task_id", "unknown")
                    task_name = task.get("task_name", task_id)
                    task_action = task.get("action", "unchanged")
                    task_changes = task.get("changes", {})

                    t_color, t_symbol = get_action_style(task_action)
                    task_label = f"[{t_color}][{t_symbol}] {task_name}[/{t_color}]"
                    if task_id != task_name:
                        task_label += f" [dim](id: {task_id})[/dim]"

                    task_branch = wf_branch.add(task_label)

                    # Show task field changes
                    if task_changes and verbose:
                        for field, change in task_changes.items():
                            if isinstance(change, dict) and "old" in change and "new" in change:
                                task_branch.add(
                                    f"[cyan]{field}[/cyan]: "
                                    f"[red]{change['old']}[/red] → [green]{change['new']}[/green]"
                                )
                            else:
                                task_branch.add(f"[cyan]{field}[/cyan]: {change}")

        console.print(tree)

    # Legend
    console.print()
    console.print(
        "[dim]Legend: [green][+] create[/green] | "
        "[yellow][~] update[/yellow] | "
        "[red][-] delete[/red] | "
        "[=] unchanged[/dim]"
    )


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

    console.print(f"\n[bold]Computing diff...[/bold]")
    console.print(f"[dim]Bundle: {bundle_name} | Environment: {env}[/dim]")

    client = BundleClient(config.api_url, config.session)

    # Find bundle by name
    bundle = client.get_bundle_by_name(bundle_name)
    if not bundle:
        console.print(
            f"\n[red]Error:[/red] Bundle '{bundle_name}' not found. Run [cyan]fdpbundle import[/cyan] first."
        )
        raise SystemExit(1)

    result = client.diff(bundle["id"], env)

    if not result.get("success"):
        console.print(f"\n[red]✗ Diff Failed[/red]")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    data = result.get("data", {})
    display_diff_result(data, config.verbose)
    raise SystemExit(0)
