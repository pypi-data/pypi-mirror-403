"""
Configuration settings for OpenCode.

Supports JSON configuration with:
- Environment variable substitution: {env:VAR_NAME}
- File inclusion: {file:path/to/file}
- Merging of global and project configs
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from opencode.config.paths import (
    get_global_config_path,
    get_project_config_path,
)


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""

    api_key: str | None = None
    base_url: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    whitelist: list[str] = field(default_factory=list)
    blacklist: list[str] = field(default_factory=list)
    models: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class MCPConfig:
    """Configuration for an MCP server."""

    type: Literal["local", "remote"] = "local"
    command: list[str] = field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout: int = 30000


@dataclass
class AgentConfig:
    """Configuration for a custom agent."""

    prompt: str = ""
    model: str | None = None
    mode: Literal["primary", "subagent", "all"] = "primary"
    description: str = ""
    color: str | None = None
    steps: int = 10
    temperature: float | None = None
    top_p: float | None = None
    hidden: bool = False
    permission: dict[str, str] = field(default_factory=dict)


@dataclass
class PermissionConfig:
    """Permission rules for tools."""

    read: str | dict[str, str] = "allow"
    write: str | dict[str, str] = "ask"
    edit: str | dict[str, str] = "ask"
    bash: str | dict[str, str] = "ask"
    glob: str | dict[str, str] = "allow"
    grep: str | dict[str, str] = "allow"
    webfetch: str | dict[str, str] = "ask"
    external_directory: str = "ask"
    doom_loop: str = "ask"


@dataclass
class RLMConfig:
    """Recursive Language Model configuration."""

    enabled: bool = True
    threshold_ratio: float = 0.33
    max_context_blocks: int = 100
    auto_retrieve: bool = True
    semantic_search: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "embedding_model": "openai/text-embedding-3-small",
            "similarity_threshold": 0.45,
            "proactive_threshold": 0.40,
            "hybrid_weights": {"keyword": 0.3, "semantic": 0.7},
        }
    )
    task_based: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "archive_on_todo_complete": True,
            "archive_on_user_phrase": True,
        }
    )


@dataclass
class TUIConfig:
    """TUI-specific configuration."""

    scroll_speed: int = 3
    scroll_acceleration: bool = True
    diff_style: Literal["inline", "side-by-side"] = "inline"
    show_line_numbers: bool = True
    word_wrap: bool = True
    mouse_support: bool = True


@dataclass
class KeybindConfig:
    """Keybinding configuration."""

    leader: str = "ctrl+x"
    bindings: dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    """Main configuration object."""

    # Display
    theme: str = "opencode"
    username: str | None = None

    # Models
    model: str = "anthropic/claude-sonnet-4"
    small_model: str = "anthropic/claude-haiku"
    default_agent: str = "build"

    # Behavior
    log_level: str = "info"
    autoupdate: bool | Literal["notify"] = True
    share: Literal["manual", "auto", "disabled"] = "manual"
    snapshot: bool = True
    layout: Literal["auto", "stretch"] = "auto"

    # Instructions
    instructions: list[str] = field(default_factory=list)

    # Providers
    disabled_providers: list[str] = field(default_factory=list)
    enabled_providers: list[str] = field(default_factory=list)
    provider: dict[str, ProviderConfig] = field(default_factory=dict)

    # MCP
    mcp: dict[str, MCPConfig] = field(default_factory=dict)

    # Agents
    agent: dict[str, AgentConfig] = field(default_factory=dict)

    # Permissions
    permission: PermissionConfig = field(default_factory=PermissionConfig)

    # RLM
    rlm: RLMConfig = field(default_factory=RLMConfig)

    # TUI
    tui: TUIConfig = field(default_factory=TUIConfig)

    # Keybindings
    keybinds: KeybindConfig = field(default_factory=KeybindConfig)

    # Server
    server: dict[str, Any] = field(
        default_factory=lambda: {
            "port": 4096,
            "hostname": "127.0.0.1",
        }
    )

    # Commands
    command: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Experimental
    experimental: dict[str, Any] = field(default_factory=dict)


# Global config instance
_config: Config | None = None


def _substitute_env_vars(value: str) -> str:
    """Replace {env:VAR_NAME} with environment variable value."""
    pattern = r"\{env:([^}]+)\}"

    def replace(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(pattern, replace, value)


def _substitute_file_includes(value: str, base_path: Path) -> str:
    """Replace {file:path} with file contents."""
    pattern = r"\{file:([^}]+)\}"

    def replace(match: re.Match) -> str:
        file_path = match.group(1)
        full_path = base_path / file_path
        if full_path.exists():
            return full_path.read_text().strip()
        return ""

    return re.sub(pattern, replace, value)


def _process_value(value: Any, base_path: Path) -> Any:
    """Process a config value, handling substitutions recursively."""
    if isinstance(value, str):
        value = _substitute_env_vars(value)
        value = _substitute_file_includes(value, base_path)
        return value
    if isinstance(value, dict):
        return {k: _process_value(v, base_path) for k, v in value.items()}
    if isinstance(value, list):
        return [_process_value(v, base_path) for v in value]
    return value


def _merge_configs(base: dict, override: dict) -> dict:
    """Deep merge two config dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def _dict_to_config(data: dict) -> Config:
    """Convert a dictionary to a Config object."""
    config = Config()

    # Simple fields
    for field_name in [
        "theme",
        "username",
        "model",
        "small_model",
        "default_agent",
        "log_level",
        "autoupdate",
        "share",
        "snapshot",
        "layout",
        "instructions",
        "disabled_providers",
        "enabled_providers",
        "server",
        "command",
        "experimental",
    ]:
        if field_name in data:
            setattr(config, field_name, data[field_name])

    # Provider configs
    if "provider" in data:
        config.provider = {
            name: ProviderConfig(**cfg) if isinstance(cfg, dict) else cfg
            for name, cfg in data["provider"].items()
        }

    # MCP configs
    if "mcp" in data:
        config.mcp = {
            name: MCPConfig(**cfg) if isinstance(cfg, dict) else cfg
            for name, cfg in data["mcp"].items()
        }

    # Agent configs
    if "agent" in data:
        config.agent = {
            name: AgentConfig(**cfg) if isinstance(cfg, dict) else cfg
            for name, cfg in data["agent"].items()
        }

    # Permission config
    if "permission" in data:
        config.permission = PermissionConfig(**data["permission"])

    # RLM config
    if "rlm" in data:
        config.rlm = RLMConfig(**data["rlm"])

    # TUI config
    if "tui" in data:
        config.tui = TUIConfig(**data["tui"])

    # Keybind config
    if "keybinds" in data:
        if isinstance(data["keybinds"], dict):
            config.keybinds = KeybindConfig(
                leader=data["keybinds"].get("leader", "ctrl+x"),
                bindings=data["keybinds"].get("bindings", {}),
            )

    return config


