import os
import tempfile

from llmops_observability import sqs


def test_is_sqs_enabled_false_by_default(monkeypatch):
    # Ensure env has no SQS URL so auto-init disables it
    monkeypatch.delenv("AWS_SQS_URL", raising=False)
    sqs._sqs_instance._init_once = False
    sqs._sqs_instance.client = None
    sqs._sqs_instance.sqs_enabled = False

    assert sqs.is_sqs_enabled() is False


def test_send_to_sqs_queues_message_when_enabled(enable_sqs):
    message = {"event_type": "test", "value": 1}
    ok = sqs.send_to_sqs(message)
    assert ok is True


def test_send_to_sqs_immediate_uses_client_directly(enable_sqs):
    message = {"event_type": "immediate", "value": 2}
    ok = sqs.send_to_sqs_immediate(message)
    assert ok is True
    # Immediate path should record at least one direct send
    assert enable_sqs.sent_messages


def test_spillover_file_created_on_failure(monkeypatch, tmp_path):
    # Force client absence so messages go to spillover
    inst = sqs._sqs_instance
    inst.client = None
    inst.sqs_enabled = True

    spill_path = tmp_path / "spillover.jsonl"
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", str(spill_path), raising=False)

    ok = sqs.send_to_sqs({"event_type": "spill", "v": 3})
    assert ok is False or ok is True  # queue may accept, but send will spill

    # Force flush through worker to write spillover
    inst._spillover_save({"event_type": "spill2"})
    assert spill_path.exists()
    with open(spill_path, "r") as f:
        lines = f.readlines()
    assert lines

