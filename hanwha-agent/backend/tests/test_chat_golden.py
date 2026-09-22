# 골든셋 회귀 테스트
# - LLM 은 같은 질문에 매번 다르게 답하므로, 응답 문자열을 그대로 비교할 수 없다
#   대신 "이 답에 반드시 있어야 할 것 / 절대 없어야 할 것"만 판정한다
# - 모델을 실제로 부르지 않는다. 미리 정해둔 응답을 돌려주는 StubLLM 으로 갈아끼운다
#   덕분에 결과가 항상 같고(재현 가능), 돈이 들지 않고, 인터넷 없이도 돈다
from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.integrations.factory as factory
from app.core.exceptions import GuardTripped
from app.core.guards import check_model
from app.integrations.ports import LLMResult
from app.services import chat_service

# 문항은 코드가 아니라 JSON 파일에 둔다
# - 문항을 늘릴 때 테스트 코드를 고치지 않아도 된다
# - __file__ 기준으로 찾으므로 pytest 를 어느 폴더에서 실행해도 같은 파일을 읽는다
GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "chat_golden.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


# 미리 정해둔 응답을 순서대로 돌려주는 가짜 어댑터
# - LLMPort 를 상속하지 않는다. Protocol 이라 answer 메서드만 같으면 그대로 들어간다
# - 응답이 replies 보다 더 필요해지면 마지막 것을 계속 돌려준다 (min 으로 인덱스를 묶어둔다)
class StubLLM:
    name = "stub"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls = 0

    # 키워드 전용(*)까지 포트와 똑같이 맞춘다
    # - runtime_checkable Protocol 은 이름만 보고 서명은 검사하지 않으므로, 여기서 어긋나면
    #   isinstance 는 통과하는데 호출에서 TypeError 가 난다
    def answer(self, *, question: str, contexts: list[dict], user: dict) -> LLMResult:
        text = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return LLMResult(
            text=text,
            model="claude-haiku-4-5",
            input_tok=1200,
            output_tok=300,
            cost_krw=2.3,
            latency_ms=900,
        )


# 판정 함수 — 실패 사유 목록을 돌려준다 (빈 목록 = 통과)
# - assert 를 여기서 바로 쓰지 않는다. 첫 번째 위반에서 멈추지 않고 사유를 모두 모아야
#   "무엇이 몇 개 어긋났는지"를 한 번에 볼 수 있다
def check(case: dict, out) -> list[str]:
    expect = case["expect"]
    problems: list[str] = []

    # 핵심 숫자·낱말이 답에 있는지 (문장 전체가 아니라 요점만 본다)
    for needle in expect.get("contains", []):
        if needle not in out.answer:
            problems.append(f"answer 에 '{needle}' 이 없습니다")

    # 근거에 없는 내용을 끌어다 지어내지 않았는지
    for needle in expect.get("not_contains", []):
        if needle in out.answer:
            problems.append(f"answer 에 '{needle}' 이 들어 있습니다")

    # 근거 건수 — 있어야 할 때는 최소, 없어야 할 때는 최대로 본다
    if "min_sources" in expect and len(out.sources) < expect["min_sources"]:
        problems.append(
            f"근거가 {expect['min_sources']}건 이상이어야 합니다 (현재 {len(out.sources)}건)"
        )
    if "max_sources" in expect and len(out.sources) > expect["max_sources"]:
        problems.append(
            f"sources 가 {expect['max_sources']}건이어야 합니다 (현재 {len(out.sources)}건)"
        )

    # 실행 정보 — 몇 번 만에 성공했는지, 폴백이었는지, 근거가 충분하다고 했는지
    for key in ("attempts", "fallback_used", "enough_evidence"):
        if key in expect and getattr(out, key) != expect[key]:
            problems.append(f"{key} 가 {expect[key]} 여야 합니다")

    # 화이트리스트 — 등록된 문서 번호만 인용했는지
    if "doc_ids" in expect:
        for source in out.sources:
            if source.doc_id not in expect["doc_ids"]:
                problems.append(f"허용되지 않은 doc_id: {source.doc_id}")

    return problems


# 문항의 질문 문자열을 만든다
# - repeat 는 2000자 초과 같은 긴 질문을 JSON 에 그대로 적지 않기 위한 장치다
def _question_of(case: dict) -> str:
    return case["question"] * case.get("repeat", 1)


# 골든셋 한 문항을 돌린다
# - ids= 를 주면 실패했을 때 test_golden[F-02] 처럼 문항 번호가 그대로 보인다
@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_golden(case: dict, monkeypatch) -> None:
    expect = case["expect"]

    # G 유형 — 가드가 막아야 하는 문항
    # - 답을 보는 게 아니라 "예외가 났는가"를 본다. 여기서 폴백 답변이 나오면 가드를 둔 의미가 없다
    if "raises" in expect:
        with pytest.raises(GuardTripped) as caught:
            if case.get("guard") == "check_model":
                check_model(case["question"])
            else:
                # 가드는 서비스 맨 앞에 있어서 모델을 부르기 전에 막힌다 (Stub 도 필요 없다)
                chat_service.ask(question=_question_of(case))
        for needle in expect.get("contains", []):
            assert needle in str(caught.value)
        return

    # 팩토리의 get_llm 만 갈아끼운다 — 서비스 코드는 손대지 않는다
    # - monkeypatch 는 테스트가 끝나면 원래 함수로 되돌려 준다 (직접 되돌리면 빠뜨리기 쉽다)
    # - chat_service 가 factory 모듈을 통째로 import 해뒀기 때문에 이 교체가 먹는다
    #   (from ... import get_llm 이었다면 서비스가 쥔 이름은 바뀌지 않아 교체가 안 먹는다)
    stub = StubLLM(case["stub"])
    monkeypatch.setattr(factory, "get_llm", lambda: stub)

    out = chat_service.ask(question=_question_of(case))

    # 교체가 실제로 먹었는지 확인한다 — 0 이면 판정이 전부 통과해도 의미가 없다
    assert stub.calls > 0, "가짜 어댑터가 한 번도 불리지 않았습니다"
    assert check(case, out) == []
