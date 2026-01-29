"""Rich UI rendering helpers."""

from rich.box import ROUNDED
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# UI render helpers return Rich objects.


def _get_logo() -> Text:
    """Get the pixel art logo.

    Returns:
        Rendered logo text.
    """
    logo_lines = [
        '╭─────╮',
        '│ ◉ ◉ │',
        '│  ▽  │',
        '╰─────╯',
    ]
    return Text('\n'.join(logo_lines), style='bold #ff6b9d')


def render_header(version: str, current_path: str) -> Panel:
    """Render the CLI header panel.

    Args:
        version: Current app version string.
        current_path: Current working directory.

    Returns:
        Header panel for the CLI.
    """
    logo = _get_logo()

    title = Text.from_markup(f'[bold cyan]Project kiko[/] v{version}')
    current_path_text = Text.from_markup(
        f'[dim]Current Path:[/] {current_path}'
    )

    group = Group(title, current_path_text)

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify='center', vertical='middle')
    grid.add_column(justify='left', vertical='middle')
    grid.add_row(logo, group)

    return Panel(
        grid,
        box=ROUNDED,
        expand=False,
    )


def render_message(role: str, text: str) -> Panel:
    """Render a chat message panel.

    Args:
        role: Message role.
        text: Message content.

    Returns:
        A message panel renderable.
    """
    color = 'green' if role == 'user' else 'magenta'
    title = 'User' if role == 'user' else 'kiko Agent'

    # Render markdown content in the message body.
    content = Markdown(text)

    return Panel(
        content,
        title=f'[bold {color}]{title}[/]',
        border_style=color,
        expand=False,
        padding=(1, 2),
    )


def render_sysinfo(info_dict: dict) -> Table:
    """Render a system info table.

    Args:
        info_dict: Key-value pairs to render.

    Returns:
        A Rich table of system information.
    """
    table = Table(box=ROUNDED, show_header=False)
    for key, value in info_dict.items():
        table.add_row(f'[bold dim]{key}[/]', str(value))
    return table
