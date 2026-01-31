"""
Configuration system for zwarm.

Supports:
- config.toml for user settings (weave project, defaults)
- .env for environment variables
- Composable YAML configs with inheritance (extends:)
- CLI overrides via --set key=value
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class WeaveConfig:
    """Weave integration settings."""

    project: str | None = None
    enabled: bool = True


@dataclass
class ExecutorConfig:
    """Configuration for an executor (coding agent)."""

    adapter: str = "codex_mcp"  # codex_mcp | codex_exec | claude_code
    model: str | None = None
    sandbox: str = "workspace-write"  # read-only | workspace-write | danger-full-access
    timeout: int = 3600
    reasoning_effort: str | None = "high"  # low | medium | high (default to high for compatibility)
    # Note: web_search is always enabled via .codex/config.toml (set up by `zwarm init`)


@dataclass
class CompactionConfig:
    """Configuration for context window compaction."""

    enabled: bool = True
    max_tokens: int = 100000  # Trigger compaction when estimated tokens exceed this
    threshold_pct: float = 0.85  # Compact when at this % of max_tokens
    target_pct: float = 0.7  # Target this % after compaction
    keep_first_n: int = 2  # Always keep first N messages (system + task)
    keep_last_n: int = 10  # Always keep last N messages (recent context)


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""

    lm: str = "gpt-5-mini"
    prompt: str | None = None  # path to prompt yaml
    tools: list[str] = field(default_factory=lambda: ["delegate", "converse", "check_session", "end_session", "bash"])
    max_steps: int = 50
    max_steps_per_turn: int = 60  # Max tool-call steps before returning to user (pilot mode)
    parallel_delegations: int = 4
    compaction: CompactionConfig = field(default_factory=CompactionConfig)

    # Directory restrictions for agent delegations
    # None = only working_dir allowed (most restrictive, default)
    # ["*"] = any directory allowed (dangerous)
    # ["/path/a", "/path/b"] = only these directories allowed
    allowed_dirs: list[str] | None = None


@dataclass
class WatcherConfigItem:
    """Configuration for a single watcher."""

    name: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class WatchersConfig:
    """Configuration for watchers."""

    enabled: bool = True
    watchers: list[WatcherConfigItem] = field(default_factory=lambda: [
        WatcherConfigItem(name="progress"),
        WatcherConfigItem(name="budget"),
        WatcherConfigItem(name="delegation_reminder"),
    ])
    # Role for watcher nudge messages: "user" | "assistant" | "system"
    # "user" (default) - Appears as if user sent the message, strong nudge
    # "assistant" - Appears as previous assistant thought, softer nudge
    # "system" - Appears as system instruction, authoritative
    message_role: str = "user"


@dataclass
class ZwarmConfig:
    """Root configuration for zwarm."""

    weave: WeaveConfig = field(default_factory=WeaveConfig)
    executor: ExecutorConfig = field(default_factory=ExecutorConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    watchers: WatchersConfig = field(default_factory=WatchersConfig)
    state_dir: str = ".zwarm"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ZwarmConfig:
        """Create config from dictionary."""
        weave_data = data.get("weave", {})
        executor_data = data.get("executor", {})
        orchestrator_data = data.get("orchestrator", {})
        watchers_data = data.get("watchers", {})

        # Parse compaction config from orchestrator
        compaction_data = orchestrator_data.pop("compaction", {}) if orchestrator_data else {}
        compaction_config = CompactionConfig(**compaction_data) if compaction_data else CompactionConfig()

        # Parse watchers config - handle both list shorthand and dict format
        if isinstance(watchers_data, list):
            # Shorthand: watchers: [progress, budget, scope]
            watchers_config = WatchersConfig(
                enabled=True,
                watchers=[
                    WatcherConfigItem(name=w) if isinstance(w, str) else WatcherConfigItem(**w)
                    for w in watchers_data
                ],
            )
        else:
            # Full format: watchers: {enabled: true, watchers: [...], message_role: "user"}
            watchers_config = WatchersConfig(
                enabled=watchers_data.get("enabled", True),
                watchers=[
                    WatcherConfigItem(name=w) if isinstance(w, str) else WatcherConfigItem(**w)
                    for w in watchers_data.get("watchers", [])
                ] or WatchersConfig().watchers,
                message_role=watchers_data.get("message_role", "user"),
            )

        # Build orchestrator config with nested compaction
        if orchestrator_data:
            orchestrator_config = OrchestratorConfig(**orchestrator_data, compaction=compaction_config)
        else:
            orchestrator_config = OrchestratorConfig(compaction=compaction_config)

        return cls(
            weave=WeaveConfig(**weave_data) if weave_data else WeaveConfig(),
            executor=ExecutorConfig(**executor_data) if executor_data else ExecutorConfig(),
            orchestrator=orchestrator_config,
            watchers=watchers_config,
            state_dir=data.get("state_dir", ".zwarm"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "weave": {
                "project": self.weave.project,
                "enabled": self.weave.enabled,
            },
            "executor": {
                "adapter": self.executor.adapter,
                "model": self.executor.model,
                "sandbox": self.executor.sandbox,
                "timeout": self.executor.timeout,
                "reasoning_effort": self.executor.reasoning_effort,
            },
            "orchestrator": {
                "lm": self.orchestrator.lm,
                "prompt": self.orchestrator.prompt,
                "tools": self.orchestrator.tools,
                "max_steps": self.orchestrator.max_steps,
                "max_steps_per_turn": self.orchestrator.max_steps_per_turn,
                "parallel_delegations": self.orchestrator.parallel_delegations,
                "compaction": {
                    "enabled": self.orchestrator.compaction.enabled,
                    "max_tokens": self.orchestrator.compaction.max_tokens,
                    "threshold_pct": self.orchestrator.compaction.threshold_pct,
                    "target_pct": self.orchestrator.compaction.target_pct,
                    "keep_first_n": self.orchestrator.compaction.keep_first_n,
                    "keep_last_n": self.orchestrator.compaction.keep_last_n,
                },
            },
            "watchers": {
                "enabled": self.watchers.enabled,
                "watchers": [
                    {"name": w.name, "enabled": w.enabled, "config": w.config}
                    for w in self.watchers.watchers
                ],
                "message_role": self.watchers.message_role,
            },
            "state_dir": self.state_dir,
        }


def load_env(path: Path | None = None, base_dir: Path | None = None) -> None:
    """Load .env file if it exists."""
    if path is None:
        base = base_dir or Path.cwd()
        path = base / ".env"
    if path.exists():
        load_dotenv(path)


def load_toml_config(path: Path | None = None, base_dir: Path | None = None) -> dict[str, Any]:
    """
    Load config.toml file.

    Search order:
    1. Explicit path (if provided)
    2. .zwarm/config.toml (new standard location)
    3. config.toml (legacy location for backwards compat)

    Args:
        path: Explicit path to config.toml
        base_dir: Base directory to search in (defaults to cwd)
    """
    if path is None:
        base = base_dir or Path.cwd()
        # Try new location first
        new_path = base / ".zwarm" / "config.toml"
        legacy_path = base / "config.toml"
        if new_path.exists():
            path = new_path
        elif legacy_path.exists():
            path = legacy_path
        else:
            return {}
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_yaml_config(path: Path) -> dict[str, Any]:
    """
    Load YAML config with inheritance support.

    Supports 'extends: path/to/base.yaml' for composition.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    # Handle inheritance
    extends = data.pop("extends", None)
    if extends:
        base_path = (path.parent / extends).resolve()
        base_data = load_yaml_config(base_path)
        # Deep merge: data overrides base
        data = deep_merge(base_data, data)

    return data


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def apply_overrides(config: dict[str, Any], overrides: list[str]) -> dict[str, Any]:
    """
    Apply CLI overrides in format 'key.path=value'.

    Example: 'orchestrator.lm=claude-sonnet' sets config['orchestrator']['lm'] = 'claude-sonnet'
    """
    result = config.copy()
    for override in overrides:
        if "=" not in override:
            continue
        key_path, value = override.split("=", 1)
        keys = key_path.split(".")

        # Parse value (try int, float, bool, then string)
        parsed_value: Any = value
        if value.lower() == "true":
            parsed_value = True
        elif value.lower() == "false":
            parsed_value = False
        else:
            try:
                parsed_value = int(value)
            except ValueError:
                try:
                    parsed_value = float(value)
                except ValueError:
                    pass  # Keep as string

        # Navigate and set
        target = result
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = parsed_value

    return result


