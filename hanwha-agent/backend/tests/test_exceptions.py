# 예외 계층 검증
# - 예외마다 정해둔 상태 코드와 코드 문자열이 그대로 유지되는지 확인한다
# - 이 값들은 API 응답으로 그대로 나가기 때문에, 바뀌면 화면 쪽이 같이 깨진다
import pytest

from app.core.exceptions import (
    AgentError, NotFound, PermissionDenied, ValidationFailed, GuardTripped,
    RateLimited, ExternalServiceError, ModeNotAvailable, ApprovalRequired,
)

# (예외 클래스, 기대 상태 코드, 기대 코드 문자열)
CASES = [
    (NotFound, 404, "not_found"),
    (PermissionDenied, 403, "permission_denied"),
    (ValidationFailed, 422, "validation_failed"),
    (GuardTripped, 400, "guard_tripped"),
    (RateLimited, 429, "rate_limited"),
    (ExternalServiceError, 502, "external_service_error"),
    (ModeNotAvailable, 409, "mode_not_available"),
    (ApprovalRequired, 409, "approval_required"),
]

# parametrize : 같은 검사를 값만 바꿔 반복한다
# - 테스트 1개가 아니라 8개로 세어져서, 어느 예외가 깨졌는지 결과에 그대로 나온다
@pytest.mark.parametrize("exc_cls,status,code", CASES)
def test_domain_exception_maps_to_status_and_code(exc_cls, status, code) -> None:
    exc = exc_cls("문서를 찾을 수 없습니다: DOC-HR-014")
    assert exc.status_code == status
    assert exc.code == code


# 모든 예외가 AgentError를 상속하는지 확인
# - 예외 핸들러가 AgentError 하나로 다 잡기 때문에, 상속이 빠지면 그 예외만 500으로 새어 나간다
# - 여기서는 "전부 해당하는가" 하나만 보면 되므로 for 문으로 충분하다
def test_every_domain_exception_is_agent_error() -> None:
    for exc_cls, _status, _code in CASES:
        assert issubclass(exc_cls, AgentError)


# detail 은 선택값이다 (conftest.py의 travel_doc fixture를 받아서 사용)
# - 안 주면 None, 주면 그대로 보관된다
# - message 는 사용자에게, detail 은 내부 확인용으로 나눠 쓴다
def test_detail_is_optional_and_kept(travel_doc) -> None:
    없음 = NotFound(f"문서를 찾을 수 없습니다: {travel_doc['doc_id']}")
    assert 없음.detail is None
    assert 없음.message == "문서를 찾을 수 없습니다: DOC-HR-014"

    있음 = NotFound("문서를 찾을 수 없습니다: DOC-HR-014", detail="인사팀 시드 데이터 누락")
    assert 있음.detail == "인사팀 시드 데이터 누락"
