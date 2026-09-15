# 문서 목록 화면과 API 연동

[[18_로그인과_인증]]까지는 화면과 서버가 따로 떠 있기만 했다. 여기서 프론트엔드(Streamlit)가 백엔드(FastAPI)에 실제로 HTTP 요청을 보내 로그인하고, 문서 목록을 받아 표로 그리는 연결을 붙인다.

```text
브라우저 ── http://localhost:8501 ──▶ Streamlit (frontend)
                                        │  httpx2 로 HTTP 요청
                                        ▼
                               http://127.0.0.1:8000 ──▶ FastAPI (backend) ──▶ DB
```

브라우저가 백엔드를 직접 부르는 게 아니라, **Streamlit 서버의 파이썬 코드가 백엔드를 부른다.** 그래서 파이썬에서 HTTP 요청을 보내는 라이브러리가 필요하다.

## httpx2

```bash
python -m pip install "httpx2==2.12.0"
```

파이썬 코드로 HTTP 요청을 보내는 라이브러리다. 기본 사용 형태는 이렇다(프로젝트 코드에는 이 형태 그대로 넣지 않는다).

```python
import httpx2

# 백엔드 서버가 떠 있어야 한다
with httpx2.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
    response = client.get("/api/v1/documents", params={"limit": 8})
    response.raise_for_status()   # 4xx, 5xx면 여기서 예외
    documents = response.json()
```

## `frontend/core/api_client.py` — 백엔드로 가는 통로를 한 곳에

화면 코드마다 `httpx2`를 직접 부르면 주소, 타임아웃, 헤더, 에러 처리가 파일마다 흩어진다. 그래서 **백엔드 호출은 전부 `api_client`를 거치게** 하고, 화면은 `api_client.list_documents(...)`처럼 함수만 부른다.

```python
BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = 10.0

class ApiError(RuntimeError):
    pass
```

주소는 환경변수로 바꿀 수 있게 두고, 기본값은 로컬 백엔드다.

### `_request` — 모든 호출이 지나가는 공용 함수

```python
def _request(method, path, *, params=None, json=None, emp_no=None) -> Any:
    clean_params = None
    if params is not None:
        # None, 빈 문자열, "전체"는 쿼리스트링에서 뺀다
        clean_params = {k: v for k, v in params.items() if v not in (None, "", "전체")}

    headers = {"X-Emp-No": emp_no} if emp_no else None
    url = f"{BASE_URL}{path}"

    try:
        response = httpx2.request(method, url, params=clean_params, json=json,
                                  headers=headers, timeout=TIMEOUT)
    except httpx2.ConnectError as exc:
        raise ApiError(f"백엔드에 연결하지 못했습니다. 터미널에서 서버가 떠 있는지 확인하세요 ({BASE_URL}).") from exc
    except httpx2.TimeoutException as exc:
        raise ApiError("응답이 너무 늦습니다. 서버가 멎었는지 확인하세요.") from exc

    if response.status_code >= 400:
        try:
            message = response.json().get("message") or response.text
        except ValueError:
            message = response.text
        raise ApiError(message)

    return response.json()
```

이 함수가 하는 일은 네 가지다.

1. **쿼리스트링 정리** — 필터를 안 고른 값(`None`, `""`, `"전체"`)은 아예 보내지 않는다. `?dept_id=&status=전체` 같은 요청이 가면 백엔드가 "전체"라는 부서를 찾으려고 한다.
2. **신원 헤더** — 로그인한 사번이 있으면 [[18_로그인과_인증]]에서 정한 `X-Emp-No` 헤더로 싣는다.
3. **예외 변환** — 서버가 꺼져 있거나(`ConnectError`), 응답이 늦거나(`TimeoutException`), 4xx·5xx가 오면 전부 `ApiError` 하나로 바꾼다. 화면은 `httpx2`의 예외 종류를 몰라도 `except api_client.ApiError`만 잡으면 된다. `from exc`로 원래 예외는 원인으로 남긴다.
4. **에러 메시지 꺼내기** — 백엔드의 `AgentError` 핸들러가 `{"code", "message", "detail"}` 형태로 응답하므로 `message`만 꺼내 사용자에게 보여준다. JSON이 아닌 응답이면 본문 텍스트를 그대로 쓴다.

함수 이름 앞의 `_`는 "이 파일 안에서만 쓰는 내부 함수"라는 표시다.

### 공개 함수

