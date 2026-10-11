export default function Sidebar({
  items,
  active,
  onSelect,
  onNew,
  open,
  onClose,
  busy,
}) {
  return (
    <>
      {open && (
        <button
          className="overlay"
          aria-label="Close navigation"
          onClick={onClose}
        />
      )}
      <aside className={open ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <span>✳</span> northstar
          <button
            className="mobile-close"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            ×
          </button>
        </div>
        <div className="workspace">CUSTOMER EXPERIENCE</div>
        <button className="new-chat" onClick={onNew} disabled={busy}>
          ＋ New conversation
        </button>
        <div className="sidebar-label">YOUR CONVERSATIONS</div>
        <nav>
          {items.length === 0 && (
            <p className="sidebar-empty">
              Your conversations will appear here.
            </p>
          )}
          {items.map((item) => (
            <button
              disabled={busy}
              className={active === item.id ? "history active" : "history"}
              key={item.id}
              onClick={() => onSelect(item.id)}
            >
              ◷ <span>{item.title}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="online-dot" />
          Support, a little simpler.
          <small>Policies · Orders · Human help</small>
          <div className="profile">
            <span className="avatar">AM</span>
            <div>
              Alex Morgan<small>Demo customer</small>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
