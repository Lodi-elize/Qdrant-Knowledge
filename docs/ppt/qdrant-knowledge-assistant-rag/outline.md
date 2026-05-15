# Qdrant Knowledge Assistant 25页 PPT 大纲

风格：清爽专业技术汇报风，浅色背景，蓝绿主色，信息图和流程图为主。

## Slide 1: Qdrant Knowledge Assistant

- 副标题：面向产品文档的 RAG 知识助手
- 页面角色：cover
- 视觉设计：heroNodes
- Qdrant + FastAPI + React
- 产品线与版本隔离
- AI 幻觉控制与 Token 成本分析

## Slide 2: 目录

- 副标题：从业务问题到成本控制
- 页面角色：agenda
- 视觉设计：agenda
- 项目背景与目标
- 系统架构与核心流程
- AI 幻觉与治理方式
- Token 损耗估算
- 总结与改进方向

## Slide 3: 项目背景：企业知识难以直接进入大模型

- 副标题：通用模型知道很多，但不知道企业最新文档
- 页面角色：problem
- 视觉设计：problemCards
- 产品文档更新快，训练数据无法覆盖
- 客服回答依赖人工经验，口径容易不一致
- 用户需要按产品线和版本获得精确答案

## Slide 4: 目标：让回答基于可检索的官方资料

- 副标题：用 RAG 把文档临时提供给模型
- 页面角色：objective
- 视觉设计：target
- 管理员维护官方文档
- 用户按产品线和版本提问
- 系统先检索证据，再生成回答
- 答案保留来源，便于追溯

## Slide 5: 项目定位

- 副标题：客户-facing 的产品知识问答系统
- 页面角色：position
- 视觉设计：twoRoles
- 面向产品文档问答，而不是通用聊天机器人
- 支持管理员上传和用户查询两类角色
- 重点解决知识可信度、版本隔离和回答可追溯

## Slide 6: 核心功能总览

- 副标题：从文档管理到问答展示的完整链路
- 页面角色：features
- 视觉设计：featureGrid
- React + Vite 聊天界面
- FastAPI 后端与 OpenAPI 文档
- Qdrant 向量存储与元数据过滤
- DeepSeek / OpenAI-compatible 模型生成
- Markdown 回答与来源证据面板

## Slide 7: 技术栈

- 副标题：轻量、清晰、便于本地运行和测试
- 页面角色：tech
- 视觉设计：stack
- 前端：React、Vite、TypeScript
- 后端：FastAPI、Pydantic Settings、LangChain
- 向量库：Qdrant
- 模型：DeepSeek 或 OpenAI-compatible Chat Model
- 测试：pytest、Vitest

## Slide 8: 系统架构

- 副标题：前端、后端、向量库和大模型分层协作
- 页面角色：architecture
- 视觉设计：architecture
- 前端负责聊天与上传交互
- 后端负责权限、切片、检索和生成编排
- Qdrant 保存向量和元数据
- 大模型只负责组织最终回答

## Slide 9: 文档上传流程

- 副标题：官方资料进入知识库的路径
- 页面角色：process
- 视觉设计：uploadFlow
- 管理员校验上传密钥
- 解析 txt、md、pdf 文档
- 按 chunk_size=900 切片，overlap=120
- 生成 embedding 并写入 Qdrant

## Slide 10: 问答检索流程

- 副标题：用户问题先变成检索任务
- 页面角色：process
- 视觉设计：queryFlow
- 用户提交产品线、版本和问题
- 后端构建 KnowledgeBaseScope
- 问题向量进入 ScopedRetrievalService
- Qdrant 使用元数据过滤后返回相关片段

## Slide 11: 知识库隔离机制

- 副标题：避免 A 产品的问题检索到 B 产品答案
- 页面角色：boundary
- 视觉设计：isolation
- 每个 chunk 都带有 product_line
- 每个 chunk 都带有 product_version
- 查询时必须携带同样的 scope
- Qdrant 先过滤元数据，再做相似度匹配

## Slide 12: 回答生成策略

- 副标题：检索内容优先，模型知识补充受控
- 页面角色：generation
- 视觉设计：decisionTree
- 有 sources 时优先基于检索内容回答
- 精确条款类问题优先抽取原文
- AI 生成失败时回退到本地片段答案
- 无匹配内容时给出明确提示

## Slide 13: 接口与响应结构

- 副标题：答案之外，还返回证据和生成状态
- 页面角色：api
- 视觉设计：apiShape
- 请求包含 product_line、product_version、question、top_k
- 响应包含 answer、sources、grounded_summary
- 返回 generated_by_ai 和 generation_notice
- 保留 supplemental_note 表示是否使用补充知识

