import base64
from io import BytesIO
from app.core.tool_base import ToolBase
from app.llm.qwen_client import QwenClient
from app.config.settings import LLM_CONFIG


class ParserTool(ToolBase):
    """报告解析工具：PDF/图片 → 文本"""

    name = "parser"

    def __init__(self):
        self._llm = QwenClient()

    def execute(self, **kwargs) -> dict:
        input_type = kwargs.get("input_type", "text")
        content = kwargs.get("content", "")

        if input_type == "text":
            return {"text": content, "input_type": "text"}

        if input_type == "pdf":
            text = self._parse_pdf(content)
        elif input_type in ("image", "img"):
            text = self._parse_image(content)
        else:
            text = content

        return {"text": text, "input_type": input_type}

    def _parse_pdf(self, content: str) -> str:
        """解析 PDF 文件，提取文本"""
        try:
            import pdfplumber
            pdf_bytes = base64.b64decode(content)
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(pages_text)
            if text.strip():
                return text
        except Exception:
            pass
        # Fallback to VL model
        return self._llm.chat(
            LLM_CONFIG["models"]["parser"],
            f"请提取以下PDF图片中的所有文字内容，保持原始格式：\n![image]({content})",
        )

    def _parse_image(self, content: str) -> str:
        """使用 VL 模型解析图片"""
        return self._llm.chat(
            LLM_CONFIG["models"]["parser"],
            f"请提取以下图片中的所有文字内容，保持原始格式：\n![image]({content})",
        )
