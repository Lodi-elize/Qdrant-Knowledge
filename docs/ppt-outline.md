# Qdrant Knowledge Assistant 项目 PPT 大纲

## 1. 封面

**标题：** Qdrant Knowledge Assistant：面向产品文档的 RAG 知识助手

**副标题：** 基于 Qdrant、FastAPI、React 和大模型的企业知识问答系统

---

## 2. 项目背景

- 普通大模型不了解企业内部最新产品文档。
- 客服或用户问答容易出现答案不一致、查找慢、依赖人工经验的问题。
- 企业产品文档通常按产品线、版本、条款组织，直接让模型回答容易混淆。
- 本项目目标是把官方产品文档接入大模型，让回答基于可检索知识库。

---

## 3. 项目定位

- 本项目是一个客户-facing 的 RAG 产品知识助手。
- 管理员上传官方产品文档。
- 用户选择产品线和产品版本后提问。
- 系统从 Qdrant 检索相关文档片段，再调用 OpenAI-compatible 大模型生成答案。
- 适用于产品客服、售前支持、内部知识库问答等场景。

---

## 4. 核心功能

- React + Vite 构建客户聊天界面。
- FastAPI 提供后端接口和 OpenAPI 文档。
- 管理员上传官方文档。
- 支持 `.txt`、`.md`、`.pdf` 文档。
- 按 `product_line` 和 `product_version` 隔离知识库。
- 使用 Qdrant 进行向量存储和元数据过滤检索。
- 支持 DeepSeek / OpenAI-compatible 模型生成回答。
- 回答支持 Markdown 渲染和来源证据展示。

---

## 5. 系统架构

```text
frontend/
  React 聊天界面和管理员上传界面

backend/
  FastAPI API 层
  ingestion service -> 文档解析、切片、向量化、写入 Qdrant
  retrieval service -> 按产品线和版本检索
  generation service -> 本地回退或大模型生成答案

qdrant/
  保存文档片段向量和产品/版本元数据
```

关键设计：

- 前端负责交互。
- 后端负责权限、检索、生成和响应结构。
- Qdrant 只负责向量存储和相似度检索。
- 大模型只在检索证据基础上组织最终回答。

---

## 6. 文档上传流程

1. 管理员输入上传密钥。
2. 选择产品线和产品版本。
3. 上传官方文档。
4. 后端解析文档内容。
5. 按 `chunk_size=900`、`chunk_overlap=120` 切片。
6. 为每个片段生成 embedding。
7. 写入 Qdrant，并保存产品线、版本、文件名等元数据。

上传链路：

```text
管理员上传文档
  -> 后端读取文件
  -> 文档切片
  -> 生成 embedding
  -> 写入 Qdrant
  -> 返回 document_id 和 indexed chunks
```

---

## 7. 用户问答流程

1. 用户选择产品线和产品版本。
2. 输入问题。
3. 后端生成问题向量。
4. Qdrant 按产品线和版本过滤检索。
5. 默认返回 `top_k=4` 个相关片段。
6. 大模型基于检索内容生成答案。
7. 后端返回答案、来源、摘要和生成状态。

问答链路：

```text
用户提问
  -> 构建 KnowledgeBaseScope
  -> ScopedRetrievalService 检索
  -> Qdrant metadata filter
  -> GenerationService 生成答案
  -> 返回 answer、sources、grounded_summary
```

---

## 8. 项目亮点

- 知识库按产品线和版本隔离，避免跨产品、跨版本串答案。
- 检索服务封装统一，业务接口不直接访问 Qdrant。
- 支持本地 deterministic embedding，便于测试和离线开发。
- 支持 HuggingFace BGE 中文 embedding，提升中文检索效果。
- 无匹配内容时返回明确提示，降低误导风险。
- 精确条款类问题优先抽取原文，减少模型自由改写。
- 回答结构中保留 `sources`，方便用户追溯依据。

---

## 9. 什么是 AI 幻觉

