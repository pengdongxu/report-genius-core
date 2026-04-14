from dashscope import TextEmbedding
from app.config.settings import LLM_CONFIG


class EmbeddingClient:
    """Embedding 客户端"""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._call_api(texts)

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        response = TextEmbedding.call(
            model=LLM_CONFIG["embedding"]["model"],
            input=texts,
            api_key=LLM_CONFIG["api_key"],
        )

        if response.status_code == 200:
            return [item["embedding"] for item in response.output["embeddings"]]
        raise RuntimeError(f"Embedding call failed: {response.status_code}")
