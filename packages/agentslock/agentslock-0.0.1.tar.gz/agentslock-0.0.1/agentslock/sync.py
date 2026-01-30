"""Sync engine for agents.lock."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from difflib import unified_diff
from pathlib import Path
from typing import Any, cast

import tomlkit
from tomlkit.items import Table

from agentslock.cache import GitCache
from agentslock.lockfile import parse_lockfile
from agentslock.model import ClientId
from agentslock.paths import Scope, get_managed_prefix
from agentslock.render import render_all
from agentslock.render.base import ConfigUpdate, DirectoryOutput, FileOutput
from agentslock.resolve import SourceResolver
from agentslock.state import StateManager
from agentslock.util import atomic_write, copy_file, copy_tree, ensure_dir, temp_directory


@dataclass
class Change:
    """Represents a single change to be applied."""

    path: Path
    action: str  # create, update, delete
    change_type: str  # file, directory, config_key
    old_content: str | None = None
    new_content: str | None = None
    source_path: Path | None = None


@dataclass
class SyncPlan:
    """Plan for sync operation."""

    changes: list[Change] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def creates(self) -> list[Change]:
        return [c for c in self.changes if c.action == "create"]

    @property
    def updates(self) -> list[Change]:
        return [c for c in self.changes if c.action == "update"]

    @property
    def deletes(self) -> list[Change]:
        return [c for c in self.changes if c.action == "delete"]

    def summary(self) -> dict[str, int]:
        return {
            "create": len(self.creates),
            "update": len(self.updates),
            "delete": len(self.deletes),
        }


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    applied: list[Change] = field(default_factory=list)
    failed: list[tuple[Change, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class SyncEngine:
    """Orchestrates the sync operation."""

    def __init__(
        self,
        lockfile_path: Path,
        scope: Scope = "project",
        clients: list[ClientId] | None = None,
        groups: list[str] | None = None,
        project_root: Path | None = None,
        cache: GitCache | None = None,
    ):
        self.lockfile_path = lockfile_path.resolve()
        self.scope: Scope = scope
        self.project_root = project_root or lockfile_path.parent
        self.cache = cache or GitCache()
        self.state_manager = StateManager(scope, self.project_root, lockfile_path)
        self.prefix = get_managed_prefix()

        # Load and filter lockfile
        self.lockfile = parse_lockfile(lockfile_path)
        if groups:
            self.lockfile = self.lockfile.filter_by_groups(groups)
        self.lockfile = self.lockfile.filter_enabled()

        # Override clients if specified
        self.clients = clients or self.lockfile.defaults.clients

        # Create resolver
        self.resolver = SourceResolver(self.lockfile, self.cache)

    def plan(self) -> SyncPlan:
        plan = SyncPlan()

        # Ensure all sources are resolved
        try:
            self.resolver.ensure_all()
        except Exception as e:
            plan.warnings.append(f"Source resolution warning: {e}")

        # Render all client configurations
        render_results = render_all(
            self.lockfile,
            self.resolver,
            self.scope,
            self.clients,
            self.project_root,
        )

        # Collect all planned outputs
        planned_paths: set[str] = set()

        for client, result in render_results.items():
            plan.warnings.extend(result.warnings)
            plan.skipped.extend(result.skipped)

            # Plan file outputs
            for file_out in result.files:
                self._plan_file(plan, file_out, planned_paths)

            # Plan directory outputs
            for dir_out in result.directories:
                self._plan_directory(plan, dir_out, planned_paths)

            # Plan config updates
            for config_update in result.config_updates:
                self._plan_config_update(plan, config_update, planned_paths)

        # Plan deletions for orphaned managed files
        orphans = self.state_manager.get_orphans(planned_paths)
        for orphan_path in orphans:
            path = Path(orphan_path)
            if path.exists():
                plan.changes.append(
                    Change(
                        path=path,
                        action="delete",
                        change_type="directory" if path.is_dir() else "file",
                    )
                )

        return plan

    def _plan_file(self, plan: SyncPlan, file_out: FileOutput, planned_paths: set[str]) -> None:
        path = file_out.path
        planned_paths.add(str(path.resolve()))

        new_content = (
            file_out.content if isinstance(file_out.content, str) else file_out.content.decode()
        )

        if path.exists():
            old_content = path.read_text()
            if old_content != new_content:
                plan.changes.append(
                    Change(
                        path=path,
                        action="update",
                        change_type="file",
                        old_content=old_content,
                        new_content=new_content,
                    )
                )
        else:
            plan.changes.append(
                Change(
                    path=path,
                    action="create",
                    change_type="file",
                    new_content=new_content,
                )
            )

    def _plan_directory(
        self, plan: SyncPlan, dir_out: DirectoryOutput, planned_paths: set[str]
    ) -> None:
        path = dir_out.path
        planned_paths.add(str(path.resolve()))

        if path.exists():
            # Check if contents differ (simplified - just mark as update)
            plan.changes.append(
                Change(
                    path=path,
                    action="update",
                    change_type="directory",
                    source_path=dir_out.source_path,
                )
            )
        else:
            plan.changes.append(
                Change(
                    path=path,
                    action="create",
                    change_type="directory",
                    source_path=dir_out.source_path,
                )
            )

    def _plan_config_update(
        self, plan: SyncPlan, config_update: ConfigUpdate, planned_paths: set[str]
    ) -> None:
        path = config_update.path
        planned_paths.add(str(path.resolve()))

        # Handle instruction append/prepend
        if config_update.key.startswith("__instructions__"):
            self._plan_instruction_merge(plan, config_update)
            return

        # Handle JSON/TOML config merging
        if path.suffix == ".json":
            self._plan_json_merge(plan, config_update)
        elif path.suffix == ".toml":
            self._plan_toml_merge(plan, config_update)
        else:
            plan.warnings.append(f"Unknown config format for {path}")

    def _plan_instruction_merge(self, plan: SyncPlan, config_update: ConfigUpdate) -> None:
        path = config_update.path
        value = config_update.value
        if not value:
            return

        content = value["content"]
        mode = value["mode"]
        name = config_update.key.split("__")[-1]

        if path.exists():
            old_content = path.read_text()
            # Check for existing managed section
            from agentslock.render.base import INSTRUCTION_MARKER_BEGIN, INSTRUCTION_MARKER_END

            begin = INSTRUCTION_MARKER_BEGIN.format(name=name)
            start = old_content.find(begin)

            if start != -1:
                # Replace existing section
                end_marker = INSTRUCTION_MARKER_END
                end = old_content.find(end_marker, start)
                if end != -1:
                    end += len(end_marker)
                    if end < len(old_content) and old_content[end] == "\n":
                        end += 1
                    new_content = old_content[:start] + content + old_content[end:]
                else:
                    new_content = old_content[:start] + content + old_content[start:]
            else:
                # Add new section
                if mode == "prepend":
                    new_content = content + "\n" + old_content
                else:
                    new_content = old_content + "\n" + content

            if old_content != new_content:
                plan.changes.append(
                    Change(
                        path=path,
                        action="update",
                        change_type="file",
                        old_content=old_content,
                        new_content=new_content,
                    )
                )
        else:
            plan.changes.append(
                Change(
                    path=path,
                    action="create",
                    change_type="file",
                    new_content=content,
                )
            )

    def _plan_json_merge(self, plan: SyncPlan, config_update: ConfigUpdate) -> None:
        path = config_update.path
        key_parts = config_update.key.split(".")

        if path.exists():
            try:
                old_data = json.loads(path.read_text())
            except json.JSONDecodeError:
                old_data = {}
        else:
            old_data = {}

        new_data = self._deep_copy(old_data)
        self._set_nested(new_data, key_parts, config_update.value)

        old_content = json.dumps(old_data, indent=2) if old_data else ""
        new_content = json.dumps(new_data, indent=2)

        if old_content != new_content:
            action = "update" if path.exists() else "create"
            plan.changes.append(
                Change(
                    path=path,
                    action=action,
                    change_type="config_key",
                    old_content=old_content,
                    new_content=new_content,
                )
            )

    def _plan_toml_merge(self, plan: SyncPlan, config_update: ConfigUpdate) -> None:
        path = config_update.path
        key_parts = config_update.key.split(".")

        if path.exists():
            try:
                old_content = path.read_text()
                old_data = tomlkit.loads(old_content)
            except Exception:
                old_data = tomlkit.document()
                old_content = ""
        else:
            old_data = tomlkit.document()
            old_content = ""

        new_data = tomlkit.loads(tomlkit.dumps(old_data))
        self._set_nested_toml(new_data, key_parts, config_update.value)

        new_content = tomlkit.dumps(new_data)

        if old_content != new_content:
            action = "update" if path.exists() else "create"
            plan.changes.append(
                Change(
                    path=path,
                    action=action,
                    change_type="config_key",
                    old_content=old_content,
                    new_content=new_content,
                )
            )

    def _deep_copy(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(v) for v in obj]
        return obj

    def _set_nested(self, data: dict[str, Any], keys: list[str], value: Any) -> None:
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]

        if value is None:
            data.pop(keys[-1], None)
        else:
            data[keys[-1]] = value

    def _set_nested_toml(self, data: tomlkit.TOMLDocument, keys: list[str], value: Any) -> None:
        current: Table | tomlkit.TOMLDocument = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = tomlkit.table()
            current = cast(Table, current[key])

        if value is None:
            if keys[-1] in current:
                del current[keys[-1]]
        else:
            current[keys[-1]] = value

    def apply(self, plan: SyncPlan, dry_run: bool = False) -> SyncResult:
        result = SyncResult(success=True, warnings=plan.warnings, skipped=plan.skipped)

        if dry_run:
            result.applied = plan.changes
            return result

        with temp_directory() as staging:
            # Stage all changes
            for change in plan.changes:
                try:
                    self._stage_change(change, staging)
                except Exception as e:
                    result.failed.append((change, str(e)))
                    result.success = False

            if not result.success:
                return result

            # Apply staged changes
            for change in plan.changes:
                try:
                    self._apply_change(change, staging)
                    result.applied.append(change)

                    # Update state
                    if change.action == "delete":
                        self.state_manager.unrecord(change.path)
                    else:
                        entry_type = "directory" if change.change_type == "directory" else "file"
                        self.state_manager.record(change.path, entry_type)

                except Exception as e:
                    result.failed.append((change, str(e)))
                    result.success = False

        return result

    def _stage_change(self, change: Change, staging: Path) -> None:
        if change.action == "delete":
            return

        staged_path = staging / str(change.path).lstrip("/")
        ensure_dir(staged_path.parent)

        if change.change_type == "directory":
            if change.source_path:
                copy_tree(change.source_path, staged_path)
        else:
            if change.new_content:
                atomic_write(staged_path, change.new_content)

    def _apply_change(self, change: Change, staging: Path) -> None:
        if change.action == "delete":
            if change.path.is_dir():
                shutil.rmtree(change.path)
            elif change.path.exists():
                change.path.unlink()
            return

        staged_path = staging / str(change.path).lstrip("/")

        if change.change_type == "directory":
            ensure_dir(change.path.parent)
            if change.path.exists():
                shutil.rmtree(change.path)
            copy_tree(staged_path, change.path)
        else:
            ensure_dir(change.path.parent)
            copy_file(staged_path, change.path)

    def get_diff(self, change: Change) -> str | None:
        if change.change_type == "directory":
            return f"[directory copy from {change.source_path}]"

        if change.action == "delete":
            if change.old_content:
                return "\n".join(
                    unified_diff(
                        change.old_content.splitlines(keepends=True),
                        [],
                        fromfile=str(change.path),
                        tofile="/dev/null",
                    )
                )
            return f"[delete {change.path}]"

        old_lines = (change.old_content or "").splitlines(keepends=True)
        new_lines = (change.new_content or "").splitlines(keepends=True)

        return "".join(
            unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{change.path.name}",
                tofile=f"b/{change.path.name}",
            )
        )


def sync(
    lockfile_path: Path,
    scope: Scope = "project",
    clients: list[ClientId] | None = None,
    groups: list[str] | None = None,
    dry_run: bool = False,
    project_root: Path | None = None,
) -> SyncResult:
    engine = SyncEngine(
        lockfile_path=lockfile_path,
        scope=scope,
        clients=clients,
        groups=groups,
        project_root=project_root,
    )
    plan = engine.plan()
    return engine.apply(plan, dry_run=dry_run)
