import Sources from "./Sources";
import ToolStatus from "./ToolStatus";
export default function MessageBubble({ message }) {
  return (
    <article className={`message ${message.role}`}>
      <div className="avatar">{message.role === "user" ? "AM" : "✳"}</div>
      <div className="message-body">
        <div className="message-label">
          {message.role === "user" ? "You" : "Northstar assistant"}
          {message.route && <span className="route">{message.route}</span>}
        </div>
        <ToolStatus tool={message.tool} />
        <div className="bubble">
          {message.content || (
            <span role="status" className="thinking">
              Thinking ···
            </span>
          )}
        </div>
        <Sources sources={message.sources} />
      </div>
    </article>
  );
}
