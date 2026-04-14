from app.core.tool_base import ToolBase
from app.rag.retriever import Retriever
from app.rag.formatter import RefFormatter


class RAGTool(ToolBase):
    """知识检索工具：查询 RAG 知识库"""

    name = "rag"

    def __init__(self):
        self._retriever = Retriever()
        self._formatter = RefFormatter()

    def execute(self, **kwargs) -> dict:
        query = kwargs.get("query", "")

        docs = self._retriever.search(query)
        formatted = self._formatter.format(docs)

        return {
            "formatted_context": formatted,
            "references": self._formatter.to_list(),
        }
