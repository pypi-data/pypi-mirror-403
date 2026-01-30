"""Gemini CLI configuration renderer."""

from __future__ import annotations

from agentslock.model import ClientId, MCPConfig, Transport
from agentslock.render.base import (
    BaseRenderer,
    ConfigUpdate,
    DirectoryOutput,
    FileOutput,
    RenderResult,
)


class GeminiRenderer(BaseRenderer):
    """Renderer for Gemini CLI configuration."""

    client = ClientId.GEMINI

    def _render_skills(self, result: RenderResult) -> None:
        """Render skills to .github/skills/ or ~/.gemini/skills/."""
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
        """Gemini doesn't support agents - skip with warning."""
        for agent in self.lockfile.agents:
            if self._is_enabled(agent):
                result.warnings.append(
                    f"Agent '{agent.name}' skipped: Gemini does not support custom agents"
                )
            else:
                result.skipped.append(f"agent:{agent.name} (disabled)")

    def _render_mcp_servers(self, result: RenderResult) -> None:
        """Render MCP servers to ~/.gemini/settings.json."""
        if self.scope == "project":
            for mcp in self.lockfile.mcp_servers:
                if self._is_enabled(mcp):
                    result.warnings.append(
                        f"MCP server '{mcp.name}' skipped: Gemini only supports global MCP config"
                    )
            return

        mcp_path = self.paths.mcp_config_path(self.scope)
        if mcp_path is None:
            for mcp in self.lockfile.mcp_servers:
                if self._is_enabled(mcp):
                    result.warnings.append(
                        f"MCP server '{mcp.name}' skipped: Gemini config path not found. "
                        "Use --gemini-config to specify."
                    )
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

            gemini_config = self._mcp_to_gemini_format(config)
            result.config_updates.append(
                ConfigUpdate(path=mcp_path, key=f"mcpServers.{key}", value=gemini_config)
            )

    def _mcp_to_gemini_format(self, config: MCPConfig) -> dict:
        """Convert MCPConfig to Gemini's settings.json format."""
        if config.transport == Transport.STDIO:
            result = {
                "command": config.command,
                "args": config.args,
            }
            if config.env:
                result["env"] = config.env
        else:
            result = {
                "url": config.url,
                "transport": config.transport.value,
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
        """Gemini doesn't have standard instructions file - skip unless output_path specified."""
        for instr in self.lockfile.instructions:
            if not self._is_enabled(instr):
                result.skipped.append(f"instructions:{instr.name} (disabled)")
                continue

            # Check if this instruction targets Gemini
            if instr.targets:
                if ClientId.GEMINI not in instr.targets:
                    continue
            else:
                # Gemini doesn't have native instructions unless explicitly targeted
                continue

            if not instr.output_path:
                result.warnings.append(
                    f"Instructions '{instr.name}' targets Gemini but no output_path specified. "
                    "Gemini requires explicit output path for instructions."
                )
                continue

            dest = self.project_root / instr.output_path

            resolved = self.resolver.resolve_instructions(instr)
            if resolved.content:
                content = resolved.content
            elif resolved.path and resolved.path.exists():
                content = resolved.path.read_text()
            else:
                result.warnings.append(f"Instructions source not found: {instr.name}")
                continue

            result.files.append(FileOutput(path=dest, content=content))
