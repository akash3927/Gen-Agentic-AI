import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

async function api(path, body) {
  const response = await fetch(
    "/api" + path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
function App() {
  const [goal, setGoal] = useState(
    "Compare the benefits and limitations of solar and wind energy",
  );
  const [demo, setDemo] = useState(true),
    [maxSteps, setMaxSteps] = useState(12),
    [budget, setBudget] = useState(24000);
  const [run, setRun] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const active = run && ["running", "awaiting_approval"].includes(run.status);
  useEffect(() => {
    if (!run || run.status !== "running") return;
    // Clean up polling and ignore late responses when this run changes or the UI unmounts.
    let disposed = false;
    const timer = setInterval(async () => {
      try {
        const data = await api("/runs/" + run.id);
        if (!disposed) setRun(data);
      } catch (e) {
        if (!disposed) setError(e.message);
      }
    }, 700);
    return () => {
      disposed = true;
      clearInterval(timer);
    };
  }, [run?.id, run?.status]);
  async function action(path, body) {
    setBusy(true);
    setError("");
    try {
      setRun(await api(path, body));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main>
      <header>
        <span>PROJECT 06 · PYTHON + REACT</span>
        <h1>Autonomous research agent</h1>
        <p>LLM → Decision → Tool → Observation → LLM</p>
      </header>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          action("/runs", {
            goal,
            max_steps: Number(maxSteps),
            token_budget: Number(budget),
            demo,
          });
        }}
      >
        <label htmlFor="goal">Research goal</label>
        <textarea
          id="goal"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          minLength={5}
          maxLength={2000}
          required
          disabled={active}
        />
        <div className="controls">
          <label>
            Maximum steps{" "}
            <input
              type="number"
              min="1"
              max="30"
              value={maxSteps}
              onChange={(e) => setMaxSteps(e.target.value)}
              disabled={active}
            />
          </label>
          <label>
            Token budget{" "}
            <input
              type="number"
              min="2000"
              max="100000"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              disabled={active}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={demo}
              onChange={(e) => setDemo(e.target.checked)}
              disabled={active}
            />{" "}
            Offline demo
          </label>
        </div>
        <button disabled={busy || active}>Start research</button>
        {active && (
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={() => action("/runs/" + run.id + "/stop", {})}
          >
            Stop
          </button>
        )}
        <p className="muted">
          Demo uses illustrative evidence. Live mode requires backend OpenAI and
          Brave Search keys.
        </p>
      </form>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {run && (
        <>
          <div className="metrics" aria-live="polite">
            <strong>{run.status.replaceAll("_", " ")}</strong>
            <span>
              {run.steps.length}/{run.max_steps} steps
            </span>
            <span>{run.input_tokens + run.output_tokens} tokens</span>
            <span>
              {run.estimated_cost_usd == null
                ? "Cost rates not configured"
                : "Estimated $" + run.estimated_cost_usd.toFixed(4)}
            </span>
          </div>
          <p>{run.reason}</p>
          {run.pending && (
            <section className="approval">
              <h2>Approval requested</h2>
              <p>{run.pending.reason}</p>
              <pre>{run.pending.arguments.content}</pre>
              <button
                disabled={busy}
                onClick={() =>
                  action("/runs/" + run.id + "/approval", { approved: true })
                }
              >
                Approve save
              </button>
              <button
                className="secondary"
                disabled={busy}
                onClick={() =>
                  action("/runs/" + run.id + "/approval", { approved: false })
                }
              >
                Reject
              </button>
            </section>
          )}
          <div className="columns">
            <section>
              <h2>Current plan</h2>
              {run.plan.length ? (
                <ol>
                  {run.plan.map((task, i) => (
                    <li key={i}>
                      <span className="muted">
                        {task.status.replaceAll("_", " ")} ·{" "}
                      </span>
                      {task.title}
                    </li>
                  ))}
                </ol>
              ) : (
                <p>Planning…</p>
              )}
              <h2>Sources</h2>
              {run.sources.map((source, i) => (
                <p key={i}>
                  <a href={source.url} target="_blank" rel="noreferrer">
                    {source.title}
                  </a>
                  <small> · {source.kind}</small>
                </p>
              ))}
              <h2>Saved notes</h2>
              {run.notes.map((note, i) => (
                <pre key={i}>{note}</pre>
              ))}
            </section>
            <section>
              <h2>Agent iterations</h2>
              {run.steps.map((step) => (
                <article key={step.number}>
                  <strong>
                    {step.number}. {step.tool || "Finish"} · {step.status}
                  </strong>
                  <p>{step.summary}</p>
                  <details open>
                    <summary>Tool arguments and observation</summary>
                    <pre>
                      {JSON.stringify(
                        {
                          arguments: step.arguments,
                          observation: step.observation,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                </article>
              ))}
            </section>
          </div>
          {run.report && (
            <section>
              <h2>
                {run.status === "completed" ? "Final report" : "Partial report"}
              </h2>
              <pre className="report">{run.report}</pre>
            </section>
          )}
        </>
      )}
    </main>
  );
}
createRoot(document.getElementById("root")).render(<App />);
