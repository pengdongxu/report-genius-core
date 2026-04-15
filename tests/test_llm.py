import pytest
from unittest.mock import patch, MagicMock
from app.llm.qwen_client import QwenClient
from app.llm.embedding_client import EmbeddingClient


def test_qwen_client_chat():
    client = QwenClient()
    with patch.object(client, "_call_api", return_value='{"result": "ok"}') as mock:
        result = client.chat("qwen-plus", "hello", [])
        assert result == '{"result": "ok"}'
        mock.assert_called_once_with("qwen-plus", "hello", [], None)


def test_embedding_client_embed():
    client = EmbeddingClient()
    with patch.object(client, "_call_api", return_value=[[0.1] * 10]) as mock:
        result = client.embed(["hello"])
        assert result == [[0.1] * 10]
        mock.assert_called_once_with(["hello"])
