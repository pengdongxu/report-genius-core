import pytest
from unittest.mock import patch
from app.tools.rag_tool import RAGTool


def test_rag_tool_search():
    tool = RAGTool()
    mock_docs = [
        {"id": "doc_1", "content": "白细胞升高提示感染", "source": "临床指南", "url": "https://xxx"}
    ]
    with patch.object(tool._retriever, "search", return_value=mock_docs):
        result = tool.execute(query="白细胞升高怎么办")
        assert "formatted_context" in result
        assert "references" in result
        assert len(result["references"]) == 1


def test_rag_tool_empty():
    tool = RAGTool()
    with patch.object(tool._retriever, "search", return_value=[]):
        result = tool.execute(query="未知指标")
        assert result["formatted_context"] == ""
        assert result["references"] == []
