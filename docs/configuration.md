# 配置与模型选型

## 一、Prompt 设计

### 1.1 Extract Prompt
请提取以下信息：
- 指标名称
- 数值
- 正常范围
- 是否异常

输出 JSON

### 1.2 Explain Prompt（带引用）
【资料】
[ref_1] xxx
[ref_2] xxx

要求：
1. 必须使用 [ref_x] 标注来源
2. 不要编造
3. 用通俗语言解释

---

## 二、模型选型

基于通义千问：

| 模块 | 模型 | 说明 |
| --- | --- | --- |
| Parser | Qwen-VL | 图片/PDF 解析 |
| Extract | Qwen-Plus | 结构化提取 |
| Explain | Qwen-Max | 解释生成 |
| RAG | text-embedding-v2 | 向量嵌入 |

---

## 三、联网搜索设计

基于阿里云百炼平台，支持但通过 Tool 调用，不作为主路径。

使用策略：
```
if rag_confidence < threshold:
    use_web_search()
```

当前默认关闭，通过 `settings.py` 中 `WEB_SEARCH_CONFIG["enabled"]` 开启。

---

## 四、性能与优化

### 优化点
- RAG 缓存（热点问题）
- PDF 解析缓存
- Embedding 缓存

### 成本控制
- 优先使用 Qwen-Plus
- 关键步骤使用 Qwen-Max

---

## 五、系统演进

### 第一阶段（当前）
- 固定流程
- Tool 链路

### 第二阶段
- Planner 动态规划
- 引入 LangGraph

### 第三阶段
- Multi-Agent 协作
- 更复杂任务调度
