"""Declares all cli exceptions."""

from typing import TYPE_CHECKING

from click.globals import get_current_context

if TYPE_CHECKING:
    from cmem_cmemc.context import ApplicationContext


class CmemcError(ValueError):
    """Base exception for CMEM-CMEMC-related errors."""

    def __init__(self, message: str, app: "ApplicationContext | None" = None):
        super().__init__(message)
        if app is None:
            ctx = get_current_context(silent=True)
            if ctx and hasattr(ctx, "obj"):
                app = ctx.obj
        self.app = app


class InvalidConfigurationError(CmemcError):
    """The configuration given was not found or is broken."""


class ServerError(CmemcError):
    """The server reported an error with a process."""
