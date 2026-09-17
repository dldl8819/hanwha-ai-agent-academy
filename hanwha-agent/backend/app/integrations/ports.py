# 외부 연동 Protocol
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# LLM 호출 결과
@dataclass
class LLMResult:
    text: str
    model: str
    input_tok: int = 0
    cache_tok: int = 0
    output_tok: int = 0
    cost_krw: float = 0.0
    latency_ms: int = 0
    # 화면에 필요한 여분 데이터 세팅
    extras: dict = field(default_factory=dict)

# LLM 어댑터가 지켜야할 규칙
# - 인터페이스
# - 코드 규격
@runtime_checkable
class LLMPort(Protocol):
    def answer(
        self, 
        *, 
        question:str,
        contexts: list[dict],
        user: dict
    ) -> LLMResult: ...
