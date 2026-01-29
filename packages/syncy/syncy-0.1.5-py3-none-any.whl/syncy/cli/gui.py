from __future__ import annotations

import click

from .base import cli


@cli.command("gui")
def gui() -> None:
    """Launch the desktop GUI wrapper."""
    try:
        from ..gui.app import main as gui_main
    except Exception as exc:  # pragma: no cover - GUI-only failure
        raise click.ClickException(f"GUI not available: {exc}")
    gui_main()


__all__ = ["gui"]
