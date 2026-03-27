from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv(override=False)


def _read_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _read_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


@dataclass(slots=True)
class Settings:
    backend: str
    prompt_version: str
    debug: bool
    save_trace: bool
    trace_dir: Path
    timeout_seconds: int
    constraint_mode: str
    gemini_api_key: str
    gemini_model: str
    ollama_base_url: str
    ollama_model: str


def get_settings() -> Settings:
    return Settings(
        backend=_read_str("SOLARWILL_BACKEND", "stub").lower(),
        prompt_version=_read_str("SOLARWILL_PROMPT_VERSION", "v0.1"),
        debug=_read_bool("SOLARWILL_DEBUG", False),
        save_trace=_read_bool("SOLARWILL_SAVE_TRACE", True),
        trace_dir=Path(_read_str("SOLARWILL_TRACE_DIR", "artifacts/traces")),
        timeout_seconds=max(1, _read_int("SOLARWILL_TIMEOUT_SECONDS", 30)),
        constraint_mode=_read_str("SOLARWILL_CONSTRAINT_MODE", "basic").lower(),
        gemini_api_key=_read_str("GEMINI_API_KEY", ""),
        gemini_model=_read_str("SOLARWILL_GEMINI_MODEL", "models/gemini-2.5-flash"),
        ollama_base_url=_read_str("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=_read_str("OLLAMA_MODEL", "llama3.1:8b"),
    )
