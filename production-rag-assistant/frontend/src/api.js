const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed. Please try again.");
  }
  return response.json();
}

export const api = {
  listDocuments: () => request("/documents"),
  upload(file, chunkSize, chunkOverlap) {
    const body = new FormData();
    body.append("file", file);
    body.append("chunk_size", chunkSize);
    body.append("chunk_overlap", chunkOverlap);
    return request("/documents", { method: "POST", body });
  },
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  reindexDocument: (id) => request(`/documents/${id}/reindex`, {
    method: "POST",
    body: new FormData(),
  }),
  ask(payload) {
    return request("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
};
