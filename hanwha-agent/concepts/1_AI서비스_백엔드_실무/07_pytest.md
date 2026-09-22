# pytest

## pytest란

파이썬 테스트용 프레임워크다. 내가 만든 함수/코드가 예상대로 동작하는지 사람이 매번 눈으로 확인하지 않고, 자동으로 검사해주는 도구다.

```bash
python -m pip install pytest
```

## TDD (Test-Driven Development)

**테스트 코드가 실패하는 코드는 만들지 않겠다**는 개발 방식이다. 기능을 먼저 만들고 나중에 테스트를 붙이는 대신, 무엇이 맞는 동작인지를 테스트로 먼저 적어두고 그 테스트를 통과시키는 방향으로 구현한다. 그러면 "이 코드가 무엇을 보장하는지"가 테스트 파일에 남는다.

## 이름 규칙이 곧 등록이다

pytest에는 "이 테스트를 실행하라"고 별도로 등록하는 곳이 없다. 대신 이름 규칙을 따르기만 하면 pytest가 알아서 찾아서 실행해준다.

- 파일명: `test_`로 시작하거나 `_test`로 끝난다 (`test_config.py`)
- 함수명: `test_`로 시작한다 (`def test_xxxx():`)
- 클래스명: `Test`로 시작한다

규칙을 벗어난 이름은 **에러 없이 그냥 실행되지 않는다.**

```python
def clean_title(raw):
    return raw.strip()

def test_앞뒤_공백을_지운다():
    assert clean_title("     앞뒤 공백이 있는 문자열    ") == "앞뒤 공백이 있는 문자열"

# test_ 가 안 붙어 있어서 실행되지 않는다
def 빈_제목이면_빈_문자열():
    assert clean_title("   ") == ""
```

함수 이름은 한글로 써도 된다. 실행 결과에 이름이 그대로 찍혀서 무엇을 검사하는 테스트인지 읽기 쉬워진다.

```python
def add(a, b):
    return a + b

# 30이 나오는지 테스트
def test_add():
    assert add(10, 20) == 30
```

## assert로 검사하기

기대하는 값과 실제 값이 같은지는 `assert`로 확인한다. `assert 조건`이 참이면 통과, 거짓이면 그 테스트는 실패로 표시된다.

```python
from calculator import add, substract

def test_add():
    result = add(10, 20)
    assert result == 30

def test_substract():
    result = substract(10, 3)
    assert result == 5  # substract(10, 3)은 7이라 일부러 실패하는 케이스로 남겨둔 것
```

실행은 `pytest 파일경로 -v`로 한다. `-v`를 붙이면 각 테스트 함수 이름과 통과(`PASSED`)/실패(`FAILED`) 여부가 한 줄씩 보인다.

```bash
pytest sandbox/w2/day02/test_calculator.py -v
```

## 실습 중 만난 이슈: `__init__.py`가 있으면 import 경로가 바뀐다

`sandbox/` 아래 `day02/` 폴더에 빈 `__init__.py`를 하나 넣어뒀더니, 바로 옆에 있는 `calculator.py`를 `from calculator import add, substract`로 못 찾고 `ModuleNotFoundError: No module named 'calculator'`가 났다.

이유는 pytest의 기본 import 방식 때문이다. 테스트 파일이 있는 폴더에 `__init__.py`가 있으면 pytest는 그 폴더를 "패키지"로 보고, `__init__.py`가 없는 첫 상위 폴더(`w2`)를 `sys.path`에 넣는다. 그러면 `day02` 폴더 자체는 `sys.path`에 안 잡혀서, 같은 폴더의 `calculator.py`를 바로 `import`할 수 없다(`day02.calculator`로는 가능하지만 그렇게 쓰고 있지 않았다).

```text
day02/__init__.py 있음  → sys.path에 w2가 들어감 → from calculator import ... 실패
day02/__init__.py 없음  → sys.path에 day02가 들어감 → from calculator import ... 성공
```

`sandbox/day0N/`처럼 스크립트와 테스트를 나란히 두고 pytest로 그 파일만 바로 돌리는 구조에서는 `__init__.py`를 넣지 않는 게 맞다. 반대로 `backend/app/...`처럼 실제로 다른 모듈에서 import해서 쓰는 패키지에는 `__init__.py`가 필요하다.

