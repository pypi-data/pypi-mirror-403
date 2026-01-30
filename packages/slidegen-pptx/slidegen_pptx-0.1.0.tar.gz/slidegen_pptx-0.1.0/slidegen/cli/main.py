"""Main CLI entry point for SlideGen."""

import click

from slidegen.cli.build import build_cmd
from slidegen.cli.init import init_cmd
from slidegen.cli.layouts import layouts_cmd
from slidegen.cli.validate import validate_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="slidegen")
def cli() -> None:
    """SlideGen: AI-powered slide generation tool."""
    pass


cli.add_command(init_cmd, name="init")
cli.add_command(validate_cmd, name="validate")
cli.add_command(build_cmd, name="build")
cli.add_command(layouts_cmd, name="layouts")


if __name__ == "__main__":
    cli()

