# Phase 1: 固定流程 Tool 链路 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现报告解读系统的固定流程 Tool 链路：用户上传报告 → Parser → Desensitize → Extract → RAG → Explain → 返回结果（带引用）

**Architecture:** 基于能力模块（Tool）+ RAG 的设计，Orchestrator 调度 Planner/Executor/Memory 三个 Agent，Executor 按固定顺序执行 Tool 链路。所有领域知识通过 RAG 检索获取，不写死在代码中。

**Tech Stack:** Python 3.10+, FastAPI, DashScope（通义千问 SDK）, FAISS（向量检索）, Redis, MongoDB, Pydantic

---

## File Structure

```
app/
├── main.py                          # FastAPI 入口
├── controller/
│   └── agent_controller.py          # HTTP API 路由
├── core/
│   ├── agent_base.py                # Agent 基类
│   ├── tool_base.py                 # Tool 基类
│   ├── orchestrator.py              # 调度核心
│   ├── registry.py                  # Tool/Agent 注册表
│   └── context.py                   # 请求上下文（Agent 间共享数据）
├── agents/
│   ├── planner/planner_agent.py     # 任务规划（Phase 1 返回固定计划）
│   ├── executor/executor_agent.py   # 执行器（按计划调用 Tool）
│   └── memory/memory_agent.py       # 上下文管理
├── tools/
│   ├── parser_tool.py               # PDF/图片 → 文本
│   ├── desensitize_tool.py          # 脱敏
│   ├── extract_tool.py              # 文本 → 结构化数据
│   ├── rag_tool.py                  # 知识检索
│   ├── explain_tool.py              # 解释生成（带引用）
│   └── web_search_tool.py           # 联网搜索（可选）
├── rag/
│   ├── retriever.py                 # 向量检索
│   ├── formatter.py                 # ref_id 封装
│   └── knowledge_loader.py          # 知识导入
├── llm/
│   ├── qwen_client.py               # 通义千问 API 客户端
│   └── embedding_client.py          # Embedding 客户端
├── prompt/
│   ├── extract_prompt.txt           # Extract 提示词
│   ├── explain_prompt.txt           # Explain 提示词
│   └── planner_prompt.txt           # Planner 提示词
├── memory_store/
│   ├── redis_store.py               # Redis 缓存
│   ├── mongo_store.py               # MongoDB 持久化
│   └── sensitive_mapping_store.py   # 脱敏映射持久化
└── config/
    └── settings.py                  # 全局配置
```

---

### Task 1: 项目配置与依赖

**Files:**
- Create: `requirements.txt`
- Modify: `app/config/settings.py`

- [ ] **Step 1: 安装依赖并写入 requirements.txt**

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
dashscope>=1.14.0
faiss-cpu>=1.7.4
redis>=5.0.0
pymongo>=4.6.0
python-multipart>=0.0.6
Pillow>=10.0.0
pdfplumber>=0.10.0
pytest>=7.4.0
httpx>=0.25.0
```

Run: `pip install -r requirements.txt`

- [ ] **Step 2: 实现 settings.py 配置**

```python
import os


# LLM 配置
LLM_CONFIG = {
    "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
    "models": {
        "parser": "qwen-vl-max",       # 图片/PDF解析
        "extract": "qwen-plus",         # 结构化提取
        "explain": "qwen-max",          # 解释生成
        "planner": "qwen-plus",         # 任务规划
    },
    "embedding": {
        "model": "text-embedding-v2",
        "dimension": 1536,
    },
}

# RAG 配置
RAG_CONFIG = {
    "faiss_index_path": os.getenv("FAISS_INDEX_PATH", "./data/faiss_index"),
    "top_k": 5,
    "score_threshold": 0.7,
}

# Redis 配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD", ""),
}

# MongoDB 配置
MONGO_CONFIG = {
    "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    "db_name": os.getenv("MONGO_DB_NAME", "report_genius"),
}

