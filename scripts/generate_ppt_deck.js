const fs = require("fs");
const path = require("path");
const sharp = require("sharp");
const PptxGenJS = require("pptxgenjs");

const repoRoot = "E:\\aiAgent";
const deckName = "qdrant-knowledge-assistant-rag";
const baseDir = path.join(repoRoot, "docs", "ppt");
const deckDir = path.join(baseDir, deckName);
const imageDir = path.join(deckDir, "origin_image");
const W = 2560;
const H = 1440;

const slides = [
  {
    title: "Qdrant Knowledge Assistant",
    subtitle: "面向产品文档的 RAG 知识助手",
    role: "cover",
    tag: "项目汇报",
    points: ["Qdrant + FastAPI + React", "产品线与版本隔离", "AI 幻觉控制与 Token 成本分析"],
    visual: "heroNodes",
    notes:
      "本页用于建立汇报主题：这是一个围绕产品文档构建的 RAG 知识助手。重点不只是演示功能，还会解释为什么需要 RAG、如何降低 AI 幻觉，以及一次问答大致会产生多少 token 消耗。",
  },
  {
    title: "目录",
    subtitle: "从业务问题到成本控制",
    role: "agenda",
    points: ["项目背景与目标", "系统架构与核心流程", "AI 幻觉与治理方式", "Token 损耗估算", "总结与改进方向"],
    visual: "agenda",
    notes:
      "整份 PPT 分为五个部分。先说明项目解决什么问题，再进入架构和流程，随后解释 AI 幻觉，最后分析 token 成本和后续优化。",
  },
  {
    title: "项目背景：企业知识难以直接进入大模型",
    subtitle: "通用模型知道很多，但不知道企业最新文档",
    role: "problem",
    points: ["产品文档更新快，训练数据无法覆盖", "客服回答依赖人工经验，口径容易不一致", "用户需要按产品线和版本获得精确答案"],
    visual: "problemCards",
    notes:
      "普通大模型并不知道企业内部最新产品文档，因此不能直接承担正式产品问答。企业问答尤其强调版本、条款和边界条件，错一个版本就可能产生错误承诺。",
  },
  {
    title: "目标：让回答基于可检索的官方资料",
    subtitle: "用 RAG 把文档临时提供给模型",
    role: "objective",
    points: ["管理员维护官方文档", "用户按产品线和版本提问", "系统先检索证据，再生成回答", "答案保留来源，便于追溯"],
    visual: "target",
    notes:
      "本项目的目标是让大模型基于企业提供的官方文档回答问题。RAG 的核心价值是把外部知识在推理时提供给模型，而不是依赖模型参数记忆。",
  },
  {
    title: "项目定位",
    subtitle: "客户-facing 的产品知识问答系统",
    role: "position",
    points: ["面向产品文档问答，而不是通用聊天机器人", "支持管理员上传和用户查询两类角色", "重点解决知识可信度、版本隔离和回答可追溯"],
    visual: "twoRoles",
    notes:
      "这个项目不是单纯的聊天页面，而是一个有知识库边界的产品知识助手。它的价值来自上传、检索、隔离、生成和来源展示组成的闭环。",
  },
  {
    title: "核心功能总览",
    subtitle: "从文档管理到问答展示的完整链路",
    role: "features",
    points: ["React + Vite 聊天界面", "FastAPI 后端与 OpenAPI 文档", "Qdrant 向量存储与元数据过滤", "DeepSeek / OpenAI-compatible 模型生成", "Markdown 回答与来源证据面板"],
    visual: "featureGrid",
    notes:
      "项目功能覆盖前端交互、后端接口、文档上传、向量检索和模型生成。来源证据面板默认折叠，但需要时可以展开检查依据。",
  },
  {
    title: "技术栈",
    subtitle: "轻量、清晰、便于本地运行和测试",
    role: "tech",
    points: ["前端：React、Vite、TypeScript", "后端：FastAPI、Pydantic Settings、LangChain", "向量库：Qdrant", "模型：DeepSeek 或 OpenAI-compatible Chat Model", "测试：pytest、Vitest"],
    visual: "stack",
    notes:
      "技术栈选择偏实用：前端用于快速构建页面，FastAPI 提供清晰接口，Qdrant 负责向量检索，模型层可以接入 DeepSeek 或其他 OpenAI-compatible 服务。",
  },
  {
    title: "系统架构",
    subtitle: "前端、后端、向量库和大模型分层协作",
    role: "architecture",
    points: ["前端负责聊天与上传交互", "后端负责权限、切片、检索和生成编排", "Qdrant 保存向量和元数据", "大模型只负责组织最终回答"],
    visual: "architecture",
    notes:
      "系统架构有明确分层。业务接口不直接拼接 Qdrant 查询，而是经过检索服务；生成服务也只接收检索后的 sources，便于控制边界和测试。",
  },
  {
    title: "文档上传流程",
    subtitle: "官方资料进入知识库的路径",
    role: "process",
    points: ["管理员校验上传密钥", "解析 txt、md、pdf 文档", "按 chunk_size=900 切片，overlap=120", "生成 embedding 并写入 Qdrant"],
    visual: "uploadFlow",
    notes:
      "上传流程把原始文档变成可检索的向量片段。每个片段都会保存产品线、版本、文件名和 chunk index，这些元数据是后续隔离检索的关键。",
  },
  {
    title: "问答检索流程",
    subtitle: "用户问题先变成检索任务",
    role: "process",
    points: ["用户提交产品线、版本和问题", "后端构建 KnowledgeBaseScope", "问题向量进入 ScopedRetrievalService", "Qdrant 使用元数据过滤后返回相关片段"],
    visual: "queryFlow",
    notes:
      "问答链路中最重要的是 scope。问题不会在全部文档里搜索，而是在指定产品线和版本内搜索，这能减少跨产品、跨版本污染。",
  },
  {
    title: "知识库隔离机制",
    subtitle: "避免 A 产品的问题检索到 B 产品答案",
    role: "boundary",
    points: ["每个 chunk 都带有 product_line", "每个 chunk 都带有 product_version", "查询时必须携带同样的 scope", "Qdrant 先过滤元数据，再做相似度匹配"],
    visual: "isolation",
    notes:
      "隔离机制是项目的核心可靠性设计。没有隔离时，向量相似度可能把相似条款从其他产品或版本中找出来，导致答案看似合理但实际错误。",
  },
  {
    title: "回答生成策略",
    subtitle: "检索内容优先，模型知识补充受控",
    role: "generation",
    points: ["有 sources 时优先基于检索内容回答", "精确条款类问题优先抽取原文", "AI 生成失败时回退到本地片段答案", "无匹配内容时给出明确提示"],
    visual: "decisionTree",
    notes:
      "生成服务不是无条件调用模型。它会先检查是否有来源，条款类问题还会尝试精确抽取。这样可以减少模型改写带来的风险。",
  },
  {
    title: "接口与响应结构",
    subtitle: "答案之外，还返回证据和生成状态",
    role: "api",
    points: ["请求包含 product_line、product_version、question、top_k", "响应包含 answer、sources、grounded_summary", "返回 generated_by_ai 和 generation_notice", "保留 supplemental_note 表示是否使用补充知识"],
    visual: "apiShape",
    notes:
      "响应结构不只返回一段答案，还返回来源、摘要和生成状态。这样前端可以展示证据，也方便后续做审计和质量分析。",
  },
  {
    title: "前端体验",
    subtitle: "客户提问与管理员上传共存",
    role: "frontend",
    points: ["聊天区支持 Markdown 答案", "管理员面板用于上传官方文档", "来源证据默认折叠，降低阅读干扰", "用户需要先选择产品线和版本"],
    visual: "uiMock",
    notes:
      "前端设计服务于两个核心动作：上传知识和查询知识。来源默认折叠是为了保持问答体验简洁，同时保留可验证性。",
  },
  {
    title: "质量验证",
    subtitle: "测试重点围绕隔离、检索和接口契约",
    role: "verification",
    points: ["管理员上传权限测试", "响应 schema 测试", "跨版本泄漏防护测试", "Qdrant repository 过滤测试", "前端构建与 Vitest"],
    visual: "checklist",
    notes:
      "测试覆盖重点不是 UI 细节，而是知识边界和接口契约。特别是跨版本泄漏测试，直接对应产品知识问答中最危险的问题。",
  },
  {
    title: "什么是 AI 幻觉",
    subtitle: "模型生成了看似合理但没有依据的内容",
    role: "concept",
    points: ["事实错误，但语言很流畅", "没有来源，却表现得很确定", "把通用知识误当成企业官方答案", "在缺少证据时仍然强行补全"],
    visual: "hallucination",
    notes:
      "AI 幻觉的危险在于它通常不是语法错误，而是事实错误。对企业知识库来说，最怕的是模型把不确定的内容说得非常确定。",
  },
  {
    title: "知识库问答中的幻觉场景",
    subtitle: "越像正式答案，越需要证据约束",
    role: "risk",
    points: ["编造不存在的产品功能", "混淆不同版本的规则", "把旧文档内容用于新版本", "对价格、参数、限制条件错误补全"],
    visual: "riskMatrix",
    notes:
      "在产品问答场景里，幻觉常常发生在功能、版本、价格、限制条件这些边界上。这些内容一旦答错，可能直接影响客户决策。",
  },
  {
    title: "本项目的幻觉控制手段",
    subtitle: "用检索证据压缩模型自由发挥空间",
    role: "mitigation",
    points: ["RAG 提供官方文档上下文", "产品线和版本强制过滤", "sources 让答案可追溯", "低相关片段被 min_retrieval_score 过滤", "条款问题尽量原文抽取"],
    visual: "shield",
    notes:
      "这些策略不能百分之百消除幻觉，但能明显降低幻觉概率。核心思想是让模型围绕证据组织语言，而不是凭通用知识猜测。",
  },
  {
    title: "仍然存在的风险",
    subtitle: "RAG 不是幻觉免疫系统",
    role: "limitations",
    points: ["检索召回错误会影响生成", "文档本身过期或不完整会造成误导", "模型可能误读相邻条款", "来源展示不能替代最终审核"],
    visual: "caution",
    notes:
      "RAG 能降低幻觉，但不能保证永远正确。检索质量、文档质量和 prompt 约束都会影响最终答案，所以仍需要质量监控和人工兜底。",
  },
  {
    title: "Token 消耗从哪里来",
    subtitle: "RAG 的成本主要来自上下文注入",
    role: "tokenSources",
    points: ["文档上传：chunk embedding 消耗 tokens", "用户提问：query embedding 消耗 tokens", "答案生成：提示词、检索片段、工具调用和输出都消耗 tokens", "最大成本通常是检索上下文"],
    visual: "tokenFlow",
    notes:
      "token 成本不是只来自用户的问题。RAG 会把检索片段放进上下文，这部分通常远大于用户问题本身，是成本优化的重点。",
  },
  {
    title: "当前参数下的 Token 损耗估算",
    subtitle: "chunk_size=900，overlap=120，top_k=4",
    role: "calculation",
    points: ["切片重叠额外损耗约 15.4%", "单次最多注入约 3600 个 token", "如果只需要 1 个片段，潜在冗余约 2700 个 token", "上下文浪费比例约 75%"],
    visual: "formula",
    notes:
      "这里是基于参数的粗略估算，不是实际 API usage 日志。它说明默认 top_k=4 比较稳，但在简单问题上会带来明显上下文冗余。",
  },
  {
    title: "单次问答 Token 预算",
    subtitle: "一次 RAG 调用约 4070 - 4700 tokens",
    role: "budget",
    points: ["问题 embedding：20 - 100 tokens", "系统提示词和工具开销：300 - 600 tokens", "检索上下文：最多约 3600 tokens", "模型回答：150 - 400 tokens"],
    visual: "barChart",
    notes:
      "这页给出单次问答预算。实际数值会随问题长度、片段长度、模型实现和工具调用方式变化。项目目前还没有记录实际 token usage。",
  },
  {
    title: "Token 优化策略",
    subtitle: "在准确率和成本之间做动态平衡",
    role: "optimization",
    points: ["根据问题复杂度动态调整 top_k", "增加 rerank，只保留最相关片段", "对长片段做上下文压缩", "条款类问题直接抽取原文", "记录 token usage 并估算成本"],
    visual: "optimization",
    notes:
      "优化 token 的关键不是一味减少上下文，而是动态选择足够的上下文。简单问题少拿片段，复杂问题保留更多证据。",
  },
  {
    title: "后续演进路线",
    subtitle: "从可用系统走向可运营系统",
    role: "roadmap",
    points: ["增加 token usage 日志和成本报表", "完善答案引用标注", "接入 reranker 提升检索质量", "对低置信度问题明确拒答", "支持更多文档格式和增量更新"],
    visual: "roadmap",
    notes:
      "后续重点是可运营性和可靠性。除了功能扩展，更重要的是能观测成本、质量和失败场景。",
  },
  {
    title: "总结",
    subtitle: "RAG 的价值是让模型回答有边界、有依据、可追溯",
    role: "summary",
    points: ["项目实现了完整的产品文档问答闭环", "产品线和版本隔离降低错误检索风险", "AI 幻觉通过证据、过滤和回退机制被压低", "Token 成本主要来自上下文冗余", "下一步应加强观测、压缩和动态检索"],
    visual: "summary",
    notes:
      "最后总结：这个项目的核心不是单纯把模型接进来，而是围绕文档、版本、证据和成本建立可控的问答系统。",
  },
  {
    title: "Q&A",
    subtitle: "问题与讨论",
    role: "closing",
    points: ["系统边界", "AI 幻觉治理", "Token 成本优化", "后续落地场景"],
    visual: "qa",
    notes:
      "本页用于收尾和讨论。可以引导听众围绕业务落地、数据质量、模型选择和成本优化继续提问。",
  },
];

