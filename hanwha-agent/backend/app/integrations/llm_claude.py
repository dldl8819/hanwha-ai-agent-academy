# Claude 어댑터
# - ports.py 의 LLMPort 규약을 Claude Messages API 로 구현한다
# - 서비스는 이 파일을 직접 import 하지 않고 factory.get_llm() 으로만 받는다 (test_layers.py 가 검사)
from __future__ import annotations
import json
import re
import time
from pathlib import Path
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.integrations.ports import LLMResult

# 로거 생성
log = get_logger(__name__)

# 프롬프트 파일이 있는 폴더
# - 이 파일(app/integrations/llm_claude.py) 기준 두 단계 위(app) / agent / prompts
# - 실행 위치와 상관없이 같은 폴더를 가리키도록 __file__ 기준으로 잡는다
PROMPTS = Path(__file__).resolve().parent.parent / 'agent' / 'prompts'

# 요금표 (USD / 100만 토큰)
# - 모델을 바꾸면 여기만 수정한다
# - 공급자마다 가격이 달라서 서비스가 아니라 어댑터 파일 안에 둔다
PRICING = {'input': 1.0, 'cache_write': 1.25, 'cache_read': 0.1, 'output': 5.0}
# 환율
USD_KRW = 1400.0

# 호출 한 번의 비용을 원화로 어림 잡아 계산
# - 캐시 쓰기/읽기 단가는 아직 반영하지 않는다 (입력은 전부 input 단가로 계산한다)
def estimate_cost_krw(input_tok: int, output_tok: int) -> float:
    usd = input_tok / 1000000 * PRICING['input'] + output_tok / 1000000 * PRICING['output']
    return round(usd * USD_KRW, 1)

# 프롬프트 파일을 하나 읽어서 문자열로 리턴해주는 함수
# - 파일이 없으면 에러 대신 빈 문자열을 돌려준다
# - 주의 : 파일 이름에 오타가 나도 에러가 없고, 규칙이 빠진 빈 system 프롬프트로 호출된다
def _load_prompt(name: str) -> str:
    path = PROMPTS / name
    return path.read_text(encoding="utf-8") if path.exists() else ""

# 근거 문서 목록을 모델이 읽을 문자열 한 덩어리로 변환해서 리턴하는 함수
# - contexts : 근거 항목 목록 (title, version, locator, score, quote 또는 text)
# - 근거가 0건이면 빈 칸이 아니라 "(근거 문서 없음)"을 넣는다
#   : 모델이 "근거가 없다"는 사실을 알아야 지어내지 않고 모른다고 답한다
def _context_block(contexts: list[dict]) -> str:
    lines = []
    # enumerate(..., 1) : 번호를 1부터 매긴다 ([근거 1], [근거 2] ...)
    for i, c in enumerate(contexts, 1):
        lines.append(
            f"[근거 {i}] {c.get('title')} {c.get('version')} · {c.get('locator')} "
            f"(유사도 {c.get('score', 0):.2f})\n{c.get('quote') or c.get('text') or ''}"
        )
    return "\n\n".join(lines) if lines else "(근거 문서 없음)"

