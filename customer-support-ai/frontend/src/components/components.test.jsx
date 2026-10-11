import React from "react";
import { it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import Sidebar from "./Sidebar";
import { request, stream } from "../services/api";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("input supports send, multiline and loading", () => {
  const send = vi.fn();
  const view = render(<ChatInput onSend={send} busy={false} />);
  const input = screen.getByLabelText("Message support");
  fireEvent.change(input, { target: { value: "Hello" } });
  fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
  expect(send).not.toHaveBeenCalled();
  fireEvent.keyDown(input, { key: "Enter" });
  expect(send).toHaveBeenCalledWith("Hello");
  view.rerender(<ChatInput onSend={send} busy />);
  expect(screen.getByLabelText("Send message")).toBeDisabled();
});
it("renders sources, tool state and loading", () => {
  const view = render(
    <MessageBubble
      message={{
        role: "assistant",
        content: "",
        tool: { name: "status", status: "running" },
      }}
    />,
  );
  expect(screen.getByText("Thinking ···")).toBeInTheDocument();
  expect(screen.getByText(/status · running/)).toBeInTheDocument();
  view.rerender(
    <MessageBubble
      message={{
        role: "assistant",
        content: "Policy [1]",
        sources: [
          { source: "kb://1", title: "Refund policy", content: "30 days" },
        ],
      }}
    />,
  );
  fireEvent.click(screen.getByText("Refund policy"));
  expect(screen.getByText("30 days")).toBeInTheDocument();
});
it("drawer navigation has accessible close and empty state", () => {
  const close = vi.fn();
  render(<Sidebar items={[]} open onClose={close} />);
  expect(screen.getByText(/will appear/)).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText("Close navigation"));
  expect(close).toHaveBeenCalled();
});
it("surfaces API errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: "Order unavailable" }),
      }),
  );
  await expect(request("/test", {})).rejects.toThrow("Order unavailable");
});
it("parses split streaming chunks", async () => {
  const encoder = new TextEncoder();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(c) {
          c.enqueue(encoder.encode('{"type":"delta","text":"Hel'));
          c.enqueue(encoder.encode('lo"}\n{"type":"done"}\n'));
          c.close();
        },
      }),
    }),
  );
  const events = [];
  await stream("id", "hello", (e) => events.push(e));
  expect(events).toEqual([{ type: "delta", text: "Hello" }, { type: "done" }]);
});
it("detects interrupted streams", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(c) {
          c.close();
        },
      }),
    }),
  );
  await expect(stream("id", "hello", () => {})).rejects.toThrow("interrupted");
});
