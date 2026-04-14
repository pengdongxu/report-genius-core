import pytest
from unittest.mock import patch, MagicMock
from app.memory_store.sensitive_mapping_store import SensitiveMappingStore


def test_save_mapping():
    store = SensitiveMappingStore()
    with patch.object(store, "_collection", new_callable=MagicMock) as mock_col:
        store.save_mapping("req_001", {"[姓名_1]": "张三"})
        mock_col.insert_one.assert_called_once()


def test_get_mapping():
    store = SensitiveMappingStore()
    with patch.object(store, "_collection", new_callable=MagicMock) as mock_col:
        mock_col.find_one.return_value = {
            "request_id": "req_001",
            "mappings": {"[姓名_1]": "张三"},
        }
        result = store.get_mapping("req_001")
        assert result == {"[姓名_1]": "张三"}
