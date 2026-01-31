import asyncio

from llmops_observability.trace_manager import TraceManager, track_function, serialize_value


def test_start_and_end_trace(fake_langfuse):
    trace_id = TraceManager.start_trace(name="op_test")
    assert TraceManager.has_active_trace()
    assert TraceManager._active["trace_id"] is not None
    assert TraceManager._active["trace_obj"] in fake_langfuse.root_spans

    ended_id = TraceManager.end_trace(final_output={"ok": True})
    assert ended_id == TraceManager._active["trace_id"] or ended_id is not None
    # After end, no active trace
    assert not TraceManager.has_active_trace()
    assert TraceManager._active["trace_obj"] is None


def test_finalize_and_send_updates_trace(fake_langfuse):
    TraceManager.start_trace(name="http_request")

    ok = TraceManager.finalize_and_send(
        user_id="u1",
        session_id="s1",
        trace_name="trace_final",
        trace_input={"a": 1},
        trace_output={"b": 2},
        extra_spans=[],
    )
    assert ok is True
    # Root span should have at least one update_trace call with input/output
    root = fake_langfuse.root_spans[-1]
    assert root.trace_updates
    last = root.trace_updates[-1]
    assert last["name"] == "trace_final"
    assert last["user_id"] == "u1"
    assert last["session_id"] == "s1"
    assert "input" in last and "output" in last


def test_start_observation_context_creates_child_span(fake_langfuse):
    TraceManager.start_trace(name="parent_op")
    ctx = TraceManager.start_observation_context("child_span", "span", {"x": 1})
    assert ctx is not None
    # Using the context manager should not raise
    with ctx as obs:
        assert obs.name == "child_span"


def test_track_function_without_active_trace_buffers_span(fake_langfuse):
    @track_function()
    def add(x, y):
        return x + y

    result = add(1, 2)
    assert result == 3
    # No active trace → span buffered
    assert TraceManager._pending_spans
    pending = TraceManager._pending_spans[-1]
    assert pending["name"] == "add"
    assert pending["output"]["status"] == "success"


def test_track_function_with_active_trace_sync(fake_langfuse):
    TraceManager.start_trace(name="sync_trace")

    @track_function(metadata={"k": "v"}, capture_locals=True)
    def mul(a, b):
        c = a * b
        return c

    result = mul(3, 4)
    assert result == 12
    # After call, Langfuse client should have flushed
    assert fake_langfuse.flushed is True


def test_track_function_with_active_trace_async(fake_langfuse):
    """Run async function via asyncio.run so no async plugin is required."""

    async def _runner():
        TraceManager.start_trace(name="async_trace")

        @track_function(capture_locals=["value"])
        async def async_func(value):
            await asyncio.sleep(0)
            return value * 2

        result = await async_func(5)
        assert result == 10
        assert fake_langfuse.flushed is True

    asyncio.run(_runner())


def test_serialize_value_truncates_large_payload():
    large = "x" * (250 * 1024)
    out = serialize_value({"data": large})
    assert isinstance(out, dict)
    assert out.get("_truncated") is True
    assert "_preview" in out

