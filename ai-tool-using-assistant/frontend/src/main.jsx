import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function send(event) {
    event.preventDefault();
    if (busy || !text.trim()) return;
    // Keep a local snapshot because React state updates do not change this running handler.
    const next = [...messages, { role: "user", content: text.trim() }];
    setMessages(next);
    setText("");
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: next
            .slice(-29)
            .map(({ role, content }) => ({ role, content })),
        }),
        signal: AbortSignal.timeout(240000),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Request rejected. Please check your message.",
        );
      setMessages([
        ...next,
        {
          role: "assistant",
          content: data.answer,
          calls: data.tool_calls,
          limited: data.limit_reached,
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main>
      <header>
        <span className="eyebrow">PROJECT 05 · PYTHON TOOLS</span>
        <h1>Tool-Using Assistant</h1>
        <p>Ask a question. See the tools behind the answer.</p>
        <button
          disabled={busy}
          onClick={() => {
            setMessages([]);
            setError("");
          }}
        >
          New chat
        </button>
      </header>
      {!messages.length && (
        <section className="examples">
          <p>Try a question</p>
          {[
            "Explain what a Python dictionary is.",
            "What is the weather in Pune?",
            "Calculate (1499 + 799) * 0.9 and show orders for Asha.",
            "Create a task titled Review Project 05 with note Run the tests.",
          ].map((prompt) => (
            <button key={prompt} onClick={() => setText(prompt)}>
              {prompt}
            </button>
          ))}
        </section>
      )}
      <section className="conversation" aria-live="polite">
        {messages.map((message, index) => (
          <article key={index} className={message.role}>
            <strong>{message.role === "user" ? "You" : "Assistant"}</strong>
            {message.calls?.map((call) => (
              <details key={call.call_id} open className="trace">
                <summary>
                  {call.tool} · {call.status} · round {call.round}
                </summary>
                <p className="stages">{call.stages.join(" → ")}</p>
                <small>Arguments</small>
                <pre>{JSON.stringify(call.arguments, null, 2)}</pre>
                <small>Result</small>
                <pre>{JSON.stringify(call.result, null, 2)}</pre>
              </details>
            ))}
            <p className="answer">{message.content}</p>
            {message.calls?.length === 0 && (
              <small>Answered without tools</small>
            )}
            {message.limited && <small>Tool-round limit reached</small>}
          </article>
        ))}
      </section>
      {busy && (
        <p role="status">
          Selecting tools, validating arguments, and preparing an answer…
        </p>
      )}
      {error && (
        <p role="alert" className="error">
          {error} Your previous message remains visible; resend it to retry.
        </p>
      )}
      <form onSubmit={send}>
        <label htmlFor="message">Your message</label>
        <textarea
          id="message"
          value={text}
          maxLength={8000}
          disabled={busy}
          onChange={(event) => setText(event.target.value)}
          placeholder="Ask about weather, orders, arithmetic, or create a task…"
        />
        <button type="submit" disabled={busy || !text.trim()}>
          {busy ? "Working…" : "Send message"}
        </button>
      </form>
      <footer>
        Weather: Open-Meteo · Orders: mock data · Tasks: saved locally. Tool
        traces appear when the response completes.
      </footer>
    </main>
  );
}
createRoot(document.getElementById("root")).render(<App />);
