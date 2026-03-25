import json
import sys

from solarwill.cli import _run, main
from solarwill.domain.models import DecisionRequest


def _set_stub_env(monkeypatch) -> None:
    monkeypatch.setenv("SOLARWILL_BACKEND", "stub")
    monkeypatch.setenv("SOLARWILL_SAVE_TRACE", "false")
    monkeypatch.setenv("SOLARWILL_PROMPT_VERSION", "test-v0")


def test_run_smoke_stub_ok(monkeypatch) -> None:
    _set_stub_env(monkeypatch)

    response = _run(DecisionRequest(question="転職するべきか悩んでいる"))

    assert response.status == "ok"
    assert response.question == "転職するべきか悩んでいる"
    assert len(response.options) == 3
    assert response.recommendation
    assert len(response.reasons) >= 1
    assert len(response.risks) >= 1
    assert len(response.next_questions) >= 1
    assert response.trace.backend_requested == "stub"
    assert response.trace.backend_used == "stub"
    assert response.trace.constraint_result == "passed"


def test_cli_run_pretty_prints_json(monkeypatch, capsys) -> None:
    _set_stub_env(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["solarwill", "run", "転職するべきか悩んでいる", "--pretty"],
    )

    main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["status"] == "ok"
    assert payload["question"] == "転職するべきか悩んでいる"
    assert payload["trace"]["backend_used"] == "stub"