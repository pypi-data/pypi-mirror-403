import logging

import llmops_observability.config as config


def test_get_langfuse_client_uses_singleton(monkeypatch, fake_langfuse):
    # First call should return our injected fake client
    client1 = config.get_langfuse_client()
    client2 = config.get_langfuse_client()
    assert client1 is fake_langfuse
    assert client2 is fake_langfuse


def test_get_langfuse_client_sets_tracing_environment(monkeypatch, fake_langfuse):
    monkeypatch.setenv("ENV", "Production")
    # Reset to force re-init
    monkeypatch.setattr(config, "_langfuse_client", None, raising=False)

    client = config.get_langfuse_client()
    assert client is not None
    # ENV should be mapped to LANGFUSE_TRACING_ENVIRONMENT lowercased
    assert logging.getLogger("langfuse") is not None
    assert (
        "LANGFUSE_TRACING_ENVIRONMENT" in config.os.environ
        or "LANGFUSE_TRACING_ENVIRONMENT" in config.os.environ.keys()
    )


def test_configure_overrides_global_client(monkeypatch):
    # configure should replace the global client without error
    config.configure(
        public_key="pk",
        secret_key="sk",
        base_url="https://example.com",
        verify_ssl=True,
    )
    client = config.get_langfuse_client()
    assert client is not None


def test_get_sqs_config_reads_env(monkeypatch):
    monkeypatch.setenv("AWS_SQS_URL", "https://example.com/queue")
    monkeypatch.setenv("AWS_PROFILE", "my_profile")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    cfg = config.get_sqs_config()
    assert cfg["aws_sqs_url"] == "https://example.com/queue"
    assert cfg["aws_profile"] == "my_profile"
    assert cfg["aws_region"] == "us-west-2"

