from app.core.tool_base import ToolBase
from app.config.settings import WEB_SEARCH_CONFIG


class WebSearchTool(ToolBase):
    """联网搜索工具：补充实时信息（可选，默认关闭）"""

    name = "web_search"

    def execute(self, **kwargs) -> dict:
        if not WEB_SEARCH_CONFIG["enabled"]:
            return {"web_context": "", "used": False}

        query = kwargs.get("query", "")
        return {"web_context": "", "used": False, "query": query}