# 脱敏配置
DESENSITIZE_CONFIG = {
    "rules": {
        "name":          {"pattern": r"[\u4e00-\u9fa5]{2,4}(?=的|先生|女士|患者)", "strategy": "placeholder", "label": "[姓名]"},
        "id_card":       {"pattern": r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b", "strategy": "placeholder", "label": "[身份证号]"},
        "phone":         {"pattern": r"\b1[3-9]\d{9}\b", "strategy": "mask", "label": ""},
        "address":       {"pattern": r"[\u4e00-\u9fa5]{2,}(?:省|市|区|县|镇|乡|村|路|号|栋|室)", "strategy": "placeholder", "label": "[地址]"},
        "medical_id":    {"pattern": r"(?:就诊号|门诊号)[：:]\s*\S+", "strategy": "placeholder", "label": "[就诊号]"},
        "record_no":     {"pattern": r"(?:病历号)[：:]\s*\S+", "strategy": "placeholder", "label": "[病历号]"},
        "bed_no":        {"pattern": r"(?:床号|床位)[：:]\s*\S+", "strategy": "placeholder", "label": "[床号]"},
        "hospital_name": {"pattern": r"[\u4e00-\u9fa5]{2,}(?:医院|卫生院|诊所|中心)", "strategy": "placeholder", "label": "[医院名称]"},
    },
    "custom_rules": [],
    "default_strategy": "placeholder",
}

# Web Search 配置
WEB_SEARCH_CONFIG = {
    "enabled": False,
    "rag_confidence_threshold": 0.5,
}
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt app/config/settings.py
git commit -m "feat: add project dependencies and settings configuration"
```

---

### Task 2: Core - Tool 基类与 Agent 基类

**Files:**
- Modify: `app/core/tool_base.py`
- Modify: `app/core/agent_base.py`
- Create: `tests/test_core.py`

- [ ] **Step 1: 编写 tool_base 和 agent_base 的测试**

```python
# tests/test_core.py
import pytest
from abc import ABC
from app.core.tool_base import ToolBase
from app.core.agent_base import AgentBase


class MockTool(ToolBase):
    name = "mock_tool"

    def execute(self, **kwargs):
        return {"result": kwargs.get("input", "")}


class MockAgent(AgentBase):
    name = "mock_agent"

    def run(self, context):
        return context


def test_tool_has_name():
    tool = MockTool()
    assert tool.name == "mock_tool"


def test_tool_execute():
    tool = MockTool()
    result = tool.execute(input="hello")
    assert result == {"result": "hello"}


def test_tool_execute_empty():
    tool = MockTool()
    result = tool.execute()
    assert result == {"result": ""}


def test_agent_has_name():
    agent = MockAgent()
    assert agent.name == "mock_agent"


def test_agent_run():
    agent = MockAgent()
    ctx = {"key": "value"}
    result = agent.run(ctx)
    assert result == {"key": "value"}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_core.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: 实现 ToolBase**

```python
# app/core/tool_base.py
from abc import ABC, abstractmethod


class ToolBase(ABC):
    """能力模块基类"""

    name: str = ""

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """执行工具，返回结果字典"""
        ...
```

- [ ] **Step 4: 实现 AgentBase**

```python
# app/core/agent_base.py
from abc import ABC, abstractmethod


class AgentBase(ABC):
    """Agent 基类"""

    name: str = ""

    @abstractmethod
    def run(self, context: dict) -> dict:
        """执行 Agent 逻辑，context 为共享上下文"""
        ...
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_core.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add app/core/tool_base.py app/core/agent_base.py tests/test_core.py
git commit -m "feat: add ToolBase and AgentBase abstract classes"
```

---

### Task 3: Core - Context 请求上下文

**Files:**
- Modify: `app/core/context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_context.py
import pytest
from app.core.context import SharedContext


def test_set_and_get():
    ctx = SharedContext(request_id="req_001")
    ctx.set("parsed_text", "白细胞 12.5")
    assert ctx.get("parsed_text") == "白细胞 12.5"


def test_get_default():
    ctx = SharedContext(request_id="req_001")
    assert ctx.get("missing", "default") == "default"


def test_request_id():
    ctx = SharedContext(request_id="req_001")
    assert ctx.request_id == "req_001"


def test_to_dict():
    ctx = SharedContext(request_id="req_001")
    ctx.set("key", "value")
    d = ctx.to_dict()
    assert d["request_id"] == "req_001"
    assert d["data"]["key"] == "value"


def test_update():
    ctx = SharedContext(request_id="req_001")
    ctx.update({"a": 1, "b": 2})
    assert ctx.get("a") == 1
    assert ctx.get("b") == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_context.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: 实现 SharedContext**

```python
# app/core/context.py
class SharedContext:
    """Agent 间共享的请求上下文"""

    def __init__(self, request_id: str):
        self.request_id = request_id
        self._data: dict = {}

    def set(self, key: str, value):
        self._data[key] = value

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def update(self, data: dict):
        self._data.update(data)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "data": self._data,
        }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_context.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/context.py tests/test_context.py
git commit -m "feat: add SharedContext for inter-agent data sharing"
```

---

### Task 4: Core - Registry 注册表

**Files:**
- Modify: `app/core/registry.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_registry.py
import pytest
from app.core.registry import Registry
from app.core.tool_base import ToolBase


class FakeTool(ToolBase):
    name = "fake_tool"
    def execute(self, **kwargs):
        return {}


def test_register_and_get():
    reg = Registry()
    tool = FakeTool()
    reg.register("fake_tool", tool)
    assert reg.get("fake_tool") is tool


