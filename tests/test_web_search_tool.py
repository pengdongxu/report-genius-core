import pytest
from app.tools.web_search_tool import WebSearchTool


def test_web_search_disabled():
    tool = WebSearchTool()
    result = tool.execute(query="白细胞高怎么办")
    assert result["web_context"] == ""
    assert result["used"] is False
