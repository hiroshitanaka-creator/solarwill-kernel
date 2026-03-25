from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote

from dotenv import load_dotenv

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_env() -> None:
    load_dotenv()


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _timeout_seconds() -> int:
    raw = _get_env("SOLARWILL_TIMEOUT_SECONDS", "30")
    try:
        return max(1, int(raw))
    except ValueError:
        return 30


def _constraint_check(question: str) -> ConstraintResult:
    for term in BLOCK_TERMS:
        if term in question:
            return "blocked"
    for term in WARN_TERMS:
        if term in question:
            return "warn"
    return "passed"


def _status_from_constraint(result: ConstraintResult) -> str:
    if result == "blocked":
        return "blocked"
    if result == "warn":
        return "warn"
    return "ok"


def _default_payload(question: str, constraint_result: ConstraintResult) -> dict[str, Any]:
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


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()
    return cleaned


def _normalize_payload(raw: dict[str, Any], question: str, constraint_result: ConstraintResult) -> dict[str, Any]:
    fallback = _default_payload(question, constraint_result)

    def _list_of_str(value: Any, default: list[str]) -> list[str]:
        if not isinstance(value, list):
            return default
        items = [str(v).strip() for v in value if str(v).strip()]
        return items or default

    def _str_value(value: Any, default: str) -> str:
        text = str(value).strip() if value is not None else ""
        return text or default

    return {
        "options": _list_of_str(raw.get("options"), fallback["options"]),
        "recommendation": _str_value(raw.get("recommendation"), fallback["recommendation"]),
        "reasons": _list_of_str(raw.get("reasons"), fallback["reasons"]),
        "risks": _list_of_str(raw.get("risks"), fallback["risks"]),
        "next_questions": _list_of_str(raw.get("next_questions"), fallback["next_questions"]),
    }


def _json_contract_prompt(question: str, constraint_result: ConstraintResult) -> str:
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


def _http_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _call_gemini(question: str, constraint_result: ConstraintResult, timeout: int) -> dict[str, Any]:
    api_key = _get_env("GEMINI_API_KEY")
    model = _get_env("SOLARWILL_GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is empty")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model)}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": _json_contract_prompt(question, constraint_result)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    raw = _http_json(url, payload, timeout)
    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(_strip_code_fences(text))
    return _normalize_payload(parsed, question, constraint_result)


def _call_ollama(question: str, constraint_result: ConstraintResult, timeout: int) -> dict[str, Any]:
    base_url = _get_env("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = _get_env("OLLAMA_MODEL", "llama3.1:8b")

    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": _json_contract_prompt(question, constraint_result),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    raw = _http_json(url, payload, timeout)
    text = raw["response"]
    parsed = json.loads(_strip_code_fences(text))
    return _normalize_payload(parsed, question, constraint_result)


def _build_response(
    req: DecisionRequest,
    backend_requested: str,
    backend_used: str,
    constraint_result: ConstraintResult,
    payload: dict[str, Any],
    notes: list[str],
) -> DecisionResponse:
    trace = DecisionTrace(
        backend_requested=backend_requested,
        backend_used=backend_used,
        prompt_version=_get_env("SOLARWILL_PROMPT_VERSION", "v0.1"),
        constraint_result=constraint_result,
        input_summary=req.normalized_question()[:80],
        timestamp=_now_iso(),
        notes=notes,
    )
    return DecisionResponse(
        status=_status_from_constraint(constraint_result),
        question=req.normalized_question(),
        options=payload["options"],
        recommendation=payload["recommendation"],
        reasons=payload["reasons"],
        risks=payload["risks"],
        next_questions=payload["next_questions"],
        trace=trace,
    )


def _run(req: DecisionRequest) -> DecisionResponse:
    backend_requested = _get_env("SOLARWILL_BACKEND", "stub").lower()
    timeout = _timeout_seconds()
    constraint_result = _constraint_check(req.normalized_question())
    notes: list[str] = []

    if constraint_result == "blocked":
        payload = _default_payload(req.normalized_question(), constraint_result)
        notes.append("blocked by basic constraint rule before model call")
        return _build_response(
            req=req,
            backend_requested=backend_requested,
            backend_used="stub",
            constraint_result=constraint_result,
            payload=payload,
            notes=notes,
        )

    try:
        if backend_requested == "gemini":
            payload = _call_gemini(req.normalized_question(), constraint_result, timeout)
            return _build_response(
                req=req,
                backend_requested=backend_requested,
                backend_used="gemini",
                constraint_result=constraint_result,
                payload=payload,
                notes=notes,
            )

        if backend_requested == "ollama":
            payload = _call_ollama(req.normalized_question(), constraint_result, timeout)
            return _build_response(
                req=req,
                backend_requested=backend_requested,
                backend_used="ollama",
                constraint_result=constraint_result,
                payload=payload,
                notes=notes,
            )

    except (RuntimeError, KeyError, ValueError, error.URLError, TimeoutError) as exc:
        notes.append(f"backend fallback to stub: {exc}")

    payload = _default_payload(req.normalized_question(), constraint_result)
    if backend_requested != "stub":
        notes.append("stub fallback used")
    return _build_response(
        req=req,
        backend_requested=backend_requested,
        backend_used="stub",
        constraint_result=constraint_result,
        payload=payload,
        notes=notes,
    )


def _save_trace(response: DecisionResponse) -> Path | None:
    save_trace = _get_env("SOLARWILL_SAVE_TRACE", "true").lower() == "true"
    if not save_trace:
        return None

    trace_dir = Path(_get_env("SOLARWILL_TRACE_DIR", "artifacts/traces"))
    trace_dir.mkdir(parents=True, exist_ok=True)

    filename = response.trace.timestamp.replace(":", "-") + ".json"
    path = trace_dir / filename
    path.write_text(
        json.dumps(response.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="solarwill", description="SolarWill Kernel CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one decision-support query")
    run_parser.add_argument("question", help="Question to evaluate")
    run_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    return parser


def main() -> None:
    _load_env()
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "run":
        parser.error("unknown command")

    req = DecisionRequest(question=args.question)
    result = _run(req)
    trace_path = _save_trace(result)

    if trace_path is not None:
        print(f"[solarwill] trace saved to: {trace_path}", file=sys.stderr)

    if args.pretty:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()