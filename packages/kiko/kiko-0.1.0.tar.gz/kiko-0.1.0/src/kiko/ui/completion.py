"""Command auto-completion helpers."""

from prompt_toolkit.completion import Completer, Completion

from kiko.runtime.command_spec import CommandSpec


class CommandCompleter(Completer):
    """Completion provider for slash-prefixed commands."""

    def __init__(self, commands: dict[str, CommandSpec]):
        """Store command metadata for completions."""
        self.commands = commands

    def get_completions(self, document, _complete_event):
        """Yield completions for the current input buffer."""
        text = document.text_before_cursor

        # Only complete when the input starts with "/".
        if text.startswith('/'):
            cmd_prefix = text[1:].strip()

            for cmd_name, cmd_info in self.commands.items():
                if cmd_name.startswith(cmd_prefix):
                    help_text = cmd_info.help
                    display_text = (
                        f'{cmd_name} - {help_text}' if help_text else cmd_name
                    )

                    yield Completion(
                        cmd_name,
                        start_position=-len(cmd_prefix),
                        display=display_text,
                    )
