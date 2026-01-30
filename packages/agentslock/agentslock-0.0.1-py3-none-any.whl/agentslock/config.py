"""Global configuration management for agents.lock."""

from __future__ import annotations

import tomllib
from pathlib import Path

import tomlkit

from agentslock.model import ClientId, Defaults, GlobalConfig
from agentslock.paths import get_global_config_path
from agentslock.util import atomic_write, ensure_dir


def load_global_config() -> GlobalConfig:
    config_path = get_global_config_path()

    if not config_path.exists():
        return GlobalConfig()

    try:
        data = tomllib.loads(config_path.read_text())
    except tomllib.TOMLDecodeError:
        return GlobalConfig()

    defaults_data = data.get("defaults", {})
    clients = [ClientId.from_str(c) for c in defaults_data.get("clients", ["claude"])]

    return GlobalConfig(
        defaults=Defaults(
            clients=clients,
            groups=defaults_data.get("groups", ["default"]),
        ),
        aliases=data.get("aliases", {}),
    )


def save_global_config(config: GlobalConfig) -> None:
    config_path = get_global_config_path()
    ensure_dir(config_path.parent)

    doc = tomlkit.document()

    defaults = tomlkit.table()
    defaults.add("clients", [c.value for c in config.defaults.clients])
    defaults.add("groups", config.defaults.groups)
    doc.add("defaults", defaults)

    if config.aliases:
        aliases = tomlkit.table()
        for name, path in config.aliases.items():
            aliases.add(name, path)
        doc.add("aliases", aliases)

    atomic_write(config_path, tomlkit.dumps(doc))


def resolve_lockfile_alias(alias_or_path: str) -> Path:
    path = Path(alias_or_path)

    # If it looks like a path, return it
    if path.exists() or "/" in alias_or_path or alias_or_path.endswith(".lock"):
        return path

    # Try to resolve as alias
    config = load_global_config()
    if alias_or_path in config.aliases:
        return Path(config.aliases[alias_or_path])

    # Return as-is (may not exist)
    return path
