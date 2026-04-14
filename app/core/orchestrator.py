from app.core.context import SharedContext
from app.agents.planner.planner_agent import PlannerAgent
from app.agents.executor.executor_agent import ExecutorAgent
from app.agents.memory.memory_agent import MemoryAgent
from app.tools.parser_tool import ParserTool
from app.tools.desensitize_tool import DesensitizeTool
from app.tools.extract_tool import ExtractTool
from app.tools.rag_tool import RAGTool
from app.tools.explain_tool import ExplainTool
from app.tools.web_search_tool import WebSearchTool


class Orchestrator:
    """调度核心：协调 Agent 和 Tool 的执行流程"""

    def __init__(self):
        self.memory = MemoryAgent()
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()

        # 注册所有 Tool
        self.executor.register_tool(ParserTool())
        self.executor.register_tool(DesensitizeTool())
        self.executor.register_tool(ExtractTool())
        self.executor.register_tool(RAGTool())
        self.executor.register_tool(ExplainTool())
        self.executor.register_tool(WebSearchTool())

    def process(self, request_id: str, content: str, input_type: str = "text") -> dict:
        """处理报告解读请求的完整流程"""
        # 1. 创建共享上下文
        context = SharedContext(request_id=request_id)
        context.set("input_type", input_type)
        context.set("user_request", content)

        # 2. 规划执行计划
        plan = self.planner.run(context)

        # 3. 注入用户输入到 parser 参数
        if plan and plan[0]["tool"] == "parser":
            plan[0]["params"]["content"] = content

        # 4. 执行计划
        self.executor.run({"context": context, "plan": plan})

        # 5. 返回结果
        explain_result = context.get("explain_result", {})
        rag_result = context.get("rag_result", {})

        return {
            "request_id": request_id,
            "answer": explain_result.get("answer", ""),
            "references": rag_result.get("references", []),
        }
