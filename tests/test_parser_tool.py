import pytest
from unittest.mock import patch
from app.tools.parser_tool import ParserTool


def test_parse_text_input():
    tool = ParserTool()
    result = tool.execute(input_type="text", content="白细胞 12.5")
    assert result["text"] == "白细胞 12.5"
    assert result["input_type"] == "text"


def test_parse_pdf_calls_llm():
    tool = ParserTool()
    with patch.object(tool._llm, "chat", return_value="解析出的文本内容") as mock:
        result = tool.execute(input_type="pdf", content="base64encoded...")
        mock.assert_called_once()
        assert "text" in result
