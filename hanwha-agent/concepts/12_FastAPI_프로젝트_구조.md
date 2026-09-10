# FastAPI 프로젝트 구조 — Router, 의존성 주입, 스키마, 예외/lifespan

[[11_FastAPI]]에서 다룬 라우팅·쿼리 파라미터를 실제 프로젝트 규모로 확장할 때 쓰는 패턴들이다.

## API Router

모든 요청 경로를 `main.py` 하나에 다 넣으면 프로젝트가 커질수록 유지보수가 어려워진다. `APIRouter`로 기능별(경로별)로 파일을 나누고, `main.py`에서 그것들을 모아 등록하는 구조로 바꾼다.

### `backend/app/main.py`의 역할

- `.env` 환경변수 로딩
- FastAPI 앱 생성
- 미들웨어 설정 (CORS, 로깅 등)
- 라우터 등록 — `/documents`, `/chat`, `/members`처럼 기능별로 분리된 라우터를 연결
- 예외 핸들러 등록
- lifecycle 이벤트 등록 (startup/shutdown)

### 폴더 배치

```text
backend/app/
    main.py
    core/
    api/
        __init__.py
        v1/
            __init__.py
            documents.py   # 문서 관련 라우터
    schemas/
    models/
```

### 라우터 파일 (`api/v1/documents.py`)

```python
from fastapi import APIRouter, Query
from typing import Annotated

router = APIRouter(prefix="/documents", tags=["documents"])

documents = [ ... ]  # DB 사용 전 임시 데이터

# .../documents
@router.get("")
def list_documents(
    dept: str | None = None,
    security_level: str | None = None,
    file_format: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict]:
    result = documents.copy()
    if dept is not None:
        result = [doc for doc in result if doc["dept"] == dept]
    if security_level is not None:
        result = [doc for doc in result if doc["security_level"] == security_level]
    if file_format is not None:
        result = [doc for doc in result if doc["file_format"] == file_format]
    return result[:limit]

# .../documents/{doc_id}
@router.get("/{doc_id}")
def get_document(doc_id: str) -> dict:
    for doc in documents:
        if doc["doc_id"] == doc_id:
            return doc
    return {"doc_id": doc_id, "message": "문서를 찾지 못했습니다."}
```

`APIRouter(prefix="/documents", ...)`로 접두사를 지정해두면, 라우터 안의 각 경로(`""`, `"/{doc_id}"`)는 그 뒤에 붙는 부분만 신경 쓰면 된다.

### `main.py`에서 라우터 연결

```python
from fastapi import FastAPI
from app.api.v1.documents import router as documents_router

app = FastAPI(title="사내 AI 에이전트", version="0.1.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

app.include_router(documents_router, prefix="/api/v1")
```

`include_router`에 준 `prefix="/api/v1"`이 라우터 자체의 `prefix="/documents"` 앞에 더 붙어서, 최종 경로는 `/api/v1/documents`가 된다.

```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```

## 의존성 주입 (Dependency Injection)

필요한 객체를 함수 내부에서 직접 만들지 않고, 외부에서 공급받는 방식이다.

```python
def list_doc():
    settings = Settings()  # 직접 생성 X — 이 함수가 Settings를 어떻게 만드는지까지 알아야 함

def list_doc(settings=Depends(get_settings)):
    # 설정 정보가 필요하다고 "선언"만 하면, FastAPI가 만들어서 공급해준다
    ...
```

### `Depends()`

```python
from fastapi import Depends

def get_settings() -> Settings:
    return Settings()

@app.get("/example")
def example(settings: Settings = Depends(get_settings)):
    # 요청을 처리할 때 FastAPI가 get_settings()를 호출해서 넣어준다
    return {...}
```

### `Annotated` 별칭

매번 `Depends(get_settings)`를 반복해서 쓰지 않도록, 타입 별칭으로 정리해둔다.

```python
from typing import Annotated
from fastapi import Depends

SettingsDep = Annotated[Settings, Depends(get_settings)]

def list_doc(settings: SettingsDep):
    ...
```

### 의존성 캐시

같은 요청 안에서 동일한 의존성을 여러 곳(여러 매개변수·중첩 의존성)이 요구해도, FastAPI는 기본적으로 한 번만 실행하고 결과를 재사용한다. `Depends(get_settings, use_cache=False)`로 끌 수 있다.

### 중첩 의존

의존성 함수도 또 다른 의존성을 요구할 수 있다.

```python
def aaa() -> str: ...

def bbb(aaa: str = Depends(aaa)): ...

def ccc(bbb = Depends(bbb)): ...
```

### 의존성 오버라이딩 (테스트용)

실제 설정 대신 테스트용 설정을 넣고 돌려보고 싶을 때, 함수 자체를 바꿔치기할 수 있다.

```python
def fake_settings():
    return Settings(app_name="test")

app.dependency_overrides[get_settings] = fake_settings
# ... 테스트 실행 ...
app.dependency_overrides.clear()  # 오버라이딩 해제
```

## 요청/응답 스키마

Pydantic 모델을 `schemas/` 패키지에 모아두고, 요청용과 응답용을 분리한다 — 서버 내부 데이터가 무분별하게 그대로 외부에 노출되지 않도록 하기 위해서다.

