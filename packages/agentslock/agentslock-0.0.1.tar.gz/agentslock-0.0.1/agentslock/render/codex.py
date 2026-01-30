"""Codex CLI configuration renderer."""

from __future__ import annotations

from agentslock.model import ClientId, InstructionKind, InstructionMode, MCPConfig, Transport
from agentslock.render.base import (
    BaseRenderer,
    ConfigUpdate,
    DirectoryOutput,
    FileOutput,
    RenderResult,
)


class CodexRenderer(BaseRenderer):
    """Renderer for Codex CLI configuration."""

    client = ClientId.CODEX

    def _render_skills(self, result: RenderResult) -> None:
        """Render skills to .codex/skills/ directory."""
        for skill in self.lockfile.skills:
            if not self._is_enabled(skill):
                result.skipped.append(f"skill:{skill.name} (disabled)")
                continue

            resolved = self.resolver.resolve_skill(skill)
            if not resolved.exists:
                result.warnings.append(f"Skill source not found: {skill.name}")
                continue

            name = self._get_name(skill)
            dest = self.paths.skill_path(name, self.scope)

            if resolved.is_directory:
                if resolved.path is None:
                    result.warnings.append(f"Skill source path missing: {skill.name}")
                    continue
                result.directories.append(DirectoryOutput(path=dest, source_path=resolved.path))
            else:
                skill_dir = dest
                if resolved.path is None:
                    result.warnings.append(f"Skill source path missing: {skill.name}")
                    continue
                content = resolved.path.read_text()
                result.files.append(FileOutput(path=skill_dir / "SKILL.md", content=content))

    def _render_agents(self, result: RenderResult) -> None:
        """Codex doesn't support agents - skip with warning."""
        for agent in self.lockfile.agents:
            if self._is_enabled(agent):
                result.warnings.append(
                    f"Agent '{agent.name}' skipped: Codex does not support custom agents"
                )
            else:
                result.skipped.append(f"agent:{agent.name} (disabled)")

    def _render_mcp_servers(self, result: RenderResult) -> None:
        """Render MCP servers to ~/.codex/config.toml."""
        if self.scope == "project":
            for mcp in self.lockfile.mcp_servers:
                if self._is_enabled(mcp):
                    result.warnings.append(
                        f"MCP server '{mcp.name}' skipped: Codex only supports global MCP config"
                    )
            return

        mcp_path = self.paths.mcp_config_path(self.scope)
        if mcp_path is None:
            return

        for mcp in self.lockfile.mcp_servers:
            if not self._is_enabled(mcp):
                result.skipped.append(f"mcp:{mcp.name} (disabled)")
                continue

            name = self._get_name(mcp)
            key = self._managed_key(name)

            override = self._get_override(mcp)
            config = mcp.config
            if override and override.config:
                config = self._merge_mcp_config(config, override.config)

            codex_config = self._mcp_to_codex_format(config)
            result.config_updates.append(
                ConfigUpdate(path=mcp_path, key=f"mcp_servers.{key}", value=codex_config)
            )

    def _mcp_to_codex_format(self, config: MCPConfig) -> dict:
        """Convert MCPConfig to Codex's config.toml format."""
        if config.transport == Transport.STDIO:
            result = {
                "type": "stdio",
                "command": config.command,
                "args": config.args,
            }
            if config.env:
                result["env"] = config.env
        else:
            result = {
                "type": config.transport.value,
                "url": config.url,
            }
            if config.headers:
                result["headers"] = config.headers

        if config.timeout:
            result["timeout"] = config.timeout
        if config.tool_filters:
            result["tool_filters"] = config.tool_filters

        return result

    def _merge_mcp_config(self, base: MCPConfig, override: dict) -> MCPConfig:
        """Merge override dict into MCPConfig."""
        return MCPConfig(
            transport=Transport(override.get("transport", base.transport.value)),
            command=override.get("command", base.command),
            args=override.get("args", base.args),
            env={**base.env, **override.get("env", {})},
            cwd=override.get("cwd", base.cwd),
            url=override.get("url", base.url),
            headers={**base.headers, **override.get("headers", {})},
            timeout=override.get("timeout", base.timeout),
            tool_filters=override.get("tool_filters", base.tool_filters),
        )

    def _render_instructions(self, result: RenderResult) -> None:
        """Render instructions to AGENTS.md."""
        for instr in self.lockfile.instructions:
            if not self._is_enabled(instr):
                result.skipped.append(f"instructions:{instr.name} (disabled)")
                continue

            # Check if this instruction targets Codex
            if instr.targets:
                if ClientId.CODEX not in instr.targets:
                    continue
            elif instr.kind not in (InstructionKind.AGENTS_MD,):
                # Codex only uses AGENTS.md
                continue

            if instr.output_path:
                dest = self.project_root / instr.output_path
            else:
                dest = self.paths.instructions_path(self.scope)

            if dest is None:
                result.warnings.append(f"No instructions path for Codex in {self.scope} scope")
                continue

            resolved = self.resolver.resolve_instructions(instr)
            if resolved.content:
                content = resolved.content
            elif resolved.path and resolved.path.exists():
                content = resolved.path.read_text()
            else:
                result.warnings.append(f"Instructions source not found: {instr.name}")
                continue

            # Handle self-reference
            if resolved.path and resolved.path.resolve() == dest.resolve():
                result.skipped.append(f"instructions:{instr.name} (self-reference)")
                continue

            if instr.mode == InstructionMode.REPLACE:
                result.files.append(FileOutput(path=dest, content=content))
            else:
                wrapped = self._wrap_instructions_content(instr.name, content)
                result.config_updates.append(
                    ConfigUpdate(
                        path=dest,
                        key=f"__instructions__{instr.mode.value}__{instr.name}",
                        value={"content": wrapped, "mode": instr.mode.value},
                    )
                )
