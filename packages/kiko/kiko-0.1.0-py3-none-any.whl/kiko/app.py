"""CLI application and command dispatch loop."""

import asyncio
import shlex
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from kiko.runtime import Context, get_app_version
from kiko.runtime.command_spec import CommandSpec
from kiko.runtime.renderer import NullRenderer, Renderer, RichRenderer
from kiko.runtime.session_state import SessionState
from kiko.runtime.session_store import SessionStore
from kiko.runtime.settings import Settings, load_settings
from kiko.ui import components
from kiko.ui.completion import CommandCompleter

F = TypeVar('F', bound=Callable[..., Any])


class kikoApp:
    """CLI application state and command dispatcher."""

    def __init__(self):
        """Initialize the application state."""
        self.commands: dict[str, CommandSpec] = {}
        self.session: PromptSession = None
        self.history: InMemoryHistory | None = None
        self.context: Context = None
        self.should_exit: bool = False
        self.settings: Settings | None = None
        self.session_store: SessionStore | None = None
        self.session_state: SessionState | None = None
        self.renderer: Renderer = NullRenderer()

    def command(
        self,
        name: str | None = None,
        help: str = '',
        *,
        category: str | None = None,
        usage: str | None = None,
        example: str | None = None,
    ) -> Callable[[F], F]:
        """Register a command handler.

        Args:
            name: Optional command name override.
            help: Help text to expose in `/help`.
            category: Optional command category label.
            usage: Optional usage string.
            example: Optional example string.

        Returns:
            A decorator that registers the command function.
        """

        def decorator(func: F) -> F:
            cmd_name = (name or func.__name__).lower()

            self.commands[cmd_name] = CommandSpec.from_func(
                func,
                help,
                category=category,
                usage=usage,
                example=example,
            )
            return func

        return decorator

    def request_exit(self) -> None:
        """Request exit after the current command completes."""
        self.should_exit = True

    def command_manifest(self) -> list[dict[str, Any]]:
        """Return a sorted list of command metadata.

        Returns:
            A list of command metadata dictionaries.
        """
        items = sorted(self.commands.items())
        manifest: list[dict[str, Any]] = []
        for name, info in items:
            manifest.append(
                {
                    'name': name,
                    'help': info.help,
                    'category': info.category,
                    'usage': info.usage,
                    'example': info.example,
                    'is_async': info.is_async,
                }
            )
        return manifest

    def resume_session(self, session_id: str) -> int:
        """Resume a session and return the number of loaded messages.

        Args:
            session_id: Session identifier to resume.

        Returns:
            The number of messages loaded into the context.
        """
        store = self.session_store or SessionStore.for_current_project()
        messages = self._resume_session_state(store, session_id)
        return len(messages)

    def _resume_session_state(
        self, store: SessionStore, session_id: str
    ) -> list[dict[str, str]]:
        """Resume a session and return loaded messages.

        Args:
            store: Session store for the current project.
            session_id: Session identifier to resume.

        Returns:
            Loaded message entries for the session.
        """
        session_state = store.resume_state(session_id)
        messages = session_state.recorder.load_messages()
        self.session_store = store
        self.session_state = session_state
        if self.context is not None:
            self.context.set_session_state(self.session_state)
            self.context.replace_messages(messages)
        return messages

    def _init_runtime(self, resume_session_id: str | None) -> None:
        """Initialize UI and session state for a run.

        Args:
            resume_session_id: Optional session to resume.
        """
        self.renderer = RichRenderer.create()
        style = Style.from_dict({'prompt': 'ansicyan bold'})
        key_bindings = KeyBindings()

        @key_bindings.add('tab')
        def _toggle_thinking(event):  # noqa: ANN001
            if self.context is None:
                return
            if event.app.current_buffer.text.strip():
                event.app.current_buffer.complete_next()
                return
            enabled = self.context.toggle_thinking_mode()
            state = 'ON' if enabled else 'OFF'

            def _notify() -> None:
                self.renderer.render(
                    role='system',
                    text=f'Thinking mode: {state}',
                    render=None,
                    print_text=f'[dim]Thinking mode: {state}[/]',
                )

            run_in_terminal(_notify)
            event.app.invalidate()

        # Configure command auto-completion.
        completer = CommandCompleter(self.commands)
        self.history = InMemoryHistory()
        self.session = PromptSession(
            style=style,
            completer=completer,
            complete_while_typing=True,
            history=self.history,
            key_bindings=key_bindings,
        )

        self.session_store = SessionStore.for_current_project()
        if resume_session_id:
            messages = self._resume_session_state(
                self.session_store, resume_session_id
            )
        else:
            self.session_state = self.session_store.start_new_state()
            messages = []

        self.context = Context(
            self.session,
            self.renderer,
            history=self.history,
            session_state=self.session_state,
        )
        if messages:
            self.context.replace_messages(messages)

    def _prepare_run(self, show_banner: bool) -> None:
        """Load settings and optionally render the banner.

        Args:
            show_banner: Whether to print the header UI.
        """
        current_version = get_app_version()
        self.settings = load_settings(current_version)
        if self.context is not None:
            self.context.set_settings(self.settings)
        if show_banner:
            self.renderer.render(
                role='system',
                text='',
                render=components.render_header(
                    current_version, str(Path.cwd())
                ),
                print_text=None,
            )
            if self.session_state is not None:
                self.renderer.render(
                    role='system',
                    text=f'Session ID: {self.session_state.session_id}',
                    render=None,
                    print_text=(
                        f'[dim]Session ID:[/] {self.session_state.session_id}'
                    ),
                )
        if self.settings is not None:
            self.settings.mark_app_version(current_version)
        self._record_last_session()

    def _record_last_session(self) -> None:
        """Persist the last session ID for the current project."""
        if self.settings is None or self.session_state is None:
            return
        self.settings.set_last_session(
            self.session_state.project_id, self.session_state.session_id
        )

    def _prompt_text(self) -> str:
        """Build the prompt string based on the current mode.

        Returns:
            The prompt string.
        """
        if self.context is None:
            return 'kiko> '
        suffix = ' (thinking)' if self.context.thinking_mode else ''
        return f'kiko{suffix}> '

    async def run(self):
        """Run the interactive prompt loop."""
        self._init_runtime(None)
        self._prepare_run(show_banner=True)
        await self._run_loop()

    async def run_with_resume(self, session_id: str) -> None:
        """Run the interactive prompt loop resuming a session.

        Args:
            session_id: Session identifier to resume.
        """
        self._init_runtime(session_id)
        self._prepare_run(show_banner=True)
        await self._run_loop()

    async def run_once(
        self, user_input: str, resume_session_id: str | None = None
    ) -> None:
        """Process a single input and exit.

        Args:
            user_input: Input text or command.
            resume_session_id: Optional session to resume.
        """
        self._init_runtime(resume_session_id)
        self._prepare_run(show_banner=False)
        cleaned = user_input.strip()
        if not cleaned:
            return
        await self.handle_input(cleaned)

    async def _run_loop(self) -> None:
        """Run the main interactive loop."""
        while True:
            try:
                user_input = await self.session.prompt_async(self._prompt_text)
                user_input = user_input.strip()

                if not user_input:
                    continue

                await self.handle_input(user_input)
                if self.should_exit:
                    break

            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                self.renderer.render(
                    role='system',
                    text=f'Unexpected Error: {e}',
                    render=None,
                    print_text=f'[bold red]Unexpected Error:[/] {e}',
                )

        self.renderer.render(
            role='system',
            text='Shutting down...',
            render=None,
            print_text='[bold yellow]Shutting down...[/]',
        )

    async def handle_input(self, user_input: str):
        """Parse and dispatch a single input line."""
        if user_input.startswith('/'):
            parts = shlex.split(user_input[1:])
            if not parts:
                self.context.emit(
                    'system',
                    'No command provided. Try /help.',
                    print_text='[yellow]No command provided. Try /help.[/]',
                )
                return
            cmd_name = parts[0]
            args = parts[1:]

            if cmd_info := self.commands.get(cmd_name):
                if cmd_info.is_async:
                    await cmd_info.func(self.context, args)
                else:
                    cmd_info.func(self.context, args)
            else:
                self.context.emit(
                    'system',
                    f'Unknown command: {cmd_name}',
                    print_text=f'[red]Unknown command:[/red] {cmd_name}',
                )
        else:
            await self.process_agent_message(user_input)

    async def process_agent_message(self, message: str):
        """Handle non-command user input."""
        # TODO: LLM Processing Logic
        self.context.add_message('user', message)
        with self.renderer.status('[bold green]Thinking...[/]'):
            await asyncio.sleep(0.5)  # Mock
            response = f'Echo: {message}'
            self.context.emit(
                'assistant', response, print_text=f'[dim]{response}[/]'
            )


# Global Instance
app = kikoApp()
