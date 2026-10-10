"""Allowlisted Python tools. Model strings are never evaluated as Python."""
import ast
import asyncio
import math
import operator
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class Calculate(Arguments):
    expression: str = Field(min_length=1, max_length=200)


class Weather(Arguments):
    city: str = Field(min_length=1, max_length=100)


class Clock(Arguments):
    timezone: str = Field(min_length=1, max_length=100)

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use a valid IANA timezone, e.g. Asia/Kolkata") from exc
        return value


class Search(Arguments):
    query: str = Field(min_length=1, max_length=100)


class Task(Arguments):
    title: str = Field(min_length=1, max_length=120)
    note: str = Field(max_length=1000)


class Empty(Arguments):
    pass


async def calculate(args):
    tree = ast.parse(args.expression, mode="eval")
    if len(list(ast.walk(tree))) > 60:
        raise ValueError("Expression too complex")
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                  ast.Div: operator.truediv, ast.Mod: operator.mod}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            value = operations[type(node.op)](visit(node.left), visit(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        else:
            raise ValueError("Only numbers, parentheses, +, -, *, / and % are allowed")
        if abs(value) > 1e15 or not math.isfinite(value):
            raise ValueError("Result exceeds safe numeric range")
        return value

    return {"value": visit(tree.body)}


async def weather(args):
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get("https://geocoding-api.open-meteo.com/v1/search",
                                    params={"name": args.city, "count": 1, "language": "en"})
        response.raise_for_status()
        places = response.json().get("results", [])
        if not places:
            raise ValueError("City not found; include a more specific city name")
        place = places[0]
        response = await client.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": place["latitude"], "longitude": place["longitude"],
            "current": "temperature_2m,apparent_temperature,wind_speed_10m", "timezone": "auto"})
        response.raise_for_status()
        data = response.json()
        return {"city": place["name"], "country": place.get("country"),
                "current": data["current"], "units": data["current_units"],
                "source": "Open-Meteo", "source_url": "https://open-meteo.com/"}


async def current_time(args):
    return {"timezone": args.timezone, "datetime": datetime.now(ZoneInfo(args.timezone)).isoformat()}


ORDERS = [
    {"order_id": "ORD-1001", "customer_id": "C001", "customer": "Asha Patel", "status": "shipped", "total": 1499, "currency": "INR"},
    {"order_id": "ORD-1002", "customer_id": "C002", "customer": "Ravi Shah", "status": "processing", "total": 799, "currency": "INR"},
    {"order_id": "ORD-1003", "customer_id": "C001", "customer": "Asha Patel", "status": "delivered", "total": 2499, "currency": "INR"},
]


async def search_orders(args):
    return {"mock_data": True, "orders": [row for row in ORDERS if any(
        args.query.casefold() in str(row[key]).casefold() for key in ("order_id", "customer_id", "customer"))]}


def connection():
    db = sqlite3.connect(os.getenv("TASK_DB_PATH", "tasks.sqlite3"), timeout=2)
    db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, note TEXT NOT NULL)")
    return db


async def create_task(args):
    # No await between starting and committing a local write: timeout cannot leave a background write.
    with connection() as db:
        cursor = db.execute("INSERT INTO tasks(title, note) VALUES (?, ?)", (args.title, args.note))
        result = {"id": cursor.lastrowid, **args.model_dump()}
    db.close()
    return result


async def list_tasks(args):
    with connection() as db:
        rows = db.execute("SELECT id, title, note FROM tasks ORDER BY id DESC LIMIT 100").fetchall()
    db.close()
    return {"tasks": [dict(zip(("id", "title", "note"), row)) for row in rows]}


@dataclass(frozen=True)
class Tool:
    arguments: type[Arguments]
    function: object
    description: str
    modifies_data: bool = False


TOOLS = {
    "calculate": Tool(Calculate, calculate, "Calculate basic arithmetic; no powers or Python code."),
    "get_weather": Tool(Weather, weather, "Get current live weather for a city using Open-Meteo."),
    "current_time": Tool(Clock, current_time, "Get current date/time for an IANA timezone."),
    "search_orders": Tool(Search, search_orders, "Search mock customer orders by customer name, customer ID or order ID."),
    "create_task": Tool(Task, create_task, "Create a local task only when the user explicitly asks to create/save one. Supply title and note (empty if absent).", True),
    "list_tasks": Tool(Empty, list_tasks, "List up to 100 most recent saved local tasks."),
}


def schemas():
    return [{"type": "function", "name": name, "description": tool.description,
             "parameters": tool.arguments.model_json_schema(), "strict": True} for name, tool in TOOLS.items()]


async def execute(call, timeout=8):
    trace = {"call_id": call.call_id, "tool": call.name, "arguments": call.arguments,
             "stages": ["proposed"], "status": "error"}
    try:
        tool = TOOLS.get(call.name)
        if tool is None:
            raise ValueError("Unknown tool")
        args = tool.arguments.model_validate_json(call.arguments)
        trace["arguments"] = args.model_dump()
        trace["stages"].append("validated")
        trace["stages"].append("executing")
        trace["result"] = await asyncio.wait_for(tool.function(args), timeout)
        trace["status"] = "success"
        trace["stages"].append("completed")
    except (asyncio.TimeoutError, httpx.TimeoutException):
        trace["result"] = {"error": "Tool timed out", "code": "timeout"}
        trace["stages"].append("failed")
    except Exception as exc:
        # Do not expose provider responses, paths, credentials or internal stack traces.
        if isinstance(exc, (ValueError, SyntaxError, ZeroDivisionError)):
            message = "Invalid arguments or arithmetic operation" if hasattr(exc, "errors") else str(exc)
        else:
            message = "Tool failed; please retry"
        trace["result"] = {"error": message, "code": "tool_error"}
        trace["stages"].append("failed")
    return trace
