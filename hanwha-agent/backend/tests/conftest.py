# 테스트 공용 준비물(fixture)을 모아두는 파일
# - 파일 이름이 conftest.py 면 pytest가 알아서 읽는다 (import 하지 않아도 된다)
# - 이 폴더 아래의 모든 테스트 파일이 여기 fixture를 쓸 수 있다
import pytest
from fastapi.testclient import TestClient

from app.main import app

# 테스트용 문서 한 건
# - 테스트마다 다시 실행되므로, 한 테스트에서 값을 고쳐도 다음 테스트는 깨끗한 값을 받는다
@pytest.fixture
def travel_doc() -> dict:
    return {
        "doc_id": "DOC-HR-014",
        "title": "국내출장 여비 규정",
        "dept": "인사",
        "version": "v2.0",
        "security_level": "일반",
        "file_format": "docx",
        "status": "현행",
    }

# API 호출용 클라이언트
# - TestClient는 uvicorn을 띄우지 않고 app 객체를 직접 호출한다 (포트, 별도 터미널 불필요)
# - with 로 감싸야 main.py의 lifespan(setup_logging 등)이 실제로 실행된다
# - yield 뒤는 테스트가 끝난 뒤 정리 단계에서 실행된다
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
