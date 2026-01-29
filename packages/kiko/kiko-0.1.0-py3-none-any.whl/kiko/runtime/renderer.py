# Copyright (c) 2026

"""Output rendering helpers."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from typing import Any, Protocol

from rich.console import Console


class Renderer(Protocol):
    """Renderer interface for emitting output."""

    def render(
        self,
        *,
        role: str,
        text: str,
        render: Any | None,
        print_text: str | None,
    ) -> None:
        """Render output for a message."""

    def clear(self) -> None:
        """Clear the output."""

    def status(self, message: str) -> AbstractContextManager[object]:
        """Return a status context manager."""


@dataclass(frozen=True)
class RichRenderer:
    """Renderer that prints to a Rich console."""

    console: Console

    @classmethod
    def create(cls) -> RichRenderer:
        """Create a renderer with a new Rich console.

        Returns:
            A configured RichRenderer instance.
        """
        return cls(Console())

    def render(
        self,
        *,
        role: str,
        text: str,
        render: Any | None = None,
        print_text: str | None = None,
    ) -> None:
        """Render output for a message."""
        _ = role
        if render is not None:
            self.console.print(render)
        elif print_text is not None:
            self.console.print(print_text)
        else:
            self.console.print(text)

    def clear(self) -> None:
        """Clear the console output."""
        self.console.clear()

    def status(self, message: str) -> AbstractContextManager[object]:
        """Return a status context manager."""
        return self.console.status(message)


@dataclass(frozen=True)
class NullRenderer:
    """Renderer that performs no output."""

    def render(
        self,
        *,
        role: str,
        text: str,
        render: Any | None = None,
        print_text: str | None = None,
    ) -> None:
        """Render output for a message."""
        _ = (role, text, render, print_text)

    def clear(self) -> None:
        """Clear the output."""

    def status(self, message: str) -> AbstractContextManager[object]:
        """Return a no-op status context manager."""
        _ = message
        return nullcontext()
