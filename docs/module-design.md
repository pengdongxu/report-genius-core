# 核心模块与 Tool 设计

## 一、核心模块说明

### 1.1 Orchestrator（调度核心）
职责：
- 调度 Agent 执行流程
- 控制任务流转

### 1.2 Planner Agent
职责：
- 拆解任务
- 生成执行计划

示例：
```json
[
  {"tool": "parser"},
  {"tool": "desensitize"},
  {"tool": "extract"},
  {"tool": "rag"},
  {"tool": "explain"}
]
```

### 1.3 Executor Agent
职责：
- 按计划执行 Tool
- 串联数据流

### 1.4 Memory Agent
职责：
- 管理上下文
- 存储中间结果

---

## 二、Tool 设计（核心能力模块）

### 2.1 Parser Tool（解析）
- 输入：PDF / 图片
- 输出：文本

### 2.2 Desensitize Tool（脱敏）
- 输入：解析后的文本 + request_id
- 输出：脱敏后文本 + 映射数量
- 职责：
  - 预置规则匹配（姓名/身份证/手机号/地址/就诊号/病历号/床号/医院名称）
  - 自定义规则匹配（正则/关键词，可配置扩展）
  - 按配置策略替换（占位符/遮掩/删除）
  - 生成映射关系 → 持久化到 memory_store
- 设计原则：
  - 独立 Tool，插拔式，由 Orchestrator 在 Parser 之后调度
  - 不影响其他 Tool，可随时去掉或替换

详细设计见 [脱敏设计](desensitize-design.md)

### 2.3 Extract Tool（结构化）
- 输入：脱敏后文本
- 输出：结构化数据

### 2.4 RAG Tool（知识检索）
- 输入：问题 / 指标
- 输出：相关知识

详细设计见 [RAG 设计](rag-design.md)

### 2.5 Explain Tool（解释生成）
- 输入：
  - 结构化数据
  - RAG 上下文
- 输出：
  - 用户可读解释
  - 引用标注

### 2.6 Web Search Tool
用于补充实时信息，不作为主路径。

---

## 三、返回结果设计

### 标准返回格式
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

### 原则
- 引用必须来自 RAG
- 不允许模型编造
