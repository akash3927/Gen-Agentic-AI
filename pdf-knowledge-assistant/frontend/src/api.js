const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Something went wrong. Please try again.");
  }
  return response.json();
}

export const api = {
  listDocuments: () => request("/documents"),

  uploadDocument(file, chunkSize, chunkOverlap) {
    const form = new FormData();
    form.append("file", file);
    form.append("chunk_size", chunkSize);
    form.append("chunk_overlap", chunkOverlap);
    return request("/documents", { method: "POST", body: form });
  },

  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),

  reindexDocument(id) {
    return request(`/documents/${id}/reindex`, {
      method: "POST",
      body: new FormData(),
    });
  },

  search(query, topK) {
    return request("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: Number(topK) }),
    });
  },
};
