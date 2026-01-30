"""CLI module for iqtoolkit-analyzer"""

from .main import cli, main
from .pg_commands import postgresql_group

__all__ = ["cli", "main", "postgresql_group"]
