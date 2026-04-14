# tests/test_orchestrator.py
import pytest
from app.core.orchestrator import Orchestrator


def test_orchestrator_creates_context():
    orch = Orchestrator()
    assert orch is not None


def test_orchestrator_has_agents():
    orch = Orchestrator()
    assert hasattr(orch, "planner")
    assert hasattr(orch, "executor")
    assert hasattr(orch, "memory")
