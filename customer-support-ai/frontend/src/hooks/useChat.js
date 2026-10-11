import { useState, useEffect } from "react";
import { request, stream } from "../services/api";
export function useChat() {
  const [items, setItems] = useState([]),
    [active, setActive] = useState(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [pending, setPending] = useState(null),
    [toast, setToast] = useState("");
  const [mode, setMode] = useState("");
  useEffect(() => {
    request("/health")
      .then((r) => r.json())
      .then((d) => setMode(d.mode))
      .catch(() =>
        setError(
          "Cannot reach the support server. Start FastAPI and try again.",
        ),
      );
  }, []);
  const messages = items.find((x) => x.id === active)?.messages || [];
  function update(id, fn) {
    setItems((prev) =>
      prev.map((x) => (x.id === id ? { ...x, messages: fn(x.messages) } : x)),
    );
  }
  async function create() {
    const data = await (await request("/conversations", {})).json();
    setItems((prev) => [
      { id: data.id, title: "New conversation", messages: [] },
      ...prev,
    ]);
    setActive(data.id);
    return data.id;
  }
  async function newChat() {
    setError("");
    try {
      await create();
    } catch (e) {
      setError(e.message);
    }
  }
  async function send(text) {
    setBusy(true);
    setError("");
    try {
      const id = active || (await create());
      setItems((prev) =>
        prev.map((x) =>
          x.id === id
            ? { ...x, title: x.messages.length ? x.title : text.slice(0, 35) }
            : x,
        ),
      );
      update(id, (m) => [
        ...m,
        { role: "user", content: text },
        { role: "assistant", content: "" },
      ]);
      await stream(id, text, (event) => {
        if (event.type === "error") throw new Error(event.message);
        if (event.type === "confirmation")
          setPending({ ...event, session: id });
        update(id, (m) => {
          const copy = [...m],
            last = { ...copy.at(-1) };
          if (event.type === "delta") last.content += event.text;
          if (event.type === "sources") last.sources = event.sources;
          if (event.type === "route") last.route = event.route;
          if (event.type === "tool") last.tool = event;
          copy[copy.length - 1] = last;
          return copy;
        });
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function confirm(approved) {
    setBusy(true);
    setError("");
    try {
      const data = await (
        await request(`/conversations/${pending.session}/confirm`, {
          token: pending.token,
          approved,
        })
      ).json();
      update(pending.session, (m) => [
        ...m,
        { role: "assistant", content: data.message, route: "tool" },
      ]);
      setPending(null);
      setToast(data.message);
      setTimeout(() => setToast(""), 4000);
    } catch (e) {
      setPending(null);
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return {
    mode,
    items,
    active,
    messages,
    busy,
    error,
    pending,
    toast,
    newChat,
    send,
    confirm,
    select: setActive,
  };
}
