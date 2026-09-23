# 채점기 — 고치지 말 것
import 시작

기대 = {"answer": "7만원", "enough_evidence": True}
본문 = '{"answer": "7만원", "enough_evidence": true}'


def test_순수_JSON():
    assert 시작._extract_json(본문) == 기대


def test_코드펜스_json_표기():
    assert 시작._extract_json(f"```json\n{본문}\n```") == 기대


def test_코드펜스_표기_없음():
    assert 시작._extract_json(f"```\n{본문}\n```") == 기대


def test_앞뒤에_설명이_붙은_경우():
    텍스트 = f"말씀하신 규정을 찾아봤습니다.\n{본문}\n도움이 되었길 바랍니다."
    assert 시작._extract_json(텍스트) == 기대


def test_여러_줄에_걸친_JSON():
    텍스트 = '```json\n{\n  "answer": "7만원",\n  "enough_evidence": true\n}\n```'
    assert 시작._extract_json(텍스트) == 기대


def test_중첩된_구조가_살아_있다():
    텍스트 = (
        '```json\n{"answer": "7만원", "sources": '
        '[{"doc_id": "DOC-HR-014", "locator": "제12조"}], "enough_evidence": true}\n```'
    )
    out = 시작._extract_json(텍스트)
    assert out["sources"][0]["doc_id"] == "DOC-HR-014"


def test_꺼내지_못하면_빈_딕셔너리():
    for 텍스트 in ["", "중괄호가 아예 없습니다", "죄송합니다. 답변할 수 없습니다."]:
        assert 시작._extract_json(텍스트) == {}


def test_깨진_JSON_이어도_예외가_나가지_않는다():
    for 텍스트 in ['{"answer": }', '{"answer" "7만원"}', "{'answer': '작은따옴표'}"]:
        assert 시작._extract_json(텍스트) == {}