def load_config(
    project_dir: Path | str | None = None,
    reload: bool = False,
) -> Config:
    """
    Load configuration from global and project files.

    Args:
        project_dir: Project directory to load config from
        reload: Force reload even if already loaded

    Returns:
        Merged configuration object
    """
    global _config

    if _config is not None and not reload:
        return _config

    merged_data: dict = {}

    # Load global config
    global_path = get_global_config_path()
    if global_path.exists():
        try:
            raw = json.loads(global_path.read_text())
            processed = _process_value(raw, global_path.parent)
            merged_data = processed
        except (json.JSONDecodeError, OSError):
            pass

    # Load project config
    project_path = get_project_config_path(project_dir)
    if project_path is not None:
        try:
            raw = json.loads(project_path.read_text())
            processed = _process_value(raw, project_path.parent)
            merged_data = _merge_configs(merged_data, processed)
        except (json.JSONDecodeError, OSError):
            pass

    _config = _dict_to_config(merged_data)
    return _config


def get_config() -> Config:
    """Get the current configuration, loading if necessary."""
    if _config is None:
        return load_config()
    return _config


def save_config(config: Config, path: Path | None = None) -> None:
    """Save configuration to a file."""
    if path is None:
        path = get_global_config_path()

    data = {
        "theme": config.theme,
        "model": config.model,
        "small_model": config.small_model,
        "default_agent": config.default_agent,
        "log_level": config.log_level,
        "autoupdate": config.autoupdate,
        "share": config.share,
    }

    # Only include non-default values
    if config.username:
        data["username"] = config.username
    if config.instructions:
        data["instructions"] = config.instructions
    if config.disabled_providers:
        data["disabled_providers"] = config.disabled_providers
    if config.enabled_providers:
        data["enabled_providers"] = config.enabled_providers

    path.write_text(json.dumps(data, indent=2))
