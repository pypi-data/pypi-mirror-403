"""Runtime context passed to command handlers."""

from datetime import datetime
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import History

from kiko.runtime.renderer import Renderer
from kiko.runtime.session_state import SessionState
from kiko.runtime.settings import Settings


class Context:
    """Context passed to command execution."""

    def __init__(
        self,
        session: PromptSession,
        renderer: Renderer,
        history: History | None = None,
        session_state: SessionState | None = None,
    ):
        """Initialize the runtime context."""
        self.session = session
        self.history = history
        self.messages: list[dict[str, str]] = []
        self.session_state = session_state
        self.thinking_mode = False
        self.renderer = renderer
        self.settings: Settings | None = None

    def add_message(self, role: str, text: str) -> dict[str, str]:
        """Record a message entry in history.

        Args:
            role: Message role label.
            text: Message content.

        Returns:
            The stored message entry.
        """
        entry = {
            'role': role,
            'text': text,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
        }
        self.messages.append(entry)
        if self.session_state is not None:
            self.session_state.recorder.record_message(entry)
        return entry

    def emit(
        self,
        role: str,
        text: str,
        *,
        render: Any | None = None,
        print_text: str | None = None,
    ) -> dict[str, str]:
        """Add a message and render it via the configured renderer.

        Args:
            role: Message role label.
            text: Message content.
            render: Rich renderable to print.
            print_text: Markup string to print.

        Returns:
            The stored message entry.
        """
        entry = self.add_message(role, text)
        self.renderer.render(
            role=role,
            text=text,
            render=render,
            print_text=print_text,
        )
        return entry

    def set_session_state(self, session_state: SessionState | None) -> None:
        """Attach session state to the context."""
        self.session_state = session_state

    def set_settings(self, settings: Settings | None) -> None:
        """Attach settings to the context."""
        self.settings = settings

    def replace_messages(self, messages: list[dict[str, str]]) -> None:
        """Replace the in-memory message history."""
        self.messages = list(messages)

    def toggle_thinking_mode(self) -> bool:
        """Toggle thinking mode.

        Returns:
            The updated thinking mode state.
        """
        self.thinking_mode = not self.thinking_mode
        if self.session_state is not None:
            self.session_state.recorder.record_event(
                'thinking_mode',
                {
                    'enabled': self.thinking_mode,
                    'changed_at': datetime.now().isoformat(timespec='seconds'),
                },
            )
        return self.thinking_mode
