from llmops_observability.models import TraceConfig, SpanContext


def test_trace_config_defaults_from_env(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "proj_from_env")
    monkeypatch.setenv("ENV", "production")

    cfg = TraceConfig(name="op_name")

    assert cfg.project_id == "proj_from_env"
    assert cfg.environment == "production"
    assert cfg.metadata["project_id"] == "proj_from_env"
    assert cfg.metadata["environment"] == "production"
    # trace_name is derived from project_id
    assert cfg.trace_name == "proj_from_env"


def test_trace_config_explicit_values_override_env(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "ignored_project")
    monkeypatch.setenv("ENV", "ignored_env")

    cfg = TraceConfig(
        name="op",
        project_id="explicit_proj",
        environment="staging",
        metadata={"foo": "bar"},
    )

    assert cfg.project_id == "explicit_proj"
    assert cfg.environment == "staging"
    # base metadata preserved and enriched
    assert cfg.metadata["foo"] == "bar"
    assert cfg.metadata["project_id"] == "explicit_proj"
    assert cfg.metadata["environment"] == "staging"


def test_span_context_duration_ms_increases(monkeypatch):
    ctx = SpanContext(
        trace_id="t",
        span_id="s",
        parent_span_id=None,
        start_time=0.0,
        span_name="span",
    )
    # duration_ms should be an int >= 0
    assert isinstance(ctx.duration_ms, int)
    assert ctx.duration_ms >= 0

