import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Bot, ChevronDown, Database, FileText, FileUp, KeyRound, MessageSquare, Send, Sparkles, UserRound } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  createKnowledgeBase,
  KnowledgeBase,
  listKnowledgeBases,
  loginAdmin,
  queryAssistant,
  QueryResponse,
  uploadDocument,
} from './api/client';

type Message = {
  role: 'user' | 'assistant';
  text: string;
  response?: QueryResponse;
};

export function App() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [productLine, setProductLine] = useState('Alpha');
  const [productVersion, setProductVersion] = useState('v1');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [adminSecret, setAdminSecret] = useState('');
  const [adminReady, setAdminReady] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);

  async function refreshKnowledgeBases() {
    const items = await listKnowledgeBases();
    setKnowledgeBases(items);
    if (items.length && !items.some((item) => item.product_line === productLine && item.product_version === productVersion)) {
      setProductLine(items[0].product_line);
      setProductVersion(items[0].product_version);
    }
  }

  useEffect(() => {
    refreshKnowledgeBases().catch(() => setKnowledgeBases([]));
  }, []);

  const selectedLabel = useMemo(() => `${productLine} / ${productVersion}`, [productLine, productVersion]);

  async function submitQuestion(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    const current = question.trim();
    setQuestion('');
    setBusy(true);
    setMessages((items) => [...items, { role: 'user', text: current }]);
    try {
      const response = await queryAssistant(productLine, productVersion, current);
      setMessages((items) => [...items, { role: 'assistant', text: response.answer, response }]);
    } catch (error) {
      setMessages((items) => [
        ...items,
        { role: 'assistant', text: error instanceof Error ? error.message : '请求失败，请检查后端服务或模型配置。' },
      ]);
    } finally {
      setBusy(false);
    }
  }

  async function submitAdminLogin(event: FormEvent) {
    event.preventDefault();
    setStatus('');
    try {
      await loginAdmin(adminSecret);
      setAdminReady(true);
      setAdminSecret('');
      setStatus('管理员会话已启用');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '管理员登录失败');
    }
  }

  async function submitUpload(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setStatus('请选择文件');
      return;
    }
    setStatus('上传处理中');
    try {
      await createKnowledgeBase(productLine, productVersion);
      await uploadDocument(productLine, productVersion, file);
      await refreshKnowledgeBases();
      setFile(null);
      setStatus('文档已写入知识库');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '上传失败');
    }
  }

  function selectKnowledgeBase(value: string) {
    const [line, version] = value.split('::');
    setProductLine(line);
    setProductVersion(version);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>产品知识助手</h1>
            <p>{selectedLabel}</p>
          </div>
          <label className="kb-select">
            <Database size={18} aria-hidden />
            <select value={`${productLine}::${productVersion}`} onChange={(event) => selectKnowledgeBase(event.target.value)}>
              <option value={`${productLine}::${productVersion}`}>{selectedLabel}</option>
              {knowledgeBases.map((item) => (
                <option key={`${item.product_line}::${item.product_version}`} value={`${item.product_line}::${item.product_version}`}>
                  {item.product_line} / {item.product_version}
                </option>
              ))}
            </select>
          </label>
        </header>

        <div className="chat-panel">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                <MessageSquare size={30} aria-hidden />
                <strong>选择知识库后开始提问</strong>
                <span>回答会展示引用片段，并标记模型补充内容。</span>
              </div>
            ) : (
              messages.map((message, index) => <ChatMessage message={message} key={`${message.role}-${index}`} />)
            )}
            {busy ? (
              <article className="message assistant loading">
                <MessageHeader role="assistant" />
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            ) : null}
          </div>

          <form className="composer" onSubmit={submitQuestion}>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="输入产品或文档问题"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !question.trim()} title="发送">
              <Send size={18} aria-hidden />
            </button>
          </form>
        </div>
      </section>

      <aside className="admin-panel">
        <h2>管理员</h2>
        <form className="stack" onSubmit={submitAdminLogin}>
          <label>
            <span>管理密钥</span>
            <div className="with-icon">
              <KeyRound size={17} aria-hidden />
              <input
                type="password"
                value={adminSecret}
                onChange={(event) => setAdminSecret(event.target.value)}
                placeholder="APP_ADMIN_SECRET"
              />
            </div>
          </label>
          <button type="submit">启用会话</button>
        </form>

        <form className="stack" onSubmit={submitUpload}>
          <label>
            <span>产品线</span>
            <input value={productLine} onChange={(event) => setProductLine(event.target.value)} />
          </label>
          <label>
            <span>产品版本</span>
            <input value={productVersion} onChange={(event) => setProductVersion(event.target.value)} />
          </label>
          <label>
            <span>官方文档</span>
            <div className="file-input">
              <FileUp size={17} aria-hidden />
              <input
                type="file"
                accept=".txt,.md,.pdf"
                disabled={!adminReady}
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </div>
          </label>
          <button type="submit" disabled={!adminReady}>上传到知识库</button>
        </form>
        <p className="status">{status}</p>
      </aside>
    </main>
  );
}

function ChatMessage({ message }: { message: Message }) {
  return (
    <article className={`message ${message.role}`}>
      <MessageHeader role={message.role} />
      <div className="message-body">
        {message.role === 'assistant' && message.response ? (
          <>
            <section className="answer-block">
              <div className="section-label">
                <Sparkles size={15} aria-hidden />
                <span>回答</span>
              </div>
              <MarkdownContent content={message.text} />
            </section>
            <Evidence response={message.response} />
          </>
        ) : (
          <p>{message.text}</p>
        )}
      </div>
    </article>
  );
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}

function MessageHeader({ role }: { role: 'user' | 'assistant' }) {
  const isUser = role === 'user';
  return (
    <div className="message-header">
      <span className="avatar">{isUser ? <UserRound size={16} aria-hidden /> : <Bot size={16} aria-hidden />}</span>
      <strong>{isUser ? '你' : '知识助手'}</strong>
    </div>
  );
}

function Evidence({ response }: { response: QueryResponse }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`evidence ${expanded ? 'expanded' : ''}`}>
      <button className="evidence-toggle" type="button" onClick={() => setExpanded((value) => !value)}>
        <div className="section-label">
          <FileText size={15} aria-hidden />
          <strong>文档依据</strong>
        </div>
        <span>{response.sources.length} 个片段</span>
        <ChevronDown size={16} aria-hidden />
      </button>
      {expanded ? (
        <>
          {response.grounded_summary ? <p className="grounded-summary">{response.grounded_summary}</p> : null}
          <div className="source-list">
            {response.sources.slice(0, 3).map((source) => (
              <blockquote key={`${source.document_id}-${source.chunk_index}`}>
                <span>{source.file_name} · {source.product_line}/{source.product_version}</span>
                <p>{source.text}</p>
              </blockquote>
            ))}
          </div>
        </>
      ) : null}
      {response.used_supplemental_knowledge && response.sources.length === 0 ? (
        <div className="supplemental">{response.supplemental_note || '回答包含模型补充内容。'}</div>
      ) : null}
    </div>
  );
}
