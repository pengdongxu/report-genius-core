import os
import json
import numpy as np
import faiss
from app.llm.embedding_client import EmbeddingClient
from app.config.settings import RAG_CONFIG, LLM_CONFIG


class KnowledgeLoader:
    """知识库导入"""

    def __init__(self):
        self._client = EmbeddingClient()
        self._dimension = LLM_CONFIG["embedding"]["dimension"]

    def load_from_file(self, file_path: str) -> int:
        """从 JSON 文件导入知识，返回导入数量"""
        with open(file_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        return self._build_index(docs)

    def load_from_list(self, docs: list[dict]) -> int:
        """从列表导入知识，返回导入数量"""
        return self._build_index(docs)

    def _build_index(self, docs: list[dict]) -> int:
        """构建 FAISS 索引"""
        if not docs:
            return 0

        texts = [doc.get("content", "") for doc in docs]
        embeddings = self._client.embed(texts)
        vectors = np.array(embeddings, dtype=np.float32)

        index = faiss.IndexFlatL2(self._dimension)
        index.add(vectors)

        index_path = RAG_CONFIG["faiss_index_path"]
        os.makedirs(index_path, exist_ok=True)
        faiss.write_index(index, os.path.join(index_path, "index.faiss"))

        with open(os.path.join(index_path, "docs.json"), "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

        return len(docs)