## 테스트 파일은 한곳에 모은다

날짜 폴더마다 흩어 두면 나중에 전체를 한 번에 돌리기 어려워서, 테스트 실습용 파일은 `sandbox/pytest/`로 모았다.

```bash
pytest sandbox/pytest -v
```

## 실습 중 만난 이슈: 테스트에서 `app` 모듈을 못 찾는다

프로젝트 설정을 검사하는 테스트를 만들었더니 수집 단계에서 바로 멈췄다.

```python
# sandbox/pytest/test_import_fail.py
from app.core.config import get_settings

def test_설정_불러오기():
    assert get_settings().app_mode == "mock"
```

```text
ERROR collecting sandbox/pytest/test_import_fail.py
E   ModuleNotFoundError: No module named 'app'
!!!!!!! Interrupted: 1 error during collection !!!!!!!
```

`app` 패키지는 `backend/` 아래에 있는데, `pytest sandbox/pytest`로 실행하면 `sandbox/pytest`만 `sys.path`에 들어가서 `backend`는 검색 경로에 없다. 위 "`__init__.py`가 있으면 import 경로가 바뀐다"와 같은 뿌리의 문제로, **pytest가 어떤 폴더를 `sys.path`에 넣는지**가 핵심이다.

또 하나 눈여겨볼 것은 실패 방식이다. 테스트 하나가 실패한 게 아니라 **수집 단계에서 중단(Interrupted)돼서 나머지 테스트도 실행되지 않았다.** import 오류는 개별 테스트 실패와 다르게 파일 전체를 못 읽게 만든다.

해결은 `backend`를 검색 경로에 알려주는 것이고, 보통 프로젝트 루트의 `pyproject.toml`에 pytest 설정을 넣어 처리한다.

```toml
[tool.pytest.ini_options]
pythonpath = ["backend"]      # backend 를 sys.path 에 넣어 app.* 를 import 할 수 있게 한다
testpaths = ["backend/tests"] # 인자 없이 pytest 만 쳐도 여기서 찾는다
```

`testpaths`에 적은 폴더가 없으면 `No files were found in testpaths` 경고가 뜨고, pytest가 현재 폴더 전체를 훑으면서 엉뚱한 옛 파일까지 수집한다.

## 진짜 테스트는 `backend/tests/`로

연습은 `sandbox/pytest/`에서 하고, 프로젝트 코드를 검증하는 테스트는 `backend/tests/`에 둔다.

```python
# backend/tests/test_core_config.py
from app.core.config import get_settings

def test_get_settings_returns_same_instance() -> None:
    assert get_settings() is get_settings()   # @lru_cache 가 걸려 있으니 같은 객체여야 한다

def test_settings_has_defaults() -> None:
    settings = get_settings()
    assert settings.app_mode == "mock"
    assert settings.debug is False
```

`is`로 비교하는 첫 테스트는 값이 같은지가 아니라 **같은 객체인지**를 본다. `get_settings`에 `@lru_cache`가 걸려 있다는 사실 자체를 테스트로 고정해두는 것이다([[20_Docker와_PostgreSQL]]에서 이 캐시 때문에 `.env`를 바꿔도 반영이 안 됐던 그 동작이다).

## fixture — 준비 작업을 한 번만 적는다

같은 준비 데이터를 테스트마다 복사해 두면, 값 하나 바뀔 때 전부 고쳐야 한다.

```python
def test_제목이_있다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["title"]

def test_보안등급이_세_값_중_하나다():
    문서 = {"doc_id": "DOC-HR-014", ...}   # 같은 것을 또 쓴다
```

`@pytest.fixture`로 빼면 **함수 인자 이름만 맞춰도 pytest가 알아서 넣어준다.**

```python
import pytest

@pytest.fixture
def travel_doc():
    return {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}

def test_제목이_있다(travel_doc):          # 인자 이름 = fixture 이름
    assert travel_doc["title"]

def test_문서번호_형식이_맞다(travel_doc):
    assert travel_doc["doc_id"].startswith("DOC-")
```

fixture는 **테스트마다 다시 실행된다.** 그래서 한 테스트가 딕셔너리를 고쳐도 다음 테스트는 깨끗한 값을 받는다.

### `conftest.py` — 여러 파일이 같이 쓰는 fixture

