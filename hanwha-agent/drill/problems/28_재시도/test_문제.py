# 채점기 — 고치지 말 것
import 시작


def test_오류_한_건():
    errors = [{"loc": ("sources",), "msg": "Field required"}]
    assert 시작._hint_from(errors) == "sources: Field required"


def test_중첩된_위치는_점으로_잇는다():
    errors = [{"loc": ("sources", 0, "doc_id"), "msg": "Field required"}]
    assert 시작._hint_from(errors) == "sources.0.doc_id: Field required"


def test_여러_건은_슬래시로_잇는다():
    errors = [
        {"loc": ("answer",), "msg": "Field required"},
        {"loc": ("sources",), "msg": "Field required"},
    ]
    assert 시작._hint_from(errors) == "answer: Field required/sources: Field required"


def test_위치가_비어_있으면_최상위():
    assert 시작._hint_from([{"loc": (), "msg": "Input should be valid"}]) == "(최상위): Input should be valid"
    # loc 키 자체가 없어도 터지지 않는다
    assert "(최상위)" in 시작._hint_from([{"msg": "Input should be valid"}])


def test_빈_목록이면_빈_문자열():
    assert 시작._hint_from([]) == ""


def test_폴백은_예외가_아니라_정상_응답이다():
    out = 시작._fallback("RUN-8821", 3)
    assert isinstance(out, 시작.AskOut)
    assert out.run_id == "RUN-8821"
    assert out.attempts == 3
    assert out.fallback_used is True
    assert out.sources == []
    assert out.enough_evidence is False
    assert out.answer == 시작.FALLBACK_ANSWER


def test_폴백_문장은_비어_있지_않다():
    assert isinstance(시작.FALLBACK_ANSWER, str)
    assert 시작.FALLBACK_ANSWER.strip()


def test_폴백_문장에_내부_용어가_새지_않는다():
    낮춘 = 시작.FALLBACK_ANSWER.lower()
    for 금지 in ["스키마", "schema", "validation", "검증 실패", "재시도", "attempt", "json"]:
        assert 금지 not in 낮춘, f"사용자에게 보여줄 문장에 '{금지}' 가 들어 있습니다"