function ensureDirs() {
  fs.mkdirSync(imageDir, { recursive: true });
}

function xmlEscape(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function wrapText(text, maxLen) {
  const out = [];
  let line = "";
  for (const ch of text) {
    const width = /[ -~]/.test(ch) ? 0.55 : 1;
    const current = [...line].reduce((sum, c) => sum + (/[ -~]/.test(c) ? 0.55 : 1), 0);
    if (current + width > maxLen && line) {
      out.push(line);
      line = ch;
    } else {
      line += ch;
    }
  }
  if (line) out.push(line);
  return out;
}

function textSvg(text, x, y, opts = {}) {
  const {
    size = 42,
    weight = 400,
    fill = "#132238",
    anchor = "start",
    family = "Noto Sans SC, Microsoft YaHei, SimHei, Arial",
    opacity = 1,
  } = opts;
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" opacity="${opacity}">${xmlEscape(text)}</text>`;
}

function linesSvg(lines, x, y, opts = {}) {
  const { size = 42, lineHeight = Math.round(size * 1.35), fill = "#132238", weight = 400, anchor = "start" } = opts;
  return lines
    .map((line, idx) => textSvg(line, x, y + idx * lineHeight, { ...opts, size, fill, weight, anchor }))
    .join("\n");
}

function iconSvg(kind, x, y, s, color = "#0F766E") {
  if (kind === "database") {
    return `<g transform="translate(${x},${y})" fill="none" stroke="${color}" stroke-width="10"><ellipse cx="${s / 2}" cy="${s * 0.18}" rx="${s * 0.38}" ry="${s * 0.14}"/><path d="M${s * 0.12},${s * 0.18}v${s * 0.48}c0,${s * 0.08} ${s * 0.17},${s * 0.14} ${s * 0.38},${s * 0.14}s${s * 0.38},-${s * 0.06} ${s * 0.38},-${s * 0.14}v-${s * 0.48}"/><path d="M${s * 0.12},${s * 0.42}c0,${s * 0.08} ${s * 0.17},${s * 0.14} ${s * 0.38},${s * 0.14}s${s * 0.38},-${s * 0.06} ${s * 0.38},-${s * 0.14}"/></g>`;
  }
  if (kind === "model") {
    return `<g transform="translate(${x},${y})" fill="none" stroke="${color}" stroke-width="9"><rect x="${s * 0.18}" y="${s * 0.18}" width="${s * 0.64}" height="${s * 0.64}" rx="${s * 0.12}"/><path d="M${s * 0.34},${s * 0.35}h${s * 0.32}M${s * 0.34},${s * 0.5}h${s * 0.32}M${s * 0.34},${s * 0.65}h${s * 0.2}"/><path d="M${s * 0.08},${s * 0.32}h${s * 0.1}M${s * 0.08},${s * 0.5}h${s * 0.1}M${s * 0.08},${s * 0.68}h${s * 0.1}M${s * 0.82},${s * 0.32}h${s * 0.1}M${s * 0.82},${s * 0.5}h${s * 0.1}M${s * 0.82},${s * 0.68}h${s * 0.1}"/></g>`;
  }
  if (kind === "shield") {
    return `<path d="M${x + s * 0.5} ${y + s * 0.08} L${x + s * 0.82} ${y + s * 0.22} V${y + s * 0.48} C${x + s * 0.82} ${y + s * 0.7},${x + s * 0.66} ${y + s * 0.86},${x + s * 0.5} ${y + s * 0.94} C${x + s * 0.34} ${y + s * 0.86},${x + s * 0.18} ${y + s * 0.7},${x + s * 0.18} ${y + s * 0.48} V${y + s * 0.22} Z" fill="none" stroke="${color}" stroke-width="10"/><path d="M${x + s * 0.34} ${y + s * 0.5} l${s * 0.1} ${s * 0.1} l${s * 0.24} -${s * 0.28}" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round"/>`;
  }
  return `<circle cx="${x + s / 2}" cy="${y + s / 2}" r="${s * 0.35}" fill="none" stroke="${color}" stroke-width="9"/>`;
}

function card(x, y, w, h, opts = {}) {
  const fill = opts.fill || "#FFFFFF";
  const stroke = opts.stroke || "#D8E2EA";
  const rx = opts.rx || 28;
  const shadow = opts.shadow ? 'filter="url(#shadow)"' : "";
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="2" ${shadow}/>`;
}

function arrow(x1, y1, x2, y2, color = "#238B82") {
  return `<path d="M${x1} ${y1} L${x2} ${y2}" stroke="${color}" stroke-width="8" stroke-linecap="round" marker-end="url(#arrow)"/>`;
}

function titleBlock(slide, index) {
  const eyebrow = `${slide.role.toUpperCase()}  ·  QDRANT KNOWLEDGE ASSISTANT`;
  return `
    ${textSvg(eyebrow, 132, 96, { size: 28, fill: "#5B6F82", weight: 600 })}
    ${linesSvg(wrapText(slide.title, 22), 132, 174, { size: slide.title.length > 18 ? 66 : 76, fill: "#102033", weight: 800, lineHeight: 88 })}
    ${slide.subtitle ? linesSvg(wrapText(slide.subtitle, 34), 134, slide.title.length > 18 ? 350 : 318, { size: 34, fill: "#516272", weight: 400, lineHeight: 48 }) : ""}
  `;
}

function bullets(points, x, y, maxLen = 33, opts = {}) {
  const size = opts.size || 39;
  const lineHeight = opts.lineHeight || 58;
  let cy = y;
  let out = "";
  for (const p of points) {
    const lines = wrapText(p, maxLen);
    out += `<circle cx="${x}" cy="${cy - 13}" r="8" fill="${opts.dot || "#0F766E"}"/>`;
    out += linesSvg(lines, x + 34, cy, { size, fill: opts.fill || "#172B3A", weight: 500, lineHeight: Math.round(size * 1.32) });
    cy += Math.max(lineHeight, lines.length * Math.round(size * 1.32) + 20);
  }
  return out;
}

