import pytest
import json
from unittest.mock import patch
from app.tools.extract_tool import ExtractTool


def test_extract_calls_llm():
    tool = ExtractTool()
    mock_response = json.dumps([
        {"name": "白细胞", "value": "12.5", "normal_range": "4-10", "is_abnormal": True}
    ], ensure_ascii=False)
    with patch.object(tool._llm, "chat", return_value=mock_response) as mock:
        result = tool.execute(text="白细胞 12.5×10^9/L")
        mock.assert_called_once()
        data = result["extracted_data"]
        assert len(data) == 1
        assert data[0]["name"] == "白细胞"
