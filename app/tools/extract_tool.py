import json
import os
from app.core.tool_base import ToolBase
from app.llm.qwen_client import QwenClient
from app.config.settings import LLM_CONFIG


class ExtractTool(ToolBase):
    """结构化提取工具：文本 → 结构化数据"""

    name = "extract"

    def __init__(self):
        self._llm = QwenClient()
        self._prompt = self._load_prompt()

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        prompt = self._prompt.replace("{report_text}", text)

        raw = self._llm.chat(LLM_CONFIG["models"]["extract"], prompt)

        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                data = [data]
        except json.JSONDecodeError:
            data = []

        return {"extracted_data": data}

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompt", "extract_prompt.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
