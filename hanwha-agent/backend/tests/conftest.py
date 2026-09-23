# 테스트 공용 준비물(fixture)을 모아두는 파일
# - 파일 이름이 conftest.py 면 pytest가 알아서 읽는다 (import 하지 않아도 된다)
# - 이 폴더 아래의 모든 테스트 파일이 여기 fixture를 쓸 수 있다
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


# 테스트가 개발 DB 를 건드리지 않게 막는 fixture
# - autouse=True : 테스트에서 부르지 않아도 항상 먼저 돈다
# - scope="session" : DB 파일을 하나 만들어 전체 테스트가 같이 쓴다 (매번 만들면 느리다)
#
# 왜 필요한가
#   chat_service.ask() 가 runs·usage_logs 에 INSERT 하게 되면서, pytest 를 한 번
#   돌릴 때마다 개발 DB 에 행이 쌓이고 run_id 가 앞으로 밀렸다.
#
# 어떻게 갈아끼우는가
#   session_scope() 는 불릴 때마다 get_settings().database_url 을 다시 읽는다.
#   그래서 환경변수를 바꾸고 캐시만 비우면 서비스 코드를 한 줄도 고치지 않고 DB 가 바뀐다.
@pytest.fixture(scope="session", autouse=True)
def test_db(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    db_path = tmp_path_factory.mktemp("db") / "test.db"

    previous = os.environ.get("DATABASE_URL")
    # as_posix() : 윈도우 역슬래시를 그대로 넣으면 SQLAlchemy 가 URL 로 읽지 못한다
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    get_settings.cache_clear()          # .env 에서 읽어둔 PostgreSQL 주소를 버린다

    # models 를 통째로 import 해야 Base.metadata 에 모든 표가 등록된다
    # - Alembic 의 autogenerate 가 models/__init__.py 를 보는 것과 같은 이유다
    import app.models  # noqa: F401
    from app.db.seed import seed_all
    from app.db.session import get_engine
    from app.models.base import Base

    Base.metadata.create_all(get_engine())

    # runs.user_id 는 users.id 를 가리키는 FK 라, 빈 DB 에서는 ask() 가 FK 위반으로 죽는다
    seed_all()

    yield

    # 같은 터미널에서 이어지는 다음 명령에 영향이 가지 않게 되돌린다
    if previous is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous
    get_settings.cache_clear()

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
