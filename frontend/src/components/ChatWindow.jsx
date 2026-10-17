import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Check, Copy, FileText } from "lucide-react";
import "./ChatWindow.css";

const SUGGESTIONS = [
  "Summarize this document",
  "What are the key points?",
  "Explain the main idea in simple words",
];

function formatTime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked, nothing to do */
    }
  };

  return (
    <button className="msg-action" onClick={copy} aria-label="Copy answer">
      {copied ? <Check size={14} /> : <Copy size={14} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function Message({ message, userName }) {
  const isUser = message.role === "User";

  if (isUser) {
    return (
      <div className="msg msg-user">
        <div className="msg-bubble">{message.content}</div>
        <span className="msg-meta mono">{formatTime(message.created_at)}</span>
      </div>
    );
  }

  return (
    <div className="msg msg-ai">
      <div className="msg-ai-head">
        <span className="msg-ai-mark" aria-hidden="true">A</span>
        {message.model && <span className="msg-meta mono">{message.model}</span>}
      </div>
      <div className="prose">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
      <div className="msg-actions">
        <CopyButton text={message.content} />
      </div>
    </div>
  );
}

function Thinking() {
  return (
    <div className="msg msg-ai" aria-live="polite">
      <div className="msg-ai-head">
        <span className="msg-ai-mark" aria-hidden="true">A</span>
        <span className="msg-meta mono">thinking</span>
      </div>
      <div className="dots" aria-label="The model is thinking">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

function EmptyState({ documents, onSend }) {
  const hasDocs = documents.length > 0;

  return (
    <div className="empty">
      <p className="eyebrow">{hasDocs ? "Ready" : "Start here"}</p>
      <h2>
        {hasDocs ? "Ask something about your PDF." : "Chat, or attach a PDF."}
      </h2>
      <p className="empty-body">
        {hasDocs
          ? "Answers come from the pages you uploaded. If it isn't in the document, the model will say so."
          : "Ask a general question, or use the paperclip below to add a PDF and ask about what's inside."}
      </p>

      {hasDocs && (
        <>
          <ul className="empty-files">
            {documents.map((d) => (
              <li key={d.id} className="mono">
                <FileText size={14} />
                {d.filename}
              </li>
            ))}
          </ul>

          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => onSend(s)}>
                {s}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default function ChatWindow({
  messages,
  documents,
  user,
  loading,
  sending,
  onSend,
}) {
  const scrollRef = useRef(null);
  const stickRef = useRef(true); // true while the user is near the bottom

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    stickRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  useEffect(() => {
    const el = scrollRef.current;
    if (el && stickRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, sending]);

  // opening a different chat always starts at the bottom
  useEffect(() => {
    stickRef.current = true;
  }, [loading]);

  if (loading) {
    return (
      <div className="chat-scroll">
        <p className="chat-loading mono">Loading conversation…</p>
      </div>
    );
  }

  const isEmpty = messages.length === 0 && !sending;

  return (
    <div className="chat-scroll" ref={scrollRef} onScroll={handleScroll}>
      <div className="chat-column">
        {isEmpty ? (
          <EmptyState documents={documents} onSend={onSend} />
        ) : (
          messages.map((m) => (
            <Message key={m.id} message={m} userName={user?.name} />
          ))
        )}
        {sending && <Thinking />}
      </div>
    </div>
  );
}