```python
def login(emp_no: str, password: str) -> dict:
    return _request("POST", "/api/v1/auth/login", json={"emp_no": emp_no, "password": password})

def me(emp_no: str) -> dict:
    return _request("GET", "/api/v1/auth/me", emp_no=emp_no)

def list_documents(*, dept_id=None, security_level=None, status=None, q=None,
                   limit: int = 20, emp_no=None) -> list[dict]:
    params = {"dept_id": dept_id, "security_level": security_level,
              "status": status, "q": q, "limit": limit}
    return _request("GET", "/api/v1/documents", params=params, emp_no=emp_no)

def get_document(doc_id: str, *, emp_no=None) -> dict:
    return _request("GET", f"/api/v1/documents/{doc_id}", emp_no=emp_no)
```

로그인은 본문(`json=`)으로, 목록 필터는 쿼리스트링(`params=`)으로 보낸다. 비밀번호를 쿼리스트링에 실으면 URL에 그대로 남아 서버 접근 로그에 찍히기 때문이다.

이 파일이 생기면서 `views/login.py`의 `try: from core import api_client / except ImportError` 분기가 드디어 통과한다. 로그인 버튼이 실제로 백엔드를 부르게 된다.

### `stats` — 지표용 집계

```python
def stats(*, emp_no=None) -> dict:
    rows = list_documents(limit=100, emp_no=emp_no)
    return {
        "total": len(rows),
        "current": sum(1 for row in rows if row["status"] == "현행"),
        "expired": sum(1 for row in rows if row["status"] == "만료"),
        "reindexing": sum(1 for row in rows if row["index_status"] == "재임베딩"),
    }
```

집계 전용 API를 아직 안 만들어서, 목록을 받아 프론트에서 센다. 문서가 100건이 안 되니까 `limit=100`으로 전부 받는다.

**문자열 비교라서 오타가 나도 에러가 안 난다.** 교안 코드는 `"재임베딩 "`(끝에 공백)으로 되어 있었는데, 이러면 일치하는 행이 영원히 없어서 재임베딩 지표가 조용히 0으로만 나온다. [[16_Streamlit]]의 UI 킷 배지 판정과 같은 종류의 함정이다.

## `backend/app/main.py` — 422 응답에서 비밀번호 감추기

사번을 비우고 로그인 요청을 보내면 FastAPI가 요청 본문 검증에 실패해 422를 돌려준다. 문제는 **기본 422 응답에 사용자가 보낸 값이 통째로 담긴다**는 점이다.

실제로 `LoginIn`에 사번 없이 비밀번호만 넣어 검증해보면 에러 정보가 이렇게 나온다.

```text
{'type': 'missing', 'loc': ('emp_no',), 'input': {'password': 'passwd1234!'}}
```

`input`에 비밀번호가 평문으로 들어 있다. 이게 응답으로 나가면 화면 에러 메시지나 로그에 비밀번호가 찍힌다. 그래서 검증 에러 전용 핸들러를 따로 둔다.

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # exc.errors()에는 사용자가 보낸 값이 통째로 들어 있다. 필드 이름만 돌려주고 값은 감춘다.
    fields = ", ".join(
        ".".join(str(p) for p in e["loc"][1:]) or "요청 본문" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"code": "validation_failed", "message": f"입력값을 확인하세요 — {fields}", "detail": None},
    )
