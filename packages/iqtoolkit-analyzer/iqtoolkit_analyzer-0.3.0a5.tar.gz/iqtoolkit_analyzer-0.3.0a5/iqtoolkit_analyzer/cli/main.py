"""Main CLI entry point for iqtoolkit-analyzer"""

import logging

import click

from ..__version__ import __version__

# Import CLI command groups
from .mongodb_commands import mongodb_group
from .pg_commands import postgresql_group

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@click.group(invoke_without_command=False)
@click.version_option(version=__version__, prog_name="iqtoolkit-analyzer")
def cli() -> None:
    """
    iqtoolkit-analyzer: Database analysis and optimization toolkit

    Use 'iqtoolkit-analyzer --help' to see all available commands.
    """
    pass


# Register command groups
cli.add_command(postgresql_group)
cli.add_command(mongodb_group)


def main() -> None:
    """Entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()
