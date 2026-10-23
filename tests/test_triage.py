"""Regression tests for the /triage endpoint.

These tests run without an Anthropic API key. They replace the SDK call with a
capturing mock and validate that the request we build is compatible with the
installed anthropic SDK (argument names, message format, and tool schema).
"""
import inspect
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


class CapturingClient:
    """Stands in for main.client and records the exact kwargs passed through."""

    def __init__(self, response_content):
        self.response_content = response_content
        self.captured_kwargs = None

    class messages:
        # accessed as client.messages.create(...)
        @staticmethod
        def create(**kwargs):
            import main as _main
            _main._capture["kwargs"] = kwargs
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type=b["type"],
                        text=b.get("text", ""),
                        input=b.get("input", {}),
                    )
                    for b in _main._capture["response_content"]
                ]
            )


def _setup(monkeypatch_response_content):
    main._capture = {"response_content": monkeypatch_response_content}
    main.client = CapturingClient(monkeypatch_response_content)
    return TestClient(main.app)


def test_triage_request_is_sdk_compatible_tool_use():
    tool_response = [
        {
            "type": "tool_use",
            "id": "toolu_1",
            "input": {"patterns": ["DB_CONN_TIMEOUT"], "rca": "Connection pool exhausted."},
        }
    ]
    client = _setup(tool_response)
    r = client.post("/triage", json={"logs": "ERROR DB_CONN_TIMEOUT while serving request"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {
        "patterns": ["DB_CONN_TIMEOUT"],
        "rca": "Connection pool exhausted.",
    }

    kwargs = main._capture["kwargs"]
    # Every kwarg we pass must be accepted by the installed SDK's create() signature.
    sdk_params = set(
        inspect.signature(
            __import__("anthropic").Anthropic().messages.create
        ).parameters
    )
    unknown = set(kwargs) - sdk_params
    assert not unknown, f"messages.create received kwargs rejected by SDK: {unknown}"

    # Messages must be plain dicts with role/content.
    msgs = kwargs["messages"]
    assert isinstance(msgs, list) and msgs, "messages must be a non-empty list"
    for m in msgs:
        assert isinstance(m, dict), "each message must be a dict, not an SDK object"
        assert set(m) == {"role", "content"}

    # Tool schemas must use input_schema (SDK ToolParam contract).
    from anthropic.types import ToolParam

    allowed = set(ToolParam.__annotations__)
    for tool in kwargs["tools"]:
        assert "input_schema" in tool, "tool schema must use input_schema, not parameters"
        assert set(tool) <= allowed, f"unknown tool keys: {set(tool) - allowed}"


def test_triage_text_fallback():
    text_response = [{"type": "text", "text": "Plain text RCA fallback."}]
    client = _setup(text_response)
    r = client.post("/triage", json={"logs": "ERROR CACHE_MISS on request"})
    assert r.status_code == 200, r.text
    assert r.json()["rca"] == "Plain text RCA fallback."
    assert r.json()["patterns"] == ["ERROR", "CACHE_MISS"]


def test_triage_no_patterns_400():
    client = _setup([])
    r = client.post("/triage", json={"logs": "everything is fine"})
    assert r.status_code == 400


def test_health():
    client = _setup([])
    assert client.get("/health").json() == {"status": "ok"}