function drawVisual(slide, index) {
  const v = slide.visual;
  if (v === "heroNodes") {
    return `
      <g transform="translate(1330,250)">
        ${card(0, 60, 920, 720, { fill: "#F8FBFD", stroke: "#C9DCE8", rx: 36, shadow: true })}
        ${iconSvg("database", 120, 150, 190, "#0F766E")}
        ${iconSvg("model", 620, 150, 190, "#2563EB")}
        ${arrow(330, 245, 600, 245)}
        ${textSvg("官方文档", 215, 420, { size: 42, weight: 800, anchor: "middle" })}
        ${textSvg("RAG 检索", 460, 420, { size: 42, weight: 800, anchor: "middle", fill: "#0F766E" })}
        ${textSvg("可信回答", 715, 420, { size: 42, weight: 800, anchor: "middle" })}
        <path d="M155 560 C300 500, 430 650, 615 560 S800 575, 850 520" fill="none" stroke="#A7C7E7" stroke-width="12" stroke-linecap="round"/>
      </g>`;
  }
  if (v === "agenda") {
    return slide.points
      .map((p, i) => {
        const y = 370 + i * 150;
        return `${card(780, y - 64, 1300, 108, { fill: i === 0 ? "#EAF6F3" : "#FFFFFF", stroke: "#D8E6EF", rx: 24, shadow: true })}
          <circle cx="850" cy="${y - 10}" r="34" fill="${i === 0 ? "#0F766E" : "#E8EEF5"}"/>
          ${textSvg(String(i + 1), 850, y + 2, { size: 30, fill: i === 0 ? "#FFFFFF" : "#486273", weight: 800, anchor: "middle" })}
          ${textSvg(p, 930, y + 4, { size: 42, fill: "#132238", weight: 700 })}`;
      })
      .join("\n");
  }
  if (["problemCards", "featureGrid", "stack"].includes(v)) {
    return slide.points
      .map((p, i) => {
        const col = i % 2;
        const row = Math.floor(i / 2);
        const x = 980 + col * 640;
        const y = 300 + row * 235;
        return `${card(x, y, 560, 180, { fill: "#FFFFFF", stroke: "#D6E4EC", rx: 26, shadow: true })}
          <rect x="${x}" y="${y}" width="12" height="180" rx="6" fill="${i % 2 === 0 ? "#0F766E" : "#2563EB"}"/>
          ${linesSvg(wrapText(p, 15), x + 42, y + 72, { size: 35, fill: "#162B3D", weight: 700, lineHeight: 46 })}`;
      })
      .join("\n");
  }
  if (["uploadFlow", "queryFlow"].includes(v)) {
    const labels = v === "uploadFlow" ? ["上传文档", "解析切片", "Embedding", "Qdrant"] : ["用户提问", "构建 Scope", "过滤检索", "生成答案"];
    return labels
      .map((label, i) => {
        const x = 820 + i * 395;
        const y = 580 + (i % 2) * 70;
        return `${card(x, y, 270, 160, { fill: "#FFFFFF", stroke: "#CDE0EA", rx: 30, shadow: true })}
          ${textSvg(label, x + 135, y + 94, { size: 36, fill: "#132238", weight: 800, anchor: "middle" })}
          ${i < labels.length - 1 ? arrow(x + 282, y + 80, x + 370, 615 + ((i + 1) % 2) * 70) : ""}`;
      })
      .join("\n");
  }
  if (v === "architecture") {
    const boxes = [
      ["React 前端", 850, 260, "#2563EB"],
      ["FastAPI 后端", 850, 540, "#0F766E"],
      ["Qdrant 向量库", 1420, 540, "#7C3AED"],
      ["Chat Model", 1420, 820, "#D97706"],
    ];
    return boxes
      .map(([label, x, y, color]) => `${card(x, y, 430, 170, { fill: "#FFFFFF", stroke: "#D8E6EF", rx: 30, shadow: true })}
        <circle cx="${Number(x) + 70}" cy="${Number(y) + 85}" r="34" fill="${color}"/>
        ${textSvg(label, Number(x) + 130, Number(y) + 98, { size: 38, fill: "#132238", weight: 800 })}
      `)
      .join("\n") + arrow(1065, 430, 1065, 535) + arrow(1285, 625, 1410, 625) + arrow(1635, 710, 1635, 815);
  }
  if (["formula", "barChart", "calculation"].includes(v)) {
    return `
      ${card(890, 320, 1220, 620, { fill: "#FFFFFF", stroke: "#D8E6EF", rx: 34, shadow: true })}
      ${textSvg("Token 损耗估算", 1500, 420, { size: 48, weight: 800, anchor: "middle", fill: "#0F766E" })}
      <rect x="1070" y="545" width="760" height="54" rx="27" fill="#E8EEF5"/>
      <rect x="1070" y="545" width="655" height="54" rx="27" fill="#0F766E"/>
      ${textSvg("chunk overlap ≈ 15.4%", 1450, 585, { size: 32, weight: 700, anchor: "middle", fill: "#FFFFFF" })}
      <rect x="1070" y="680" width="760" height="54" rx="27" fill="#E8EEF5"/>
      <rect x="1070" y="680" width="570" height="54" rx="27" fill="#2563EB"/>
      ${textSvg("潜在上下文冗余 ≈ 75%", 1450, 720, { size: 32, weight: 700, anchor: "middle", fill: "#FFFFFF" })}
      ${textSvg("单次 RAG：约 4070 - 4700 tokens", 1500, 840, { size: 40, weight: 800, anchor: "middle", fill: "#132238" })}
    `;
  }
  if (["shield", "mitigation"].includes(v)) {
    return `${iconSvg("shield", 1180, 320, 520, "#0F766E")}
      ${card(920, 870, 980, 130, { fill: "#EAF6F3", stroke: "#BFE0D7", rx: 30 })}
      ${textSvg("检索证据 + 范围过滤 + 回退机制", 1410, 950, { size: 42, weight: 800, anchor: "middle", fill: "#0F766E" })}`;
  }
  if (v === "roadmap") {
    return [0, 1, 2, 3, 4]
      .map((i) => {
        const x = 780 + i * 300;
        const y = 680 - (i % 2) * 95;
        return `<circle cx="${x}" cy="${y}" r="34" fill="${i < 2 ? "#0F766E" : "#2563EB"}"/>
          <path d="M${x + 34} ${y} H${x + 266}" stroke="#C9DCE8" stroke-width="8"/>
          ${linesSvg(wrapText(slide.points[i], 8), x - 70, y + 92, { size: 28, weight: 700, fill: "#132238", lineHeight: 36 })}`;
      })
      .join("\n");
  }
  if (v === "qa") {
    return `${card(1010, 330, 820, 520, { fill: "#FFFFFF", stroke: "#D8E6EF", rx: 42, shadow: true })}
      ${textSvg("?", 1420, 700, { size: 330, weight: 900, anchor: "middle", fill: "#0F766E" })}
      ${textSvg("Discussion", 1420, 820, { size: 48, weight: 800, anchor: "middle", fill: "#516272" })}`;
  }
  return `
    ${card(920, 310, 980, 580, { fill: "#FFFFFF", stroke: "#D8E6EF", rx: 36, shadow: true })}
    <circle cx="1410" cy="565" r="190" fill="#EAF6F3"/>
    <circle cx="1410" cy="565" r="120" fill="#DDEBFF"/>
    ${textSvg(slide.role.toUpperCase(), 1410, 586, { size: 42, weight: 900, anchor: "middle", fill: "#0F766E" })}
  `;
}

