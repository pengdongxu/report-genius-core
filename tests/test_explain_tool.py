import pytest
from unittest.mock import patch
from app.tools.explain_tool import ExplainTool


def test_explain_calls_llm():
    tool = ExplainTool()
    with patch.object(tool._llm, "chat", return_value="白细胞升高提示感染 [ref_1]") as mock:
        result = tool.execute(
            extracted_data=[{"name": "白细胞", "value": "12.5", "is_abnormal": True}],
            references="[ref_1] 白细胞升高通常提示感染",
        )
        mock.assert_called_once()
        assert "answer" in result
        assert result["answer"] == "白细胞升高提示感染 [ref_1]"
