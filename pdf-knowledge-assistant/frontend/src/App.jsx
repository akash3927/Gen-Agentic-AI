import { useEffect, useState } from "react";
import { api } from "./api.js";

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  const loadDocuments = async () => {
    try {
      setDocuments(await api.listDocuments());
    } catch (error) {
      setMessage(error.message);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const upload = async (event) => {
    event.preventDefault();
    if (!file) return;
    setBusy("upload");
    setMessage("");
    try {
      await api.uploadDocument(file, chunkSize, chunkOverlap);
      setFile(null);
      event.currentTarget.reset();
      setMessage("PDF indexed successfully.");
      await loadDocuments();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  const remove = async (id) => {
    setBusy(id);
    setMessage("");
    try {
      await api.deleteDocument(id);
      setResults((current) => current.filter((item) => item.document_id !== id));
      await loadDocuments();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  const reindex = async (id) => {
    setBusy(id);
    setMessage("");
    try {
      await api.reindexDocument(id);
      setMessage("PDF re-indexed successfully.");
      await loadDocuments();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  const search = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    setBusy("search");
    setMessage("");
    try {
      const response = await api.search(query.trim(), topK);
      setResults(response.results);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">Project 03</p>
        <h1>PDF Knowledge Assistant</h1>
        <p className="subtitle">Index your PDFs, then search their content by meaning.</p>
      </header>

      {message && <div className="notice" role="status">{message}</div>}

      <section className="card">
        <h2>Upload PDF</h2>
        <form onSubmit={upload} className="stack">
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
            required
          />
          <div className="settings">
            <label>
              Chunk size
              <input type="number" min="50" max="20000" value={chunkSize} onChange={(e) => setChunkSize(e.target.value)} />
            </label>
            <label>
              Overlap
              <input type="number" min="0" max="10000" value={chunkOverlap} onChange={(e) => setChunkOverlap(e.target.value)} />
            </label>
          </div>
          <button disabled={busy === "upload"}>{busy === "upload" ? "Indexing…" : "Upload and index"}</button>
        </form>
      </section>

      <section className="card">
        <div className="section-heading">
          <h2>Indexed Documents</h2>
          <span>{documents.length}</span>
        </div>
        {documents.length === 0 ? (
          <p className="empty">No PDFs indexed yet.</p>
        ) : (
          <div className="document-list">
            {documents.map((document) => (
              <article className="document" key={document.id}>
                <div>
                  <strong>{document.filename}</strong>
                  <small>
                    {document.page_count} {document.page_count === 1 ? "page" : "pages"} · {document.chunk_count} chunks · {dateFormatter.format(new Date(document.indexed_at))}
                  </small>
                </div>
                <div className="actions">
                  <button className="secondary" disabled={busy === document.id} onClick={() => reindex(document.id)}>Re-index</button>
                  <button className="danger" disabled={busy === document.id} onClick={() => remove(document.id)}>Delete</button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <h2>Semantic Search</h2>
        <form onSubmit={search} className="search-form">
          <label className="query-field">
            Search across all indexed PDFs
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="What does the document say about…" required />
          </label>
          <label>
            Top K
            <input type="number" min="1" max="50" value={topK} onChange={(e) => setTopK(e.target.value)} />
          </label>
          <button disabled={busy === "search"}>{busy === "search" ? "Searching…" : "Search"}</button>
        </form>

        <div className="results">
          {results.map((result, index) => (
            <article className="result" key={`${result.document_id}-${result.chunk_index}`}>
              <div className="result-meta">
                <strong>#{index + 1} · Score {result.score.toFixed(3)}</strong>
                <span>{result.pdf_name} · Page {result.page_number}</span>
              </div>
              <p>{result.text}</p>
            </article>
          ))}
          {results.length === 0 && <p className="empty">Search results will appear here.</p>}
        </div>
      </section>
    </main>
  );
}