function buildSlideSvg(slide, index) {
  const leftBullets = bullets(slide.points, 150, 560, 20, { size: 36, lineHeight: 68 });
  const accent = index % 3 === 0 ? "#0F766E" : index % 3 === 1 ? "#2563EB" : "#7C3AED";
  return `
  <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#19364A" flood-opacity="0.12"/>
      </filter>
      <marker id="arrow" markerWidth="16" markerHeight="16" refX="12" refY="8" orient="auto">
        <path d="M2,2 L14,8 L2,14 Z" fill="#238B82"/>
      </marker>
      <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
        <stop offset="0" stop-color="#F7FAFC"/>
        <stop offset="1" stop-color="#EEF6F5"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#bg)"/>
    <circle cx="2320" cy="160" r="340" fill="${accent}" opacity="0.09"/>
    <circle cx="2270" cy="1250" r="460" fill="#0F766E" opacity="0.055"/>
    <path d="M0 1180 C360 1080, 510 1290, 940 1190 S1500 1125, 2560 1250 V1440 H0 Z" fill="#FFFFFF" opacity="0.55"/>
    <rect x="92" y="72" width="10" height="1220" rx="5" fill="${accent}" opacity="0.95"/>
    ${titleBlock(slide, index)}
    ${leftBullets}
    ${drawVisual(slide, index)}
    <text x="132" y="1320" font-family="Noto Sans SC, Microsoft YaHei, SimHei, Arial" font-size="24" fill="#789">Qdrant Knowledge Assistant · RAG 项目汇报</text>
  </svg>`;
}

