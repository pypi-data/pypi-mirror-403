"""Deploy command - Full deployment flow (validate -> import -> diff -> apply)."""

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..client import BundleClient, load_bundle_file
from .validate import display_validation_result
from .diff import display_diff_result
from .apply import display_apply_result

console = Console()


def require_api_config(api_url: str) -> None:
    """Check that API URL is configured."""
    if not api_url:
        console.print(
            "[red]Error:[/red] API URL required. "
            "Use --api-url or set WORKFLOW_ENGINE_URL environment variable."
        )
        raise SystemExit(1)


def print_step(step: int, total: int, message: str, status: str = "running"):
    """Print a step progress indicator."""
    icons = {
        "running": ("blue", "..."),
        "success": ("green", "✓"),
        "failed": ("red", "✗"),
    }
    color, icon = icons.get(status, ("white", "•"))
    console.print(f"\n[bold {color}][{step}/{total}] {icon} {message}[/bold {color}]")


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
def deploy(ctx, bundle_file: str, env: str, dry_run: bool):
    """Full deploy: validate -> import -> diff -> apply.

    Performs the complete deployment flow for a bundle.

    \b
    Example:
      fdpbundle deploy bundles/etl-pipeline/bundle.json --env dev
      fdpbundle deploy bundles/etl-pipeline/bundle.json --env prod --dry-run
    """
    config = ctx.obj
    require_api_config(config.api_url)

    # Load bundle file first
    try:
        spec = load_bundle_file(bundle_file)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise SystemExit(1)

    bundle_name = spec.get("bundle", {}).get("name", "unknown")

    # Print header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Bundle:[/bold] {bundle_name}\n"
            f"[bold]File:[/bold] {bundle_file}\n"
            f"[bold]Environment:[/bold] {env.upper()}\n"
            f"[bold]Dry Run:[/bold] {'Yes' if dry_run else 'No'}",
            title=f"[bold blue]Deploy to {env.upper()}[/bold blue]",
            border_style="blue",
        )
    )

    client = BundleClient(config.api_url, config.username, config.password)

    # ========== Step 1: Validate ==========
    print_step(1, 4, "Validating bundle...")

    result = client.validate(spec)
    validation_data = result.get("data", {})

    # Check if we have validation data (even on 400)
    if not validation_data:
        print_step(1, 4, "Validation request failed", "failed")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    is_valid = validation_data.get("is_valid", False)
    errors = validation_data.get("errors", [])
    warnings = validation_data.get("warnings", [])

    if not is_valid:
        print_step(1, 4, "Validation failed", "failed")
        display_validation_result(validation_data, config.verbose)
        raise SystemExit(1)

    print_step(1, 4, "Validation passed", "success")
    
    # Show summary
    if errors:
        console.print(f"  [red]Errors: {len(errors)}[/red]")
    if warnings:
        console.print(f"  [yellow]Warnings: {len(warnings)}[/yellow]")
        if config.verbose:
            for w in warnings:
                console.print(f"    [yellow]•[/yellow] {w.get('field', '-')}: {w.get('message', '-')}")

    # ========== Step 2: Import ==========
    print_step(2, 4, "Importing bundle...")

    result = client.import_bundle(spec)

    if not result.get("success") and not result.get("data"):
        print_step(2, 4, "Import failed", "failed")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    import_data = result.get("data", {})
    bundle_id = import_data.get("bundle_id")
    version_id = import_data.get("version_id")
    version_number = import_data.get("version_number")
    content_hash = import_data.get("content_hash", "")[:16]
    is_new_bundle = import_data.get("is_new_bundle", False)
    is_new_version = import_data.get("is_new_version", False)

    print_step(2, 4, "Import successful", "success")
    console.print(f"  Bundle ID: [cyan]{bundle_id}[/cyan] | Version: [cyan]{version_number}[/cyan]")
    console.print(f"  Version ID: [cyan]{version_id}[/cyan] | Hash: [dim]{content_hash}...[/dim]")
    
    if is_new_bundle:
        console.print(f"  [green]✦ New bundle created[/green]")
    elif is_new_version:
        console.print(f"  [yellow]✦ New version created[/yellow]")
    else:
        console.print(f"  [dim]✦ No changes (same content hash)[/dim]")

    # ========== Step 3: Diff ==========
    print_step(3, 4, f"Computing diff for {env.upper()}...")

    result = client.diff(bundle_id, env)

    if not result.get("success") and not result.get("data"):
        print_step(3, 4, "Diff failed", "failed")
        console.print(f"[red]Error:[/red] {result.get('error')}")
        raise SystemExit(1)

    diff_data = result.get("data", {})
    has_changes = diff_data.get("has_changes", False)
    summary = diff_data.get("summary", {})

    print_step(3, 4, "Diff computed", "success")
    
    if has_changes:
        console.print(f"  [yellow]⚡ Changes detected[/yellow]")
        # Show summary counts
        wf_create = summary.get("workflows_create", 0)
        wf_update = summary.get("workflows_update", 0)
        tasks_create = summary.get("tasks_create", 0)
        tasks_update = summary.get("tasks_update", 0)
        tasks_delete = summary.get("tasks_delete", 0)
        
        parts = []
        if wf_create:
            parts.append(f"[green]+{wf_create} wf[/green]")
        if wf_update:
            parts.append(f"[yellow]~{wf_update} wf[/yellow]")
        if tasks_create:
            parts.append(f"[green]+{tasks_create} tasks[/green]")
        if tasks_update:
            parts.append(f"[yellow]~{tasks_update} tasks[/yellow]")
        if tasks_delete:
            parts.append(f"[red]-{tasks_delete} tasks[/red]")
        
        if parts:
            console.print(f"  {', '.join(parts)}")
    else:
        console.print(f"  [dim]No changes detected[/dim]")

    # ========== Step 4: Apply ==========
    if dry_run:
        print_step(4, 4, "Dry run - showing diff details", "success")
        
        console.print()
        console.print(Panel.fit(
            "[bold cyan]Dry Run Complete[/bold cyan]\n"
            "No changes were applied. Review the diff below:",
            border_style="cyan",
        ))
        
        # Show detailed diff
        display_diff_result(diff_data, config.verbose)
    else:
        print_step(4, 4, f"Applying to {env.upper()}...")

        result = client.apply(bundle_id, env, dry_run=False)

        if not result.get("success") and not result.get("data"):
            print_step(4, 4, "Apply failed", "failed")
            console.print(f"[red]Error:[/red] {result.get('error')}")
            raise SystemExit(1)

        apply_data = result.get("data", {})
        print_step(4, 4, "Apply successful", "success")
        
        # Show apply summary
        created_wf = len(apply_data.get("created_workflows", []))
        updated_wf = len(apply_data.get("updated_workflows", []))
        unlinked_wf = len(apply_data.get("unlinked_workflows", []))
        created_tasks = len(apply_data.get("created_tasks", []))
        updated_tasks = len(apply_data.get("updated_tasks", []))
        deleted_tasks = len(apply_data.get("deleted_tasks", []))

        if created_wf:
            console.print(f"  [green]+{created_wf} workflow(s) created[/green]")
        if updated_wf:
            console.print(f"  [yellow]~{updated_wf} workflow(s) updated[/yellow]")
        if unlinked_wf:
            console.print(f"  [red]⊘{unlinked_wf} workflow(s) unlinked[/red]")
        if created_tasks:
            console.print(f"  [green]+{created_tasks} task(s) created[/green]")
        if updated_tasks:
            console.print(f"  [yellow]~{updated_tasks} task(s) updated[/yellow]")
        if deleted_tasks:
            console.print(f"  [red]-{deleted_tasks} task(s) deleted[/red]")

        total_changes = created_wf + updated_wf + unlinked_wf + created_tasks + updated_tasks + deleted_tasks
        if total_changes == 0:
            console.print(f"  [dim]No changes applied (already up to date)[/dim]")

    # ========== Final Summary ==========
    console.print()
    if dry_run:
        console.print(
            Panel.fit(
                f"[bold cyan]Dry run for {env.upper()} completed![/bold cyan]\n"
                f"Run without [cyan]--dry-run[/cyan] to apply changes.",
                border_style="cyan",
            )
        )
    else:
        console.print(
            Panel.fit(
                f"[bold green]✓ Deploy to {env.upper()} completed successfully![/bold green]",
                border_style="green",
            )
        )

    raise SystemExit(0)
