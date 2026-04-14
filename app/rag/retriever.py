import os
import json
import numpy as np
import faiss
from app.llm.embedding_client import EmbeddingClient
from app.config.settings import RAG_CONFIG


class Retriever:
    """向量检索器"""

    def __init__(self):
        self._client = EmbeddingClient()
        self._top_k = RAG_CONFIG["top_k"]
        self._threshold = RAG_CONFIG["score_threshold"]
        self._index = None
        self._docs: list[dict] = []
        self._load_index()

    def _load_index(self):
        index_path = RAG_CONFIG["faiss_index_path"]
        faiss_file = os.path.join(index_path, "index.faiss")
        docs_file = os.path.join(index_path, "docs.json")
        if os.path.exists(faiss_file) and os.path.exists(docs_file):
            self._index = faiss.read_index(faiss_file)
            with open(docs_file, "r", encoding="utf-8") as f:
                self._docs = json.load(f)

    def search(self, query: str) -> list[dict]:
        """检索与 query 最相关的文档"""
        if self._index is None:
            return []

        embeddings = self._client.embed([query])
        query_vector = np.array(embeddings, dtype=np.float32)
        distances, indices = self._index.search(query_vector, self._top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self._docs):
                score = 1.0 / (1.0 + distances[0][i])
                if score >= self._threshold:
                    results.append(self._docs[idx])

        return results