AI 幻觉是指模型生成了看似合理、但事实错误或没有依据的内容。

在知识库问答中，常见表现包括：

- 编造产品功能。
- 混淆不同版本文档。
- 把通用知识当成官方答案。
- 检索不到内容时仍然强行回答。
- 对条款、参数、价格、限制条件进行错误补全。

AI 幻觉的核心问题不是语言不通顺，而是答案没有可靠依据。

---

## 10. 本项目如何降低 AI 幻觉

- 使用 RAG，把官方文档作为主要依据。
- Qdrant 检索时强制使用 `product_line` 和 `product_version` 过滤。
- 返回 `sources`，让答案可以追溯来源。
- 设置 `min_retrieval_score=0.2`，过滤低相关片段。
- 精确条款问题优先抽取原文，不让模型自由发挥。
- AI 生成失败时回退到本地知识库片段答案。
- 无相关内容时返回“当前知识库未加载/未检索到内容”。

这些设计不能彻底消除幻觉，但可以显著降低幻觉发生概率，并让用户知道答案是否有依据。

---

## 11. Token 消耗来源

Token 消耗主要来自三个阶段：

### 文档上传阶段

- 文档切片后生成 embedding。
- 每个 chunk 都会消耗 embedding tokens。
- chunk overlap 会带来重复 token 消耗。

### 用户提问阶段

- 用户问题需要生成 query embedding。
- 问题越长，embedding token 消耗越高。

### 答案生成阶段

- 系统提示词消耗 tokens。
- 用户问题消耗 tokens。
- 检索片段作为上下文消耗 tokens。
- 工具调用和最终回答也会消耗 tokens。

RAG 系统最大的 token 成本通常来自“把检索片段塞进模型上下文”。

---

## 12. Token 损耗数估算

基于当前项目默认参数：

```text
chunk_size = 900
chunk_overlap = 120
default_top_k = 4
```

### 1. 文档切片重叠损耗

每个 900 字符片段之间重叠 120 字符。

长文档的额外 embedding 损耗约为：

```text
120 / (900 - 120) = 15.4%
```

也就是说，文档越长，因 overlap 带来的重复 embedding 成本越明显。

### 2. 单次问答检索上下文

默认最多检索 4 个片段：

```text
4 × 900 = 3600 字符
```

在中文场景中，可粗略按约 `3600 tokens` 估算。

### 3. 如果实际只需要 1 个片段

```text
有效上下文：约 900 tokens
额外检索上下文：约 2700 tokens
上下文浪费比例：约 75%
```

这说明 `top_k=4` 更稳，但也会带来额外上下文成本。

### 4. 单次 RAG 问答粗略 token 预算

```text
问题 embedding：20 - 100 tokens
系统提示词 / 工具开销：300 - 600 tokens
检索上下文：最多约 3600 tokens
模型回答：150 - 400 tokens

单次总量：约 4070 - 4700 tokens
其中潜在损耗：约 3000 tokens 左右
```

说明：以上是基于项目参数的估算，不是实际日志统计。项目目前还没有实现 token usage 记录。

---

## 13. Token 优化方向

- 根据问题复杂度动态调整 `top_k`。
- 对检索片段做 rerank，只保留最相关内容。
- 对长片段进行上下文压缩。
- 对精确条款问题直接抽取原文，减少生成 token。
- 增加 token usage 日志，记录每次请求的输入、输出和总 token。
- 根据模型价格估算每次问答成本。

---

## 14. 总结

- 本项目实现了一个完整的产品文档 RAG 知识助手。
- 系统通过 Qdrant 检索、FastAPI 编排、React 展示和大模型生成完成问答闭环。
- 产品线和版本隔离是降低错误回答的重要设计。
- AI 幻觉无法彻底消除，但可以通过检索证据、来源展示和拒答机制降低风险。
- 当前主要 token 损耗来自 chunk overlap 和默认 `top_k=4` 的上下文冗余。
- 后续可以通过动态检索、上下文压缩和 token 日志进一步降低成本。