`conftest.py`에 두면 그 폴더 아래 모든 테스트 파일이 import 없이 쓴다. pytest가 자동으로 읽는 특별한 파일 이름이다.

```python
# backend/tests/conftest.py
import pytest

@pytest.fixture
def travel_doc() -> dict:
    return {
        "doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "dept": "인사",
        "version": "v2.0", "security_level": "일반", "file_format": "docx", "status": "현행",
    }
```

## `parametrize` — 같은 검사를 값만 바꿔 반복

예외 클래스 8개가 각각 맞는 상태 코드를 갖는지 확인하려고 테스트를 8개 쓰지 않는다.

```python
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

@pytest.mark.parametrize("exc_cls,status,code", CASES)
def test_domain_exception_maps_to_status_and_code(exc_cls, status, code) -> None:
    exc = exc_cls("문서를 찾을 수 없습니다: DOC-HR-014")
    assert exc.status_code == status
    assert exc.code == code
```

**테스트 하나가 아니라 8개로 세어진다.** 그래서 어느 조합이 깨졌는지 실행 결과에 그대로 나온다. 반대로 `for`문으로 돌리면 첫 실패에서 멈추고 나머지는 확인이 안 된다 — 그래서 "전부 `AgentError`를 상속하는가"처럼 하나로 묶어도 되는 검사만 `for`로 쓴다([[05_예외_계층_설계]]).

## TestClient — 서버를 안 띄우고 API를 부른다

FastAPI의 `TestClient`는 `uvicorn`을 실행하지 않고 앱 객체를 직접 호출한다. 포트도, 별도 터미널도 필요 없다.

```python
# backend/tests/conftest.py
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
```

`with`로 감싸면 [[10_FastAPI]]의 `lifespan`이 실제로 실행된다. `yield`를 쓰는 fixture는 테스트가 끝난 뒤 뒷정리까지 해준다.

```python
# backend/tests/test_healthy.py
def test_health_returns_ok(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_documents_list_returns_rows(client) -> None:
    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    문서들 = r.json()
    assert len(문서들) > 0
    assert 문서들[0]["security_level"] in ("일반", "3급", "대외비")
    # secret_note 는 응답 모델에 없으므로 밖으로 나가면 안 된다
    assert "secret_note" not in 문서들[0]

def test_unknown_document_returns_404_with_code(client) -> None:
    r = client.get("/api/v1/documents/DOC-HR-999")
    assert r.status_code == 404
    본문 = r.json()
    assert 본문["code"] == "not_found"
    assert "DOC-HR-999" in 본문["message"]
```

여기서 검증하는 것이 단순한 성공 여부가 아니라는 점이 중요하다.

- `secret_note`가 응답에 없는지 → **응답 스키마가 내부 필드를 실제로 걸러내는지**를 확인한다([[14_문서_업로드_API]]).
- 404 본문의 `code`와 `message` → 예외 핸들러가 [[05_예외_계층_설계]]의 형식대로 응답하는지 확인한다. 상태 코드만 보면 핸들러가 빠져도 통과한다.

### 실습 중 만난 이슈: DB가 내려가 있으면 테스트가 멈춘다

`pytest -q`를 돌렸더니 13개까지 통과하고 그대로 멈춰 있었다. 멈춘 지점은 `test_documents_list_returns_rows`였다.

`.env`의 `DATABASE_URL`이 PostgreSQL을 보고 있는데 컨테이너가 떠 있지 않아서, psycopg가 접속을 기다리는 중이었다. `get_engine`은 SQLite에만 `connect_args`를 주고 PostgreSQL 쪽에는 접속 제한 시간을 걸지 않는다([[20_Docker와_PostgreSQL]]의 노트북에서는 `connect_timeout=5`를 직접 줬다).

```text
.............            ← 13개 통과 후 멈춤
```

**실패가 아니라 멈춤이라 원인이 잘 안 보인다.** DB를 쓰는 테스트를 돌리기 전에 `docker compose ps`로 컨테이너부터 확인하는 편이 빠르다. 나중에는 테스트용 DB를 따로 띄우거나, 접속 제한 시간을 걸어 빨리 실패하게 만드는 쪽이 낫다.

참고: backend/tests/, sandbox/pytest/, sandbox/w2/day02/04.pytest기초.ipynb
