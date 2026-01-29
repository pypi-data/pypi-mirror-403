"""Project identification helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / '.config' / 'kiko'
PROJECT_ID_LENGTH = 12


@dataclass(frozen=True)
class ProjectInfo:
    """Metadata for the current project."""

    root_path: Path
    project_id: str
    sessions_dir: Path


def _hash_value(value: str, length: int) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:length]


def find_project_root(start: Path | None = None) -> Path:
    """Find the project root based on common markers.

    Args:
        start: Optional starting directory.

    Returns:
        The resolved project root path.
    """
    cwd = (start or Path.cwd()).resolve()
    for parent in (cwd, *cwd.parents):
        if (
            (parent / '.kiko').exists()
            or (parent / '.git').exists()
            or (parent / 'pyproject.toml').exists()
        ):
            return parent
    return cwd


def project_id_for_path(path: Path) -> str:
    """Generate a stable project identifier for a path.

    Args:
        path: Project root path.

    Returns:
        A stable project identifier.
    """
    return _hash_value(path.as_posix(), PROJECT_ID_LENGTH)


def get_project_info(start: Path | None = None) -> ProjectInfo:
    """Resolve project metadata for the given start path.

    Args:
        start: Optional starting directory.

    Returns:
        Project metadata including root path and session directory.
    """
    root_path = find_project_root(start)
    project_id = project_id_for_path(root_path)
    sessions_dir = CONFIG_DIR / 'sessions' / project_id
    return ProjectInfo(
        root_path=root_path,
        project_id=project_id,
        sessions_dir=sessions_dir,
    )