```

- FastAPI의 `loc`은 `("body", "emp_no")`처럼 맨 앞에 위치(body/query/header)가 붙는다. `[1:]`로 그걸 떼고 필드 이름만 남긴다. 본문 자체가 없으면 남는 게 없으니 `"요청 본문"`으로 채운다.
- 응답 형태를 `AgentError` 핸들러와 같은 `{"code", "message", "detail"}`로 맞췄다. 그래서 `api_client._request`가 422도 같은 방식으로 `message`를 꺼내 보여줄 수 있다.

## 문서 목록 화면

### 시안

```text
┌─ 사이드바 ─┬─────────────────── 문서 관리 ───────────────────┐
│            │  [지표] 전체 8   현행 7   만료 1   재임베딩 1     │  ← 상단 지표
│ AI 업무    │                                                  │
│ 문서 관리  │  부서▾   보안등급▾   상태▾   [검색어______]       │  ← 필터 4종
│ 승인함     │                             [새 문서 업로드]      │
│ 운영       │  ┌────────────────────────────────────────────┐  │
│            │  │ 문서 ID 문서명 버전 시행~만료 상태 부서 …   │  │  ← 8열 표
│ 김지원     │  │ DOC-HR-014 국내출장 여비 규정 v2.0 …        │  │
│ 로그아웃   │  └────────────────────────────────────────────┘  │
└────────────┴──────────────────────────────────────────────────┘
```

| 열 | 응답 필드 | 표시 |
| --- | --- | --- |
| 문서 ID | `doc_id` | 글자 |
| 문서명 | `title` | 글자 |
| 버전 | `version` | 글자 |
| 시행 ~ 만료 | `effective_from` ~ `expires_at` | 만료일이 없으면 "현행" |
| 상태 | `status` | 배지 |
| 부서 | `dept` | 글자 |
| 등급 | `security_level` | 글자 |
| 색인 | `index_status` + `index_progress` | 배지 |

목록은 **문서 단위가 아니라 버전 단위**다. 백엔드 리포지토리가 `DocumentVersion`과 `Document`를 조인해서 버전마다 한 행씩 돌려주기 때문에, `DOC-HR-014`는 `v2.0`(현행)과 `v1.1`(만료) 두 줄로 나온다. 지표 설명에 "문서 버전 기준"이라고 붙인 이유다.

### 배지 색

UI 킷의 `badge_html`은 글자가 **무엇으로 시작하는지**로 색을 정한다.

| 글자 | 색 | 쓰는 열 |
| --- | --- | --- |
| 현행 · 완료 · 승인 | 초록 (`ok`) | 상태 · 색인 |
| 대기 · 재임베딩 | 주황 (`wait`) | 색인 |
| 만료 · 반려 | 빨강 (`no`) | 상태 |
| 보관 | 회색 (`neutral`) | 색인 |

색인 열은 `"재임베딩 62%"`처럼 상태 낱말을 앞에, 진행률을 뒤에 붙인다. 순서를 바꿔 `"62% 재임베딩"`으로 쓰면 판정에 안 걸려서 회색이 된다.

### `frontend/views/documents.py`

#### 상수

```python
DEPTS: dict[str, str | None] = {
    "전체": None, "인사총무": "HRGA", "구매팀": "PU", "보안팀": "SE", "PMO": "PMO",
}
LEVELS = ["전체", "일반", "3급", "대외비"]
STATUSES = ["전체", "현행", "만료"]

HEADERS = ["문서 ID", "문서명", "버전", "시행 ~ 만료", "상태", "부서", "등급", "색인"]
ALIGNS = ["ag-nowrap", "", "", "ag-nowrap", "", "", "", "ag-nowrap"]
```

- `DEPTS`는 **화면에 보이는 이름 → 백엔드가 받는 ID** 매핑이다. 사용자는 "인사총무"를 고르고, 요청에는 `dept_id=HRGA`가 나간다.
- `ALIGNS`는 UI 킷이 가진 클래스 이름만 쓴다. 문서 ID·기간·색인처럼 폭이 일정한 열을 `ag-nowrap`으로 고정하고 남는 폭을 문서명이 가져가게 한다.

#### 지표 — `_metrics_row`

```python
def _metrics_row() -> None:
    try:
        counts = api_client.stats(emp_no=session.emp_no())
    except api_client.ApiError as exc:
        st.caption(f"지표를 불러오지 못했습니다: {exc}")
        return

    metrics([
        {"label": "전체", "value": counts["total"], "delta": "문서 버전 기준"},
        {"label": "현행", "value": counts["current"], "delta": "지금 유효한 판", "tone": "ok"},
        {"label": "만료", "value": counts["expired"], "delta": "지난 판", "tone": "no"},
        {"label": "재임베딩", "value": counts["reindexing"], "delta": "색인을 다시 만드는 중", "tone": "wait"},
    ])
```

지표를 못 불러와도 `st.error`가 아니라 `st.caption`으로 작게 알리고 넘어간다. 지표는 부가 정보라 실패해도 아래 목록은 계속 그려져야 한다.

#### 필터 — `_filter_row`

```python
def _filter_row() -> dict:
    left, middle, right, search = st.columns([1, 1, 1, 2])
    with left:
        dept_name = st.selectbox("부서", list(DEPTS), key="f_dept")
    with middle:
        level = st.selectbox("보안등급", LEVELS, key="f_level")
    with right:
        status = st.selectbox("상태", STATUSES, key="f_status")
    with search:
        keyword = st.text_input("검색어", key="f_q", placeholder="문서명 또는 문서 ID")

    return {
        "dept_id": DEPTS[dept_name],
        "security_level": None if level == "전체" else level,
        "status": None if status == "전체" else status,
        "q": keyword or None,
    }
```

위젯 `key`가 `f_dept`, `f_level`, `f_status`, `f_q`인 것이 핵심이다. [[18_로그인과_인증]]의 `core/session.py` `DEFAULTS`에 미리 잡아둔 키와 같은 이름이라, 필터 선택값이 재실행에도 유지되고 **로그아웃하면 `session.logout()`이 이 키들을 "전체"/빈 문자열로 되돌린다.** 다음 사람이 로그인했을 때 앞사람의 필터가 남지 않는다.

"전체"를 `None`으로 바꾸는 처리는 여기서 한 번, `api_client._request`에서 한 번 더 한다. 화면이 실수로 "전체"를 넘겨도 쿼리스트링에는 안 실린다.

#### 표 — `_table`

```python
def _table(documents: list[dict]) -> None:
    rows = []
    for document in documents:
        period = f"{document['effective_from']} ~ {document['expires_at'] or '현행'}"
        index_label = f"{document['index_status']} {document['index_progress']}%"
        rows.append([
            escape(document["doc_id"]),
            escape(document["title"]),
            escape(document["version"]),
            escape(period),
            badge_html(document["status"]),
            escape(document["dept"]),
            escape(document["security_level"]),
            badge_html(index_label),
        ])
    table(HEADERS, rows, align=ALIGNS)
