export default function Sources({ sources = [] }) {
  return (
    sources.length > 0 && (
      <div className="sources">
        <span className="eyebrow">KNOWLEDGE SOURCES</span>
        {sources.map((s, i) => (
          <details key={s.source}>
            <summary>
              <span className="source-number">{i + 1}</span>
              {s.title}
              <span>↗</span>
            </summary>
            <p>{s.content}</p>
            <small>{s.source}</small>
          </details>
        ))}
      </div>
    )
  );
}