def load_config(
    config_path: Path | None = None,
    toml_path: Path | None = None,
    env_path: Path | None = None,
    overrides: list[str] | None = None,
    working_dir: Path | None = None,
) -> ZwarmConfig:
    """
    Load configuration with full precedence chain:
    1. Defaults (in dataclasses)
    2. config.toml (user settings)
    3. YAML config file (if provided)
    4. CLI overrides (--set key=value)
    5. Environment variables (for secrets)

    Args:
        config_path: Path to YAML config file
        toml_path: Explicit path to config.toml
        env_path: Explicit path to .env file
        overrides: CLI overrides (--set key=value)
        working_dir: Working directory to search for config files (defaults to cwd).
                    This is important when using --working-dir flag to ensure
                    config is loaded from the project directory, not invoke directory.
    """
    # Load .env first (for secrets)
    load_env(env_path, base_dir=working_dir)

    # Start with defaults
    config_dict: dict[str, Any] = {}

    # Layer in config.toml
    toml_config = load_toml_config(toml_path, base_dir=working_dir)
    if toml_config:
        config_dict = deep_merge(config_dict, toml_config)

    # Layer in YAML config
    if config_path and config_path.exists():
        yaml_config = load_yaml_config(config_path)
        config_dict = deep_merge(config_dict, yaml_config)

    # Apply CLI overrides
    if overrides:
        config_dict = apply_overrides(config_dict, overrides)

    # Apply environment variables for weave
    if os.getenv("WEAVE_PROJECT"):
        if "weave" not in config_dict:
            config_dict["weave"] = {}
        config_dict["weave"]["project"] = os.getenv("WEAVE_PROJECT")

    return ZwarmConfig.from_dict(config_dict)
