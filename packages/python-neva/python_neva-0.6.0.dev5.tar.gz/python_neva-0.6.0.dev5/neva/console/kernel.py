"""Defines the CLI kernel."""

import asyncio
from functools import wraps
from typing import Any, Callable, override
from typer import Typer
from typer.core import click

from typer.models import CommandFunctionType

from neva.arch import Application


class Kernel(Typer):
    """CLI kernel."""

    def __init__(
        self,
        callback: Callable[..., Any] | None = None,
    ) -> None:
        """Initialize the CLI kernel."""
        super().__init__(callback=callback)

    @override
    def command(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        base_decorator = super().command(*args, **kwargs)

        def decorator(f: CommandFunctionType) -> CommandFunctionType:
            @wraps(f)
            def wrapper(*f_args: Any, **f_kwargs: Any) -> Any:  # noqa: ANN401
                ctx = click.get_current_context()
                config_path = ctx.obj.get("config_path", None)
                app = Application(config_path)

                async def runner() -> Any:  # noqa: ANN401
                    async with app.lifespan():
                        return f(*f_args, **f_kwargs)

                return asyncio.run(runner())

            return base_decorator(wrapper)

        return decorator