# Claude Messages API 어댑터
class ClaudeLLM:
    name = 'claude'

    # 1. SDK와 키를 확인
    # 2. 클라이언트 생성
    # - anthropic 을 파일 맨 위가 아니라 여기서 import 한다
    #   : SDK 가 없는 환경이나 mock 모드에서도 이 파일을 import 하는 것만으로 앱이 죽지 않게
    def __init__(self) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ExternalServiceError("Anthropic 패키지가 설치되어 있지 않습니다.") from exc

        settings = get_settings()
        key = settings.anthropic_api_key  # SecretStr | None
        if key is None:
            raise ExternalServiceError("ANTHROPIC_API_KEY 값이 비어있습니다.")
        # 키는 SDK 에 넘기는 이 순간에만 꺼낸다
        self._client = Anthropic(api_key=key.get_secret_value())
        self._model = settings.llm_model

    # 공통으로 사용할 호출 함수
    # - Messages API 를 한 번 호출하고 (본문, 토큰 사용량, 걸린 시간) 을 리턴
    # - answer, draft 처럼 기능이 늘어도 실제 호출은 여기 한 곳에서만 한다
    def _call(self, system: str, user_text: str) -> tuple[str, dict, int]:
        # system    : 시스템 프롬프트 (역할·규칙·출력 형식 - 매 요청 같다)
        # user_text : 사용자 메시지 본문 (사용자·근거·질문 - 매 요청 다르다)

        # perf_counter()
        # - 경과 시간을 재기 위한 시계 함수 (시스템 시간 조정의 영향을 받지 않는다)
        started = time.perf_counter()
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=get_settings().max_tokens,
                system=system,
                messages=[
                    {
                        "role": "user",
                        "content": user_text
                    }
                ]
            )
        # 주의 : Exception 으로 넓게 잡아서, 이 블록 안의 우리 코드 오타(AttributeError 등)도
        #        "Claude 호출 실패"로 보인다. 진짜 원인은 from exc 로 트레이스백에 남는다.
        except Exception as exc:
            log.exception("Claude 호출 실패")
            # SDK 원문 에러는 detail 로 보낸다
            # - message 는 main.py 의 예외 핸들러가 그대로 화면에 응답하므로 일반 문구만 둔다
            raise ExternalServiceError("Claude 호출에 실패했습니다.", detail=str(exc)) from exc

        # 응답 받은 내용 중 필요한 부분만 추출해서 우리 규격으로 만들기
        # - content 는 블록 리스트라, type 이 text 인 블록만 모아 이어 붙인다
        text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
        # 사용량 정보 꺼내기
        usg = response.usage
        # 사용량 정보 정리
        # - getattr(..., 0) : 필드가 없어도 0
        # - or 0            : 값이 None 이어도 0
        usage = {
            "input": getattr(usg, "input_tokens", 0) or 0,
            "cache_read": getattr(usg, "cache_read_input_tokens", 0) or 0,
            "cache_write": getattr(usg, "cache_creation_input_tokens", 0) or 0,
            "output": getattr(usg, "output_tokens", 0) or 0,
        }
        # 응답 시간 계산 (밀리초)
        elapsed = int((time.perf_counter() - started) * 1000)
        # 결과 리턴
        return text, usage, elapsed

    # 근거 문서를 기반으로 질문에 답하는 함수
    # - ports.py 의 LLMPort.answer 구현체
    # - 인자 이름이 LLMPort 와 정확히 같아야 한다
    #   : runtime_checkable 은 메서드 이름만 보므로, 인자 이름이 달라도 isinstance 는 통과한다
    def answer(self, *, question: str, contexts: list[dict], user: dict) -> LLMResult:
        # question : 사용자 질문
        # contexts : 근거 문서 목록
        # user     : 질문한 사람 (name, dept ...)
        system = _load_prompt("answer_system.md")
        # 사용자 메시지는 요청마다 코드가 조립한다
        # - ## 제목으로 나눠, 모델이 어디까지가 근거이고 어디부터가 질문인지 구분하게 한다
        prompt = (
            f"## 사용자\n{user.get('name')} - {user.get('dept')}\n\n"
            f"## 근거 문서\n{_context_block(contexts)}\n\n"
            f"## 질문\n{question}"
        )

        # 위 _call 함수를 불러서 호출하고 리턴 데이터 받기
        text, usage, ms = self._call(system, prompt)
        # 입력 토큰 합계 (일반 입력 + 캐시 읽기 + 캐시 쓰기)
        total_in = usage["input"] + usage["cache_read"] + usage["cache_write"]
        return LLMResult(
            text=text,
            model=self._model,
            input_tok=total_in,
            cache_tok=usage["cache_read"],
            output_tok=usage["output"],
            cost_krw=estimate_cost_krw(total_in, usage["output"]),
            latency_ms=ms
        )

# 모델 응답 문자열에서 JSON 객체만 꺼내는 함수
# - 프롬프트에 "JSON 만 보내라"고 적어도 모델이 ```json ... ``` 코드펜스로 감싸 보낼 때가 있다
# - 그대로 json.loads / model_validate_json 에 넣으면 첫 글자(`)에서 실패한다
# - 꺼내지 못하면 에러 대신 빈 dict 를 돌려준다
#   : 호출하는 쪽에서 AnswerOut 검증 실패로 이어지므로 그 자리에서 처리해야 한다
def _extract_json(text: str) -> dict:
    # 1) 코드펜스가 있으면 안쪽 { ... } 만 꺼낸다
    # - (?:json)? : 펜스 뒤 "json" 표기는 있어도 없어도 된다
    # - re.S      : . 이 줄바꿈까지 포함하게 한다 (JSON 이 여러 줄일 수 있어서)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = fenced.group(1) if fenced else text

    # 2) 펜스가 없으면 앞뒤에 설명 문장이 붙어 있을 수 있다.
    # 첫 { 와 마지막 } 사이만 남긴다.
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        log.warning("응답 JSON 파싱 실패")
        return {}
