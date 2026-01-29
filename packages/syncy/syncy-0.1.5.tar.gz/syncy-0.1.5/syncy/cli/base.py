import click

from .. import __version__


@click.group()
@click.version_option(__version__, prog_name="syncy")
def cli() -> None:
    """Syncy CLI - Validate cross-engine DB migrations."""


__all__ = ["cli"]
