import pytest
from unittest.mock import patch, MagicMock
from app.tools.desensitize_tool import DesensitizeTool


def test_desensitize_phone_mask():
    with patch("app.tools.desensitize_tool.SensitiveMappingStore") as MockStore:
        mock_instance = MagicMock()
        MockStore.return_value = mock_instance
        tool = DesensitizeTool()
        result = tool.execute(text="联系电话13812345678，请回拨", request_id="req_001")
        assert "13812345678" not in result["desensitized_text"]
        assert "138****5678" in result["desensitized_text"]
        assert result["mapping_count"] > 0


def test_desensitize_placeholder():
    with patch("app.tools.desensitize_tool.SensitiveMappingStore") as MockStore:
        mock_instance = MagicMock()
        MockStore.return_value = mock_instance
        tool = DesensitizeTool()
        result = tool.execute(text="患者张三先生，前往北京协和医院就诊", request_id="req_002")
        assert "张三" not in result["desensitized_text"]
        assert "[姓名]" in result["desensitized_text"]
        assert "[医院名称]" in result["desensitized_text"]


def test_desensitize_no_match():
    with patch("app.tools.desensitize_tool.SensitiveMappingStore") as MockStore:
        mock_instance = MagicMock()
        MockStore.return_value = mock_instance
        tool = DesensitizeTool()
        result = tool.execute(text="白细胞升高，建议复查", request_id="req_003")
        assert result["desensitized_text"] == "白细胞升高，建议复查"
        assert result["mapping_count"] == 0
