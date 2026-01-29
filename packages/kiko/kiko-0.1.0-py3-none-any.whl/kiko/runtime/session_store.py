"""Session storage operations."""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from kiko.runtime.project import ProjectInfo, get_project_info
from kiko.runtime.session import SessionInfo, SessionRecorder
from kiko.runtime.session_state import SessionState
from kiko.runtime.version import get_app_version

SESSION_ID_LENGTH = 12


def _ensure_sessions_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _hash_session(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:SESSION_ID_LENGTH]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class SessionStore:
    """Create, resume, and list session logs for a project."""

    def __init__(self, project: ProjectInfo):
        """Initialize the store for a project.

        Args:
            project: Project metadata.
        """
        self.project = project

    @classmethod
    def for_current_project(cls) -> SessionStore:
        """Create a store bound to the current project.

        Returns:
            A session store scoped to the current project.
        """
        return cls(get_project_info())

    def start_new(self) -> SessionRecorder:
        """Create a new session log and return a recorder.

        Returns:
            A recorder bound to the new session.
        """
        _ensure_sessions_dir(self.project.sessions_dir)
        seed = (
            f'{self.project.project_id}:{_now_iso()}:{os.getpid()}:'
            f'{uuid.uuid4().hex}'
        )
        session_id = _hash_session(seed)
        info = SessionInfo(
            session_id=session_id,
            project_id=self.project.project_id,
            project_path=self.project.root_path,
            path=self.session_path(session_id),
        )
        recorder = SessionRecorder(info)
        recorder.record_event(
            'session_start',
            {
                'started_at': _now_iso(),
                'app_version': get_app_version(),
            },
        )
        return recorder

    def start_new_state(self) -> SessionState:
        """Create a new session and return session state.

        Returns:
            A session state bound to the new session.
        """
        return SessionState.from_recorder(self.start_new())

    def resume(self, session_id: str) -> SessionRecorder:
        """Resume an existing session.

        Args:
            session_id: Session identifier to resume.

        Returns:
            A recorder bound to the resumed session.

        Raises:
            FileNotFoundError: If the session file does not exist.
        """
        path = self.session_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f'Session not found: {session_id}')
        info = SessionInfo(
            session_id=session_id,
            project_id=self.project.project_id,
            project_path=self.project.root_path,
            path=path,
        )
        recorder = SessionRecorder(info)
        recorder.record_event(
            'session_resume',
            {
                'resumed_at': _now_iso(),
                'app_version': get_app_version(),
            },
        )
        return recorder

    def resume_state(self, session_id: str) -> SessionState:
        """Resume a session and return session state.

        Args:
            session_id: Session identifier to resume.

        Returns:
            A session state bound to the resumed session.

        """
        return SessionState.from_recorder(self.resume(session_id))

    def list_sessions(self) -> list[str]:
        """List session IDs for the current project.

        Returns:
            A list of session identifiers for the current project.
        """
        if not self.project.sessions_dir.exists():
            return []
        sessions = [
            path.stem
            for path in self.project.sessions_dir.iterdir()
            if path.is_file() and path.suffix == '.jsonl'
        ]
        sessions.sort()
        return sessions

    def session_path(self, session_id: str) -> Path:
        """Resolve the session log path for an identifier.

        Args:
            session_id: Session identifier.

        Returns:
            Path to the session log.
        """
        return self.project.sessions_dir / f'{session_id}.jsonl'
