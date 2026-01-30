"""Main CLI entry point for fdpbundle."""

import os
import sys

import click
from dotenv import load_dotenv
from rich.console import Console

from . import __version__
from .commands import apply, deploy, diff, import_cmd, init, validate

console = Console()


class Config:
    """Global configuration object passed to commands."""

    def __init__(self):
        self.api_url: str = ""
        self.session: str = ""
        self.verbose: bool = False


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option(
    "--api-url",
    envvar="WORKFLOW_ENGINE_URL",
    help="Workflow Engine API URL (env: WORKFLOW_ENGINE_URL)",
)
@click.option(
    "--session",
    envvar="WORKFLOW_ENGINE_SESSION",
    help="Airflow session cookie value (env: WORKFLOW_ENGINE_SESSION)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.version_option(version=__version__, prog_name="fdpbundle")
@click.pass_context
def main(ctx, api_url, session, verbose):
    """FDP Bundle CLI - Manage workflow bundles for FDP Workflow Engine.

    \b
    Examples:
      fdpbundle init my-project
      fdpbundle validate bundles/etl-pipeline/bundle.json
      fdpbundle deploy bundles/etl-pipeline/bundle.json --env dev
    """
    # Load .env file if present
    load_dotenv()

    # Re-read env vars after loading .env (click might have read them before)
    if not api_url:
        api_url = os.getenv("WORKFLOW_ENGINE_URL", "")
    if not session:
        session = os.getenv("WORKFLOW_ENGINE_SESSION", "")

    ctx.ensure_object(Config)
    ctx.obj.api_url = api_url
    ctx.obj.session = session
    ctx.obj.verbose = verbose


# Register commands
main.add_command(init.init)
main.add_command(validate.validate)
main.add_command(import_cmd.import_bundle)
main.add_command(diff.diff)
main.add_command(apply.apply)
main.add_command(deploy.deploy)


if __name__ == "__main__":
    main()
