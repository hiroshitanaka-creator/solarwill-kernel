from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ConstraintResult = Literal["passed", "warn", "blocked"]
RunStatus = Literal["ok", "warn", "blocked"]


@dataclass(slots=True)
class DecisionRequest:
    question: str

    def normalized_question(self) -> str:
        return " ".join(self.question.split()).strip()


@dataclass(slots=True)
class DecisionTrace:
    backend_requested: str
    backend_used: str
    prompt_version: str
    constraint_result: ConstraintResult
    input_summary: str
    timestamp: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionResponse:
    status: RunStatus
    question: str
    options: list[str]
    recommendation: str
    reasons: list[str]
    risks: list[str]
    next_questions: list[str]
    trace: DecisionTrace

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["trace"] = self.trace.to_dict()
        return payload