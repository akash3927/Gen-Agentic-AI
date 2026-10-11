export default function ToolStatus({ tool }) {
  return (
    tool && (
      <div className="tool-status" role="status">
        ◈ {tool.name} · {tool.status}
        {tool.result && (
          <details>
            <summary>View result</summary>
            <pre>{JSON.stringify(tool.result, null, 2)}</pre>
          </details>
        )}
      </div>
    )
  );
}
