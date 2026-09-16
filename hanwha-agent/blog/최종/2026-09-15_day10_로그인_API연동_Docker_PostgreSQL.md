# [한화 내일 아카데미 ICT부문] 10일차 후기 — 로그인, 화면-API 연동, Docker, PostgreSQL

지난 포스팅에서는 async/await와 Streamlit, UI 킷, 비밀번호 해싱을 정리했었습니다. 오늘은 한화 내일 아카데미 ICT부문 과정 10일차로, 그동안 따로 떠 있던 프론트엔드와 백엔드를 실제로 연결했습니다. 로그인 API와 로그인 화면을 만들고, 문서 목록 화면이 백엔드에서 데이터를 받아 표로 그리는 데까지 붙인 뒤, 오후에는 SQLite에서 PostgreSQL로 옮기기 위해 Docker로 DB 서버를 띄웠습니다.

오늘 학습한 내용을 순서대로 정리해봅니다.

1. 로그인 API — 계층별로 나눠 만들기
2. 로그인 화면과 상태 유지
3. 프론트엔드와 백엔드 연결 — httpx2
4. 문서 목록 화면
5. Docker와 PostgreSQL

## 1. 로그인 API — 계층별로 나눠 만들기

로그인은 두 개의 경로로 처리합니다.

| 경로 | 하는 일 |
| --- | --- |
| `POST /api/v1/auth/login` | 사번 + 비밀번호를 받아 사용자 정보를 돌려준다 |
| `GET /api/v1/auth/me` | 지금 요청한 사람이 누구인지 돌려준다 |

로그인한 뒤에는 `X-Emp-No` 헤더에 사번을 실어 보내서 누구인지 알립니다. 사번만 알면 누구나 흉내 낼 수 있어서 진짜 인증은 아니고, 헤더를 검증할 JWT 토큰은 이후에 붙입니다.

코드는 앞에서 만든 계층 구조를 그대로 따라 스키마 → 리포지토리 → 서비스 → 라우터 순으로 쌓았습니다.

```python
# schemas/auth.py
class LoginIn(BaseModel):
    emp_no: str = Field(examples=["2016-0231"])
    password: str = Field(min_length=1)

class UserOut(BaseModel):
    id: int
    emp_no: str
    name: str
    dept: str
    role: Literal["일반", "팀장", "관리자"]
    clearance: Literal["일반", "3급", "대외비"]
```

요청 모델에는 `password`가 있지만 응답 모델에는 비밀번호 관련 필드가 아예 없습니다. DB 모델을 그대로 내보내면 `password_hash`까지 나가기 때문에 응답 전용 스키마를 따로 둡니다.

```python
# services/auth_service.py
def authenticate(emp_no: str, password: str) -> dict:
    with session_scope() as s:
        user = user_repo.get_by_emp_no(s, emp_no)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthFailed()
        return _to_out(user)
```

사번이 없는 경우와 비밀번호가 틀린 경우를 `if`문 하나로 묶어서 같은 예외를 던집니다. "없는 사번입니다"와 "비밀번호가 틀립니다"로 응답을 나누면, 그 차이만으로 어떤 사번이 실제로 등록돼 있는지 알아낼 수 있기 때문입니다. 리포지토리에서 `.one()` 대신 `.first()`를 쓴 것도 같은 맥락으로, 사번이 없는 것은 예외가 아니라 로그인 실패라는 정상적인 결과라서 `None`으로 받아 서비스가 판단하게 했습니다.

라우터에서는 `Header()`로 헤더를 받습니다. 파이썬 변수명 `x_emp_no`가 HTTP 헤더 `X-Emp-No`에 자동으로 대응됩니다.

```python
@router.get("/me", response_model=UserOut)
def me(x_emp_no: Annotated[str | None, Header()] = None) -> dict:
    if x_emp_no is None:
        raise AuthFailed("로그인이 필요합니다.")
    return auth_service.get_me(x_emp_no)
```

