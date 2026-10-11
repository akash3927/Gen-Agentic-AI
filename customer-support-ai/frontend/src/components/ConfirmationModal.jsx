import { useEffect, useRef } from "react";
export default function ConfirmationModal({ action, onConfirm, busy }) {
  const ref = useRef();
  useEffect(() => {
    if (action) ref.current?.showModal();
    else ref.current?.close();
  }, [action]);
  useEffect(() => {
    if (action && !busy) ref.current?.querySelector("button")?.focus();
  }, [action, busy]);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onConfirm(false);
      }}
      onKeyDown={(e) => {
        if (e.key === "Tab") {
          const buttons = [...ref.current.querySelectorAll("button")];
          if (e.shiftKey && document.activeElement === buttons[0]) {
            e.preventDefault();
            buttons.at(-1).focus();
          } else if (!e.shiftKey && document.activeElement === buttons.at(-1)) {
            e.preventDefault();
            buttons[0].focus();
          }
        }
      }}
      aria-labelledby="confirm-title"
    >
      <div className="modal-icon">!</div>
      <h2 id="confirm-title">Confirm {action?.action}</h2>
      <p>
        This will {action?.action} mock order{" "}
        <strong>#{action?.order_id}</strong>. Review the action before
        continuing.
      </p>
      <div className="modal-actions">
        <button autoFocus disabled={busy} onClick={() => onConfirm(false)}>
          Keep my order
        </button>
        <button
          className="danger"
          disabled={busy}
          onClick={() => onConfirm(true)}
        >
          {busy ? "Working…" : "Confirm action"}
        </button>
      </div>
    </dialog>
  );
}
