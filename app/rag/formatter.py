class RefFormatter:
    """引用标注格式化"""

    def __init__(self):
        self.references: list[dict] = []

    def format(self, docs: list[dict]) -> str:
        """将检索到的文档格式化为带 [ref_x] 标注的文本"""
        self.references = []
        parts = []
        for i, doc in enumerate(docs, 1):
            ref_id = f"ref_{i}"
            self.references.append({
                "id": ref_id,
                "content": doc.get("content", ""),
                "source": doc.get("source", ""),
                "url": doc.get("url", ""),
            })
            parts.append(f"[{ref_id}] {doc.get('content', '')}")

        return "\n".join(parts)

    def to_list(self) -> list[dict]:
        """返回引用列表（用于最终结果）"""
        return [
            {"id": r["id"], "source": r["source"], "url": r["url"]}
            for r in self.references
        ]