`main.py`에서 라우터를 연결할 때 `include_router`를 두 번 부르는데, 한 번에 여러 라우터를 넘기면 `TypeError`가 납니다. 이 함수는 라우터를 하나만 받게 설계되어 있고, 그 이유는 라우터마다 `tags`나 `dependencies` 같은 옵션이 달라지기 때문입니다. 문서 API에는 로그인 검사를 걸어야 하지만 로그인 API에까지 걸면 로그인 자체를 할 수 없습니다.

## 2. 로그인 화면과 상태 유지

Streamlit은 버튼을 누를 때마다 스크립트 전체를 다시 실행하므로, 로그인 상태는 반드시 `session_state`에 있어야 합니다. 이 상태를 화면 코드마다 흩어놓지 않고 `core/session.py` 한 곳으로 모았습니다.

```python
DEFAULTS: dict = {
    "page": "login",
    "user": None,
    "f_dept": "전체", "f_level": "전체", "f_status": "전체", "f_q": "",
}

def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)

def logout() -> None:
    st.session_state["user"] = None
    st.session_state["page"] = "login"
    for key in ("f_dept", "f_level", "f_status", "f_q"):
        st.session_state[key] = DEFAULTS[key]
```

로그아웃에서 검색 필터까지 되돌리는 것은, 다음 사람이 로그인했을 때 앞사람이 걸어둔 조건이 남아 있으면 안 되기 때문입니다.

`app.py`에서는 로그인 여부를 먼저 확인하고, 로그인 전이면 로그인 화면만 그린 뒤 `return`으로 끝냅니다.

```python
def main() -> None:
    session.init_state()

    if not session.is_authenticated():
        login_view.render()
        return

    render_sidebar()
    ...
```

이 `return`이 없으면 로그인 전에도 사이드바와 본문이 같이 그려집니다. 로그인 화면에서는 성공하면 `session.login(user)`로 상태를 바꾸고 `st.rerun()`으로 화면을 다시 그리게 했습니다. `rerun` 없이 끝내면 이번 실행에서는 이미 로그인 화면을 그린 뒤라서, 한 번 더 조작해야 화면이 넘어갑니다.

## 3. 프론트엔드와 백엔드 연결 — httpx2

화면(`localhost:8501`)이 백엔드(`127.0.0.1:8000`)를 부를 때, 브라우저가 직접 부르는 게 아니라 Streamlit 서버의 파이썬 코드가 부릅니다. 그래서 파이썬에서 HTTP 요청을 보내는 `httpx2` 라이브러리를 설치했습니다.

```bash
python -m pip install "httpx2==2.12.0"
```

백엔드 호출은 전부 `core/api_client.py`를 거치게 하고, 화면은 `api_client.list_documents(...)`처럼 함수만 부르도록 했습니다. 모든 호출이 지나가는 `_request` 함수가 하는 일은 네 가지입니다.

```python
def _request(method, path, *, params=None, json=None, emp_no=None):
    clean_params = None
    if params is not None:
        clean_params = {k: v for k, v in params.items() if v not in (None, "", "전체")}
    headers = {"X-Emp-No": emp_no} if emp_no else None

    try:
        response = httpx2.request(method, f"{BASE_URL}{path}", params=clean_params,
                                  json=json, headers=headers, timeout=TIMEOUT)
    except httpx2.ConnectError as exc:
        raise ApiError("백엔드에 연결하지 못했습니다. 터미널에서 서버가 떠 있는지 확인하세요.") from exc
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

- 필터를 안 고른 값(`None`, 빈 문자열, "전체")은 쿼리스트링에서 뺀다
- 로그인한 사번을 `X-Emp-No` 헤더로 싣는다
- 서버 꺼짐, 타임아웃, 4xx·5xx를 전부 `ApiError` 하나로 바꿔서 화면은 이것만 잡으면 된다
- 백엔드 에러 응답에서 `message`만 꺼내 사용자에게 보여준다

로그인은 본문(`json=`)으로, 목록 필터는 쿼리스트링(`params=`)으로 보냅니다. 비밀번호를 쿼리스트링에 실으면 URL에 그대로 남아 서버 접근 로그에 찍히기 때문입니다.

### 422 응답에서 비밀번호 감추기

사번을 비우고 로그인하면 FastAPI가 요청 검증에 실패해 422를 돌려주는데, 기본 422 응답에는 사용자가 보낸 값이 통째로 담깁니다. 실제로 사번 없이 비밀번호만 넣어 검증해보니 에러 정보가 이렇게 나왔습니다.

```text
{'type': 'missing', 'loc': ('emp_no',), 'input': {'password': 'passwd1234!'}}
```

`input`에 비밀번호가 평문으로 들어 있습니다. 그래서 검증 에러 핸들러를 따로 두고, 필드 이름만 돌려주고 값은 감추도록 했습니다.

```python
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = ", ".join(
        ".".join(str(p) for p in e["loc"][1:]) or "요청 본문" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"code": "validation_failed", "message": f"입력값을 확인하세요 — {fields}", "detail": None},
    )
