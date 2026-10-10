import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.chat import chat, MAX_ROUNDS
from app.main import app, Message
from app.tools import TOOLS, Tool, Empty, execute, schemas


def call(name, arguments, call_id="call-1"):
    data = dict(type="function_call", name=name, arguments=json.dumps(arguments), call_id=call_id)
    return SimpleNamespace(**data, model_dump=lambda **_: data)


def response(*calls, text="Done"):
    return SimpleNamespace(output=list(calls), output_text=text)


def client(*responses):
    return SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(side_effect=responses)))


@pytest.mark.asyncio
async def test_no_tool():
    model = client(response(text="Hello"))
    result = await chat(model, "test", [Message(role="user", content="Hello")])
    assert result["answer"] == "Hello" and result["tool_calls"] == []
    assert model.responses.create.call_count == 1


@pytest.mark.asyncio
async def test_tool_selection_and_result_return():
    model = client(response(call("calculate", {"expression": "(2+3)*4"})), response(text="20"))
    result = await chat(model, "test", [Message(role="user", content="Calculate (2+3)*4")])
    trace = result["tool_calls"][0]
    assert trace["result"] == {"value": 20}
    assert trace["stages"] == ["proposed", "validated", "executing", "completed"]
    inputs = model.responses.create.call_args_list[1].kwargs["input"]
    assert inputs[-1]["call_id"] == "call-1"
    assert json.loads(inputs[-1]["output"])["result"]["value"] == 20
    assert any(tool["name"] == "calculate" for tool in model.responses.create.call_args_list[0].kwargs["tools"])


@pytest.mark.asyncio
@pytest.mark.parametrize("name,args", [
    ("calculate", {"expression": "__import__('os').system('echo unsafe')"}),
    ("calculate", {"expression": "1/0"}),
    ("calculate", {"expression": 3}),
    ("calculate", {"expression": "2+2", "extra": True}),
    ("current_time", {"timezone": "invalid/zone"}),
    ("create_task", {"title": "  ", "note": ""}),
    ("not_allowed", {}),
])
async def test_invalid_arguments(name, args):
    assert (await execute(call(name, args)))["status"] == "error"


@pytest.mark.asyncio
async def test_malformed_json():
    item = call("calculate", {})
    item.arguments = "{"
    result = await execute(item)
    assert result["stages"] == ["proposed", "failed"]


@pytest.mark.asyncio
async def test_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_DB_PATH", str(tmp_path / "tasks.db"))
    saved = await execute(call("create_task", {"title": "Review", "note": "Run tests"}))
    assert saved["result"]["id"] == 1
    listed = await execute(call("list_tasks", {}))
    assert listed["result"]["tasks"][0]["title"] == "Review"
    orders = await execute(call("search_orders", {"query": "Asha"}))
    assert len(orders["result"]["orders"]) == 2
    clock = await execute(call("current_time", {"timezone": "Asia/Kolkata"}))
    assert "+05:30" in clock["result"]["datetime"]


@pytest.mark.asyncio
async def test_timeout_and_failure(monkeypatch):
    async def slow(args):
        await asyncio.sleep(1)
    monkeypatch.setitem(TOOLS, "slow", Tool(Empty, slow, "Slow test"))
    assert (await execute(call("slow", {}), timeout=.01))["result"]["code"] == "timeout"
    async def broken(args):
        raise RuntimeError("private credentials")
    monkeypatch.setitem(TOOLS, "broken", Tool(Empty, broken, "Broken test"))
    assert "private" not in str(await execute(call("broken", {})))


@pytest.mark.asyncio
async def test_parallel_reads_and_sequential_rounds(monkeypatch):
    started = []
    both_started = asyncio.Event()
    async def read(args):
        started.append(True)
        if len(started) == 2:
            both_started.set()
        await asyncio.wait_for(both_started.wait(), .5)
        return {"ok": True}
    monkeypatch.setitem(TOOLS, "read", Tool(Empty, read, "Read test"))
    model = client(response(call("read", {}, "a"), call("read", {}, "b")),
                   response(call("calculate", {"expression": "2+2"}, "c")), response())
    result = await chat(model, "test", [Message(role="user", content="Multiple tools")])
    assert [trace["round"] for trace in result["tool_calls"]] == [1, 1, 2]
    assert all(trace["status"] == "success" for trace in result["tool_calls"])


@pytest.mark.asyncio
async def test_sequential_writes(monkeypatch):
    active = 0
    async def write(args):
        nonlocal active
        assert active == 0
        active += 1
        await asyncio.sleep(.01)
        active -= 1
        return {"saved": True}
    monkeypatch.setitem(TOOLS, "write", Tool(Empty, write, "Write test", True))
    model = client(response(call("write", {}, "a"), call("write", {}, "b")), response())
    result = await chat(model, "test", [Message(role="user", content="Save two tasks")])
    assert all(item["status"] == "success" for item in result["tool_calls"])


@pytest.mark.asyncio
async def test_failed_tool_returns_to_model():
    model = client(response(call("calculate", {"expression": "1/0"})), response(text="Cannot divide by zero"))
    result = await chat(model, "test", [Message(role="user", content="1/0")])
    assert result["tool_calls"][0]["status"] == "error"
    assert model.responses.create.call_count == 2


@pytest.mark.asyncio
async def test_bounded_rounds():
    model = client(*[response(call("calculate", {"expression": "1+1"}, str(i))) for i in range(MAX_ROUNDS)], response())
    result = await chat(model, "test", [Message(role="user", content="Keep calculating")])
    assert len(result["tool_calls"]) == MAX_ROUNDS
    assert model.responses.create.call_args.kwargs["tool_choice"] == "none"


@pytest.mark.asyncio
async def test_weather_with_mock_http(monkeypatch):
    async def get(self, url, **kwargs):
        data = {"results": [{"name": "Pune", "latitude": 18.5, "longitude": 73.8}]} if "geocoding" in url else {"current": {"temperature_2m": 24}, "current_units": {"temperature_2m": "°C"}}
        return httpx.Response(200, json=data, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    result = await execute(call("get_weather", {"city": "Pune"}))
    assert result["result"]["current"]["temperature_2m"] == 24


@pytest.mark.asyncio
async def test_weather_failure(monkeypatch):
    async def get(self, url, **kwargs):
        return httpx.Response(500, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    assert (await execute(call("get_weather", {"city": "Pune"})))["status"] == "error"


def test_schema_safety():
    for schema in schemas():
        params = schema["parameters"]
        assert params["additionalProperties"] is False
        assert set(params.get("required", [])) == set(params["properties"])


def test_http(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(app) as web:
        assert web.get("/api/health").json()["configured"] is False
        assert web.post("/api/chat", json={"messages": [{"role": "user", "content": "hello"}]}).status_code == 503
        assert web.post("/api/chat", json={"messages": [{"role": "system", "content": "unsafe"}]}).status_code == 422
        assert web.post("/api/chat", json={"messages": []}).status_code == 422


@pytest.mark.asyncio
async def test_model_failure_preserves_completed_write(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_DB_PATH", str(tmp_path / "tasks.db"))
    model = client(response(call("create_task", {"title": "Review", "note": ""})), RuntimeError("provider failed"))
    result = await chat(model, "test", [Message(role="user", content="Create a task Review")])
    assert result["tool_calls"][0]["status"] == "success"
    assert "already completed" in result["answer"]
    listed = await execute(call("list_tasks", {}))
    assert len(listed["result"]["tasks"]) == 1
