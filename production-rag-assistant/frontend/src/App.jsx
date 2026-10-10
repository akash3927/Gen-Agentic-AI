import { useEffect, useState } from "react";
import { api } from "./api.js";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.3);
  const [rewrite, setRewrite] = useState(true);
  const [conversation, setConversation] = useState([]);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  async function loadDocuments() {
    try {
      setDocuments(await api.listDocuments());
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => { loadDocuments(); }, []);

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    setBusy("upload"); setMessage("");
    try {
      await api.upload(file, 1000, 200);
      setFile(null);
      event.currentTarget.reset();
      setMessage("PDF indexed successfully.");
      await loadDocuments();
    } catch (error) { setMessage(error.message); }
    finally { setBusy(""); }
  }

  async function remove(id) {
    setBusy(id); setMessage("");
    try {
      await api.deleteDocument(id);
      setSelectedIds((ids) => ids.filter((value) => value !== id));
      await loadDocuments();
    } catch (error) { setMessage(error.message); }
    finally { setBusy(""); }
  }

  async function reindex(id) {
    setBusy(id); setMessage("");
    try {
      await api.reindexDocument(id);
      setMessage("PDF re-indexed successfully.");
      await loadDocuments();
    } catch (error) { setMessage(error.message); }
    finally { setBusy(""); }
  }

  function toggleDocument(id) {
    setSelectedIds((ids) => ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id]);
  }

  async function ask(event) {
    event.preventDefault();
    const currentQuestion = question.trim();
    if (!currentQuestion) return;
    setBusy("ask"); setMessage("");
    try {
      const response = await api.ask({
        question: currentQuestion,
        top_k: Number(topK),
        similarity_threshold: Number(threshold),
        document_ids: selectedIds.length ? selectedIds : null,
        use_query_rewrite: rewrite,
      });
      setConversation((items) => [...items, { question: currentQuestion, ...response }]);
      setQuestion("");
    } catch (error) { setMessage(error.message); }
    finally { setBusy(""); }
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">Project 04</p>
        <h1>Production RAG Assistant</h1>
        <p className="subtitle">Ask questions. Get grounded answers with inspectable PDF sources.</p>
      </header>

      {message && <div className="notice" role="status">{message}</div>}

      <div className="layout">
        <aside>
          <section className="card">
            <h2>Add knowledge</h2>
            <form className="stack" onSubmit={upload}>
              <input type="file" accept="application/pdf,.pdf" required onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <button disabled={busy === "upload"}>{busy === "upload" ? "Indexing…" : "Upload PDF"}</button>
            </form>
          </section>

          <section className="card">
            <div className="heading"><h2>Documents</h2><span>{documents.length}</span></div>
            <p className="hint">Select documents to limit retrieval. No selection searches all.</p>
            <div className="documents">
              {documents.map((document) => (
                <article className="document" key={document.id}>
                  <label className="document-select">
                    <input type="checkbox" checked={selectedIds.includes(document.id)} onChange={() => toggleDocument(document.id)} />
                    <span><strong>{document.filename}</strong><small>{document.page_count} pages · {document.chunk_count} chunks</small></span>
                  </label>
                  <div className="actions">
                    <button className="quiet" disabled={busy === document.id} onClick={() => reindex(document.id)}>Re-index</button>
                    <button className="danger" disabled={busy === document.id} onClick={() => remove(document.id)}>Delete</button>
                  </div>
                </article>
              ))}
              {!documents.length && <p className="empty">No PDFs indexed yet.</p>}
            </div>
          </section>
        </aside>

        <section className="card chat">
          <div className="heading"><h2>Ask your documents</h2><span>{conversation.length} answers</span></div>
          <div className="conversation">
            {!conversation.length && <div className="welcome"><div>?</div><p>Your grounded answers and source passages will appear here.</p></div>}
            {conversation.map((item, index) => (
              <article className="exchange" key={`${item.question}-${index}`}>
                <p className="question">{item.question}</p>
                <div className={`answer ${item.insufficient_context ? "unknown" : ""}`}>
                  <p>{item.answer}</p>
                  {item.retrieval_query !== item.question && <small>Retrieved as: “{item.retrieval_query}”</small>}
                </div>
                {!!item.sources.length && (
                  <details>
                    <summary>{item.sources.length} {item.sources.length === 1 ? "source" : "sources"}</summary>
                    {item.sources.map((source, sourceIndex) => (
                      <div className="source" key={`${source.document_id}-${source.chunk_index}`}>
                        <strong>[Source {sourceIndex + 1}] {source.pdf_name} · Page {source.page_number}</strong>
                        <span>Similarity {source.score.toFixed(3)}</span>
                        <p>{source.text}</p>
                      </div>
                    ))}
                  </details>
                )}
              </article>
            ))}
          </div>

          <form className="composer" onSubmit={ask}>
            <textarea rows="3" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question about your PDFs…" required />
            <div className="settings">
              <label>Top K<input type="number" min="1" max="50" value={topK} onChange={(e) => setTopK(e.target.value)} /></label>
              <label>Threshold<input type="number" min="-1" max="1" step="0.05" value={threshold} onChange={(e) => setThreshold(e.target.value)} /></label>
              <label className="check"><input type="checkbox" checked={rewrite} onChange={(e) => setRewrite(e.target.checked)} /> Query rewrite</label>
              <button disabled={busy === "ask" || !documents.length}>{busy === "ask" ? "Thinking…" : "Ask"}</button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
