# report-genius-core

基于多智能体（Multi-Agent）的报告解读系统。

## 一、项目目标

- 支持文本/语音/PDF/图片报告解析
- 自动结构化数据提取
- 基于知识库（RAG）进行解释
- 返回带参考文献的结果
- 支持扩展（不限领域）

---

## 二、快速开始

### 1. 环境要求

- Python 3.10+
- Redis（缓存）
- MongoDB（持久化）
- 阿里云 DashScope API Key

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 必填
export DASHSCOPE_API_KEY="your-api-key"

# 可选（有默认值）
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB_NAME="report_genius"
```

### 4. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# API 文档
# 浏览器打开 http://localhost:8000/docs
```

### 6. 调用接口

**文本报告解读：**
```bash
curl -X POST http://localhost:8000/api/v1/report/parse \
  -H "Content-Type: application/json" \
  -d '{"content": "白细胞 12.5×10^9/L，正常范围 4-10×10^9/L"}'
```

**文件上传解读：**
```bash
curl -X POST http://localhost:8000/api/v1/report/upload \
  -F "file=@report.pdf"
```

**返回示例：**
```json
{
  "request_id": "req_xxx",
  "answer": "白细胞升高提示感染 [ref_1]",
  "references": [
    {
      "id": "ref_1",
      "source": "临床指南",
      "url": "https://xxx"
    }
  ]
}
```

---

## 三、核心设计思想

### 核心原则

> 不使用"领域专家 Agent"，而是采用：
>
> 能力模块（Tool） + RAG（知识库）

| 方案 | 问题 |
| --- | --- |
| 领域 Agent | 难扩展、维护复杂 |
| 能力模块 + RAG | 灵活、可扩展、数据驱动 |

> 模型负责"能力"，RAG 负责"知识"

---

## 四、项目结构

```
report-genius-core/
├── app/
│   ├── main.py                          # FastAPI 入口
│   ├── controller/
│   │   └── agent_controller.py          # HTTP API 路由
│   ├── core/
│   │   ├── agent_base.py                # Agent 基类
│   │   ├── tool_base.py                 # Tool 基类
│   │   ├── orchestrator.py              # 调度核心
│   │   ├── registry.py                  # 注册表
│   │   └── context.py                   # 请求上下文
│   ├── agents/
│   │   ├── planner/planner_agent.py     # 任务规划
│   │   ├── executor/executor_agent.py   # 执行器
│   │   └── memory/memory_agent.py       # 上下文管理
│   ├── tools/
│   │   ├── parser_tool.py               # PDF/图片 → 文本
│   │   ├── desensitize_tool.py          # 脱敏
│   │   ├── extract_tool.py              # 文本 → 结构化数据
│   │   ├── rag_tool.py                  # 知识检索
│   │   ├── explain_tool.py              # 解释生成（带引用）
│   │   └── web_search_tool.py           # 联网搜索（可选）
│   ├── rag/
│   │   ├── retriever.py                 # 向量检索
│   │   ├── formatter.py                 # 引用格式化
│   │   └── knowledge_loader.py          # 知识导入
│   ├── llm/
│   │   ├── qwen_client.py               # 通义千问客户端
│   │   └── embedding_client.py          # Embedding 客户端
│   ├── prompt/
│   │   ├── extract_prompt.txt
│   │   ├── explain_prompt.txt
│   │   └── planner_prompt.txt
│   ├── memory_store/
│   │   ├── redis_store.py               # Redis 缓存
│   │   ├── mongo_store.py               # MongoDB 持久化
│   │   └── sensitive_mapping_store.py   # 脱敏映射持久化
│   └── config/
│       └── settings.py                  # 全局配置
├── docs/                                # 详细设计文档
├── tests/                               # 测试
└── requirements.txt
```

---

## 五、核心架构图

```
                    ┌────────────────────┐
                    │     前端 / 用户        │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Java Backend      │
                    │（业务 / 鉴权 / 存储） │
                    └─────────┬──────────┘
                              │ HTTP
                    ┌─────────▼──────────┐
                    │ Python Agent Service│
                    └─────────┬──────────┘
                              │
                 ┌────────────▼────────────┐
                 │   Orchestrator（调度）    │
                 └───────┬─────────┬───────┘
                         │         │
                ┌────────▼───┐ ┌───▼────────┐
                │ Planner    │ │  Memory     │
                │（任务规划） │ │（上下文）    │
                └────────┬───┘ └────┬──────┘
                         │           │
                         ▼           ▼
                ┌──────────────────────────┐
                │     Executor（执行器）     │
                └──────────┬──────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
 ┌──▼───────┐     ┌────────▼────────┐     ┌──────▼────────┐
 │ Parser   │     │ Extract Tool     │     │   RAG Tool     │
 │（解析）   │     │（结构化）         │     │（知识检索）    │
 └────┬─────┘     └────────┬────────┘     └──────┬────────┘
      │                    │                      │
      ▼                    │                      │
 ┌────────────────┐        │                      │
 │ Desensitize    │        │                      │
 │（脱敏）         │        │                      │
 └────┬───────────┘        │                      │
      │                    │                      │
      └──────────────┬─────┴──────────────┬──────┘
                     ▼                    ▼
              ┌─────────────────────────────────┐
              │    Explain Tool（解释生成）        │
              │    + 引用标注 [ref_x]             │
              └──────────────┬──────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  LLM（通义千问）     │
                   │  + Embedding       │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │   知识库（RAG）      │
                   │（带 source / url）   │
                   └────────────────────┘
```

---

## 六、执行流程

```
用户上传报告
 ↓
Parser（解析）
 ↓
Desensitize（脱敏）
 ↓
Extract（结构化）
 ↓
RAG（知识检索）
 ↓
Explain（带引用解释）
 ↓
返回结果
```

---

## 七、详细设计文档

| 文档 | 说明 |
| --- | --- |
| [模块与 Tool 设计](docs/module-design.md) | 核心模块说明、Tool 设计、返回格式 |
| [RAG 设计](docs/rag-design.md) | 数据结构、检索流程、引用格式化、知识导入 |
| [脱敏设计](docs/desensitize-design.md) | 脱敏规则、替换策略、映射持久化 |
| [配置与模型](docs/configuration.md) | Prompt 设计、模型选型、联网搜索、性能优化、系统演进 |

---

## 八、总结

> 本系统本质是：
>
> 一个"通用能力 Agent + 外部知识库（RAG）"系统

> 核心设计原则：
>
> - 不把领域知识写死在代码中
> - 所有知识进入 RAG 系统
> - Agent 只负责调度与能力执行
