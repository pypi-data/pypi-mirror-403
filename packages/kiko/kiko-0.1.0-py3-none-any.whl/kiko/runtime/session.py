"""Session logging helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionInfo:
    """Metadata for a persisted session."""

    session_id: str
    project_id: str
    project_path: Path
    path: Path


class SessionRecorder:
    """Append-only JSONL session recorder."""

    def __init__(self, info: SessionInfo):
        """Initialize the recorder with session metadata."""
        self.info = info

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Append a session event entry."""
        entry = {
            'type': event_type,
            'session_id': self.info.session_id,
            'project_id': self.info.project_id,
            'project_path': self.info.project_path.as_posix(),
            **payload,
        }
        self._append(entry)

    def record_message(self, message: dict[str, Any]) -> None:
        """Append a message entry."""
        entry = {
            'type': 'message',
            'session_id': self.info.session_id,
            'project_id': self.info.project_id,
            **message,
        }
        self._append(entry)

    def load_messages(self) -> list[dict[str, Any]]:
        """Load message entries from the session file.

        Returns:
            A list of message entries from the session log.
        """
        messages: list[dict[str, Any]] = []
        if not self.info.path.exists():
            return messages
        with open(self.info.path, encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get('type') == 'message':
                    data.pop('type', None)
                    data.pop('session_id', None)
                    data.pop('project_id', None)
                    messages.append(data)
        return messages

    def _append(self, entry: dict[str, Any]) -> None:
        with open(self.info.path, 'a', encoding='utf-8') as handle:
            json.dump(entry, handle, ensure_ascii=True)
            handle.write('\n')
