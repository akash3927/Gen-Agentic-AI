import { useState } from "react";
export default function ChatInput({ onSend, busy }) {
  const [text, setText] = useState("");
  function send(e) {
    e.preventDefault();
    if (text.trim() && !busy) {
      onSend(text.trim());
      setText("");
    }
  }
  return (
    <form className="composer" onSubmit={send}>
      <textarea
        aria-label="Message support"
        placeholder="Ask a question or tell us what you need…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={2}
        maxLength={4000}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            send(e);
          }
        }}
      />
      <div className="composer-bottom">
        <span>Shift + Enter for a new line</span>
        <button
          className="send"
          disabled={busy || !text.trim()}
          aria-label="Send message"
        >
          {busy ? "···" : "↑"}
        </button>
      </div>
    </form>
  );
}
