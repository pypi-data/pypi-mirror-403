import asyncio

from llmops_observability.llm import (
    extract_text,
    extract_usage,
    extract_model_info,
    track_llm_call,
)
from llmops_observability.trace_manager import TraceManager


def test_extract_text_handles_multiple_formats():
    # String passthrough
    assert extract_text("hello") == "hello"

    # Bedrock Converse
    bedrock = {"output": {"message": {"content": [{"text": "bedrock"}]}}}
    assert extract_text(bedrock) == "bedrock"

    # Anthropic Messages
    anthropic = {"content": [{"text": "anthropic"}]}
    assert extract_text(anthropic) == "anthropic"

    # OpenAI-like
    openai = {"choices": [{"message": {"content": "openai"}}]}
    assert extract_text(openai) == "openai"


def test_extract_usage_from_result_usage_object():
    class Usage:
        def __init__(self):
            self.prompt_tokens = 10
            self.completion_tokens = 20
            self.total_tokens = 30

    class Result:
        def __init__(self):
            self.usage = Usage()

    usage = extract_usage(Result(), {})
    assert usage == {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}


def test_extract_usage_from_bedrock_dict():
    resp = {"usage": {"inputTokens": 5, "outputTokens": 7, "totalTokens": 12}}
    usage = extract_usage(resp, {})
    assert usage == {"input_tokens": 5, "output_tokens": 7, "total_tokens": 12}


def test_extract_usage_from_langchain_callback():
    class Callback:
        def __init__(self):
            self.prompt_tokens = 1
            self.completion_tokens = 2
            self.total_tokens = 3

    usage = extract_usage({}, {"config": {"callbacks": [Callback()]}})
    assert usage == {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}


def test_extract_model_info_from_kwargs_and_object():
    assert extract_model_info((), {"model": "m1"}) == "m1"

    class ModelObj:
        def __init__(self):
            self.model_name = "from_attr"

    assert extract_model_info((ModelObj(),), {}) == "from_attr"


def test_track_llm_call_without_active_trace_returns_raw_result(fake_langfuse):
    @track_llm_call()
    def llm_call(prompt: str):
        return {"output": {"message": {"content": [{"text": "resp"}]}}}

    result = llm_call("hi")
    assert result["output"]["message"]["content"][0]["text"] == "resp"
    # No trace → fake_langfuse should not have any updated generations
    assert fake_langfuse.updated_generations == []


def test_track_llm_call_with_active_trace_sync(fake_langfuse, monkeypatch):
    import llmops_observability.pricing as pricing

    # Ensure model is recognized for cost calculation
    model_id = next(iter(pricing.BEDROCK_PRICING.keys()))

    TraceManager.start_trace(name="llm_trace")

    @track_llm_call(model=model_id, metadata={"m": "v"})
    def llm_call(prompt: str):
        return {
            "output": {"message": {"content": [{"text": "resp"}]}},
            "usage": {"inputTokens": 10, "outputTokens": 20, "totalTokens": 30},
        }

    result = llm_call("hi")
    assert "output" in result

    # At least one generation update should have been recorded
    assert fake_langfuse.updated_generations
    update = fake_langfuse.updated_generations[-1]
    assert update["model"] == model_id
    assert update["usage_details"]["total"] == 30
    assert "cost_details" in update


def test_track_llm_call_with_active_trace_async(fake_langfuse):
    """Run async LLM call via asyncio.run so no async plugin is required."""

    async def _runner():
        TraceManager.start_trace(name="llm_trace_async")

        @track_llm_call()
        async def async_llm(prompt: str):
            await asyncio.sleep(0)
            return {"choices": [{"message": {"content": "ok"}}]}

        result = await async_llm("hello")
        assert result["choices"][0]["message"]["content"] == "ok"
        assert fake_langfuse.updated_generations

    asyncio.run(_runner())
