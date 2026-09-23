# 채점기 — 고치지 말 것 (채점할 때마다 원본으로 덮어쓴다)
import typing

import pytest
from pydantic import BaseModel, ValidationError

import 시작

GOOD_SOURCE = {
    "doc_id": "DOC-HR-014",
    "title": "국내출장 여비 규정",
    "version": "v2.0",
    "locator": "제12조 · p.6",
}


def test_DOC_ID_는_세_건짜리_Literal_이다():
    assert typing.get_origin(시작.DOC_ID) is typing.Literal
    assert set(typing.get_args(시작.DOC_ID)) == {"DOC-HR-014", "DOC-PU-007", "DOC-SE-003"}


def test_질문은_2자_이상_2000자_이하():
    assert 시작.ChatRequest(question="안녕").question == "안녕"
    assert 시작.ChatRequest(question="가" * 2000)

    for 나쁜 in ["", "가", "가" * 2001]:
        with pytest.raises(ValidationError):
            시작.ChatRequest(question=나쁜)


def test_등록되지_않은_문서번호는_거부된다():
    assert 시작.AnswerSource(**GOOD_SOURCE).doc_id == "DOC-HR-014"
    with pytest.raises(ValidationError):
        시작.AnswerSource(**{**GOOD_SOURCE, "doc_id": "DOC-XX-999"})
    # 한 글자만 달라도 걸려야 한다
    with pytest.raises(ValidationError):
        시작.AnswerSource(**{**GOOD_SOURCE, "doc_id": "DOC_HR_014"})


def test_sources_는_문자열_목록이_아니라_모델_목록이다():
    out = 시작.AnswerOut(answer="7만원입니다.", sources=[GOOD_SOURCE], enough_evidence=True)
    assert isinstance(out.sources[0], BaseModel)
    assert out.sources[0].locator == "제12조 · p.6"

    # 안쪽까지 검증되어야 한다
    with pytest.raises(ValidationError):
        시작.AnswerOut(answer="x", sources=[{"doc_id": "DOC-HR-014"}], enough_evidence=True)
    with pytest.raises(ValidationError):
        시작.AnswerOut(answer="x", sources=["DOC-HR-014"], enough_evidence=True)


def test_세_필드_모두_필수다():
    for 빠뜨림 in ["answer", "sources", "enough_evidence"]:
        payload = {"answer": "x", "sources": [], "enough_evidence": True}
        payload.pop(빠뜨림)
        with pytest.raises(ValidationError):
            시작.AnswerOut(**payload)


def test_필드마다_설명이_달려_있다():
    for model in (시작.ChatRequest, 시작.AnswerSource, 시작.AnswerOut):
        for 이름, field in model.model_fields.items():
            assert field.description, f"{model.__name__}.{이름} 에 description 이 없습니다"
