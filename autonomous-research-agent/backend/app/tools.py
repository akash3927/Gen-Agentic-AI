from __future__ import annotations

"""Four small validated tools; no eval and no arbitrary filesystem paths."""
import ast
import asyncio
import ipaddress
import math
import operator
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from html.parser import HTMLParser


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data.strip())


from pydantic import BaseModel, ConfigDict, Field


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class Search(Arguments):
    query: str = Field(min_length=1, max_length=300)


class Page(Arguments):
    url: str = Field(min_length=1, max_length=2000)


class Calculate(Arguments):
    expression: str = Field(min_length=1, max_length=200)


class Notes(Arguments):
    content: str = Field(min_length=1, max_length=6000)


ARGUMENTS = {
    "web_search": Search,
    "read_page": Page,
    "calculator": Calculate,
    "save_notes": Notes,
}
DESCRIPTIONS = {
    "web_search": "Search Brave Search API. Arguments: query (string). Returns snippets and source URLs.",
    "read_page": "Read a public HTTPS HTML webpage. Arguments: url (string). Returns extracted text.",
    "calculator": "Basic arithmetic only. Arguments: expression (string).",
    "save_notes": "Persist research notes locally. Arguments: content (string). Requires human approval every time.",
}


async def public_url(url):
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Only public HTTPS URLs on port 443 are allowed")
    addresses = await asyncio.get_running_loop().getaddrinfo(
        parsed.hostname, 443, type=socket.SOCK_STREAM
    )
    if not addresses or any(
        not ipaddress.ip_address(row[4][0]).is_global for row in addresses
    ):
        raise ValueError("Private or reserved network addresses are blocked")


def calculator(expression):
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 60:
        raise ValueError("Expression too complex")
    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
    }

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            value = operations[type(node.op)](visit(node.left), visit(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.USub, ast.UAdd)
        ):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        else:
            raise ValueError("Only numbers and + - * / % are supported")
        if not math.isfinite(value) or abs(value) > 1e15:
            raise ValueError("Numeric limit exceeded")
        return value

    return {"value": visit(tree.body)}


async def perform(name, args, state):
    if name == "calculator":
        return calculator(args.expression)
    if name == "save_notes":
        # Approved only by the loop. Filename is server-generated, never model-controlled.
        directory = Path(os.getenv("NOTES_DIR", "data/notes"))
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / f"{state.id}.md").open("a") as file:
            file.write(args.content + "\n\n")
        state.notes.append(args.content)
        return {"saved": True, "content": args.content}
    async with httpx.AsyncClient(
        timeout=10, follow_redirects=False, trust_env=False
    ) as client:
        if name == "web_search":
            key = os.getenv("BRAVE_SEARCH_API_KEY")
            if not key:
                raise ValueError("Set BRAVE_SEARCH_API_KEY to use live search")
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": args.query, "count": 5},
                headers={"X-Subscription-Token": key},
            )
            response.raise_for_status()
            results = response.json().get("web", {}).get("results", [])
            return {
                "sources": [
                    {
                        "title": r["title"],
                        "url": r["url"],
                        "snippet": r.get("description", "")[:1200],
                        "kind": "search_snippet",
                    }
                    for r in results
                ]
            }
        await public_url(args.url)
        async with client.stream("GET", args.url) as response:
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                raise ValueError("Only HTML pages are supported")
            chunks = bytearray()
            async for chunk in response.aiter_bytes():
                chunks.extend(chunk)
                if len(chunks) > 1_000_000:
                    raise ValueError("Page exceeds 1 MB limit")
        parser = PageText()
        parser.feed(
            bytes(chunks).decode(response.encoding or "utf-8", errors="replace")
        )
        return {
            "text": " ".join(parser.parts)[:10000],
            "sources": [{"title": args.url, "url": args.url, "kind": "read_page"}],
        }


async def execute(name, arguments, state, timeout=15):
    """Retry transient network failures once; validation and writes are never retried."""
    try:
        args = ARGUMENTS[name].model_validate(arguments)
        for attempt in range(2):
            try:
                return await asyncio.wait_for(perform(name, args, state), timeout)
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                transient = not isinstance(
                    exc, httpx.HTTPStatusError
                ) or exc.response.status_code in (429, 500, 502, 503, 504)
                if attempt or not transient or name == "save_notes":
                    raise
                await asyncio.sleep(0.25)
    except (asyncio.TimeoutError, httpx.TimeoutException):
        return {"error": "Tool timed out"}
    except (ValueError, SyntaxError, ZeroDivisionError, KeyError):
        return {
            "error": "Invalid tool arguments, unsupported URL/arithmetic, or missing search configuration"
        }
    except Exception:
        return {"error": "Tool failed; try another source or approach"}
