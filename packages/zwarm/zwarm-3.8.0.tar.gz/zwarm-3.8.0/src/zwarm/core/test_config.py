"""Tests for the config system."""

import tempfile
from pathlib import Path

import pytest

from zwarm.core.config import (
    ZwarmConfig,
    apply_overrides,
    deep_merge,
    load_config,
    load_yaml_config,
)


def test_default_config():
    """Test default configuration values."""
    config = ZwarmConfig()
    assert config.executor.adapter == "codex_mcp"
    assert config.executor.sandbox == "workspace-write"
    assert config.orchestrator.lm == "gpt-5-mini"
    assert config.state_dir == ".zwarm"


def test_config_from_dict():
    """Test creating config from dictionary."""
    data = {
        "executor": {"adapter": "claude_code", "model": "claude-sonnet"},
        "orchestrator": {"lm": "gpt-5", "max_steps": 100},
        "state_dir": ".my_state",
    }
    config = ZwarmConfig.from_dict(data)
    assert config.executor.adapter == "claude_code"
    assert config.executor.model == "claude-sonnet"
    assert config.orchestrator.lm == "gpt-5"
    assert config.orchestrator.max_steps == 100
    assert config.state_dir == ".my_state"


def test_config_to_dict():
    """Test converting config to dictionary."""
    config = ZwarmConfig()
    data = config.to_dict()
    assert data["executor"]["adapter"] == "codex_mcp"
    assert data["orchestrator"]["lm"] == "gpt-5-mini"


def test_deep_merge():
    """Test deep merging of dictionaries."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}, "e": 4}
    result = deep_merge(base, override)
    assert result == {"a": 1, "b": {"c": 99, "d": 3}, "e": 4}


def test_apply_overrides():
    """Test CLI override application."""
    config = {"executor": {"adapter": "codex"}, "orchestrator": {"max_steps": 10}}

    # Override nested value
    result = apply_overrides(config, ["orchestrator.max_steps=50"])
    assert result["orchestrator"]["max_steps"] == 50

    # Override with string
    result = apply_overrides(config, ["executor.adapter=claude_code"])
    assert result["executor"]["adapter"] == "claude_code"

    # Override with boolean
    result = apply_overrides(config, ["executor.web_search=true"])
    assert result["executor"]["web_search"] is True

    # Create new nested path
    result = apply_overrides(config, ["weave.project=my-project"])
    assert result["weave"]["project"] == "my-project"


def test_yaml_inheritance():
    """Test YAML config inheritance via extends."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "base.yaml"
        child_path = Path(tmpdir) / "child.yaml"

        # Write base config
        base_path.write_text("""
executor:
  adapter: codex_mcp
  timeout: 3600
orchestrator:
  lm: gpt-5-mini
  max_steps: 30
""")

        # Write child config that extends base
        child_path.write_text("""
extends: base.yaml
orchestrator:
  lm: gpt-5
  prompt: prompts/aggressive.yaml
""")

        config = load_yaml_config(child_path)
        assert config["executor"]["adapter"] == "codex_mcp"
        assert config["executor"]["timeout"] == 3600
        assert config["orchestrator"]["lm"] == "gpt-5"  # overridden
        assert config["orchestrator"]["max_steps"] == 30  # inherited
        assert config["orchestrator"]["prompt"] == "prompts/aggressive.yaml"  # new


def test_load_config_full_chain():
    """Test full config loading with precedence."""
    import os

    # Save and clear WEAVE_PROJECT to test config precedence
    orig_weave = os.environ.pop("WEAVE_PROJECT", None)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write config.toml
            toml_path = tmpdir / "config.toml"
            toml_path.write_text("""
[weave]
project = "my-weave-project"

[executor]
adapter = "codex_mcp"
""")

            # Write yaml config
            yaml_path = tmpdir / "experiment.yaml"
            yaml_path.write_text("""
orchestrator:
  lm: claude-sonnet
  max_steps: 100
""")

            # Load with override (use non-existent env_path to prevent loading cwd's .env)
            config = load_config(
                config_path=yaml_path,
                toml_path=toml_path,
                env_path=tmpdir / ".env.nonexistent",
                overrides=["orchestrator.max_steps=200"],
            )

            # Check precedence: override > yaml > toml > default
            assert config.weave.project == "my-weave-project"  # from toml
            assert config.executor.adapter == "codex_mcp"  # from toml
            assert config.orchestrator.lm == "claude-sonnet"  # from yaml
            assert config.orchestrator.max_steps == 200  # from override
    finally:
        # Restore WEAVE_PROJECT
        if orig_weave is not None:
            os.environ["WEAVE_PROJECT"] = orig_weave


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
