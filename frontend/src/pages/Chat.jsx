import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu } from "lucide-react";
import { apiFetch, clearToken } from "../api";
import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import MessageInput from "../components/MessageInput";
import DocumentPanel from "../components/DocumentPanel";
import ConfirmDialog from "../components/ConfirmDialog";
import "./Chat.css";

export default function Chat() {
  const navigate = useNavigate();
  const activeRef = useRef(null); // always-current active conversation id

  const [booting, setBooting] = useState(true);
  const [user, setUser] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [models, setModels] = useState([]);
  const [model, setModel] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [sending, setSending] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState("");

  /* ---------- first load ---------- */
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const [me, convos, modelData] = await Promise.all([
          apiFetch("/me"),
          apiFetch("/conversations"),
          apiFetch("/get_models"),
        ]);
        if (cancelled) return;

        // backend returns {"Available Models": {key: ollamaName}}
        const list =
          modelData.models ?? Object.keys(modelData["Available Models"] ?? {});
        const saved = localStorage.getItem("model");

        setUser(me);
        setConversations(convos);
        setModels(list);
        setModel(list.includes(saved) ? saved : list[0] ?? "");
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setBooting(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await apiFetch("/conversations"));
    } catch {
      /* the sidebar just keeps its old list */
    }
  }, []);

  /* ---------- opening / starting chats ---------- */
  const openConversation = useCallback(async (id) => {
    activeRef.current = id;
    setActiveId(id);
    setSidebarOpen(false);
    setError("");
    setLoadingChat(true);

    try {
      const [detail, docs] = await Promise.all([
        apiFetch(`/conversations/${id}`),
        apiFetch(`/conversations/${id}/documents`),
      ]);
      if (activeRef.current !== id) return; // user already moved on

      setMessages(detail.messges ?? detail.messages ?? []);
      setDocuments(docs);
    } catch (err) {
      if (activeRef.current === id) setError(err.message);
    } finally {
      if (activeRef.current === id) setLoadingChat(false);
    }
  }, []);

  const startNewChat = useCallback(() => {
    activeRef.current = null;
    setActiveId(null);
    setMessages([]);
    setDocuments([]);
    setError("");
    setLoadingChat(false);
    setSidebarOpen(false);
  }, []);

  // Creates the conversation on the server the first time it's needed
  // (first message or first PDF). Returns its id.
  const ensureConversation = useCallback(async () => {
    if (activeRef.current) return activeRef.current;

    const convo = await apiFetch("/conversations", { method: "POST" });
    activeRef.current = convo.id;
    setActiveId(convo.id);
    setConversations((prev) => [convo, ...prev]);
    return convo.id;
  }, []);

  /* ---------- sending ---------- */
  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || sending || !model) return;

    setError("");
    setMessages((prev) => [
      ...prev,
      {
        id: `temp-${Date.now()}`,
        role: "User",
        content: trimmed,
        model: null,
        created_at: new Date().toISOString(),
      },
    ]);
    setSending(true);

    try {
      const convoId = await ensureConversation();

      const data = await apiFetch("/chat", {
        method: "POST",
        body: { conversation_id: convoId, model, message: trimmed },
      });

      // only show the reply if the user is still looking at this chat
      if (activeRef.current === convoId) {
        setMessages((prev) => [
          ...prev,
          {
            id: `reply-${Date.now()}`,
            role: "Assistant",
            content: data.message,
            model: data.model,
            created_at: new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
      refreshConversations(); // picks up the new title and ordering
    }
  };

  const changeModel = (m) => {
    setModel(m);
    localStorage.setItem("model", m);
  };

    /* ---------- documents ---------- */
  const uploadFile = async (file) => {
    if (!file || uploading || sending) return;

    if (file.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError("That file is over the 20 MB limit.");
      return;
    }

    setError("");
    setUploading(true);

    try {
      const convoId = await ensureConversation();

      const body = new FormData();
      body.append("file", file);

      const doc = await apiFetch(`/conversations/${convoId}/documents`, {
        method: "POST",
        body,
      });

      if (activeRef.current === convoId) {
        setDocuments((prev) => [...prev, doc]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const removeDocument = async (doc) => {
    const convoId = activeRef.current;
    if (!convoId) return;

    try {
      await apiFetch(`/conversations/${convoId}/documents/${doc.id}`, {
        method: "DELETE",
      });
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err) {
      setError(err.message);
    }
  };

  /* ---------- deleting / logout ---------- */
  const confirmDelete = async () => {
    const convo = pendingDelete;
    setPendingDelete(null);
    if (!convo) return;

    try {
      await apiFetch(`/conversations/${convo.id}`, { method: "DELETE" });
      setConversations((prev) => prev.filter((c) => c.id !== convo.id));
      if (activeRef.current === convo.id) startNewChat();
    } catch (err) {
      setError(err.message);
    }
  };

  const logout = () => {
    clearToken();
    navigate("/login", { replace: true });
  };

  /* ---------- render ---------- */
  if (booting) {
    return <div className="chat-boot mono">Loading…</div>;
  }

  const active = conversations.find((c) => c.id === activeId);

  return (
    <div className="chat-shell">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        user={user}
        open={sidebarOpen}
        onSelect={openConversation}
        onNew={startNewChat}
        onDelete={setPendingDelete}
        onLogout={logout}
        onClose={() => setSidebarOpen(false)}
      />

      {sidebarOpen && (
        <div className="scrim" onClick={() => setSidebarOpen(false)} />
      )}

      <main className="chat-main">
        <header className="chat-topbar">
          <button
            className="icon-btn menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <Menu size={18} />
          </button>
          <h1 className="chat-title">{active?.title ?? "New chat"}</h1>
        </header>

        <DocumentPanel
          documents={documents}
          uploading={uploading}
          onRemove={removeDocument}
          disabled={sending}
        />

        {error && (
          <div className="chat-error" role="alert">
            <span>{error}</span>
            <button onClick={() => setError("")}>Dismiss</button>
          </div>
        )}

        <ChatWindow
          messages={messages}
          documents={documents}
          user={user}
          loading={loadingChat}
          sending={sending}
          onSend={sendMessage}
        />

        <MessageInput
          models={models}
          model={model}
          onModelChange={changeModel}
          onSend={sendMessage}
          sending={sending}
          onAttach={uploadFile}
          uploading={uploading}
        />
      </main>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete this chat?"
        message={`"${pendingDelete?.title ?? ""}" and any PDFs attached to it will be permanently removed.`}
        confirmLabel="Delete"
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}