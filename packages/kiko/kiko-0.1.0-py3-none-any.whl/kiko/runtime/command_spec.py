"""Command registration metadata."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommandSpec:
    """Metadata for a registered command."""

    func: Callable[..., Any]
    help: str
    is_async: bool
    category: str | None = None
    usage: str | None = None
    example: str | None = None

    @classmethod
    def from_func(
        cls,
        func: Callable[..., Any],
        help_text: str,
        *,
        category: str | None = None,
        usage: str | None = None,
        example: str | None = None,
    ) -> CommandSpec:
        """Build a command spec from a handler function.

        Args:
            func: Command handler function.
            help_text: Help text for the command.
            category: Optional command category label.
            usage: Optional usage string.
            example: Optional example string.

        Returns:
            A populated CommandSpec instance.
        """
        return cls(
            func=func,
            help=help_text,
            is_async=asyncio.iscoroutinefunction(func),
            category=category,
            usage=usage,
            example=example,
        )
