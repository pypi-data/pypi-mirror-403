"""Basic utility commands for the CLI."""

# commands/basic.py
import json
import platform
import sys
from datetime import datetime
from typing import Any

from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from kiko.app import app
from kiko.runtime.context import Context
from kiko.runtime.session_store import SessionStore


@app.command(
    help='Exit the application',
    category='core',
    usage='/exit',
    example='/exit',
)
def exit(ctx: Context, _args: list[Any]):
    """Exit the application."""
    ctx.add_message('system', 'Exit requested.')
    app.request_exit()


@app.command(
    help='Exit the application',
    category='core',
    usage='/quit',
    example='/quit',
)
def quit(ctx: Context, args: list[Any]):
    """Alias for /exit."""
    exit(ctx, args)


@app.command(
    help='Show help message',
    category='core',
    usage='/help',
    example='/help',
)
def help(ctx: Context, _args: list[Any]):
    """Show help for registered commands."""
    view = 'detailed'
    if ctx.settings is not None:
        view = ctx.settings.get('help_view', 'detailed')

    if view == 'compact':
        items = sorted(app.commands.items())
        entries = [f'/{name}: {info.help}' for name, info in items]
        display = '\n'.join(
            f'[bold cyan]/{name}[/]: {info.help}' for name, info in items
        )
        ctx.emit('system', '\n'.join(entries), print_text=display)
        return

    items = sorted(
        app.commands.items(),
        key=lambda item: (item[1].category or 'misc', item[0]),
    )
    grouped: dict[str, list[tuple[str, Any]]] = {}
    for name, info in items:
        category = info.category or 'misc'
        grouped.setdefault(category, []).append((name, info))

    detailed_entries: list[str] = []
    display_lines: list[str] = []
    for category in sorted(grouped):
        detailed_entries.append(f'[{category}]')
        display_lines.append(f'[bold]{category}[/]')
        for name, info in grouped[category]:
            detailed_entries.append(f'/{name}: {info.help}')
            display_lines.append(f'  [bold cyan]/{name}[/]: {info.help}')
            if info.usage:
                detailed_entries.append(f'  usage: {info.usage}')
                display_lines.append(f'  [dim]usage:[/] {info.usage}')
            if info.example:
                detailed_entries.append(f'  example: {info.example}')
                display_lines.append(f'  [dim]example:[/] {info.example}')

    ctx.emit(
        'system',
        '\n'.join(detailed_entries),
        print_text='\n'.join(display_lines),
    )


@app.command(
    help='List commands as JSON',
    category='core',
    usage='/commands [--pretty]',
    example='/commands --pretty',
)
def commands(ctx: Context, args: list[Any]):
    """List command metadata as JSON."""
    pretty = any(arg in ('--pretty', '-p') for arg in args)
    data = app.command_manifest()
    payload = json.dumps(data, indent=2 if pretty else None)
    render = Syntax(payload, 'json', word_wrap=True)
    ctx.emit('system', payload, render=render)


@app.command(
    help='Clear screen',
    category='ui',
    usage='/clear',
    example='/clear',
)
def clear(ctx: Context, _args: list[Any]):
    """Clear the console screen."""
    ctx.add_message('system', 'Screen cleared.')
    ctx.renderer.clear()


@app.command(
    help='Show current time',
    category='info',
    usage='/time',
    example='/time',
)
def time(ctx: Context, _args: list[Any]):
    """Show the current local time."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ctx.emit('system', f'Time: {now}', print_text=f'[bold green]{now}[/]')


@app.command(
    help='Show system information',
    category='info',
    usage='/sysinfo',
    example='/sysinfo',
)
def sysinfo(ctx: Context, _args: list[Any]):
    """Show system information for the host."""
    info = (
        f'- **System**: {platform.system()} {platform.release()}\n'
        f'- **Machine**: {platform.machine()}\n'
        f'- **Python**: {sys.version.split()[0]}\n'
    )
    ctx.emit(
        'system',
        info,
        render=Panel(Markdown(info), title='System Info', border_style='blue'),
    )


@app.command(
    help='Print message itself',
    category='core',
    usage='/echo <message>',
    example='/echo hello',
)
def echo(ctx: Context, args: list[Any]):
    """Echo the provided message."""
    if not args:
        ctx.emit(
            'system',
            'Usage: /echo <message>',
            print_text='[yellow]Usage: /echo <message>[/]',
        )
        return

    message = ' '.join(args)
    echo_text = f'Echo: {message}'
    ctx.emit('system', echo_text, print_text=f'[dim]{echo_text}[/]')


@app.command(
    help='Show current session information',
    category='session',
    usage='/session',
    example='/session',
)
def session(ctx: Context, _args: list[Any]):
    """Show the current session ID and project path."""
    if ctx.session_state is None:
        ctx.emit(
            'system',
            'Session not initialized.',
            print_text='[yellow]Session not initialized.[/]',
        )
        return
    session_id = ctx.session_state.session_id
    project_path = ctx.session_state.project_path
    details = f'Session ID: {session_id}\nProject: {project_path}'
    ctx.emit(
        'system',
        details,
        print_text=(
            f'[bold cyan]Session ID:[/] {session_id}\n'
            f'[dim]Project:[/] {project_path}'
        ),
    )


@app.command(
    help='List sessions for the current project',
    category='session',
    usage='/sessions',
    example='/sessions',
)
def sessions(ctx: Context, _args: list[Any]):
    """List available session IDs for the current project."""
    ids = SessionStore.for_current_project().list_sessions()
    if not ids:
        ctx.emit(
            'system',
            'No sessions found.',
            print_text='[yellow]No sessions found.[/]',
        )
        return
    listing = '\n'.join(ids)
    display = '\n'.join(f'[cyan]{item}[/]' for item in ids)
    ctx.emit('system', listing, print_text=display)


@app.command(
    help='Resume a session by ID',
    category='session',
    usage='/resume <session_id>',
    example='/resume 1234abcd',
)
def resume(ctx: Context, args: list[Any]):
    """Resume a previous session by its ID."""
    if not args:
        ctx.emit(
            'system',
            'Usage: /resume <session_id>',
            print_text='[yellow]Usage: /resume <session_id>[/]',
        )
        return
    session_id = args[0]
    try:
        count = app.resume_session(session_id)
    except FileNotFoundError:
        ctx.emit(
            'system',
            f'Session not found: {session_id}',
            print_text=f'[red]Session not found:[/] {session_id}',
        )
        return
    ctx.emit(
        'system',
        f'Resumed session {session_id} with {count} messages.',
        print_text=(f'[bold green]Resumed[/] {session_id} ({count} messages)'),
    )
