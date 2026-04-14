# tests/test_core.py
import pytest
from app.core.tool_base import ToolBase
from app.core.agent_base import AgentBase


class MockTool(ToolBase):
    name = "mock_tool"
    def execute(self, **kwargs):
        return {"result": kwargs.get("input", "")}


class MockAgent(AgentBase):
    name = "mock_agent"
    def run(self, context):
        return context


def test_tool_has_name():
    tool = MockTool()
    assert tool.name == "mock_tool"


def test_tool_execute():
    tool = MockTool()
    result = tool.execute(input="hello")
    assert result == {"result": "hello"}


def test_tool_execute_empty():
    tool = MockTool()
    result = tool.execute()
    assert result == {"result": ""}


def test_agent_has_name():
    agent = MockAgent()
    assert agent.name == "mock_agent"


def test_agent_run():
    agent = MockAgent()
    ctx = {"key": "value"}
    result = agent.run(ctx)
    assert result == {"key": "value"}
