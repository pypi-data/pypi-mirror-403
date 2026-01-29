"""Deploy command - Full deployment flow (validate -> import -> diff -> apply)."""

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


def print_step(step: int, total: int, message: str):
    """Print a step progress indicator."""
    console.print(f"\n[bold blue][{step}/{total}][/bold blue] {message}")


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
    console.print(
        Panel.fit(
            f"""[bold]Bundle:[/bold] {bundle_file}
[bold]Environment:[/bold] {env.upper()}
[bold]Dry Run:[/bold] {dry_run}""",
            title=f"[bold blue]Deploying to {env.upper()}[/bold blue]",
            border_style="blue",
        )
    )

    client = BundleClient(config.api_url, config.session)

    # Step 1: Validate
    print_step(1, 4, "Validating bundle...")

    result = client.validate(spec)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="Validate Response"))

    if not result.get("success"):
        console.print("[red]✗ Validation request failed[/red]")
        console.print(f"  Error: {result.get('error')}")
        raise SystemExit(1)

    validation_data = result.get("data", {})
    if not validation_data.get("is_valid", False):
        console.print("[red]✗ Validation failed[/red]")
        errors = validation_data.get("errors", [])
        for error in errors:
            console.print(f"  [red]•[/red] {error}")
        raise SystemExit(1)

    console.print("[green]✓ Validation passed[/green]")
    warnings = validation_data.get("warnings", [])
    if warnings:
        console.print(f"  [yellow]Warnings: {len(warnings)}[/yellow]")

    # Step 2: Import
    print_step(2, 4, "Importing bundle...")

    result = client.import_bundle(spec)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="Import Response"))

    if not result.get("success"):
        console.print("[red]✗ Import failed[/red]")
        console.print(f"  Error: {result.get('error')}")
        raise SystemExit(1)

    import_data = result.get("data", {})
    bundle_id = import_data.get("bundle_id")
    version_number = import_data.get("version_number")
    is_new_bundle = import_data.get("is_new_bundle", False)
    is_new_version = import_data.get("is_new_version", False)

    console.print("[green]✓ Import successful[/green]")
    console.print(f"  Bundle ID: [cyan]{bundle_id}[/cyan], Version: [cyan]{version_number}[/cyan]")
    console.print(f"  New bundle: [cyan]{is_new_bundle}[/cyan], New version: [cyan]{is_new_version}[/cyan]")

    # Step 3: Diff
    print_step(3, 4, f"Computing diff for {env}...")

    result = client.diff(bundle_id, env)

    if config.verbose:
        console.print(Panel(JSON(json.dumps(result, default=str)), title="Diff Response"))

    if not result.get("success"):
        console.print("[red]✗ Diff failed[/red]")
        console.print(f"  Error: {result.get('error')}")
        raise SystemExit(1)

    diff_data = result.get("data", {})
    has_changes = diff_data.get("has_changes", False)
    summary = diff_data.get("summary", {})

    console.print(f"[green]✓ Diff computed[/green] (has_changes={has_changes})")
    if summary:
        console.print(f"  Summary: {summary}")

    # Step 4: Apply
    if dry_run:
        print_step(4, 4, "Dry run - skipping apply")
        console.print("[cyan]✓ Dry run completed[/cyan]")

        if has_changes:
            console.print("\n[bold]Diff details:[/bold]")
            console.print(Panel(JSON(json.dumps(diff_data, default=str)), title="Changes"))
    else:
        print_step(4, 4, f"Applying to {env}...")

        result = client.apply(bundle_id, env, dry_run=False)

        if config.verbose:
            console.print(Panel(JSON(json.dumps(result, default=str)), title="Apply Response"))

        if not result.get("success"):
            console.print("[red]✗ Apply failed[/red]")
            console.print(f"  Error: {result.get('error')}")
            raise SystemExit(1)

        apply_data = result.get("data", {})
        created = apply_data.get("created_workflows", [])
        updated = apply_data.get("updated_workflows", [])
        deleted = apply_data.get("deleted_workflows", [])

        console.print("[green]✓ Apply successful[/green]")
        console.print(f"  Created: [cyan]{len(created)}[/cyan], Updated: [cyan]{len(updated)}[/cyan], Deleted: [cyan]{len(deleted)}[/cyan]")

    # Print success footer
    console.print()
    console.print(
        Panel.fit(
            f"[bold green]Deploy to {env.upper()} completed![/bold green]",
            border_style="green",
        )
    )

    raise SystemExit(0)