def test_get_missing_raises():
    reg = Registry()
    with pytest.raises(KeyError):
        reg.get("nonexistent")


def test_list_all():
    reg = Registry()
    reg.register("a", FakeTool())
    reg.register("b", FakeTool())
    assert len(reg.list_all()) == 2
    assert "a" in reg.list_all()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_registry.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: 实现 Registry**

```python
# app/core/registry.py


class Registry:
    """Tool 和 Agent 的注册表"""

    def __init__(self):
        self._items: dict[str, object] = {}

    def register(self, name: str, item):
        self._items[name] = item

    def get(self, name: str):
        if name not in self._items:
            raise KeyError(f"'{name}' not registered")
        return self._items[name]

    def list_all(self) -> list[str]:
        return list(self._items.keys())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_registry.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/registry.py tests/test_registry.py
git commit -m "feat: add Registry for tool/agent registration"
```

---

### Task 5: LLM 客户端

**Files:**
- Modify: `app/llm/qwen_client.py`
- Modify: `app/llm/embedding_client.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_llm.py
import pytest
from unittest.mock import patch, MagicMock
from app.llm.qwen_client import QwenClient
from app.llm.embedding_client import EmbeddingClient


def test_qwen_client_chat():
    client = QwenClient()
    with patch.object(client, "_call_api", return_value='{"result": "ok"}') as mock:
        result = client.chat("qwen-plus", "hello", [])
        assert result == '{"result": "ok"}'
        mock.assert_called_once_with("qwen-plus", "hello", [])


def test_embedding_client_embed():
    client = EmbeddingClient()
    with patch.object(client, "_call_api", return_value=[[0.1] * 10]) as mock:
        result = client.embed(["hello"])
        assert result == [[0.1] * 10]
        mock.assert_called_once_with(["hello"])
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: 实现 QwenClient**

```python
# app/llm/qwen_client.py
from dashscope import Generation
from app.config.settings import LLM_CONFIG


