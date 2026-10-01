# FastAPI 요청 테스트
# - client fixture(conftest.py)가 TestClient를 넘겨준다 : 서버를 띄우지 않고 앱을 직접 호출한다
def test_health_returns_ok(client) -> None:
    """GET /health 는 200 과 {"status":"ok"} 를 돌려준다."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# 문서 목록 조회
# - DB를 실제로 조회하므로 PostgreSQL 컨테이너가 떠 있고 시드가 들어 있어야 통과한다
def test_documents_list_returns_rows(client) -> None:
    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    문서들 = r.json()
    assert len(문서들) > 0
    assert 문서들[0]["security_level"] in ("일반", "3급", "대외비")
    # secret_note 는 응답 모델에 없으므로 밖으로 나가면 안 된다.
    # - 응답 스키마(DocumentOut)가 내부 필드를 실제로 걸러내는지 확인하는 자리다
    assert "secret_note" not in 문서들[0]


# 없는 문서를 조회했을 때
# - 상태 코드만 보면 예외 핸들러가 빠져도 통과할 수 있어서, 본문 형식까지 함께 확인한다
# - code/message 는 main.py의 AgentError 핸들러가 만들어주는 값이다
def test_unknown_document_returns_404_with_code(client) -> None:
    r = client.get("/api/v1/documents/DOC-HR-999")
    assert r.status_code == 404
    본문 = r.json()
    assert 본문["code"] == "not_found"
    assert "DOC-HR-999" in 본문["message"]
