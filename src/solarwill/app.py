from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote

from solarwill.config import get_settings, load_env
from solarwill.domain.models import (
    ConstraintResult,
    DecisionRequest,
    DecisionResponse,
    DecisionTrace,
)

BLOCK_TERMS = (
    "自殺",
    "死にたい",
    "殺す",
    "爆弾",
    "毒",
)

WARN_TERMS = (
    "投資",
    "借金",
    "裁判",
    "診断",
    "病気",
    "薬",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def constraint_check(question: str) -> ConstraintResult:
    settings = get_settings()
    if settings.constraint_mode != "basic":
        return "passed"

    for term in BLOCK_TERMS:
        if term in question:
            return "blocked"

    for term in WARN_TERMS:
        if term in question:
            return "warn"

    return "passed"


def status_from_constraint(result: ConstraintResult) -> str:
    if result == "blocked":
        return "blocked"
    if result == "warn":
        return "warn"
    return "ok"


def default_payload(question: str, constraint_result: ConstraintResult) -> dict[str, Any]:
    if constraint_result == "blocked":
        return {
            "options": [
                "一人で判断しない",
                "信頼できる人や専門家につなぐ",
                "安全確保を最優先する",
            ],
            "recommendation": "一人で進めず、安全確保と相談を優先する",
            "reasons": [
                "高リスクなテーマが含まれている",
                "単独判断より保護的対応が必要",
            ],
            "risks": [
                "一人で抱え込むこと",
                "衝動的に行動すること",
            ],
            "next_questions": [
                "今すぐ安全を確保できるか",
                "誰に連絡できるか",
            ],
        }

    if constraint_result == "warn":
        return {
            "options": [
                "今すぐ決める",
                "期限を決めて情報収集する",
                "第三者の視点を入れて比較する",
            ],
            "recommendation": "期限を決めて情報収集し、第三者視点も入れて比較する",
            "reasons": [
                "高リスク領域では確認不足の即断が危険",
                "比較材料を先に増やした方が判断しやすい",
            ],
            "risks": [
                "確認不足のまま断定すること",
                "一つの観点だけで決めること",
            ],
            "next_questions": [
                "この判断で最悪何が起きるか",
                "専門家確認が必要な点はどこか",
            ],
        }

    return {
        "options": [
            "今すぐ決める",
            "期限を決めて情報収集する",
            "一度保留して条件を言語化する",
        ],
        "recommendation": "期限を決めて情報収集する",
        "reasons": [
            "比較条件がまだ曖昧な可能性がある",
            "いきなり即断するより、判断材料を増やせる",
        ],
        "risks": [
            "先送りが長引くこと",
            "現状不満の原因が曖昧なままになること",
        ],
        "next_questions": [
            "最優先の制約は何か",
            "いちばん避けたい失敗は何か",
        ],
    }


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()
    return cleaned


def normalize_payload(
    raw: dict[str, Any],
    question: str,
    constraint_result: ConstraintResult,
) -> dict[str, Any]:
    fallback = default_payload(question, constraint_result)

    def list_of_str(value: Any, default: list[str]) -> list[str]:
        if not isinstance(value, list):
            return default
        items = [str(v).strip() for v in value if str(v).strip()]
        return items or default

    def str_value(value: Any, default: str) -> str:
        text = str(value).strip() if value is not None else ""
        return text or default

    return {
        "options": list_of_str(raw.get("options"), fallback["options"]),
        "recommendation": str_value(raw.get("recommendation"), fallback["recommendation"]),
        "reasons": list_of_str(raw.get("reasons"), fallback["reasons"]),
        "risks": list_of_str(raw.get("risks"), fallback["risks"]),
        "next_questions": list_of_str(raw.get("next_questions"), fallback["next_questions"]),
    }


def json_contract_prompt(question: str, constraint_result: ConstraintResult) -> str:
    return f"""
あなたは意思決定支援アシスタントです。
出力は必ず JSON オブジェクトのみで返してください。Markdownは禁止です。

目的:
- 質問に対して、短く、監査しやすい形で意思決定支援を返す

制約:
- constraint_result = "{constraint_result}"
- blocked の場合は安全優先の案内に寄せる
- warn の場合は断定を避け、確認事項を増やす
- 各文は短くする
- options は 3 つまで
- reasons, risks, next_questions は各 2 個まで

JSON schema:
{{
  "options": ["..."],
  "recommendation": "...",
  "reasons": ["..."],
  "risks": ["..."],
  "next_questions": ["..."]
}}

question:
{question}
""".strip()


def http_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def call_gemini(question: str, constraint_result: ConstraintResult) -> dict[str, Any]:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is empty")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(settings.gemini_model)}:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": json_contract_prompt(question, constraint_result)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    raw = http_json(url, payload, settings.timeout_seconds)
    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(strip_code_fences(text))
    return normalize_payload(parsed, question, constraint_result)


def call_ollama(question: str, constraint_result: ConstraintResult) -> dict[str, Any]:
    settings = get_settings()
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": json_contract_prompt(question, constraint_result),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    raw = http_json(url, payload, settings.timeout_seconds)
    text = raw["response"]
    parsed = json.loads(strip_code_fences(text))
    return normalize_payload(parsed, question, constraint_result)


def build_response(
    req: DecisionRequest,
    backend_requested: str,
    backend_used: str,
    constraint_result: ConstraintResult,
    payload: dict[str, Any],
    notes: list[str],
) -> DecisionResponse:
    settings = get_settings()
    trace = DecisionTrace(
        backend_requested=backend_requested,
        backend_used=backend_used,
        prompt_version=settings.prompt_version,
        constraint_result=constraint_result,
        input_summary=req.normalized_question()[:80],
        timestamp=now_iso(),
        notes=notes,
    )
    return DecisionResponse(
        status=status_from_constraint(constraint_result),
        question=req.normalized_question(),
        options=payload["options"],
        recommendation=payload["recommendation"],
        reasons=payload["reasons"],
        risks=payload["risks"],
        next_questions=payload["next_questions"],
        trace=trace,
    )


def run_decision(req: DecisionRequest) -> DecisionResponse:
    load_env()
    settings = get_settings()

    question = req.normalized_question()
    constraint_result = constraint_check(question)
    notes: list[str] = []

    if constraint_result == "blocked":
        payload = default_payload(question, constraint_result)
        notes.append("blocked by basic constraint rule before model call")
        return build_response(
            req=req,
            backend_requested=settings.backend,
            backend_used="stub",
            constraint_result=constraint_result,
            payload=payload,
            notes=notes,
        )

    try:
        if settings.backend == "gemini":
            payload = call_gemini(question, constraint_result)
            return build_response(
                req=req,
                backend_requested=settings.backend,
                backend_used="gemini",
                constraint_result=constraint_result,
                payload=payload,
                notes=notes,
            )

        if settings.backend == "ollama":
            payload = call_ollama(question, constraint_result)
            return build_response(
                req=req,
                backend_requested=settings.backend,
                backend_used="ollama",
                constraint_result=constraint_result,
                payload=payload,
                notes=notes,
            )

    except (RuntimeError, KeyError, ValueError, error.URLError, TimeoutError) as exc:
        notes.append(f"backend fallback to stub: {exc}")

    payload = default_payload(question, constraint_result)
    if settings.backend != "stub":
        notes.append("stub fallback used")

    return build_response(
        req=req,
        backend_requested=settings.backend,
        backend_used="stub",
        constraint_result=constraint_result,
        payload=payload,
        notes=notes,
    )


def save_trace(response: DecisionResponse) -> Path | None:
    settings = get_settings()
    if not settings.save_trace:
        return None

    settings.trace_dir.mkdir(parents=True, exist_ok=True)
    filename = response.trace.timestamp.replace(":", "-") + ".json"
    path = settings.trace_dir / filename
    path.write_text(
        json.dumps(response.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path