## Slide 14: 前端体验

- 副标题：客户提问与管理员上传共存
- 页面角色：frontend
- 视觉设计：uiMock
- 聊天区支持 Markdown 答案
- 管理员面板用于上传官方文档
- 来源证据默认折叠，降低阅读干扰
- 用户需要先选择产品线和版本

## Slide 15: 质量验证

- 副标题：测试重点围绕隔离、检索和接口契约
- 页面角色：verification
- 视觉设计：checklist
- 管理员上传权限测试
- 响应 schema 测试
- 跨版本泄漏防护测试
- Qdrant repository 过滤测试
- 前端构建与 Vitest

## Slide 16: 什么是 AI 幻觉

- 副标题：模型生成了看似合理但没有依据的内容
- 页面角色：concept
- 视觉设计：hallucination
- 事实错误，但语言很流畅
- 没有来源，却表现得很确定
- 把通用知识误当成企业官方答案
- 在缺少证据时仍然强行补全

## Slide 17: 知识库问答中的幻觉场景

- 副标题：越像正式答案，越需要证据约束
- 页面角色：risk
- 视觉设计：riskMatrix
- 编造不存在的产品功能
- 混淆不同版本的规则
- 把旧文档内容用于新版本
- 对价格、参数、限制条件错误补全

## Slide 18: 本项目的幻觉控制手段

- 副标题：用检索证据压缩模型自由发挥空间
- 页面角色：mitigation
- 视觉设计：shield
- RAG 提供官方文档上下文
- 产品线和版本强制过滤
- sources 让答案可追溯
- 低相关片段被 min_retrieval_score 过滤
- 条款问题尽量原文抽取

## Slide 19: 仍然存在的风险

- 副标题：RAG 不是幻觉免疫系统
- 页面角色：limitations
- 视觉设计：caution
- 检索召回错误会影响生成
- 文档本身过期或不完整会造成误导
- 模型可能误读相邻条款
- 来源展示不能替代最终审核

## Slide 20: Token 消耗从哪里来

- 副标题：RAG 的成本主要来自上下文注入
- 页面角色：tokenSources
- 视觉设计：tokenFlow
- 文档上传：chunk embedding 消耗 tokens
- 用户提问：query embedding 消耗 tokens
- 答案生成：提示词、检索片段、工具调用和输出都消耗 tokens
- 最大成本通常是检索上下文

## Slide 21: 当前参数下的 Token 损耗估算

- 副标题：chunk_size=900，overlap=120，top_k=4
- 页面角色：calculation
- 视觉设计：formula
- 切片重叠额外损耗约 15.4%
- 单次最多注入约 3600 个 token
- 如果只需要 1 个片段，潜在冗余约 2700 个 token
- 上下文浪费比例约 75%

## Slide 22: 单次问答 Token 预算

- 副标题：一次 RAG 调用约 4070 - 4700 tokens
- 页面角色：budget
- 视觉设计：barChart
- 问题 embedding：20 - 100 tokens
- 系统提示词和工具开销：300 - 600 tokens
- 检索上下文：最多约 3600 tokens
- 模型回答：150 - 400 tokens

## Slide 23: Token 优化策略

- 副标题：在准确率和成本之间做动态平衡
- 页面角色：optimization
- 视觉设计：optimization
- 根据问题复杂度动态调整 top_k
- 增加 rerank，只保留最相关片段
- 对长片段做上下文压缩
- 条款类问题直接抽取原文
- 记录 token usage 并估算成本

## Slide 24: 后续演进路线

- 副标题：从可用系统走向可运营系统
- 页面角色：roadmap
- 视觉设计：roadmap
- 增加 token usage 日志和成本报表
- 完善答案引用标注
- 接入 reranker 提升检索质量
- 对低置信度问题明确拒答
- 支持更多文档格式和增量更新

## Slide 25: 总结

- 副标题：RAG 的价值是让模型回答有边界、有依据、可追溯
- 页面角色：summary
- 视觉设计：summary
- 项目实现了完整的产品文档问答闭环
- 产品线和版本隔离降低错误检索风险
- AI 幻觉通过证据、过滤和回退机制被压低
- Token 成本主要来自上下文冗余
- 下一步应加强观测、压缩和动态检索

## Slide 26: Q&A

- 副标题：问题与讨论
- 页面角色：closing
- 视觉设计：qa
- 系统边界
- AI 幻觉治理
- Token 成本优化
- 后续落地场景
