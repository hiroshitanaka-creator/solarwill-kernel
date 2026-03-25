import json

from solarwill.cli import _run, _save_trace
from solarwill.domain.models import DecisionRequest


def _set_trace_env(monkeypatch, trace_dir: str) -> None:
    monkeypatch.setenv("SOLARWILL_BACKEND", "stub")
    monkeypatch.setenv("SOLARWILL_SAVE_TRACE", "true")
    monkeypatch.setenv("SOLARWILL_TRACE_DIR", trace_dir)
    monkeypatch.setenv("SOLARWILL_PROMPT_VERSION", "trace-test-v0")


def test_trace_metadata_is_populated(monkeypatch) -> None:
    monkeypatch.setenv("SOLARWILL_BACKEND", "stub")
    monkeypatch.setenv("SOLARWILL_SAVE_TRACE", "false")
    monkeypatch.setenv("SOLARWILL_PROMPT_VERSION", "trace-test-v0")

    response = _run(DecisionRequest(question="進学するか迷っている"))
    trace = response.trace

    assert trace.backend_requested == "stub"
    assert trace.backend_used == "stub"
    assert trace.prompt_version == "trace-test-v0"
    assert trace.constraint_result == "passed"
    assert trace.input_summary == "進学するか迷っている"
    assert trace.timestamp


def test_save_trace_writes_json_file(monkeypatch, tmp_path) -> None:
    _set_trace_env(monkeypatch, str(tmp_path))

    response = _run(DecisionRequest(question="進学するか迷っている"))
    saved_path = _save_trace(response)

    assert saved_path is not None
    assert saved_path.exists()

    payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert payload["status"] == "ok"
    assert payload["question"] == "進学するか迷っている"
    assert payload["trace"]["backend_requested"] == "stub"
    assert payload["trace"]["backend_used"] == "stub"
    assert payload["trace"]["prompt_version"] == "trace-test-v0"


def test_save_trace_returns_none_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("SOLARWILL_BACKEND", "stub")
    monkeypatch.setenv("SOLARWILL_SAVE_TRACE", "false")

    response = _run(DecisionRequest(question="進学するか迷っている"))
    saved_path = _save_trace(response)

    assert saved_path is None