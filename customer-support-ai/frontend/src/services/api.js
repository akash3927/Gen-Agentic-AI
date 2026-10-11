export async function request(path, body) {
  const res = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let data;
    try {
      data = await res.json();
    } catch {}
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return res;
}
export async function stream(id, message, onEvent) {
  const res = await request(`/conversations/${id}/chat`, { message });
  const reader = res.body.getReader(),
    decoder = new TextDecoder();
  let buffer = "",
    doneEvent = false;
  const parse = (line) => {
    if (line.trim()) {
      const event = JSON.parse(line);
      if (event.type === "done") doneEvent = true;
      onEvent(event);
    }
  };
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const lines = buffer.split("\n");
    // A network chunk can end mid-event; save that fragment for the next read.
    buffer = lines.pop();
    lines.forEach(parse);
    if (done) break;
  }
  parse(buffer);
  if (!doneEvent) throw new Error("Response interrupted. Please try again.");
}
