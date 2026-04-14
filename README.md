# report-genius-core

```
agent-service/
├── app/
│   ├── main.py                    # FastAPI入口
│   ├── controller/               # 接口层（给Java调用）
│   │   └── agent_controller.py
│   │
│   ├── core/                     # 核心框架（最重要）
│   │   ├── agent_base.py         # Agent抽象类
│   │   ├── tool_base.py          # Tool抽象类
│   │   ├── orchestrator.py       # 多Agent调度器（核心）
│   │   ├── registry.py           # Agent注册中心
│   │   └── context.py            # 全局上下文
│   │
│   ├── agents/                   # 👉 多智能体（核心）
│   │   ├── planner/              # 规划Agent
│   │   │   └── planner_agent.py
│   │   │
│   │   ├── executor/             # 执行Agent
│   │   │   └── executor_agent.py
│   │   │
│   │   ├── memory/               # 记忆Agent
│   │   │   └── memory_agent.py
│   │   │
│   │   ├── domain/               # 👉 专家Agent（关键扩展点）
│   │   │   ├── blood_test_agent.py
│   │   │   ├── liver_agent.py
│   │   │   └── general_agent.py
│   │
│   ├── tools/                    # 工具层（被Agent调用）
│   │   ├── parser_tool.py
│   │   ├── extract_tool.py
│   │   ├── rag_tool.py
│   │   └── explain_tool.py
│   │
│   ├── llm/                      # 模型封装
│   │   ├── qwen_client.py
│   │   └── embedding_client.py
│   │
│   ├── workflow/                 # 工作流（未来LangGraph替代）
│   │   └── report_workflow.py
│   │
│   ├── prompt/                   # Prompt模板
│   │   ├── extract_prompt.txt
│   │   └── explain_prompt.txt
│   │
│   ├── memory_store/             # 存储层
│   │   ├── redis_store.py
│   │   └── mongo_store.py
│   │
│   └── config/
│       └── settings.py
│
├── tests/
├── requirements.txt
└── README.md

```