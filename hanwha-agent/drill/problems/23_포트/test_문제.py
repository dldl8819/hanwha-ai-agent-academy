# 채점기 — 고치지 말 것
import dataclasses

import pytest

import 시작


def test_LLMResult_는_데이터클래스다():
    assert dataclasses.is_dataclass(시작.LLMResult)


def test_필수는_둘_나머지는_기본값():
    r = 시작.LLMResult(text="답", model="claude-haiku-4-5")
    assert (r.input_tok, r.cache_tok, r.output_tok, r.latency_ms) == (0, 0, 0, 0)
    assert r.cost_krw == 0.0
    assert r.extras == {}


def test_extras_는_인스턴스마다_따로다():
    a = 시작.LLMResult(text="a", model="m")
    b = 시작.LLMResult(text="b", model="m")
    a.extras["쓴다"] = 1
    # 기본값을 {} 로 적으면 여기서 b 까지 같이 바뀐다
    assert b.extras == {}
    assert a.extras is not b.extras


class 제대로된어댑터:
    def answer(self, *, question: str, contexts: list[dict], user: dict):
        return 시작.LLMResult(text=f"{question} 에 대한 답", model="stub", input_tok=10)


class 이름만같은어댑터:
    # 메서드 이름은 같지만 인자가 다르다
    def answer(self, q, ctx, u):
        return None


def test_Protocol_로_isinstance_가_된다():
    assert isinstance(제대로된어댑터(), 시작.LLMPort)


def test_규약대로_부르면_돌아간다():
    out = 제대로된어댑터().answer(question="숙박비?", contexts=[], user={})
    assert isinstance(out, 시작.LLMResult)
    assert out.input_tok == 10


def test_이름만_같아도_isinstance_는_통과한다는_것을_확인():
    # Protocol 은 이름만 본다 — 그래서 isinstance 만 믿으면 안 된다
    assert isinstance(이름만같은어댑터(), 시작.LLMPort)
    # 실제로 부르면 그때 터진다
    with pytest.raises(TypeError):
        이름만같은어댑터().answer(question="x", contexts=[], user={})
