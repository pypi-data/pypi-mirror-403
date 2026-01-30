"""Configuration loading for mcpmon gateway mode."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ServerConfig:
    """Configuration for a single backend server."""

    command: str | list[str]
    args: list[str] = field(default_factory=list)
    watch: str | None = None
    extensions: str = "py"  # File extensions to watch
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class GatewayConfig:
    """Configuration for the gateway."""

    servers: dict[str, ServerConfig]
    log_level: str = "info"
    notify_on_change: bool = True
    config_path: Path | None = None


def expand_env_vars(value: str) -> str:
    """Expand environment variables in a string (${VAR} syntax)."""
    if not isinstance(value, str):
        return value

    import re

    def replacer(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(r"\$\{(\w+)\}", replacer, value)


def load_config(path: str | Path) -> GatewayConfig:
    """Load gateway configuration from a YAML file."""
    path = Path(path)

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    servers = {}
    for name, cfg in data.get("servers", {}).items():
        if isinstance(cfg, str):
            # Simple form: just command
            servers[name] = ServerConfig(command=cfg)
        else:
            # Expand env vars in environment config
            env = {}
            for k, v in cfg.get("env", {}).items():
                env[k] = expand_env_vars(str(v))

            # Parse command
            command = cfg.get("command", cfg.get("cmd"))
            if command is None:
                raise ValueError(f"Server '{name}' missing 'command' field")

            servers[name] = ServerConfig(
                command=command,
                args=cfg.get("args", []),
                watch=cfg.get("watch"),
                extensions=cfg.get("extensions", cfg.get("ext", "py")),
                env=env,
            )

    settings = data.get("settings", {})
    return GatewayConfig(
        servers=servers,
        log_level=settings.get("log_level", "info"),
        notify_on_change=settings.get("notify_on_change", True),
        config_path=path,
    )


def find_config() -> Path | None:
    """Find config file in standard locations."""
    candidates = [
        Path.cwd() / ".mcpmon.yaml",
        Path.cwd() / ".mcpmon.yml",
        Path.cwd() / "mcpmon.yaml",
        Path.cwd() / "mcpmon.yml",
        Path.home() / ".config" / "mcpmon" / "config.yaml",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None
