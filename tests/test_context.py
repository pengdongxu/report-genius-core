# tests/test_context.py
import pytest
from app.core.context import SharedContext


def test_set_and_get():
    ctx = SharedContext(request_id="req_001")
    ctx.set("parsed_text", "白细胞 12.5")
    assert ctx.get("parsed_text") == "白细胞 12.5"


def test_get_default():
    ctx = SharedContext(request_id="req_001")
    assert ctx.get("missing", "default") == "default"


def test_request_id():
    ctx = SharedContext(request_id="req_001")
    assert ctx.request_id == "req_001"


def test_to_dict():
    ctx = SharedContext(request_id="req_001")
    ctx.set("key", "value")
    d = ctx.to_dict()
    assert d["request_id"] == "req_001"
    assert d["data"]["key"] == "value"


def test_update():
    ctx = SharedContext(request_id="req_001")
    ctx.update({"a": 1, "b": 2})
    assert ctx.get("a") == 1
    assert ctx.get("b") == 2
