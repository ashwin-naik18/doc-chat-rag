import { LogOut, Plus, Trash2, X } from "lucide-react";
import "./Sidebar.css";

const DAY = 24 * 60 * 60 * 1000;

function groupConversations(conversations) {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const today = startOfToday.getTime();

  const groups = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Previous 7 days", items: [] },
    { label: "Older", items: [] },
  ];

  for (const c of conversations) {
    const t = new Date(c.updated_at).getTime();
    if (t >= today) groups[0].items.push(c);
    else if (t >= today - DAY) groups[1].items.push(c);
    else if (t >= today - 7 * DAY) groups[2].items.push(c);
    else groups[3].items.push(c);
  }

  return groups.filter((g) => g.items.length > 0);
}

export default function Sidebar({
  conversations,
  activeId,
  user,
  open,
  onSelect,
  onNew,
  onDelete,
  onLogout,
  onClose,
}) {
  const groups = groupConversations(conversations);

  return (
    <aside className={`sidebar ${open ? "is-open" : ""}`}>
      <div className="sidebar-head">
        <div className="sidebar-logo">
          <span className="sidebar-logo-mark" aria-hidden="true">A</span>
          <span className="sidebar-logo-name">AshRAG</span>
        </div>
        <button
          className="icon-btn sidebar-close"
          onClick={onClose}
          aria-label="Close sidebar"
        >
          <X size={18} />
        </button>
      </div>

      <button className="btn btn-ghost sidebar-new" onClick={onNew}>
        <Plus size={16} />
        New chat
      </button>

      <nav className="sidebar-list" aria-label="Conversations">
        {groups.length === 0 && (
          <p className="sidebar-empty">
            No chats yet. Ask something, or attach a PDF to begin.
          </p>
        )}

        {groups.map((group) => (
          <section key={group.label} className="sidebar-group">
            <h2 className="eyebrow">{group.label}</h2>

            {group.items.map((c) => (
              <div
                key={c.id}
                className={`convo ${c.id === activeId ? "is-active" : ""}`}
              >
                <button
                  className="convo-open"
                  onClick={() => onSelect(c.id)}
                  title={c.title}
                >
                  {c.title}
                </button>
                <button
                  className="convo-delete"
                  onClick={() => onDelete(c)}
                  aria-label={`Delete ${c.title}`}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </section>
        ))}
      </nav>

      <footer className="sidebar-foot">
        <div className="sidebar-user">
          <span className="sidebar-avatar" aria-hidden="true">
            {(user?.name?.[0] ?? "?").toUpperCase()}
          </span>
          <div className="sidebar-user-text">
            <span className="sidebar-user-name">{user?.name}</span>
            <span className="sidebar-user-email mono">{user?.email}</span>
          </div>
        </div>
        <button
          className="icon-btn"
          onClick={onLogout}
          aria-label="Log out"
          title="Log out"
        >
          <LogOut size={17} />
        </button>
      </footer>
    </aside>
  );
}