```

## 4. 문서 목록 화면

문서 관리 화면은 상단 지표, 필터 4종, 8열 표로 구성했습니다.

```text
[지표] 전체 8   현행 7   만료 1   재임베딩 1
부서▾   보안등급▾   상태▾   [검색어______]
┌ 문서 ID │ 문서명 │ 버전 │ 시행~만료 │ 상태 │ 부서 │ 등급 │ 색인 ┐
```

필터 위젯의 `key`를 `f_dept`, `f_level`, `f_status`, `f_q`로 준 것이 핵심이었습니다. `session.py`의 `DEFAULTS`에 미리 잡아둔 키와 같은 이름이라, 선택값이 재실행에도 유지되고 로그아웃하면 함께 초기화됩니다.

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

UI 킷의 `table`은 칸 안에 배지를 넣기 위해 셀 값을 HTML로 살려서 그립니다. 그래서 DB에서 온 글자 칸은 `escape()`로 감싸고, 배지 칸만 `badge_html()` 결과를 그대로 넣었습니다.

배지 색은 글자가 무엇으로 시작하는지로 정해지기 때문에 색인 열은 `"재임베딩 62%"`처럼 상태 낱말을 앞에 둡니다. 지표를 세는 코드도 문자열 비교라서, `"재임베딩 "`처럼 끝에 공백이 하나 들어가면 에러 없이 지표가 0으로만 나옵니다.

필터 하나를 바꿀 때마다 Streamlit이 전체를 다시 실행하므로 백엔드 호출이 두 번(지표용 전체 목록, 필터 적용 목록) 나갑니다. 문서가 적은 지금은 문제가 없지만, 늘어나면 집계 전용 API나 캐시가 필요해지는 자리입니다.

## 5. Docker와 PostgreSQL

오후에는 지금까지 쓰던 SQLite 파일 DB를 PostgreSQL로 옮길 준비를 했습니다. PostgreSQL을 PC에 직접 설치하지 않고 Docker 컨테이너로 띄웠습니다.

| 용어 | 비유 | 뜻 |
| --- | --- | --- |
| 이미지 | 붕어빵 틀 | 컨테이너를 만들기 위한 틀 |
| 컨테이너 | 붕어빵 | 이미지로 만든 실체. 프로그램과 실행 환경을 묶어 격리해서 돌린다 |

Windows에서는 Docker Desktop을 WSL 2 기반으로 설치했습니다. 이미지는 PostgreSQL 16에 벡터 검색 확장이 들어 있는 `pgvector/pgvector:pg16`을 쓰고, 설정은 `docker-compose.yml` 파일로 관리합니다.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: agent-postgres
    environment:
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: agent
      POSTGRES_DB: agent
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent -d agent"]
      interval: 5s
```

`ports`는 PC의 5432를 컨테이너의 5432로 연결하고, `volumes`는 데이터를 `pgdata` 볼륨에 따로 보관해서 컨테이너를 지워도 데이터가 남게 합니다. 이 파일에는 DB 비밀번호가 들어 있어서 `.gitignore`에 추가했습니다.

