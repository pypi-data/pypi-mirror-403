import asyncio

from llmops_observability.asgi_middleware import LLMOpsASGIMiddleware
from llmops_observability.trace_manager import TraceManager


async def _dummy_app(scope, receive, send):
    assert scope["type"] == "http"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b'{"message": "ok"}',
        }
    )


def _make_http_scope(path: str = "/"):
    return {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
    }


def test_asgi_middleware_traces_request(fake_langfuse):
    app = LLMOpsASGIMiddleware(_dummy_app, service_name="svc")

    async def runner():
        messages = []

        async def receive():
            return {"type": "http.request"}

        async def send(message):
            messages.append(message)

        scope = _make_http_scope("/")
        await app(scope, receive, send)
        return messages

    messages = asyncio.run(runner())
    # Should have sent start and body messages
    types = [m["type"] for m in messages]
    assert "http.response.start" in types
    assert "http.response.body" in types

    # After middleware completes, there should be no active trace
    assert not TraceManager.has_active_trace()