```

UI 킷의 `table`은 **셀 값을 HTML로 살려서 그린다**(`raw_html=True`가 기본). 배지를 칸 안에 넣으려면 그래야 하기 때문이다. 대신 DB에서 온 글자(문서명 등)를 그대로 넣으면 `<`, `>` 같은 문자가 태그로 해석될 수 있다. 그래서 **글자 칸은 `escape()`로 감싸고, 배지 칸만 `badge_html()` 결과를 그대로 넣는다.** `badge_html`은 내부에서 글자를 이미 이스케이프한다.

#### 화면 전체 — `render`

```python
def render() -> None:
    st.title("문서 관리")
    st.caption("상태 필터가 「전체」라 지난 판까지 함께 보입니다. "
               "「현행」으로 좁히면 현재 유효한 최신본만 남습니다.")

    _metrics_row()
    filters = _filter_row()

    if st.button("새 문서 업로드"):
        st.info("업로드 화면은 추후에 만듭니다.")

    with st.spinner("문서를 불러오는 중입니다..."):
        try:
            documents = api_client.list_documents(**filters, limit=100, emp_no=session.emp_no())
        except api_client.ApiError as exc:
            st.error(str(exc))
            return

    if not documents:
        st.info("조건에 맞는 문서가 없습니다. 필터를 바꿔 보세요.")
        return

    st.caption(f"{len(documents)}건")
    _table(documents)
```

- `_filter_row()`가 돌려준 dict를 `**filters`로 풀어서 넘긴다. dict의 키 이름(`dept_id`, `security_level`, `status`, `q`)이 `list_documents`의 키워드 인자 이름과 정확히 같아야 한다.
- 목록 호출이 실패하면 지표와 달리 `st.error`로 크게 보여주고 끝낸다. 이 화면의 본체가 목록이기 때문이다.
- 결과가 0건이면 빈 표 대신 필터를 바꿔보라는 안내를 띄운다.

### `frontend/app.py` 연결

```python
from views import documents as documents_view

def main() -> None:
    ...
    page = router.current_page()
    if page == "documents":
        documents_view.render()
    else:
        st.info("아직 만들지 않은 화면입니다.")
```

## 요청 한 번이 지나가는 길

필터에서 "보안팀"을 고르면 이렇게 흘러간다.

1. Streamlit이 스크립트를 처음부터 다시 실행한다 ([[16_Streamlit]] 재실행 모델)
2. `session.init_state()` → 로그인 확인 → 사이드바 → `documents_view.render()`
3. `_metrics_row()` → `api_client.stats()` → `GET /api/v1/documents?limit=100`
4. `_filter_row()`가 `f_dept="보안팀"`을 읽어 `{"dept_id": "SE", ...}` 반환
5. `api_client.list_documents(dept_id="SE", limit=100)` → `GET /api/v1/documents?dept_id=SE&limit=100`
6. 백엔드: 라우터 → `document_service.list_documents` → `document_repo.list_documents`가 넘어온 조건만 `where`로 쌓아 조회 ([[12_리포지토리_패턴]]) → `DocumentOut` 형태로 응답
7. 프론트: 응답 JSON을 `_table`로 그린다

필터 하나를 바꿀 때마다 **백엔드 호출이 두 번**(지표용 전체 목록 + 필터 적용 목록) 나간다. 문서가 적을 때는 문제없지만, 늘어나면 집계 전용 API나 `st.cache_data` 같은 캐시가 필요해지는 자리다.

## 아직 비어 있는 부분

- 프론트는 `X-Emp-No` 헤더를 실어 보내지만 **백엔드 문서 목록 API는 아직 이 헤더를 읽지 않는다.** 그래서 지금은 누가 로그인해도 같은 목록이 나온다. 사용자의 보안등급에 따라 보이는 문서를 거르는 처리는 이 헤더를 받아서 붙이게 된다.
- "새 문서 업로드" 버튼은 자리만 있고, 업로드 화면은 이후에 만든다.

참고: frontend/core/api_client.py, frontend/views/documents.py, frontend/app.py, backend/app/main.py
