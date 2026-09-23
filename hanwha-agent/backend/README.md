# backend — 폴더와 파일이 각각 하는 일

사내 규정을 묻고 근거와 함께 답을 받는 업무 에이전트의 서버 쪽입니다. 폴더 하나가 계층 하나를 맡고, 요청은 위에서 아래로만 흐릅니다.

| | |
| --- | --- |
| 파이썬 파일 | 39개 · 2,815줄 |
| DB 테이블 | 7개 (PostgreSQL 16) |
| 엔드포인트 | 8개 |
| 테스트 | 36건 |

같은 내용을 눌러가며 보는 [해부도 페이지](https://claude.ai/artifact/5SYTT5HecsWP3amKbGT9w7)도 있습니다.

## 질문 하나가 지나가는 길

`POST /api/v1/chat/messages` 가 실제로 밟는 순서입니다.

```text
01  라우터가 받는다        api/v1/chat.py
02  모양을 검증한다        schemas/chat.py
03  가드가 앞을 막는다      core/guards.py
04  실행 번호를 만든다      services/ids.py
05  runs 행을 먼저 넣는다   models/run.py
06  mock 이냐 live 냐      integrations/factory.py
07  체인을 조립한다        agent/chain.py
08  모델을 부른다          integrations/llm_claude.py
09  사용량을 남긴다        models/usage.py
10  검증하고 돌려준다      services/chat_service.py
```

## 폴더 구조

```text
backend/
├── app/
│   ├── main.py           앱 조립 · 예외를 HTTP 로 번역
│   ├── api/v1/           요청을 받는 자리 — 얇게, 로직 없음
│   ├── schemas/          들어오고 나가는 모양 (Pydantic)
│   ├── core/             설정 · 예외 · 로깅 · 보안 · 가드
│   ├── services/         업무 규칙과 트랜잭션 경계 — 여기서만 커밋한다
│   ├── agent/            프롬프트와 체인
│   ├── repositories/     DB 접근 — SQL 을 여기 가둔다
│   ├── models/           테이블 모양 — 아무것도 import 하지 않는다
│   ├── integrations/     바깥으로 나가는 유일한 문
│   └── db/               세션 · 초기화 · 시드 · 마이그레이션
└── tests/                규칙이 문서에만 있으면 아무도 지키지 않는다
```

---

## app/main.py — 앱을 조립하는 자리

`FastAPI()` 를 만들고 `include_router` 로 라우터를 하나씩 붙입니다. 한 번에 여러 개를 넘길 수는 없어서 라우터마다 한 줄씩 부릅니다.

`@app.exception_handler(AgentError)` 가 앱이 던진 예외를 한 번에 받아 `status_code` 와 `code` 를 읽어 JSON 으로 내보냅니다. **새 예외를 만들어도 이 함수는 고치지 않습니다.**

## app/api/v1/ — 요청을 받는 자리

| 파일 | 하는 일 |
| --- | --- |
| `chat.py` | `POST /chat/messages`, `GET /chat/runs/{run_id}` |
| `documents.py` | 문서 목록 · 업로드 · 상세. `ALLOWED_EXTS` 로 확장자를 허용 목록 방식으로 거른다 |
| `auth.py` | `POST /auth/login`, `GET /auth/me` |
| `deps.py` | 요청마다 세션 하나(`get_db`), 요청 번호와 로거 |

라우터가 하는 일은 "받아서 서비스에 넘기고, 돌려준다"가 전부입니다. 가드·재시도·폴백은 전부 서비스 안에 있습니다.

**왜** — 라우터가 얇아야 같은 업무 규칙을 배치 작업이나 다른 진입점에서도 그대로 쓸 수 있습니다.

## app/schemas/ — 들어오고 나가는 모양

| 파일 | 담는 것 |
| --- | --- |
| `chat.py` | `ChatRequest` · `AnswerSource` · `AnswerOut` · `AskOut` |
| `document.py` | `DocumentOut` · `DocumentCreateOut` |
| `auth.py` | `LoginIn` · `UserOut` |
| `common.py` | `HealthOut` · `ErrorOut` |

`DOC_ID` 가 `Literal` 이라 등록되지 않은 문서 번호를 모델이 지어내면 검증에서 걸립니다.

**왜** — 할루시네이션을 `if` 로 막으면 검사를 빠뜨린 자리가 생기지만, 타입으로 막으면 빠뜨릴 자리가 없습니다.

## app/core/ — 설정·예외·로깅·보안·가드

| 파일 | 하는 일 | 짚어둘 것 |
| --- | --- | --- |
| `config.py` | `.env` → `Settings` 하나 | `@lru_cache` 라 항상 같은 객체. `app_mode` 기본값이 `mock` |
| `exceptions.py` | `AgentError` 뿌리에서 9개로 갈린다 | `AuthFailed` 만 기본 메시지를 가진다 |
| `guards.py` | 모델을 부르기 **전에** 막는다 | `ALLOWED_MODELS` 허용 목록 방식 |
| `security.py` | `bcrypt` 해싱 | 깨진 해시를 받아도 예외 대신 `False` |
| `logging.py` | 로그 형식을 한 번만 정한다 | `lifespan` 에서 한 번 부른다 |

`.env` 는 **`Settings` 객체에만** 담기고 `os.environ` 에는 안 들어갑니다. 라이브러리가 알아서 키를 찾을 거라 생각하면 인증 오류가 납니다.

`AuthFailed` 가 사번이 틀렸는지 비밀번호가 틀렸는지 알려주지 않는 이유는, 알려주면 **사번 존재 여부를 확인하는 도구**가 되기 때문입니다.

## app/services/ — 업무 규칙과 트랜잭션 경계

| 파일 | 하는 일 |
| --- | --- |
| `chat_service.py` | 질문 한 건의 전 과정 (213줄, 백엔드에서 가장 길다) |
| `document_service.py` | 문서 목록 · 상세 · 생성 |
| `auth_service.py` | 로그인 검증 |
| `ids.py` | `RUN-8821` 같은 실행 번호 발급 |

`ask()` 의 순서입니다.

```text
가드 → 어댑터 → runs INSERT → 트레이스 → 재시도 → 사용량 기록 → 검증 → 폴백 → runs UPDATE
```

**사용량을 검증 전에 기록합니다.** 형식을 어겨 버려진 응답도 토큰은 이미 과금됐기 때문입니다. 통과한 호출만 기록하면 재시도로 나간 비용이 장부에서 통째로 빠집니다.

세 번 다 실패하면 `_fallback` 이 **예외가 아니라 정상 응답 객체**를 돌려줍니다. 화면은 평소와 같은 모양을 받아 깨지지 않고, `fallback_used` 로 표시만 따로 붙일 수 있습니다.

`ids.py` 가 번호를 직접 만드는 이유는 **값을 먼저 알아야 하기 때문**입니다. LangFuse 트레이스 id, `runs` PK, `usage_logs` FK, 조회 경로, 감사 로그 다섯 군데가 같은 값을 씁니다. 자동 증가 PK 였다면 INSERT 를 기다려야 하고 그 사이 트레이스를 시작할 수 없습니다.

## app/agent/ — 프롬프트와 체인

| 파일 | 하는 일 |
| --- | --- |
| `chain.py` | 우리 포트를 LangChain 체인으로 조립 |
| `prompts/answer_system.md` | 역할 · 규칙 5개 · 출력 형식 (40줄) |

시스템 프롬프트는 `SystemMessage` 객체로 넣습니다. 튜플 `("system", ...)` 로 넣으면 **본문의 중괄호가 변수로 읽혀** JSON 예시를 한 줄만 넣어도 터집니다.

파일 맨 위 주석이 **여기서 하지 않는 일**을 먼저 적습니다.

```text
mock / live 분기 처리 X
재시도, 폴백 처리 X
```

`llm` 을 인자로 받는 것이 그 표시입니다 — 스스로 `get_llm()` 을 부르지 않습니다.

## app/integrations/ — 바깥으로 나가는 유일한 문

| 파일 | 하는 일 |
| --- | --- |
| `ports.py` | `LLMResult` · `LLMPort` (Protocol) |
| `factory.py` | mock 이냐 live 냐 — **분기는 여기 한 곳** |
| `llm_claude.py` | Claude 실제 호출 · 원가 계산 · JSON 추출 |
| `langfuse_client.py` | 관측 — 실패해도 답변은 나간다 |

`runtime_checkable` Protocol 은 **메서드 이름만 봅니다.** 인자 이름이 달라도 `isinstance` 는 통과하고, 실제로 부를 때 `TypeError` 가 납니다.

`mock` 모드에서는 `anthropic` SDK 가 아예 로드되지 않습니다 — import 를 함수 안에 두었기 때문입니다. 분기가 여러 곳에 흩어지면 하나를 빠뜨렸을 때 개발 중에 실제 과금이 일어납니다.

단가표(`PRICING`)를 서비스가 아니라 어댑터에 둡니다. **공급자마다 가격이 달라서**, 모델을 바꾸면 이 파일만 고칩니다.

## app/models/ — 테이블 모양

| 파일 | 테이블 |
| --- | --- |
| `base.py` | (공통) `Base` · `TimestampMixin` |
| `org.py` | `departments` · `users` |
| `document.py` | `documents` · `document_versions` |
| `run.py` | `runs` · `run_steps` |
| `usage.py` | `usage_logs` |

`run.py` 에 판단이 셋 들어 있습니다.

- PK 가 자동 증가 정수가 아니라 **문자열**입니다 (`RUN-8821`)
- `sources` 를 **JSON 통째로** 담습니다. "그때 이렇게 답했다"는 스냅샷이라, 문서가 개정돼도 이 기록의 버전은 그대로 남아야 합니다
- `RunStep` 에는 `TimestampMixin` 을 **안 붙였습니다.** `created_at` 으로 정렬하면 같은 밀리초에 끝난 단계들의 순서가 뒤집혀서 `ord` 로 셉니다

`__init__.py` 가 입구입니다. Alembic 의 autogenerate 는 `Base.metadata` 에 등록된 것만 봅니다. **여기서 import 하지 않은 모델은 리비전 파일에 에러 없이 아예 안 나옵니다.**

## app/repositories/ — DB 접근

| 파일 | 하는 일 |
| --- | --- |
| `document_repo.py` | 문서 조회 · 버전 추가 |
| `user_repo.py` | 사번으로 사용자 조회 |

`list_documents` 는 조건을 **준 것만** 겁니다. `joinedload(Document.dept)` 로 부서를 미리 같이 읽습니다 — 화면이 부서 이름을 꺼낼 때는 세션이 이미 닫혀 있습니다.

**커밋하지 않습니다.** 여기서 커밋하면 중간에 끊긴 상태가 DB 에 남습니다. 트랜잭션의 경계는 서비스가 쥡니다.

`user_repo` 가 `.one()` 을 안 쓰는 이유는 없을 때 예외가 나기 때문입니다. "없음"은 예외가 아니라 흔한 결과이고, 판단은 서비스가 합니다.

## app/db/ — 세션·초기화·시드·마이그레이션

| 파일 | 하는 일 |
| --- | --- |
| `session.py` | 엔진과 `session_scope()` |
| `init_db.py` | 테이블 생성 (지금은 Alembic 이 맡는다) |
| `seed.py` · `seed_data.py` | 부서 · 사용자 6명 · 문서와 버전 |
| `migrations/env.py` | Alembic 이 모델을 찾는 자리 |
| `migrations/versions/` | 리비전 4개 |

엔진을 모듈 맨 위에서 만들지 않고 **부를 때마다 설정을 다시 읽습니다.** 그래서 테스트가 환경변수만 바꿔 임시 DB 로 갈아끼울 수 있습니다.

리비전은 `initial_schema` → `add_runs_and_run_steps` → `add_usage_logs` → `rename_occured_at` 순입니다. 마지막 것은 **손으로 적었습니다** — autogenerate 는 이름이 바뀐 것을 알아보지 못하고 drop + add 로 적어주는데, 그대로 실행하면 값이 전부 사라집니다.

이미 적용된 과거 리비전은 고치지 않습니다. 마이그레이션 이력은 **무엇이 있었는지를 남기는 기록**이지 현재 상태를 적는 문서가 아닙니다.

## tests/

| 파일 | 건수 | 무엇을 보는가 |
| --- | --- | --- |
| `test_layers.py` | 5 | 계층 구조가 무너졌는지 |
| `test_chat_golden.py` | 11 | 응답이 조건을 만족하는지 |
| `test_exceptions.py` | 9 | 예외가 HTTP 로 옳게 번역되는지 |
| `test_guards.py` | 6 | 가드가 막아야 할 걸 막는지 |
| `test_healthy.py` | 3 | API 가 실제로 응답하는지 |
| `test_core_config.py` | 2 | 설정이 캐시되는지 |

골든셋은 응답 문자열을 그대로 비교하지 않고 **조건**으로 판정합니다 — 있어야 할 낱말, 없어야 할 낱말, 근거 건수, 재시도 횟수. `factory.get_llm` 만 가짜로 갈아끼워서 돈이 들지 않고 인터넷 없이도 돕니다.

`conftest.py` 의 `test_db` 픽스처가 `autouse` 라 항상 먼저 돕니다. `DATABASE_URL` 을 임시 SQLite 로 바꾸므로 **테스트가 개발 DB 를 건드리지 않습니다.**

---

## 계층 규칙

```text
api/v1  →  services  →  repositories  →  models
```

**이 화살표는 문서가 아니라 테스트입니다.** `tests/test_layers.py` 가 각 파일의 최상단 import 를 `ast` 로 읽어, 한 단계를 건너뛰거나 거꾸로 부르는 곳이 있으면 실패합니다.

라우터가 급할 때 리포지토리를 직접 부르는 식의 우회는 **기능상 잘 돌아가기 때문에**, 사람이 코드 리뷰로만 막으면 시간이 지나며 새어 나갑니다.

`services` 가 `integrations` 를 만날 때는 `factory` 만 통과할 수 있습니다. 함수 안의 지연 import 는 이 검사에 걸리지 않는데, `chat_service` 가 관측 어댑터를 함수 안에서 부르는 자리가 그것입니다 — 규칙을 우회한 것이 아니라 **관측은 계층을 타고 흐르는 의존이 아니라는 판단**입니다.

## 엔드포인트

| | |
| --- | --- |
| `POST /api/v1/chat/messages` | 질문 한 건 |
| `GET /api/v1/chat/runs/{run_id}` | 실행 기록 조회 |
| `GET /api/v1/documents` | 문서 목록 |
| `POST /api/v1/documents` | 문서 업로드 |
| `GET /api/v1/documents/{doc_id}` | 문서 상세 |
| `POST /api/v1/auth/login` | 로그인 |
| `GET /api/v1/auth/me` | 내 정보 |
| `GET /health` | 상태 확인 |

## 실행

```bash
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload --port 8000    # http://localhost:8000/docs
pytest -q
```
