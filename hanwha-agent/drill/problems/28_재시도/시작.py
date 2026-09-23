from __future__ import annotations

from pydantic import BaseModel, Field


# ── 응답 모델은 이미 있다 ──
class AnswerSource(BaseModel):
    doc_id: str
    title: str
    version: str
    locator: str


class AskOut(BaseModel):
    answer: str
    sources: list[AnswerSource]
    enough_evidence: bool
    run_id: str
    attempts: int = 1
    fallback_used: bool = False


# 첫 호출 1회 + 재시도 2회
MAX_ATTEMPTS = 3

# ══════ 여기부터 직접 채운다 ══════

# FALLBACK_ANSWER = ...
# def _hint_from(errors: list[dict]) -> str: ...
# def _fallback(run_id: str, attempts: int) -> AskOut: ...
