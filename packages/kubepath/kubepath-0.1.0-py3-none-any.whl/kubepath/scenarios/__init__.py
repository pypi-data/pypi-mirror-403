"""Scenario engine for debugging challenges."""

from kubepath.scenarios.cleanup import CleanupManager
from kubepath.scenarios.hints import HintManager, HintResult
from kubepath.scenarios.history import CommandHistory, CommandRecord
from kubepath.scenarios.engine import (
    ScenarioEngine,
    ScenarioState,
    ScenarioResult,
    ScenarioContext,
    create_scenario_engine,
)

__all__ = [
    "CleanupManager",
    "HintManager",
    "HintResult",
    "CommandHistory",
    "CommandRecord",
    "ScenarioEngine",
    "ScenarioState",
    "ScenarioResult",
    "ScenarioContext",
    "create_scenario_engine",
]
