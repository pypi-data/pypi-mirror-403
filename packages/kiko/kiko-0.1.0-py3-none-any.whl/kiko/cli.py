# Copyright (c) 2026

"""Command-line interface for kiko."""

from __future__ import annotations

import asyncio

import typer

import kiko.commands  # noqa: F401
from kiko.app import app
from kiko.runtime import get_app_version, load_settings
from kiko.runtime.project import get_project_info

cli = typer.Typer(add_completion=False)


def _resolve_resume_id(resume: str | None) -> str | None:
    if resume is None or resume != 'last':
        return resume
    settings = load_settings(get_app_version())
    project = get_project_info()
    session_id = settings.get_last_session(project.project_id)
    if session_id is None:
        typer.secho(
            'No previous session found for this project.',
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(code=1)
    return session_id


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    resume: str | None = typer.Option(
        None,
        '--resume',
        help='Resume a session ID when launching the interactive UI.',
    ),
) -> None:
    """Launch the interactive CLI.

    Raises:
        Exit: When the requested session cannot be resumed.
    """
    if ctx.invoked_subcommand is not None:
        return
    try:
        resume_id = _resolve_resume_id(resume)
        if resume_id:
            asyncio.run(app.run_with_resume(resume_id))
        else:
            asyncio.run(app.run())
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


@cli.command()
def exec(
    message: str = typer.Argument(..., help='Message or /command to execute.'),
    resume: str | None = typer.Option(
        None,
        '--resume',
        help='Resume a session ID before executing the input.',
    ),
) -> None:
    """Execute a single input and exit.

    Raises:
        Exit: When the requested session cannot be resumed.
    """
    try:
        resume_id = _resolve_resume_id(resume)
        asyncio.run(app.run_once(message, resume_session_id=resume_id))
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


@cli.command()
def resume(session_id: str = typer.Argument(..., help='Session ID to resume.')):
    """Resume a session in the interactive UI.

    Raises:
        Exit: When the requested session cannot be resumed.
    """
    try:
        resume_id = _resolve_resume_id(session_id)
        if resume_id is None:
            typer.secho(
                'Session ID is required to resume.',
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        asyncio.run(app.run_with_resume(resume_id))
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
