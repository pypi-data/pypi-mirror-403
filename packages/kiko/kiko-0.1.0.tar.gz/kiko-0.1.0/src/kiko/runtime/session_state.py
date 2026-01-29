"""Session state metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kiko.runtime.session import SessionRecorder


@dataclass(frozen=True)
class SessionState:
    """State for the current session."""

    recorder: SessionRecorder
    session_id: str
    project_id: str
    project_path: Path

    @classmethod
    def from_recorder(cls, recorder: SessionRecorder) -> SessionState:
        """Build a session state from a recorder.

        Args:
            recorder: Session recorder instance.

        Returns:
            A session state initialized from the recorder.
        """
        return cls(
            recorder=recorder,
            session_id=recorder.info.session_id,
            project_id=recorder.info.project_id,
            project_path=recorder.info.project_path,
        )