async function renderImages() {
  for (let i = 0; i < slides.length; i++) {
    const out = path.join(imageDir, `slide_${String(i + 1).padStart(2, "0")}.png`);
    await sharp(Buffer.from(buildSlideSvg(slides[i], i))).png().toFile(out);
  }
}

function writeOutline() {
  const content = [
    "# Qdrant Knowledge Assistant 25页 PPT 大纲",
    "",
    "风格：清爽专业技术汇报风，浅色背景，蓝绿主色，信息图和流程图为主。",
    "",
    ...slides.map((s, i) => [
      `## Slide ${i + 1}: ${s.title}`,
      "",
      `- 副标题：${s.subtitle}`,
      `- 页面角色：${s.role}`,
      `- 视觉设计：${s.visual}`,
      ...s.points.map((p) => `- ${p}`),
      "",
    ].join("\n")),
  ].join("\n");
  fs.writeFileSync(path.join(deckDir, "outline.md"), content, "utf8");
}

function writeSpeech() {
  const content = slides
    .map((s, i) => `## Slide ${i + 1}: ${s.title}\n\n${s.notes}\n`)
    .join("\n");
  fs.writeFileSync(path.join(deckDir, "speech.md"), content, "utf8");
}

function assemblePpt() {
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Codex";
  pptx.subject = "Qdrant Knowledge Assistant RAG project";
  pptx.title = "Qdrant Knowledge Assistant 项目汇报";
  pptx.company = "E:\\aiAgent";
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: "Microsoft YaHei",
    bodyFontFace: "Microsoft YaHei",
    lang: "zh-CN",
  };

  for (let i = 0; i < slides.length; i++) {
    const slide = pptx.addSlide();
    slide.background = { color: "F7FAFC" };
    slide.addImage({
      path: path.join(imageDir, `slide_${String(i + 1).padStart(2, "0")}.png`),
      x: 0,
      y: 0,
      w: 13.333333,
      h: 7.5,
    });
    slide.addNotes(slides[i].notes);
  }

  const out = path.join(deckDir, `${deckName}.pptx`);
  return pptx.writeFile({ fileName: out });
}

async function main() {
  ensureDirs();
  writeOutline();
  writeSpeech();
  await renderImages();
  await assemblePpt();
  console.log(JSON.stringify({
    deckDir,
    pptx: path.join(deckDir, `${deckName}.pptx`),
    imageDir,
    outline: path.join(deckDir, "outline.md"),
    speech: path.join(deckDir, "speech.md"),
    slides: slides.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
