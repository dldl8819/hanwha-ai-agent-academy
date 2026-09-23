# 채점기 — 고치지 말 것
import pytest

import 시작

표 = [
    ("AgentError", 400, "agent_error"),
    ("NotFound", 404, "not_found"),
    ("GuardTripped", 400, "guard_tripped"),
    ("RateLimited", 429, "rate_limited"),
    ("AuthFailed", 401, "auth_failed"),
]


@pytest.mark.parametrize("이름, status, code", 표, ids=[r[0] for r in 표])
def test_status_code_와_code(이름, status, code):
    cls = getattr(시작, 이름)
    assert cls.status_code == status
    assert cls.code == code


def test_전부_AgentError_로_잡힌다():
    for 이름, _, _ in 표[1:]:
        cls = getattr(시작, 이름)
        assert issubclass(cls, 시작.AgentError)
        with pytest.raises(시작.AgentError):
            raise cls("무슨 일이 있었다")


def test_메시지가_그대로_보인다():
    e = 시작.AgentError("문서를 찾지 못했습니다")
    assert e.message == "문서를 찾지 못했습니다"
    # print(e) 했을 때 메시지가 나와야 한다
    assert str(e) == "문서를 찾지 못했습니다"


def test_detail_은_선택이고_키워드_전용이다():
    assert 시작.AgentError("x").detail is None
    assert 시작.AgentError("x", detail="원인").detail == "원인"
    with pytest.raises(TypeError):
        시작.AgentError("x", "원인")


def test_AuthFailed_는_메시지_없이도_만들어진다():
    e = 시작.AuthFailed()
    assert isinstance(e.message, str) and e.message.strip()
    assert str(e) == e.message
    # 직접 준 메시지도 받아야 한다
    assert 시작.AuthFailed("직접 지정").message == "직접 지정"
    assert 시작.AuthFailed(detail="사번 없음").detail == "사번 없음"
