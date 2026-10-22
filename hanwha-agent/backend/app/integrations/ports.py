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

# 모델이 요청한 도구 호출 한 건
# - id 는 tool_result 의 tool_use_id 에 그대로 돌려줘야 한다 (모델이 짝을 맞추는 열쇠)
@dataclass
class ToolCall:
    id: str
    name: str
    args: dict

# LLM 어댑터가 지켜야할 규칙
# - 인터페이스
# - 코드 규격
@runtime_checkable
class LLMPort(Protocol):
    # 근거를 받아 한 번에 답하기 (코드가 검색 순서를 정하는 길)
    def answer(
        self,
        *,
        question:str,
        contexts: list[dict],
        user: dict,
        system: str | None = None
    ) -> LLMResult: ...

    # 도구 목록을 실어 모델을 한 번 부르기 (모델이 도구를 고르는 길)
    # - 루프는 서비스가 돌린다. 어댑터는 한 번 부르고 tool_use 블록을 ToolCall 로 바꿔 줄 뿐이다
    def answer_with_tools(
        self,
        *,
        messages: list[dict],
        tools: list[dict],
        user: dict
    ) -> LLMResult: ...

#----------- 문서 파싱 결과 -----------------------------------------------
# 파싱 결과의 최소 단위. 문서를 잘라놓은 덩어리 하나 : PDF, DOCX, HWPX  
@dataclass
class ParsedBlock: 
    kind: str            # 덩어리 종류 : 조항, 표 
    locator: str         # 원본 어디서 나온 덩어리 인지  : p.6, 표2
    text: str            # 덩어리 글자들 

# 문서 한건을 파싱한 결과 전체 
@dataclass
class ParsedDoc: 
    blocks: list[ParsedBlock] = field(default_factory=list)  # 본문에 놓은 순서 그대로 덩어리 목록 저장 
    page_count: int = 0                                      # 페이지 수. 페이지 개념이 없는 docx형식은 1로 둔다 .
    table_count: int = 0                                     # 표를 몇개 알아봤는지. 

# 파서 어댑터가 지켜야할 규칙 
# - 로컬 파서 또는 파싱 API 를 사용해도 아래 모양만 맞춰주면, 같은 코드로 사용 가능하게 해줌 
@runtime_checkable
class ParserPort(Protocol):
    def parse(self, path: str) -> ParsedDoc: ... 

# 검색 결과 담는 객체
@dataclass
class RetrievalResult:
    sources: list[dict] = field(default_factory=list) # 근거 후보 목록
    steps: list[dict] = field(default_factory=list)   # 화면의 검색 과정 보여줄 때 사용
    best_score: float = 0.0                           # 후보 중 가장 높은 유사도
    passed: bool = False                              # 최고 점수가 임계값을 넘었는가?
    version_note: str | None = None                   # 만료된 문서 버전을 걸렀을 때 사용자에게 알려줄 노트
    threshold: float = 0.55                           # 임계값


# --- embedding ---
# 임베딩 어댑터가 지켜야할 규칙
@runtime_checkable
class EmbedderPort(Protocol):
    dim: int 
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...

# --- 크로스 인코더 ---
# 크로스 인코더 어댑터가 지켜야할 규약
@runtime_checkable
class RerankerPort(Protocol):
    name: str
    def score_pairs(self, query: str, texts: list[str]) -> list[float]: ...

# --- 슬랙 ---
# 보낸 결과 한 건
@dataclass
class SlackResult:
    ok: bool
    channel: str = ""
    ts: str = ""                # 메시지 식별자
    error: str | None = None
    simulated: bool = False     # 실제로 보내지 않았으면 True

# 슬랙 어댑터가 지켜야할 규약
@runtime_checkable
class SlackPort(Protocol):
    def post(self, *, channel: str, text: str) -> SlackResult: ...
