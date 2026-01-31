"""Tests for orchestrator watcher integration."""

from zwarm.core.config import WeaveConfig, ZwarmConfig
from zwarm.core.environment import OrchestratorEnv
from zwarm.orchestrator import Orchestrator
from zwarm.prompts import get_orchestrator_prompt
from zwarm.watchers import WatcherAction


def test_run_watchers_builds_context(tmp_path):
    """Orchestrator should build WatcherContext without crashing."""
    config = ZwarmConfig(weave=WeaveConfig(enabled=False))
    env = OrchestratorEnv(task="Test task", working_dir=tmp_path)

    orchestrator = Orchestrator(
        config=config,
        working_dir=tmp_path,
        system_prompt=get_orchestrator_prompt(working_dir=str(tmp_path)),
        maxSteps=3,
        env=env,
    )

    assert orchestrator._run_watchers() == WatcherAction.CONTINUE