class QwenClient:
    """通义千问 API 客户端"""

    def chat(self, model: str, message: str, system_prompt: str = "") -> str:
        return self._call_api(model, message, system_prompt)

    def _call_api(self, model: str, message: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = Generation.call(
            model=model,
            messages=messages,
            api_key=LLM_CONFIG["api_key"],
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        raise RuntimeError(f"LLM call failed: {response.status_code} - {response.message}")
```

- [ ] **Step 4: 实现 EmbeddingClient**

```python
# app/llm/embedding_client.py
from dashscope import TextEmbedding
from app.config.settings import LLM_CONFIG


class EmbeddingClient:
    """Embedding 客户端"""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._call_api(texts)

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        response = TextEmbedding.call(
            model=LLM_CONFIG["embedding"]["model"],
            input=texts,
            api_key=LLM_CONFIG["api_key"],
        )

        if response.status_code == 200:
            return [item["embedding"] for item in response.output["embeddings"]]
        raise RuntimeError(f"Embedding call failed: {response.status_code}")
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_llm.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add app/llm/qwen_client.py app/llm/embedding_client.py tests/test_llm.py
git commit -m "feat: add QwenClient and EmbeddingClient for LLM integration"
```

---

### Task 6: Memory Store（Redis + MongoDB + 脱敏映射）

**Files:**
- Modify: `app/memory_store/redis_store.py`
- Modify: `app/memory_store/mongo_store.py`
- Modify: `app/memory_store/sensitive_mapping_store.py`
- Create: `tests/test_memory_store.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_memory_store.py
import pytest
from unittest.mock import patch, MagicMock
from app.memory_store.sensitive_mapping_store import SensitiveMappingStore


def test_save_mapping():
    store = SensitiveMappingStore()
    with patch.object(store, "_collection", new_callable=MagicMock) as mock_col:
        store.save_mapping("req_001", {"[姓名_1]": "张三"})
        mock_col.insert_one.assert_called_once()


def test_get_mapping():
    store = SensitiveMappingStore()
    with patch.object(store, "_collection", new_callable=MagicMock) as mock_col:
        mock_col.find_one.return_value = {
            "request_id": "req_001",
            "mappings": {"[姓名_1]": "张三"},
        }
        result = store.get_mapping("req_001")
        assert result == {"[姓名_1]": "张三"}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_memory_store.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 RedisStore**

```python
# app/memory_store/redis_store.py
import redis
from app.config.settings import REDIS_CONFIG


class RedisStore:
    """Redis 缓存操作"""

    def __init__(self):
        self._client = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            db=REDIS_CONFIG["db"],
            password=REDIS_CONFIG["password"] or None,
            decode_responses=True,
        )

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, expire: int = 3600):
        self._client.set(key, value, ex=expire)

    def delete(self, key: str):
        self._client.delete(key)
```

- [ ] **Step 4: 实现 MongoStore**

```python
# app/memory_store/mongo_store.py
from pymongo import MongoClient
from app.config.settings import MONGO_CONFIG


class MongoStore:
    """MongoDB 持久化操作"""

    def __init__(self):
        self._client = MongoClient(MONGO_CONFIG["uri"])
        self._db = self._client[MONGO_CONFIG["db_name"]]

    @property
    def db(self):
        return self._db
```

- [ ] **Step 5: 实现 SensitiveMappingStore**

```python
# app/memory_store/sensitive_mapping_store.py
from datetime import datetime, timezone
from app.memory_store.mongo_store import MongoStore


class SensitiveMappingStore:
    """脱敏映射关系持久化"""

    COLLECTION = "sensitive_mappings"

    def __init__(self):
        self._store = MongoStore()
        self._collection = self._store.db[self.COLLECTION]

    def save_mapping(self, request_id: str, mappings: dict):
        self._collection.insert_one({
            "request_id": request_id,
            "created_at": datetime.now(timezone.utc),
            "mappings": mappings,
        })

    def get_mapping(self, request_id: str) -> dict | None:
        doc = self._collection.find_one({"request_id": request_id})
        if doc:
            return doc.get("mappings")
        return None
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_memory_store.py -v`
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add app/memory_store/ tests/test_memory_store.py
git commit -m "feat: add RedisStore, MongoStore, and SensitiveMappingStore"
```

---

### Task 7: RAG 模块（Retriever + Formatter + KnowledgeLoader）

**Files:**
- Modify: `app/rag/retriever.py`
- Modify: `app/rag/formatter.py`
- Modify: `app/rag/knowledge_loader.py`
- Create: `tests/test_rag.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_rag.py
import pytest
from app.rag.formatter import RefFormatter


def test_format_refs():
    formatter = RefFormatter()
    docs = [
        {"id": "doc_1", "content": "白细胞升高提示感染", "source": "临床指南", "url": "https://xxx"},
        {"id": "doc_2", "content": "正常范围4-10", "source": "教材", "url": ""},
    ]
    refs = formatter.format(docs)
    assert "[ref_1]" in refs
    assert "白细胞升高提示感染" in refs
    assert len(formatter.references) == 2
    assert formatter.references[0]["id"] == "ref_1"
    assert formatter.references[0]["source"] == "临床指南"


def test_format_empty():
    formatter = RefFormatter()
    refs = formatter.format([])
    assert refs == ""
    assert formatter.references == []
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_rag.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 RefFormatter**

```python
# app/rag/formatter.py


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
```

- [ ] **Step 4: 实现 Retriever**

```python
# app/rag/retriever.py
import os
import numpy as np
import faiss
from app.llm.embedding_client import EmbeddingClient
from app.config.settings import RAG_CONFIG


class Retriever:
    """向量检索器"""

    def __init__(self):
        self._client = EmbeddingClient()
        self._dimension = RAG_CONFIG["embedding"]["dimension"]
        self._top_k = RAG_CONFIG["top_k"]
        self._threshold = RAG_CONFIG["score_threshold"]
        self._index: faiss.IndexFlatL2 | None = None
        self._docs: list[dict] = []
        self._load_index()

    def _load_index(self):
        index_path = RAG_CONFIG["faiss_index_path"]
        if os.path.exists(index_path):
            self._index = faiss.read_index(os.path.join(index_path, "index.faiss"))
            # docs 需要从 MongoDB 或文件加载，这里预留接口

    def search(self, query: str) -> list[dict]:
        """检索与 query 最相关的文档"""
        if self._index is None:
            return []

        embeddings = self._client.embed([query])
        query_vector = np.array(embeddings, dtype=np.float32)
        distances, indices = self._index.search(query_vector, self._top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self._docs):
                score = 1.0 / (1.0 + distances[0][i])  # 转换为相似度
                if score >= self._threshold:
                    results.append(self._docs[idx])

        return results
```

- [ ] **Step 5: 实现 KnowledgeLoader**

```python
# app/rag/knowledge_loader.py
import os
import json
import numpy as np
import faiss
from app.llm.embedding_client import EmbeddingClient
from app.config.settings import RAG_CONFIG


class KnowledgeLoader:
    """知识库导入"""

    def __init__(self):
        self._client = EmbeddingClient()
        self._dimension = RAG_CONFIG["embedding"]["dimension"]

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

        # 保存索引和文档
        index_path = RAG_CONFIG["faiss_index_path"]
        os.makedirs(index_path, exist_ok=True)
        faiss.write_index(index, os.path.join(index_path, "index.faiss"))

        with open(os.path.join(index_path, "docs.json"), "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

        return len(docs)
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_rag.py -v`
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add app/rag/ tests/test_rag.py
git commit -m "feat: add RAG module (Retriever, RefFormatter, KnowledgeLoader)"
```

---

### Task 8: Prompts 提示词

**Files:**
- Modify: `app/prompt/extract_prompt.txt`
- Modify: `app/prompt/explain_prompt.txt`
- Modify: `app/prompt/planner_prompt.txt`

- [ ] **Step 1: 编写 extract_prompt.txt**

```text
你是一个医疗报告数据提取专家。请从以下报告文本中提取结构化信息。

提取要求：
- 指标名称
- 数值
- 正常范围
- 是否异常（是/否）

请以 JSON 数组格式输出，每个指标一个对象：
```json
[
  {"name": "指标名称", "value": "数值", "normal_range": "正常范围", "is_abnormal": true}
]
```

报告文本：
{report_text}
```

- [ ] **Step 2: 编写 explain_prompt.txt**

```text
你是一个医疗报告解读专家。请根据以下资料和结构化数据，用通俗语言为患者解释报告内容。

【资料】
{references}

【结构化数据】
{extracted_data}

要求：
1. 必须使用 [ref_x] 标注信息来源
2. 不要编造任何信息，仅基于提供的资料
3. 用通俗语言解释，避免过多专业术语
4. 逐项说明异常指标的可能原因和建议
```

- [ ] **Step 3: 编写 planner_prompt.txt**

```text
你是一个任务规划专家。根据用户的需求，生成执行计划。

可用工具：
- parser: 解析报告文件（PDF/图片）为文本
- desensitize: 对文本进行脱敏处理
- extract: 从文本中提取结构化数据
- rag: 检索知识库中的相关知识
- explain: 生成带引用的解释说明
- web_search: 联网搜索补充信息（仅在RAG检索置信度不足时使用）

用户需求：{user_request}

请以 JSON 数组格式输出执行计划：
```json
[{"tool": "tool_name", "reason": "使用原因"}]
```
```

- [ ] **Step 4: Commit**

```bash
git add app/prompt/
git commit -m "feat: add prompt templates for extract, explain, and planner"
```

---

### Task 9: Parser Tool

**Files:**
- Modify: `app/tools/parser_tool.py`
- Create: `tests/test_parser_tool.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_parser_tool.py
import pytest
from unittest.mock import patch, MagicMock
from app.tools.parser_tool import ParserTool


def test_parse_text_input():
    tool = ParserTool()
    result = tool.execute(input_type="text", content="白细胞 12.5")
    assert result["text"] == "白细胞 12.5"
    assert result["input_type"] == "text"


def test_parse_pdf_calls_llm():
    tool = ParserTool()
    with patch.object(tool._llm, "chat", return_value="解析出的文本内容") as mock:
        result = tool.execute(input_type="pdf", content="base64encoded...")
        mock.assert_called_once()
        assert "text" in result
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_parser_tool.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ParserTool**

```python
# app/tools/parser_tool.py
import base64
import pdfplumber
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
            pdf_bytes = base64.b64decode(content)
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(pages_text)
            if text.strip():
                return text
        except Exception:
            pass

        # PDF 无法提取文本时，使用 VL 模型 OCR
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_parser_tool.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/tools/parser_tool.py tests/test_parser_tool.py
git commit -m "feat: add ParserTool for PDF/image to text conversion"
```

---

### Task 10: Desensitize Tool

**Files:**
- Modify: `app/tools/desensitize_tool.py`
- Create: `tests/test_desensitize_tool.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_desensitize_tool.py
import pytest
from unittest.mock import patch
from app.tools.desensitize_tool import DesensitizeTool


def test_desensitize_phone_mask():
    tool = DesensitizeTool()
    result = tool.execute(text="联系电话13812345678，请回拨", request_id="req_001")
    assert "13812345678" not in result["desensitized_text"]
    assert "138****5678" in result["desensitized_text"]
    assert result["mapping_count"] > 0


def test_desensitize_placeholder():
    tool = DesensitizeTool()
    result = tool.execute(text="患者张三先生，前往北京协和医院就诊", request_id="req_002")
    assert "张三" not in result["desensitized_text"]
    assert "[姓名]" in result["desensitized_text"]
    assert "[医院名称]" in result["desensitized_text"]


def test_desensitize_no_match():
    tool = DesensitizeTool()
    result = tool.execute(text="白细胞升高，建议复查", request_id="req_003")
    assert result["desensitized_text"] == "白细胞升高，建议复查"
    assert result["mapping_count"] == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_desensitize_tool.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 DesensitizeTool**

```python
# app/tools/desensitize_tool.py
import re
from app.core.tool_base import ToolBase
from app.config.settings import DESENSITIZE_CONFIG
from app.memory_store.sensitive_mapping_store import SensitiveMappingStore


class DesensitizeTool(ToolBase):
    """脱敏工具：对解析后的文本进行敏感信息脱敏"""

    name = "desensitize"

    def __init__(self):
        self._config = DESENSITIZE_CONFIG
        self._mapping_store = SensitiveMappingStore()

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        request_id = kwargs.get("request_id", "")

        rules = self._config["rules"]
        custom_rules = self._config.get("custom_rules", [])
        default_strategy = self._config["default_strategy"]

        mappings = {}
        counter = {}
        result_text = text

        # 预置规则
        for rule_name, rule_conf in rules.items():
            pattern = rule_conf.get("pattern", "")
            strategy = rule_conf.get("strategy", default_strategy)
            label = rule_conf.get("label", f"[{rule_name}]")
            result_text, new_mappings = self._apply_rule(
                result_text, pattern, strategy, label, rule_name, counter
            )
            mappings.update(new_mappings)

        # 自定义规则
        for custom_rule in custom_rules:
            pattern = custom_rule.get("pattern", "")
            strategy = custom_rule.get("strategy", default_strategy)
            label = custom_rule.get("label", "[自定义]")
            rule_name = custom_rule.get("name", "custom")
            result_text, new_mappings = self._apply_rule(
                result_text, pattern, strategy, label, rule_name, counter
            )
            mappings.update(new_mappings)

        # 持久化映射关系
        if mappings and request_id:
            self._mapping_store.save_mapping(request_id, mappings)

        return {
            "desensitized_text": result_text,
            "mapping_count": len(mappings),
        }

    def _apply_rule(
        self, text: str, pattern: str, strategy: str,
        label: str, rule_name: str, counter: dict,
    ) -> tuple[str, dict]:
        """应用单条脱敏规则"""
        mappings = {}
        if not pattern:
            return text, mappings

        counter[rule_name] = counter.get(rule_name, 0) + 1

        def replacer(match):
            original = match.group(0)
            counter[rule_name] += 1
            placeholder = f"{label}_{counter[rule_name]}" if counter[rule_name] > 1 else label
            mappings[placeholder] = original

            if strategy == "placeholder":
                return placeholder
            elif strategy == "mask":
                return self._mask_value(original)
            elif strategy == "delete":
                return ""
            return placeholder

        result = re.sub(pattern, replacer, text)
        return result, mappings

    @staticmethod
    def _mask_value(value: str) -> str:
        """部分遮掩"""
        if len(value) <= 2:
            return "*" * len(value)
        return value[:3] + "****" + value[-4:]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_desensitize_tool.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/tools/desensitize_tool.py tests/test_desensitize_tool.py
git commit -m "feat: add DesensitizeTool with configurable rules and persistent mapping"
```

---

### Task 11: Extract Tool

**Files:**
- Modify: `app/tools/extract_tool.py`
- Create: `tests/test_extract_tool.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_extract_tool.py
import pytest
import json
from unittest.mock import patch
from app.tools.extract_tool import ExtractTool


def test_extract_calls_llm():
    tool = ExtractTool()
    mock_response = json.dumps([
        {"name": "白细胞", "value": "12.5", "normal_range": "4-10", "is_abnormal": True}
    ], ensure_ascii=False)
    with patch.object(tool._llm, "chat", return_value=mock_response) as mock:
        result = tool.execute(text="白细胞 12.5×10^9/L")
        mock.assert_called_once()
        data = result["extracted_data"]
        assert len(data) == 1
        assert data[0]["name"] == "白细胞"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_extract_tool.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ExtractTool**

```python
# app/tools/extract_tool.py
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_extract_tool.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add app/tools/extract_tool.py tests/test_extract_tool.py
git commit -m "feat: add ExtractTool for structured data extraction via LLM"
```

---

### Task 12: RAG Tool

**Files:**
- Modify: `app/tools/rag_tool.py`
- Create: `tests/test_rag_tool.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_rag_tool.py
import pytest
from unittest.mock import patch
from app.tools.rag_tool import RAGTool


def test_rag_tool_search():
    tool = RAGTool()
    mock_docs = [
        {"id": "doc_1", "content": "白细胞升高提示感染", "source": "临床指南", "url": "https://xxx"}
    ]
    with patch.object(tool._retriever, "search", return_value=mock_docs):
        result = tool.execute(query="白细胞升高怎么办")
        assert "formatted_context" in result
        assert "references" in result
        assert len(result["references"]) == 1


def test_rag_tool_empty():
    tool = RAGTool()
    with patch.object(tool._retriever, "search", return_value=[]):
        result = tool.execute(query="未知指标")
        assert result["formatted_context"] == ""
        assert result["references"] == []
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_rag_tool.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 RAGTool**

```python
# app/tools/rag_tool.py
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_rag_tool.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/tools/rag_tool.py tests/test_rag_tool.py
git commit -m "feat: add RAGTool for knowledge base retrieval"
```

---

### Task 13: Explain Tool

**Files:**
- Modify: `app/tools/explain_tool.py`
- Create: `tests/test_explain_tool.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_explain_tool.py
import pytest
from unittest.mock import patch
from app.tools.explain_tool import ExplainTool


def test_explain_calls_llm():
    tool = ExplainTool()
    with patch.object(tool._llm, "chat", return_value="白细胞升高提示感染 [ref_1]") as mock:
        result = tool.execute(
            extracted_data=[{"name": "白细胞", "value": "12.5", "is_abnormal": True}],
            references="[ref_1] 白细胞升高通常提示感染",
        )
        mock.assert_called_once()
        assert "answer" in result
        assert result["answer"] == "白细胞升高提示感染 [ref_1]"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_explain_tool.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ExplainTool**

```python
# app/tools/explain_tool.py
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_explain_tool.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add app/tools/explain_tool.py tests/test_explain_tool.py
git commit -m "feat: add ExplainTool for generating referenced explanations"
```

---

### Task 14: Web Search Tool

**Files:**
- Modify: `app/tools/web_search_tool.py`
- Create: `tests/test_web_search_tool.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_web_search_tool.py
import pytest
from app.tools.web_search_tool import WebSearchTool


def test_web_search_disabled():
    tool = WebSearchTool()
    result = tool.execute(query="白细胞高怎么办")
    assert result["web_context"] == ""
    assert result["used"] is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_web_search_tool.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 WebSearchTool**

```python
# app/tools/web_search_tool.py
from app.core.tool_base import ToolBase
from app.config.settings import WEB_SEARCH_CONFIG


class WebSearchTool(ToolBase):
    """联网搜索工具：补充实时信息（可选，默认关闭）"""

    name = "web_search"

    def execute(self, **kwargs) -> dict:
        if not WEB_SEARCH_CONFIG["enabled"]:
            return {"web_context": "", "used": False}

        query = kwargs.get("query", "")
        # Phase 1: 预留接口，后续接入阿里云联网搜索 API
        return {"web_context": "", "used": False, "query": query}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_web_search_tool.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add app/tools/web_search_tool.py tests/test_web_search_tool.py
git commit -m "feat: add WebSearchTool (disabled by default, interface ready)"
```

---

### Task 15: Agents（Planner + Executor + Memory）

**Files:**
- Modify: `app/agents/planner/planner_agent.py`
- Modify: `app/agents/executor/executor_agent.py`
- Modify: `app/agents/memory/memory_agent.py`
- Create: `tests/test_agents.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_agents.py
import pytest
from app.agents.planner.planner_agent import PlannerAgent
from app.agents.executor.executor_agent import ExecutorAgent
from app.agents.memory.memory_agent import MemoryAgent
from app.core.context import SharedContext


def test_planner_returns_plan():
    planner = PlannerAgent()
    ctx = SharedContext(request_id="req_001")
    ctx.set("user_request", "解读这份血液报告")
    plan = planner.run(ctx)
    assert isinstance(plan, list)
    assert plan[0]["tool"] == "parser"
    assert any(step["tool"] == "desensitize" for step in plan)


def test_executor_runs_tools():
    executor = ExecutorAgent()
    ctx = SharedContext(request_id="req_001")
    plan = [
        {"tool": "parser", "params": {"input_type": "text", "content": "白细胞 12.5"}},
    ]
    # 使用 mock tool 避免 LLM 调用
    from unittest.mock import MagicMock
    mock_tool = MagicMock()
    mock_tool.execute.return_value = {"text": "白细胞 12.5", "input_type": "text"}
    executor._registry.register("parser", mock_tool)

    result = executor.run({"context": ctx, "plan": plan})
    assert ctx.get("parser_result") is not None


def test_memory_agent_stores_context():
    memory = MemoryAgent()
    ctx = SharedContext(request_id="req_001")
    ctx.set("parsed_text", "测试文本")
    result = memory.run(ctx)
    assert result.get("request_id") == "req_001"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_agents.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 MemoryAgent**

```python
# app/agents/memory/memory_agent.py
from app.core.agent_base import AgentBase


class MemoryAgent(AgentBase):
    """上下文管理 Agent：管理请求生命周期内的共享数据"""

    name = "memory"

    def run(self, context) -> dict:
        return context.to_dict()
```

- [ ] **Step 4: 实现 PlannerAgent**

```python
# app/agents/planner/planner_agent.py
from app.core.agent_base import AgentBase


class PlannerAgent(AgentBase):
    """任务规划 Agent：生成 Tool 执行计划"""

    name = "planner"

    def run(self, context: dict) -> list[dict]:
        # Phase 1: 返回固定流程计划
        # Phase 2: 由 LLM 动态规划
        return [
            {"tool": "parser", "params": {"input_type": context.get("input_type", "text")}},
            {"tool": "desensitize", "params": {}},
            {"tool": "extract", "params": {}},
            {"tool": "rag", "params": {}},
            {"tool": "explain", "params": {}},
        ]
```

- [ ] **Step 5: 实现 ExecutorAgent**

```python
# app/agents/executor/executor_agent.py
from app.core.agent_base import AgentBase
from app.core.registry import Registry


class ExecutorAgent(AgentBase):
    """执行器 Agent：按计划执行 Tool 链路"""

    name = "executor"

    def __init__(self):
        self._registry = Registry()

    def register_tool(self, tool):
        self._registry.register(tool.name, tool)

    def run(self, params: dict) -> dict:
        context = params["context"]
        plan = params["plan"]

        for step in plan:
            tool_name = step["tool"]
            tool_params = step.get("params", {})

            tool = self._registry.get(tool_name)

            # 从 context 中提取上游数据注入参数
            if tool_name == "desensitize":
                tool_params["text"] = context.get("parser_result", {}).get("text", "")
                tool_params["request_id"] = context.request_id
            elif tool_name == "extract":
                tool_params["text"] = context.get("desensitize_result", {}).get("desensitized_text", "")
            elif tool_name == "rag":
                extracted = context.get("extract_result", {}).get("extracted_data", [])
                tool_params["query"] = " ".join(
                    [item.get("name", "") for item in extracted if item.get("is_abnormal")]
                ) if extracted else ""
            elif tool_name == "explain":
                tool_params["extracted_data"] = context.get("extract_result", {}).get("extracted_data", [])
                tool_params["references"] = context.get("rag_result", {}).get("formatted_context", "")

            result = tool.execute(**tool_params)
            context.set(f"{tool_name}_result", result)

        return context.to_dict()
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_agents.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add app/agents/ tests/test_agents.py
git commit -m "feat: add PlannerAgent, ExecutorAgent, and MemoryAgent"
```

---

### Task 16: Orchestrator 调度核心

**Files:**
- Modify: `app/core/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import patch, MagicMock
from app.core.orchestrator import Orchestrator


def test_orchestrator_creates_context():
    orch = Orchestrator()
    assert orch is not None


def test_orchestrator_has_agents():
    orch = Orchestrator()
    assert hasattr(orch, "planner")
    assert hasattr(orch, "executor")
    assert hasattr(orch, "memory")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 Orchestrator**

```python
# app/core/orchestrator.py
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_orchestrator.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add Orchestrator for coordinating agent workflow"
```

---

### Task 17: Controller + Main 入口

**Files:**
- Modify: `app/controller/agent_controller.py`
- Modify: `app/main.py`

- [ ] **Step 1: 实现 agent_controller.py**

```python
# app/controller/agent_controller.py
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from app.core.orchestrator import Orchestrator


router = APIRouter(prefix="/api/v1", tags=["report"])
orchestrator = Orchestrator()


class TextInput(BaseModel):
    content: str


@router.post("/report/parse")
async def parse_report_text(input_data: TextInput):
    """文本报告解读"""
    request_id = str(uuid.uuid4())
    result = orchestrator.process(
        request_id=request_id,
        content=input_data.content,
        input_type="text",
    )
    return result


@router.post("/report/upload")
async def upload_report(file: UploadFile = File(...)):
    """文件报告解读（PDF/图片）"""
    request_id = str(uuid.uuid4())
    content = await file.read()
    import base64
    b64_content = base64.b64encode(content).decode("utf-8")

    input_type = "pdf" if file.filename and file.filename.endswith(".pdf") else "image"
    result = orchestrator.process(
        request_id=request_id,
        content=b64_content,
        input_type=input_type,
    )
    return result
```

- [ ] **Step 2: 实现 main.py**

```python
# app/main.py
from fastapi import FastAPI
from app.controller.agent_controller import router


app = FastAPI(title="Report Genius", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 3: Commit**

```bash
git add app/controller/agent_controller.py app/main.py
git commit -m "feat: add FastAPI controller and application entry point"
```

---

### Task 18: 全量测试与集成验证

**Files:**
- Run all tests

- [ ] **Step 1: 运行全量测试**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: 验证项目结构**

Run: `tree -I '__pycache__|.git|.idea|*.pyc' .`
Expected: 结构与 README.md 一致

- [ ] **Step 3: 验证 FastAPI 启动（语法检查）**

Run: `python -c "from app.main import app; print('OK')"`
Expected: OK
