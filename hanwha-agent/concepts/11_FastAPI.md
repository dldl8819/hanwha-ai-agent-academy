# FastAPI

## FastAPI란

파이썬으로 웹 API 서버를 만드는 프레임워크다. Django, Flask보다 빠른 개발이 가능하다는 점이 특징이다(타입 힌트 기반으로 자동 검증·자동 문서화까지 해준다).

[[05_레이어드_아키텍처]]에서 정리한 계층 구조에서, FastAPI는 API(Router)~Schema 계층을 맡는다.

```text
화면 (Streamlit)
 | HTTP 요청
FastAPI (백엔드 서버)
 |
 - Service
 - PostgreSQL
 - RAG
 - LangGraph Agent
 - Claude / Upstage
```

### 용어

| 용어 | 역할 |
| --- | --- |
| FastAPI | 프레임워크. 요청을 실제로 처리할 프로그램(라우팅, 검증, 응답 생성) |
| Uvicorn | 서버. 포트를 열어 HTTP 요청을 받고, 그 요청을 FastAPI에 전달 |

## 설치

```bash
# 버전을 명시해서 설치 (extras가 있는 패키지는 통째로 따옴표로 감싼다)
python -m pip install fastapi==0.141.1 "uvicorn[standard]==0.52.4"

# 설치 확인
python -m pip list
```

## 첫 FastAPI 만들기

`backend/app/practice_fastapi.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title="사내 업무 에이전트 연습",
    version="0.1.0",
)

# GET /health
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

서버 실행:

```bash
# --app-dir : 모듈을 찾을 시작 위치
# --reload  : 소스 수정 시 서버 자동 재구동 (dev 개발용 옵션 — live 운영 환경에는 쓰지 않는다)
# 기본 포트 : 8000
uvicorn app.practice_fastapi:app --app-dir backend --reload --port 8000
# "app.practice_fastapi 모듈의 app 객체를 실행"이라는 뜻
```

`--app-dir backend`를 기준으로 `app.practice_fastapi`를 찾기 때문에, 파일이 실제로 `backend/app/practice_fastapi.py`에 있어야 한다. 만약 `backend/practice_fastapi.py`처럼 `app/` 폴더 밖에 두면 `Could not import module "app.practice_fastapi"` 에러가 난다 — 모듈 경로(`--app-dir` 기준)와 파일의 실제 위치가 반드시 일치해야 한다.

자동으로 생성되는 문서/스펙:

| 경로 | 내용 |
| --- | --- |
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI 스펙(JSON) |

## 경로 변수 (Path Variable)

```text
http://127.0.0.1:8000/고정경로/경로변수값

http://127.0.0.1:8000/고정경로/10
http://127.0.0.1:8000/고정경로/130

@app.get("/고정경로/{경로변수명}")  →  경로변수명 = 10, 130, ...
```

```python
@app.get("/documents/{doc_id}")
def get_document(doc_id: str) -> dict:
    return {"doc_id": doc_id, "title": f"{doc_id} 문서 제목"}

@app.get("/levels/{level}")
def get_level(level: int) -> dict:
    return {"level": level}
```

경로 패턴은 반드시 `/`로 시작해야 한다. `@app.get("levels/{level}")`처럼 맨 앞 `/`를 빠뜨리면 실제 요청 경로(`/levels/1`)와 절대 매칭이 안 돼서 값에 상관없이 매번 404가 난다 — 실습 중 직접 겪은 오류다.

타입 힌트(`level: int`)를 지정해두면 FastAPI가 자동으로 형변환·검증을 해준다. `/levels/1`처럼 정수로 변환 가능한 값은 통과하고, `/levels/dff`처럼 안 되는 값은 404가 아니라 422(Unprocessable Entity)로 응답한다.

### 경로 선언 순서 — 고정 경로를 먼저

라우팅은 등록된 순서대로 위에서부터 먼저 일치하는 걸 찾는다. 고정 경로와 경로 변수 패턴이 겹칠 수 있는 경우, 고정 경로를 반드시 먼저 선언해야 한다.

```python
# 고정 경로가 위에 있어야 한다
@app.get("/documents/latest")
def get_document() -> dict:
    return {"doc_id": "latest", "title": "latest 문서 제목"}

# 경로 변수는 아래에
@app.get("/documents/{doc_id}")
def get_document(doc_id: str) -> dict:
    return {"doc_id": doc_id, "title": f"{doc_id} 문서 제목"}
```

순서가 반대라면 `/documents/latest` 요청도 `{doc_id}` 쪽 함수가 먼저 걸려서 `doc_id="latest"`로 처리돼버린다.

## 쿼리 파라미터 (쿼리 스트링)

`?이름=값&이름=값` 형태로 `?` 뒤에 붙는, 서버로 전송되는 데이터다. 함수의 매개변수로 그대로 수집한다. 매개변수에 기본값을 지정하지 않으면 그 쿼리 파라미터는 필수가 된다.

```python
# GET /documents?dept=hr&limit=20
@app.get("/documents")
def list_documents(
    dept: str | None = None,  # 기본값 있음 → 선택
    limit: int = 20,
) -> dict:
    return {"dept": dept, "limit": limit}
```

## Query()로 요청 범위 제한하기

쿼리 파라미터로 들어올 수 있는 값의 범위(최소/최대, 길이 등)를 제한하고 싶을 때는 `fastapi.Query`를 타입 힌트에 함께 붙인다.

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

함수 시그니처에서 매개변수 사이 콤마(`,`)를 빠뜨리면 모듈을 import하는 시점에 `SyntaxError`가 나서 uvicorn이 `Error loading ASGI app`으로 실패한다 — 이것도 실습 중 겪은 오류다.

## 실습: 쿼리 파라미터로 문서 필터링

DB 대신 임시 데이터(딕셔너리 리스트)를 두고, 쿼리 파라미터 조합에 맞게 걸러서 응답하는 문제다. 파라미터는 전부 생략 가능하고, `limit`만 기본값 20에 1~100 범위 제한이 있다.

```text
/practice/documents                                 문서 전체 조회
/practice/documents?dept=인사                        인사 부서의 데이터 조회
/practice/documents?security_level=3급               보안 등급 3급 데이터 조회
/practice/documents?file_format=pdf                  pdf 문서 조회
/practice/documents?dept=인사&file_format=pdf        인사 부서의 pdf 파일 조회
```

풀이 방법은, `documents` 전체에서 시작해서 넘어온 파라미터가 있을 때만(`is not None`) 그 조건으로 필터링을 이어붙이고, 마지막에 `limit`으로 잘라내는 방식이다.

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

- `if dept:` 대신 `if dept is not None:`을 쓰는 이유: 빈 문자열처럼 "값은 있지만 falsy한" 입력까지 걸러지는 걸 막기 위해서다.
- 매번 `result = [...]`로 필터링 결과를 다시 `result`에 덮어쓰면서 다음 필터를 그 위에 적용하기 때문에, 여러 조건이 동시에 와도(`dept`+`file_format`) 자동으로 AND 조건이 된다.

참고: backend/app/practice_fastapi.py
