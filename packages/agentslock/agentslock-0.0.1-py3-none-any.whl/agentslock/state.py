"""State tracking for managed outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentslock.exceptions import StateError
from agentslock.paths import Scope, get_state_path
from agentslock.util import directory_hash, ensure_dir, file_hash


@dataclass
class ManagedEntry:
    """A single managed output entry."""

    path: str
    hash: str
    entry_type: str = "file"  # file, directory, config_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "hash": self.hash,
            "type": self.entry_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManagedEntry:
        return cls(
            path=data["path"],
            hash=data["hash"],
            entry_type=data.get("type", "file"),
        )


@dataclass
class State:
    """State tracking for a lockfile."""

    lockfile: str
    managed: list[ManagedEntry] = field(default_factory=list)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "lockfile": self.lockfile,
            "managed": [m.to_dict() for m in self.managed],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> State:
        return cls(
            version=data.get("version", 1),
            lockfile=data["lockfile"],
            managed=[ManagedEntry.from_dict(m) for m in data.get("managed", [])],
        )

    def get_entry(self, path: str) -> ManagedEntry | None:
        for entry in self.managed:
            if entry.path == path:
                return entry
        return None

    def add_entry(self, path: str, hash_value: str, entry_type: str = "file") -> None:
        existing = self.get_entry(path)
        if existing:
            existing.hash = hash_value
            existing.entry_type = entry_type
        else:
            self.managed.append(ManagedEntry(path=path, hash=hash_value, entry_type=entry_type))

    def remove_entry(self, path: str) -> bool:
        for i, entry in enumerate(self.managed):
            if entry.path == path:
                self.managed.pop(i)
                return True
        return False

    def list_paths(self) -> list[str]:
        return [e.path for e in self.managed]


class StateManager:
    """Manages state tracking for managed outputs."""

    def __init__(
        self, scope: Scope, project_root: Path | None = None, lockfile_path: Path | None = None
    ):
        self.scope = scope
        self.project_root = project_root or Path.cwd()
        self.state_path = get_state_path(scope, project_root)
        self.lockfile_path = lockfile_path

    def load(self) -> State:
        if not self.state_path.exists():
            return State(lockfile=str(self.lockfile_path or ""))

        try:
            data = json.loads(self.state_path.read_text())
            return State.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            raise StateError(f"Failed to load state: {e}")

    def save(self, state: State) -> None:
        ensure_dir(self.state_path.parent)
        self.state_path.write_text(json.dumps(state.to_dict(), indent=2))

    def compute_hash(self, path: Path) -> str:
        if path.is_dir():
            return directory_hash(path)
        return file_hash(path)

    def is_managed(self, path: Path) -> bool:
        state = self.load()
        return state.get_entry(str(path.resolve())) is not None

    def has_drift(self, path: Path) -> bool:
        state = self.load()
        entry = state.get_entry(str(path.resolve()))
        if entry is None:
            return False
        if not path.exists():
            return True
        current_hash = self.compute_hash(path)
        return current_hash != entry.hash

    def get_drifted(self) -> list[tuple[str, str | None]]:
        state = self.load()
        drifted = []
        for entry in state.managed:
            path = Path(entry.path)
            if not path.exists():
                drifted.append((entry.path, None))
            else:
                current = self.compute_hash(path)
                if current != entry.hash:
                    drifted.append((entry.path, current))
        return drifted

    def record(self, path: Path, entry_type: str = "file") -> None:
        state = self.load()
        hash_value = self.compute_hash(path) if path.exists() else ""
        state.add_entry(str(path.resolve()), hash_value, entry_type)
        self.save(state)

    def unrecord(self, path: Path) -> bool:
        state = self.load()
        removed = state.remove_entry(str(path.resolve()))
        if removed:
            self.save(state)
        return removed

    def cleanup_missing(self) -> list[str]:
        state = self.load()
        removed = []
        new_managed = []
        for entry in state.managed:
            if Path(entry.path).exists():
                new_managed.append(entry)
            else:
                removed.append(entry.path)
        if removed:
            state.managed = new_managed
            self.save(state)
        return removed

    def get_orphans(self, current_paths: set[str]) -> list[str]:
        state = self.load()
        managed_paths = set(e.path for e in state.managed)
        return list(managed_paths - current_paths)
