"""CLI runner."""

from typing import Annotated

import typer

from neva.console.kernel import Kernel


def set_config(
    ctx: typer.Context,
    config_path: Annotated[
        str,
        typer.Option(help="Sets the config path"),
    ] = "",
) -> None:
    """Set the configuration path."""
    ctx.obj = {"config_path": config_path}


app = Kernel(set_config)


def main() -> None:
    """Run the CLI."""
    app()
