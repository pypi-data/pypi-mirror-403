"""Configuration loading, migration, and persistence."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / '.config' / 'kiko'
CONFIG_FILE = CONFIG_DIR / 'config.json'

SCHEMA_VERSION = 1
DEFAULT_CONFIG: dict[str, Any] = {
    'schema_version': SCHEMA_VERSION,
    'last_seen_app_version': None,
    'last_session_by_project': {},
    'help_view': 'detailed',
}

Migration = Callable[[dict[str, Any]], dict[str, Any]]
MIGRATIONS: dict[int, Migration] = {}


@dataclass(frozen=True)
class ConfigStore:
    """Filesystem-backed configuration storage."""

    config_dir: Path = CONFIG_DIR
    config_file: Path = CONFIG_FILE
    now: Callable[[], datetime] = datetime.now

    def read(self) -> dict[str, Any]:
        """Read configuration data from disk.

        Returns:
            Parsed configuration data.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, encoding='utf-8') as handle:
                content = handle.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            self._backup_corrupt()
            return {}

    def write(self, config: dict[str, Any]) -> None:
        """Persist configuration data to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_file.with_suffix(
            self.config_file.suffix + '.tmp'
        )
        with open(tmp_path, 'w', encoding='utf-8') as handle:
            json.dump(config, handle, indent=2, sort_keys=True)
            handle.write('\n')
        tmp_path.replace(self.config_file)

    def _backup_corrupt(self) -> None:
        timestamp = self.now().strftime('%Y%m%d%H%M%S')
        backup = self.config_file.with_name(
            f'{self.config_file.name}.bak-{timestamp}'
        )
        try:
            self.config_file.replace(backup)
        except OSError:
            pass


def _merge_defaults(config: dict[str, Any]) -> dict[str, Any]:
    return {**DEFAULT_CONFIG, **config}


def _migrate_config(config: dict[str, Any]) -> dict[str, Any]:
    version = int(config.get('schema_version', 0) or 0)
    while version < SCHEMA_VERSION:
        migrator = MIGRATIONS.get(version)
        if migrator is not None:
            config = migrator(config)
        version += 1
    config['schema_version'] = SCHEMA_VERSION
    return config


def _load_config(
    current_version: str, store: ConfigStore
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = store.read()
    config = _merge_defaults(raw)
    config = _migrate_config(config)
    if not config.get('last_seen_app_version'):
        config['last_seen_app_version'] = current_version
    return raw, config


def load_settings(
    current_version: str, store: ConfigStore | None = None
) -> Settings:
    """Load settings for the current app version.

    Args:
        current_version: Current application version.
        store: Optional configuration store override.

    Returns:
        Settings instance loaded from disk.
    """
    store = store or ConfigStore()
    raw, config = _load_config(current_version, store)
    if config != raw:
        store.write(config)
    return Settings(config, store)


class Settings:
    """Settings wrapper for persisted configuration."""

    def __init__(self, config: dict[str, Any], store: ConfigStore):
        """Initialize settings with a config dictionary."""
        self.config = config
        self._store = store

    def get(self, key: str, default: Any | None = None) -> Any:
        """Fetch a config value by key.

        Args:
            key: Config key to retrieve.
            default: Default value when missing.

        Returns:
            The configured value or default.
        """
        if default is None:
            return self.config[key]
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value and persist it."""
        self.config[key] = value
        self._store.write(self.config)

    def get_last_session(self, project_id: str) -> str | None:
        """Return the last session ID for a project.

        Args:
            project_id: Project identifier.

        Returns:
            The last session ID for the project, if available.
        """
        mapping = self.config.get('last_session_by_project', {})
        if isinstance(mapping, dict):
            value = mapping.get(project_id)
            return value if isinstance(value, str) else None
        return None

    def set_last_session(self, project_id: str, session_id: str) -> None:
        """Persist the last session ID for a project.

        Args:
            project_id: Project identifier.
            session_id: Session identifier to store.
        """
        mapping = self.config.get('last_session_by_project')
        if not isinstance(mapping, dict):
            mapping = {}
            self.config['last_session_by_project'] = mapping
        mapping[project_id] = session_id
        self._store.write(self.config)

    def mark_app_version(self, current_version: str) -> str | None:
        """Record the latest seen app version and return the previous one.

        Args:
            current_version: Version to store.

        Returns:
            The previously stored version, if any.
        """
        previous = self.config.get('last_seen_app_version')
        if previous != current_version:
            self.config['last_seen_app_version'] = current_version
            self._store.write(self.config)
        return previous
