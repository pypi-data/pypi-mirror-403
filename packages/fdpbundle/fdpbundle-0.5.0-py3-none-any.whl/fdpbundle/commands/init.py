"""Init command - Initialize a new FDP bundles project."""

import os
import shutil
from importlib import resources

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command()
@click.argument("project_name", default="fdp-bundles")
@click.option(
    "--force", "-f", is_flag=True, help="Overwrite existing directory if it exists"
)
def init(project_name: str, force: bool):
    """Initialize a new FDP bundles project.

    Creates a new project directory with example bundle, GitLab CI config,
    and README documentation.

    \b
    Example:
      fdpbundle init my-project
      fdpbundle init  # Uses default name 'fdp-bundles'
    """
    project_path = os.path.abspath(project_name)

    if os.path.exists(project_path):
        if not force:
            console.print(
                f"[red]Error:[/red] Directory '{project_name}' already exists. "
                "Use --force to overwrite."
            )
            raise SystemExit(1)
        console.print(f"[yellow]Warning:[/yellow] Removing existing directory '{project_name}'")
        shutil.rmtree(project_path)

    console.print(f"\n[bold blue]Initializing FDP Bundle project:[/bold blue] {project_name}\n")

    # Create directory structure
    dirs_to_create = [
        project_path,
        os.path.join(project_path, "bundles"),
        os.path.join(project_path, "bundles", "example"),
    ]

    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        console.print(f"  [green]✓[/green] Created {os.path.relpath(dir_path, os.getcwd())}/")

    # Copy template files
    try:
        # Use importlib.resources to get template files
        template_package = "fdpbundle.templates"
        
        # Copy bundle.json
        with resources.files(template_package).joinpath("bundle.json").open("r") as f:
            bundle_content = f.read()
        bundle_path = os.path.join(project_path, "bundles", "example", "bundle.json")
        with open(bundle_path, "w", encoding="utf-8") as f:
            f.write(bundle_content)
        console.print(f"  [green]✓[/green] Created bundles/example/bundle.json")

        # Copy .gitlab-ci.yml
        with resources.files(template_package).joinpath("gitlab-ci.yml").open("r") as f:
            gitlab_ci_content = f.read()
        gitlab_ci_path = os.path.join(project_path, ".gitlab-ci.yml")
        with open(gitlab_ci_path, "w", encoding="utf-8") as f:
            f.write(gitlab_ci_content)
        console.print(f"  [green]✓[/green] Created .gitlab-ci.yml")

        # Copy README.md
        with resources.files(template_package).joinpath("README.md").open("r") as f:
            readme_content = f.read()
        readme_path = os.path.join(project_path, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        console.print(f"  [green]✓[/green] Created README.md")

        # Create .gitignore
        with resources.files(template_package).joinpath("gitignore").open("r") as f:
            gitignore_content = f.read()
        gitignore_path = os.path.join(project_path, ".gitignore")
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        console.print(f"  [green]✓[/green] Created .gitignore")

        # Create .env.example
        with resources.files(template_package).joinpath("env.example").open("r") as f:
            env_content = f.read()
        env_path = os.path.join(project_path, ".env.example")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        console.print(f"  [green]✓[/green] Created .env.example")

    except Exception as e:
        console.print(f"[red]Error copying templates:[/red] {e}")
        raise SystemExit(1)

    # Print success message
    console.print()
    console.print(
        Panel.fit(
            f"""[bold green]Project initialized successfully![/bold green]

[bold]Next steps:[/bold]

  1. [cyan]cd {project_name}[/cyan]
  2. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan] and configure your credentials
  3. Edit [cyan]bundles/example/bundle.json[/cyan] or create new bundles
  4. Initialize git and push to GitLab:
     [dim]git init && git add . && git commit -m "Initial commit"[/dim]

[bold]Useful commands:[/bold]

  [cyan]fdpbundle validate bundles/example/bundle.json[/cyan]  - Validate bundle
  [cyan]fdpbundle deploy bundles/example/bundle.json --env dev[/cyan] - Deploy to dev
  [cyan]fdpbundle deploy bundles/example/bundle.json --env dev --dry-run[/cyan] - Dry run""",
            title="[bold blue]FDP Bundle CLI[/bold blue]",
            border_style="blue",
        )
    )
