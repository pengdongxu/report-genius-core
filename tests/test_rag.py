import pytest
from app.rag.formatter import RefFormatter


def test_format_refs():
    formatter = RefFormatter()
    docs = [
        {"id": "doc_1", "content": "白细胞升高提示感染", "source": "临床指南", "url": "https://xxx"},
        {"id": "doc_2", "content": "正常范围4-10", "source": "教材", "url": ""},
    ]
    refs = formatter.format(docs)
    assert "[ref_1]" in refs
    assert "白细胞升高提示感染" in refs
    assert len(formatter.references) == 2
    assert formatter.references[0]["id"] == "ref_1"
    assert formatter.references[0]["source"] == "临床指南"


def test_format_empty():
    formatter = RefFormatter()
    refs = formatter.format([])
    assert refs == ""
    assert formatter.references == []
