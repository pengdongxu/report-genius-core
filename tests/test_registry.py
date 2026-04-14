# tests/test_registry.py
import pytest
from app.core.registry import Registry
from app.core.tool_base import ToolBase


class FakeTool(ToolBase):
    name = "fake_tool"
    def execute(self, **kwargs):
        return {}


def test_register_and_get():
    reg = Registry()
    tool = FakeTool()
    reg.register("fake_tool", tool)
    assert reg.get("fake_tool") is tool


def test_get_missing_raises():
    reg = Registry()
    with pytest.raises(KeyError):
        reg.get("nonexistent")


def test_list_all():
    reg = Registry()
    reg.register("a", FakeTool())
    reg.register("b", FakeTool())
    assert len(reg.list_all()) == 2
    assert "a" in reg.list_all()
