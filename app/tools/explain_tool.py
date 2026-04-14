import json
import os
from app.core.tool_base import ToolBase
from app.llm.qwen_client import QwenClient
from app.config.settings import LLM_CONFIG


class ExplainTool(ToolBase):
    """解释生成工具：结构化数据 + RAG上下文 → 带引用的解释"""

    name = "explain"

    def __init__(self):
        self._llm = QwenClient()
        self._prompt = self._load_prompt()

    def execute(self, **kwargs) -> dict:
        extracted_data = kwargs.get("extracted_data", [])
        references = kwargs.get("references", "")

        prompt = self._prompt
        prompt = prompt.replace("{references}", references or "无相关资料")
        prompt = prompt.replace("{extracted_data}", json.dumps(
            extracted_data, ensure_ascii=False, indent=2
        ))

        answer = self._llm.chat(LLM_CONFIG["models"]["explain"], prompt)

        return {"answer": answer}

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompt", "explain_prompt.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