| 명령 | 컨테이너 | 데이터 |
| --- | --- | --- |
| `docker compose up -d` | 생성 + 실행 | — |
| `docker compose stop` / `start` | 멈춤 / 다시 실행 | 유지 |
| `docker compose down` | 삭제 | 유지 |
| `docker compose down -v` | 삭제 | 삭제 |

드라이버로 `psycopg[binary]`, 마이그레이션 도구로 `alembic`을 설치했고, SQLAlchemy는 URL만 바꾸면 같은 코드로 PostgreSQL에 붙습니다.

```text
sqlite:///./app.db
postgresql+psycopg://agent:agent@localhost:5432/agent
   방언      드라이버  계정  비번   호스트   포트  DB이름
```

### `(healthy)`인데 접속이 안 되는 문제

접속 확인 노트북을 실행했더니 `connection timeout expired`가 나왔습니다. 그런데 `docker compose ps`에서는 상태가 `(healthy)`였습니다.

```text
STATUS                    PORTS
Up 20 minutes (healthy)   5432/tcp                     ← 문제 상태
Up 7 seconds (healthy)    0.0.0.0:5432->5432/tcp, ...  ← 정상 상태
```

차이는 PORTS 칸이었습니다. `5432/tcp`만 있으면 컨테이너 안에서만 5432가 열려 있고 PC와는 연결되지 않은 상태입니다. compose 설정에는 포트가 제대로 들어 있었지만, 컨테이너가 다시 켜질 때 실제 포트 연결이 빠져 있었습니다. PC 쪽 5432에서 받아주는 곳이 없으니 노트북은 5초 동안 기다리다 타임아웃이 난 것입니다.

`(healthy)`가 떠도 안 됐던 이유는 healthcheck가 컨테이너 안에서 실행되기 때문입니다. `pg_isready`는 DB가 떠 있는지만 확인하고, PC에서 들어올 수 있는지는 보지 않습니다. 컨테이너를 다시 만들어서 해결했고, 데이터는 볼륨에 있어서 유지됐습니다.

```bash
docker compose up -d --force-recreate postgres
```

다시 접속해보니 PostgreSQL 16.15로 정상 연결됐습니다. 이후로는 STATUS의 `(healthy)`와 PORTS의 `->`를 함께 확인하고 있습니다.

## 오늘의 소감

한화 내일 아카데미 ICT부문 과정에서 백엔드와 프론트엔드를 따로 만들어 오다가, 오늘 처음으로 화면에서 로그인하고 백엔드 데이터가 표로 뜨는 흐름이 끝까지 이어졌습니다. 로그인 화면 하나에도 스키마, 리포지토리, 서비스, 라우터, 세션 상태, API 호출 통로까지 계층마다 할 일이 나뉘어 있었고, 앞에서 배운 구조가 각각 어디에 쓰이는지 연결해서 확인하는 시간이었습니다.

보안 관련해서는 기본 동작을 그대로 두면 새는 곳이 있다는 점을 코드로 확인했습니다. 422 응답에 비밀번호가 담기는 것, 사번 존재 여부가 응답 차이로 드러나는 것, DB에서 온 글자를 이스케이프 없이 HTML로 넣는 것이 모두 에러 없이 동작하는 코드에서 생기는 문제였습니다. Docker 포트 문제도 상태 표시만 믿으면 원인을 찾기 어려웠고, 설정값과 실제 적용된 값을 나눠서 확인해야 풀리는 문제였습니다.

다음 포스팅에서는 이어서 배울 내용을 정리해보겠습니다.

\#한화내일아카데미 \#한화시스템 \#AI개발자 \#K뉴딜아카데미 \#국비지원교육 \#개발자이직 \#부트캠프후기 \#백엔드개발 \#프론트엔드개발 \#AI에이전트

참고 링크 : https://blog.naver.com/dldl8819/224412738524
