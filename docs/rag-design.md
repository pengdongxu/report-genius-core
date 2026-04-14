# RAG 设计

## 一、数据结构
```json
{
  "id": "doc_1",
  "content": "白细胞升高通常提示感染",
  "source": "临床指南",
  "url": "https://xxx"
}
```

## 二、检索流程
```
Query
 ↓
Embedding（text-embedding-v2）
 ↓
向量检索（FAISS TopK）
 ↓
分数过滤（threshold >= 0.7）
 ↓
返回上下文
```

## 三、引用格式化（关键）

检索结果自动格式化为带 `[ref_x]` 标注的文本：

```json
{
  "id": "ref_1",
  "content": "...",
  "source": "...",
  "url": "..."
}
```

格式化后：
```
[ref_1] 白细胞升高通常提示感染
[ref_2] 正常范围 4-10
```

## 四、知识导入

通过 `KnowledgeLoader` 导入知识到 FAISS 索引：

```python
from app.rag.knowledge_loader import KnowledgeLoader

loader = KnowledgeLoader()

# 从 JSON 文件导入
count = loader.load_from_file("knowledge.json")

# 从列表导入
docs = [
    {"id": "doc_1", "content": "...", "source": "...", "url": "..."},
]
count = loader.load_from_list(docs)
```

知识文件格式（JSON 数组）：
```json
[
  {
    "id": "doc_1",
    "content": "白细胞升高通常提示感染",
    "source": "临床指南",
    "url": "https://xxx"
  }
]
```
