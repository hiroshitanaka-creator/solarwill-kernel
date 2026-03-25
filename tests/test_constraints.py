from solarwill.cli import _constraint_check, _run
from solarwill.domain.models import DecisionRequest


def _set_env(monkeypatch, backend: str = "stub") -> None:
    monkeypatch.setenv("SOLARWILL_BACKEND", backend)
    monkeypatch.setenv("SOLARWILL_SAVE_TRACE", "false")
    monkeypatch.setenv("SOLARWILL_PROMPT_VERSION", "test-v0")


def test_constraint_check_returns_blocked_for_high_risk_terms() -> None:
    assert _constraint_check("死にたい") == "blocked"
    assert _constraint_check("爆弾を作りたい") == "blocked"


def test_constraint_check_returns_warn_for_caution_terms() -> None:
    assert _constraint_check("投資するべきか悩んでいる") == "warn"
    assert _constraint_check("借金してでも進学すべきか") == "warn"


def test_blocked_question_short_circuits_before_model_call(monkeypatch) -> None:
    _set_env(monkeypatch, backend="gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    response = _run(DecisionRequest(question="死にたい"))

    assert response.status == "blocked"
    assert response.trace.backend_requested == "gemini"
    assert response.trace.backend_used == "stub"
    assert response.trace.constraint_result == "blocked"
    assert any(
        "blocked by basic constraint rule before model call" in note
        for note in response.trace.notes
    )


def test_warn_question_returns_warn_status(monkeypatch) -> None:
    _set_env(monkeypatch, backend="stub")

    response = _run(DecisionRequest(question="借金して転職するべきか悩んでいる"))

    assert response.status == "warn"
    assert response.trace.constraint_result == "warn"
    assert response.trace.backend_used == "stub"