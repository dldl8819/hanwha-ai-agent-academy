# [한화 내일 아카데미 ICT부문] 6일차 후기 — FastAPI, API Router, 의존성 주입, 예외 처리

어제는 레이어드 아키텍처와 예외 계층, 로깅, pytest, 네트워크·HTTP 기초까지 다뤘는데, 오늘은 그 위에 실제로 서버를 띄우는 FastAPI를 배웠습니다. 한화 내일 아카데미 ICT부문 과정 2주차 세 번째 날로, 첫 API 하나를 띄워보는 것부터 시작해서 실제 프로젝트 규모의 구조(라우터 분리, 의존성 주입, 스키마 분리, 전역 예외 처리)까지 하루 안에 이어졌습니다.

오늘 학습한 내용을 순서대로 정리해봅니다.

1. FastAPI 기초
2. API Router로 파일 분리
3. 의존성 주입 (Dependency Injection)
4. 요청/응답 스키마 분리
5. 전역 예외 처리와 lifespan

## 1. FastAPI 기초

FastAPI는 파이썬으로 웹 API 서버를 만드는 프레임워크이고, Uvicorn은 포트를 열어 HTTP 요청을 받아 FastAPI에 전달하는 서버입니다. 설치부터 첫 서버까지 순서대로 해봤습니다.

```bash
python -m pip install fastapi==0.141.1 "uvicorn[standard]==0.52.4"
```

```python
from fastapi import FastAPI

app = FastAPI(title="사내 업무 에이전트 연습", version="0.1.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

```bash
uvicorn app.practice_fastapi:app --app-dir backend --reload --port 8000
```

`--app-dir backend`를 기준으로 `app.practice_fastapi` 모듈을 찾기 때문에, 파일이 실제로 `backend/app/practice_fastapi.py` 위치에 있어야 합니다. 처음에 파일을 `backend/` 바로 밑에 둔 채로 실행했다가 `Could not import module "app.practice_fastapi"` 에러를 만났는데, 모듈 경로와 파일의 실제 위치가 정확히 일치해야 한다는 걸 직접 확인했습니다. `--reload`는 소스를 고칠 때마다 서버가 알아서 재시작해주는 옵션인데, 개발용이라 운영(live) 환경에서는 쓰지 않는다는 점도 같이 배웠습니다.

경로 변수와 쿼리 파라미터도 이어서 다뤘습니다.

```python
@app.get("/documents/{doc_id}")
def get_document(doc_id: str) -> dict:
    return {"doc_id": doc_id, "title": f"{doc_id} 문서 제목"}
```

경로 패턴은 반드시 `/`로 시작해야 하는데, `@app.get("levels/{level}")`처럼 맨 앞 슬래시를 빼먹었더니 요청 값이 뭐든 상관없이 매번 404가 났습니다. 실제 요청 경로는 항상 `/`로 시작하기 때문에 슬래시 없는 패턴과는 아예 매칭이 안 되는 것이었습니다. 그리고 고정 경로(`/documents/latest`)와 경로 변수(`/documents/{doc_id}`)가 겹칠 수 있으면, 고정 경로를 반드시 먼저 선언해야 한다는 규칙도 확인했습니다.

쿼리 파라미터는 함수 매개변수로 그대로 수집되고, `Query()`로 값의 범위를 제한할 수 있습니다.

```python
from fastapi import Query
from typing import Annotated

