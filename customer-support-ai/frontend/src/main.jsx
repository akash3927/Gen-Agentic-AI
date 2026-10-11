import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import ConfirmationModal from "./components/ConfirmationModal";
import { useChat } from "./hooks/useChat";
import "./style.css";
function App() {
  const chat = useChat(),
    [open, setOpen] = useState(false);
  return (
    <div className="app">
      <Sidebar
        {...chat}
        onNew={() => {
          chat.newChat();
          setOpen(false);
        }}
        onSelect={(id) => {
          chat.select(id);
          setOpen(false);
        }}
        open={open}
        onClose={() => setOpen(false)}
      />
      <main>
        <header>
          <div>
            <button
              className="menu"
              aria-label="Open navigation"
              onClick={() => setOpen(true)}
            >
              ☰
            </button>
            <strong>Support assistant</strong>
            <span className="mode-badge">
              {chat.mode === "demo"
                ? "DEMO"
                : chat.mode === "openai"
                  ? "OPENAI"
                  : ""}
            </span>
            <span className="header-subtitle">
              We’re here to help you move forward
            </span>
          </div>
          <span className="availability">
            <i /> Always here
          </span>
        </header>
        <ChatWindow {...chat} onSend={chat.send} />
        <div className="input-area">
          {chat.error && (
            <div className="error" role="alert">
              {chat.error}
            </div>
          )}
          <ChatInput onSend={chat.send} busy={chat.busy || !!chat.pending} />
          <div className="footnote">
            Powered by LangChain · AI can make mistakes. All order actions are
            simulated.
          </div>
        </div>
      </main>
      <ConfirmationModal
        action={chat.pending}
        onConfirm={chat.confirm}
        busy={chat.busy}
      />
      {chat.toast && (
        <div className="toast" role="status">
          ✓ {chat.toast}
        </div>
      )}
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
