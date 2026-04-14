# tests/test_agents.py
import pytest
from unittest.mock import MagicMock
from app.agents.planner.planner_agent import PlannerAgent
from app.agents.executor.executor_agent import ExecutorAgent
from app.agents.memory.memory_agent import MemoryAgent
from app.core.context import SharedContext


def test_planner_returns_plan():
    planner = PlannerAgent()
    ctx = SharedContext(request_id="req_001")
    ctx.set("user_request", "解读这份血液报告")
    plan = planner.run(ctx)
    assert isinstance(plan, list)
    assert plan[0]["tool"] == "parser"
    assert any(step["tool"] == "desensitize" for step in plan)


def test_executor_runs_tools():
    executor = ExecutorAgent()
    ctx = SharedContext(request_id="req_001")
    plan = [
        {"tool": "parser", "params": {"input_type": "text", "content": "白细胞 12.5"}},
    ]
    mock_tool = MagicMock()
    mock_tool.execute.return_value = {"text": "白细胞 12.5", "input_type": "text"}
    executor.register_tool("parser", mock_tool)

    result = executor.run({"context": ctx, "plan": plan})
    assert ctx.get("parser_result") is not None


def test_memory_agent_stores_context():
    memory = MemoryAgent()
    ctx = SharedContext(request_id="req_001")
    ctx.set("parsed_text", "测试文本")
    result = memory.run(ctx)
    assert result.get("request_id") == "req_001"