@app.get("/document-limited")
def list_document_limited(
    dept: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    return {"dept": dept, "limit": limit}
```

여러 쿼리 파라미터로 문서 목록을 필터링하는 실습도 했습니다. `documents` 전체에서 시작해서, 넘어온 파라미터가 있을 때만(`is not None`) 조건을 하나씩 이어붙이고 마지막에 `limit`으로 자르는 방식입니다.

```python
@app.get("/practice/documents")
def search_documents(
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
```

## 2. API Router로 파일 분리

모든 경로를 `main.py` 하나에 다 넣으면 프로젝트가 커질수록 유지보수가 어려워집니다. `APIRouter`로 기능별 파일을 나누고, `main.py`에서 모아 등록하는 구조로 바꿨습니다.

```python
# api/v1/documents.py
from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("")
def list_documents() -> list[dict]:
    ...

@router.get("/{doc_id}")
def get_document(doc_id: str) -> dict:
    ...
```

```python
# main.py
from app.api.v1.documents import router as documents_router

app.include_router(documents_router, prefix="/api/v1")
```

라우터 자체의 `prefix="/documents"`에 `include_router`의 `prefix="/api/v1"`이 앞에 더 붙어서, 최종 경로는 `/api/v1/documents`가 됩니다.

## 3. 의존성 주입 (Dependency Injection)

필요한 객체를 함수 안에서 직접 만들지 않고, 외부에서 공급받는 방식입니다. `Depends()`로 필요한 것을 선언만 하면 FastAPI가 만들어서 넣어줍니다.

```python
from fastapi import Depends

def get_settings() -> Settings:
    return Settings()

@app.get("/example")
def example(settings: Settings = Depends(get_settings)):
    return {...}
```

반복되는 `Depends(get_settings)`는 `Annotated` 별칭으로 정리합니다.

```python
from typing import Annotated

SettingsDep = Annotated[Settings, Depends(get_settings)]

def list_doc(settings: SettingsDep):
    ...
```

같은 요청 안에서 동일한 의존성을 여러 곳이 요구해도 FastAPI는 기본적으로 결과를 재사용(캐시)하고, 의존성 함수도 또 다른 의존성을 요구하는 중첩 구조가 가능합니다. 테스트할 때는 `app.dependency_overrides[get_settings] = fake_settings`로 실제 설정 대신 테스트용 설정을 넣어볼 수 있다는 것도 배웠습니다.

## 4. 요청/응답 스키마 분리

Pydantic 모델을 `schemas/` 패키지에 모아두고, 요청용과 응답용을 분리합니다. 서버 내부 데이터가 무분별하게 그대로 외부에 노출되지 않게 하기 위해서입니다.

```python
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

원본 데이터에는 `secret_note`처럼 내부용 필드가 섞여 있어도, 라우터에서 `response_model=DocumentOut`을 지정해두면 그 필드는 스키마에 없으니 자동으로 걸러지고 나가지 않습니다.

## 5. 전역 예외 처리와 lifespan

어제 만든 `AgentError` 계열 예외는 그냥 `raise`만 하면 FastAPI가 자동으로 HTTP 응답으로 바꿔주지 않습니다. `main.py`에 예외 핸들러를 한 번만 등록해서, 라우터 어디서든 `raise NotFound(...)`만 하면 상태 코드와 JSON으로 자동 변환되게 만들었습니다.

```python
@app.exception_handler(AgentError)
async def handle_agent_error(request: Request, exc: AgentError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": str(exc), "detail": None},
    )
```

lifespan은 앱이 시작될 때와 종료될 때 실행할 작업을 정의하는 자리입니다. `@asynccontextmanager`를 붙인 함수를 만들어서 `FastAPI(..., lifespan=...)`에 넘기면, 서버가 뜰 때 로깅 설정 같은 걸 딱 한 번만 호출할 수 있습니다.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(title="사내 AI 에이전트", version="0.1.0", lifespan=lifespan)
```

## 오늘의 소감

지금까지 배운 Pydantic, 예외 계층, 로깅이 오늘 FastAPI 안에서 실제로 어떻게 맞물리는지 확인한 하루였습니다. 라우터 분리, 의존성 주입, 스키마 분리, 전역 예외 핸들러 하나하나는 각각 단순한데, 이걸 왜 나눠야 하는지는 `main.py` 하나에 다 몰아넣었을 때 어떻게 꼬이는지를 먼저 겪어봐야 체감이 됐습니다. 중간중간 만난 오류들(파이프 설치 명령어의 따옴표 위치, uvicorn 모듈 경로와 파일 위치 불일치, 경로 슬래시 누락, 함수 매개변수 콤마 누락)도 전부 사소한 문법 실수였지만, 그때마다 에러 메시지를 정확히 읽는 연습이 됐습니다.

다음 포스팅에서는 이어서 배울 내용을 정리해보겠습니다.

---

\#한화내일아카데미 #한화시스템 #AI개발자 #AI에이전트 #FastAPI #APIRouter #의존성주입 #예외처리 #K뉴딜아카데미 #국비지원교육 #개발자이직 #부트캠프후기

참고 링크 : https://blog.naver.com/dldl8819/224406227307