### agent-app 적용 폴더 구조

```text
hanwha-agent/
    backend/
        app/
            __init__.py
            main.py
            core/
                __init__.py
                config.py
                exceptions.py
                logging.py
            schemas/            # Pydantic 모델
                __init__.py
                common.py
                documents.py
            api/
                __init__.py
                deps.py
                documents.py
    sandbox/
        w2/
            day01/
            day02/
            day03/
```

### 응답 스키마 (`schemas/document.py`)

```python
from pydantic import BaseModel
from typing import Literal

class DocumentOut(BaseModel):
    doc_id: str
    title: str
    dept: str
    version: str
    security_level: Literal["일반", "3급", "대외비"]
    file_format: Literal["docx", "pdf"]
    status: str
    # secret_note는 외부에 전달할 데이터가 아니라서 필드 자체를 뺐다
```

원본 데이터(`_DOCS`)에는 `secret_note`처럼 내부용 필드가 섞여 있어도, `response_model=DocumentOut`으로 응답 스키마를 지정해두면 그 필드는 스키마에 없으니 자동으로 걸러지고 나가지 않는다.

### 공통 스키마 (`schemas/common.py`)

```python
from pydantic import BaseModel

class HealthOut(BaseModel):
    status: str

class ErrorOut(BaseModel):
    code: str
    message: str
    detail: str | None = None
```

### 의존성 별칭 모음 (`api/deps.py`)

```python
from typing import Annotated
from fastapi import Depends
from app.core.config import Settings, get_settings

SettingsDep = Annotated[Settings, Depends(get_settings)]
```

### 라우터에 적용

```python
from fastapi import APIRouter, Query
from typing import Annotated
from app.schemas.document import DocumentOut
from app.api.v1.deps import SettingsDep
from app.core.exceptions import NotFound

router = APIRouter(prefix="/documents", tags=["documents"])

_DOCS: list[dict] = [ ... ]  # secret_note 등 내부용 필드 포함

@router.get("", response_model=list[DocumentOut])
def list_documents(
    settings: SettingsDep,  # 의존성 주입
    dept: str | None = None,
    security_level: str | None = None,
    file_format: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict]:
    result = _DOCS.copy()
    if dept is not None:
        result = [doc for doc in result if doc["dept"] == dept]
    if security_level is not None:
        result = [doc for doc in result if doc["security_level"] == security_level]
    if file_format is not None:
        result = [doc for doc in result if doc["file_format"] == file_format]
    return result[:limit]

@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str) -> dict:
    for doc in _DOCS:
        if doc["doc_id"] == doc_id:
            return doc
    raise NotFound(f"문서를 찾지 못했습니다: {doc_id}")
```

## 전역 예외 핸들러

[[06_예외_계층_설계]]에서 만든 `AgentError`(및 하위 클래스)는 그냥 `raise`만 하면 FastAPI가 자동으로 HTTP 응답으로 바꿔주지 않는다 — 우리가 만든 평범한 파이썬 예외이기 때문이다. 어디선가 이 예외를 잡아서 "상태코드 + JSON"으로 변환해주는 지점이 필요한데, 그걸 라우터마다 반복하지 않고 `main.py`에 한 번만 등록한다.

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.documents import router as documents_router
from app.core.exceptions import AgentError

app = FastAPI(title="사내 AI 에이전트", version="0.1.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

app.include_router(documents_router, prefix="/api/v1")

@app.exception_handler(AgentError)
async def handle_agent_error(request: Request, exc: AgentError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": str(exc), "detail": None},
    )
```

이렇게 등록해두면, 라우터 어디에서든 `raise NotFound(...)`만 하면 이 핸들러가 잡아서 `exc.status_code`(예: 404)와 `exc.code`(예: `"not_found"`)로 자동 변환해서 응답한다.

## lifespan — 앱 시작/종료 시점 처리

FastAPI에서 lifespan은 애플리케이션이 시작될 때와 종료될 때 실행할 작업을 정의하는 자리다. `@asynccontextmanager`를 붙인 함수를 만들어서 `FastAPI(..., lifespan=...)`에 넘긴다.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.documents import router as documents_router
from app.core.exceptions import AgentError
from app.core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()  # 서버 시작 시 로깅을 한 번만 설정
    yield
    # yield 아래에 종료 시 정리할 작업을 적으면 된다 (DB 커넥션 종료 등)

app = FastAPI(title="사내 AI 에이전트", version="0.1.0", lifespan=lifespan)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

app.include_router(documents_router, prefix="/api/v1")

@app.exception_handler(AgentError)
async def handle_agent_error(request: Request, exc: AgentError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": str(exc), "detail": None},
    )
```

[[07_로깅]]에서 만든 `setup_logging()`을 노트북/스크립트마다 각자 부르는 대신, 여기 lifespan에서 앱이 뜰 때 딱 한 번만 호출하는 것이 실제 서버에서의 올바른 위치다.

참고: 강의 노트 (별도 실습 노트북 없음, `backend/app/` 구조로 직접 실습 예정)
