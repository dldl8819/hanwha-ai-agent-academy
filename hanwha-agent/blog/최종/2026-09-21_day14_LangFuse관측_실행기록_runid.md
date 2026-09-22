# [한화 내일 아카데미 ICT부문] 14일차 후기 — LangChain·LangGraph 개요, LangFuse 관측, 실행 기록 테이블

지난 포스팅에서는 가드 함수와 스키마 검증, 재시도와 폴백, 골든셋 테스트까지 다뤘습니다. 14일차에는 만든 것을 **들여다보는** 쪽으로 넘어갔습니다. LangChain·LangGraph·LangSmith·LangFuse가 각각 무엇인지 정리한 다음, LangFuse를 실제로 붙이고 실행 기록을 우리 DB에도 남기는 작업을 했습니다.

한화 내일 아카데미 ICT부문 과정 14일차에 학습한 내용을 순서대로 정리해봅니다.

1. LangChain·LangGraph·LangSmith·LangFuse 개요
2. 관측 도구가 기록을 보는 방식
3. LangFuse 설정과 셀프 호스팅
4. 어댑터 — 관측이 실패해도 답변은 나가야 한다
5. run_id — 다섯 군데에서 같은 값
6. 실행 기록 테이블과 Alembic 리비전
7. 서비스에 붙이고 조회 API 만들기

## 1. LangChain·LangGraph·LangSmith·LangFuse 개요

이름이 비슷해서 헷갈리는데, 역할이 둘로 갈립니다.

| | 무엇을 하는가 |
| --- | --- |
| LangChain · LangGraph | AI 애플리케이션을 **만드는** 프레임워크 |
| LangSmith · LangFuse | 만든 것을 **관찰·평가·개선**하는 도구 |

```text
                     AI Agent 개발
              ┌──────────┴──────────┐
         LangChain              LangGraph
      LLM/RAG/Tool 을         복잡한 Agent 의
        쉽게 조립              흐름과 상태 제어
              └──────────┬──────────┘
                         ▼
                     AI Agent
                         │ 실행하면서
              ┌──────────┴──────────┐
         LangSmith               LangFuse
       추적/평가/관리           추적/평가/관리
      LangChain 계열 플랫폼    오픈소스·중립적
```

**LangChain은 LLM API 하나만 부르면 필요하지 않습니다.** 우리 프로젝트가 지금 그렇습니다.

```python
client.messages.create(...)     # 이게 전부라면 프레임워크를 얹을 이유가 없습니다
```

필요해지는 것은 중간 단계가 늘어날 때입니다.

```text
사용자 질문 → 질문 분석 → 문서 검색 → Embedding → pgvector 검색
          → 관련 Chunk → Prompt 작성 → Claude 호출 → Tool 호출 → 최종 답변
```

이 구성 요소들을 갈아 끼우기 쉽게 이어 주는 것이 LangChain입니다. Model, Prompt, Document Loader, Text Splitter, Tool 같은 조각으로 나뉘어 있습니다.

```python
prompt = ChatPromptTemplate.from_template("""
당신은 사내 업무 AI Assistant입니다.
다음 문서를 참고하세요.
{context}
질문:
{question}
""")
```

Model과 Prompt는 우리가 이미 손으로 만든 자리와 같습니다. `LLMPort`가 Model에 해당하고, `answer_system.md`가 Prompt에 해당합니다. **직접 만들어 본 다음에 프레임워크를 보면 무엇을 대신해 주는지가 보입니다.**

LangGraph는 흐름이 갈라지고 되돌아올 때 필요합니다.

```text
              사용자 질문 → 질문 분석
      ┌────────────┼────────────┐
   문서질문      직원질문      메일요청
     RAG           DB        Email Tool
      └────────────┼────────────┘
                결과 검증
            ┌───────┴───────┐
           성공            실패
           답변            재검색 → 다시 검증
```

분기와 **되돌아오는 화살표**가 생기면 함수 호출을 이어 붙이는 방식으로는 관리가 안 됩니다. LangGraph는 이것을 노드와 엣지를 가진 그래프로, 그리고 노드 사이를 오가는 상태로 다룹니다. 13일차에 만든 재시도 루프가 "검증 실패 → 다시 호출"이라 이 그림의 작은 조각이고, `hint` 변수가 노드 사이를 오가는 상태에 해당합니다.

LangSmith와 LangFuse는 같은 문제를 풉니다.

| | LangSmith | LangFuse |
| --- | --- | --- |
| 성격 | LangChain 계열 플랫폼 | 오픈소스, 프레임워크 중립 |
| 운영 | 클라우드 | 클라우드 또는 직접 운영(셀프 호스팅) |

수업에서 LangFuse를 쓰는 이유는 두 가지입니다. LangChain을 쓰지 않는 우리 코드에도 붙고, 내 PC에 띄워서 데이터를 밖으로 내보내지 않고 실습할 수 있습니다.

## 2. 관측 도구가 기록을 보는 방식

일반 웹 API는 같은 입력에 같은 출력이 나와서, 문제가 생기면 다시 돌려 보면 됩니다. LLM은 그게 안 됩니다. **다시 부르면 다른 답이 옵니다.** 그래서 그때 무엇을 보내고 무엇을 받았는지가 남아 있지 않으면 원인을 찾을 길이 없습니다.

기록을 계층으로 봅니다.

```text
trace  ── 질문 1건 (RUN-8881)
  ├── observation  프롬프트 읽기            (span)
  ├── observation  Claude 1차 호출          (generation)
  ├── observation  검증 실패 → 재시도
  └── observation  Claude 2차 호출          (generation)
score  ── 이 트레이스에 붙이는 점수 (골든셋 통과 여부 등)
```

| 용어 | 뜻 |
| --- | --- |
| trace | 사용자 요청 한 건 전체 |
| observation | 그 안의 단계 하나. 모델 호출은 `generation`, 나머지는 `span` |
| score | 트레이스에 나중에 붙이는 평가값 |

`generation`이 따로 있는 이유는 모델 호출에만 붙는 값(모델명·입출력 토큰)이 있어서입니다. 이 값이 있어야 화면에서 비용을 집계할 수 있습니다.

LangFuse의 기능은 세 가지입니다. Observability(실행을 trace로 기록), Prompt Management(프롬프트를 코드와 분리해 버전별로 관리), Evaluation(답이 쓸 만했는지 점수로 평가)입니다. Prompt Management는 `answer_system.md`를 파일로 뺀 것과 같은 판단이고, Evaluation은 골든셋 통과 여부를 기록에 붙이는 자리입니다.

## 3. LangFuse 설정과 셀프 호스팅

설정을 먼저 추가했습니다.

```python
# --- 관측 langfuse ---
langfuse_enabled: bool = False
langfuse_host: str = "http://localhost:3000"
langfuse_public_key: str | None = None
langfuse_secret_key: SecretStr | None = None
```

| 판단 | 이유 |
| --- | --- |
| `langfuse_enabled` 기본값 `False` | 키를 안 넣은 사람도, 패키지를 설치하지 않은 사람도 앱이 그대로 돕니다 |
| public은 `str`, secret은 `SecretStr` | public은 화면에서 다시 볼 수 있고, secret은 로그에 실수로 찍히면 안 됩니다 |

**리전 주소와 키가 짝이 맞아야 합니다.** 일본 리전에서 발급한 키를 다른 주소로 보내면 인증이 실패합니다. 이게 실습에서 가장 흔한 막힘이라 노트북에 확인 절차를 넣었습니다.

셀프 호스팅은 순서를 바꾸면 안 됩니다.

```bash
# 1) 3000 번 포트가 비었는지 먼저 확인 (쓰고 있으면 컨테이너가 조용히 안 뜹니다)
netstat -ano | findstr :3000

# 2) docker-compose.yml 에 langfuse 블럭 추가

# 3) langfuse 전용 데이터베이스를 손으로 만듭니다
docker compose exec postgres psql -U agent -d agent -c "CREATE DATABASE langfuse OWNER agent;"

# 4) 그 다음에 컨테이너를 올립니다
docker compose --profile langfuse up -d
docker compose logs -f langfuse        # 안 뜨면 로그부터 봅니다
```

3번을 먼저 하지 않으면 4번이 실패합니다. LangFuse는 뜨면서 바로 자기 DB에 붙어 마이그레이션을 돌리는데, **compose는 `DATABASE_URL`에 적힌 데이터베이스를 만들어 주지 않습니다.** 없으면 그대로 죽습니다.

```yaml
  langfuse:
    image: langfuse/langfuse:2
    container_name: agent-langfuse
    profiles: ["langfuse"]
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://agent:agent@postgres:5432/langfuse
      NEXTAUTH_URL: http://localhost:3000
    ports:
      - "3000:3000"
```

읽을 점이 세 가지입니다. `profiles`를 두면 그냥 `docker compose up -d`로는 뜨지 않아서, 필요한 날만 올릴 수 있습니다. `DATABASE_URL`의 호스트가 `localhost`가 아니라 `postgres`인데, 컨테이너끼리는 compose가 붙여준 서비스 이름으로 서로를 찾습니다. `condition: service_healthy`는 단순히 "먼저 시작"이 아니라 `pg_isready`가 통과할 때까지 기다립니다.

컨테이너를 내릴 때 주의할 것이 하나 있습니다.

```bash
docker compose stop langfuse       # langfuse 만 멈춤
docker compose down langfuse       # 서비스 이름을 빼면 postgres 까지 같이 지워집니다
```

## 4. 어댑터 — 관측이 실패해도 답변은 나가야 한다

이 파일의 원칙은 하나입니다. **기록을 남기려다 사용자 요청을 깨뜨리면 관측 도구를 붙인 것이 손해가 됩니다.** 거의 모든 설계 판단이 이 한 줄에서 나왔습니다.

```python
_client = None
_tried = False

def get_client():
    global _client, _tried
    if _tried:
        return _client          # 실패도 기억합니다
    _tried = True

    settings = get_settings()
    if not settings.langfuse_enabled:
        return None
    if not settings.langfuse_public_key or settings.langfuse_secret_key is None:
        log.warning("LANGFUSE_ENABLED=true 인데 키가 비어 있습니다. 관측을 건너뜁니다.")
        return None
    try:
        from langfuse import Langfuse
        _client = Langfuse(...)
    except Exception as e:
        log.warning("Langfuse 클라이언트를 만들지 못하였습니다 (무시하고 계속) : %s", e)
        _client = None
    return _client
```

어댑터를 한 번만 만들어 재사용하는 것은 전에 만든 팩토리와 같은데, `@lru_cache`를 쓰지 않고 전역 변수 두 개를 쓴 이유가 있습니다. **실패도 캐시해야 합니다.** `@lru_cache`는 예외를 캐시하지 않아서, 만들기에 실패하면 요청마다 다시 시도하며 같은 경고를 쏟습니다. `_tried`를 따로 두면 첫 번째 시도의 결과가 `None`이어도 그대로 재사용됩니다.

`from langfuse import Langfuse`도 함수 안에 있습니다. 관측을 끄고 쓰는 사람은 패키지를 설치하지 않아도 됩니다.

```python
except Exception as e:      # 종류를 나누지 않습니다
```

평소에는 나쁜 습관이지만 여기서는 의도한 것입니다. 패키지 미설치·주소 오타·키 형식 오류가 전부 여기로 오고, 무엇이 왔든 정답이 "관측만 포기"라서 나눌 이유가 없습니다.

같은 경고를 두 번 찍지 않는 장치도 넣었습니다.

```python
_warned = False

def _quiet(message: str, e: Exception) -> None:
    global _warned
    if not _warned:
        _warned = True
        log.warning("%s (무시하고 계속): %s", message, e)
    else:
        log.debug("%s: %s", message, e)
```

관측이 막혀 있으면 요청마다 같은 경고가 찍혀서 **로그가 정작 봐야 할 것을 덮습니다.** 첫 실패만 warning으로 알리고 그 다음은 debug로 내립니다.

트레이스는 `with`로 씁니다.

```python
@contextmanager
def trace(name: str, *, run_id: str, user_id: str = "", metadata: dict | None = None):
    client = get_client()
    handle = None
    if client is not None:
        try:
            handle = client.trace(id=run_id, name=name, user_id=user_id, metadata=metadata or {})
        except Exception as e:
            _quiet("Langfuse 트레이스를 시작하지 못했습니다.", e)
    try:
        yield handle
    finally:
        pass
```

관측이 꺼져 있으면 `handle`이 `None`입니다. 예외가 아니라 `None`이라는 게 중요합니다. **부르는 쪽은 `with` 블록을 그대로 쓰고, 안에서 `handle`을 쓸 때만 `None`을 확인하면 됩니다.**

```text
get_client() : None
trace() 의 handle : None
with 블록 안 계산 : 3 + 4 = 7
score() 호출 : 예외 없음
```

`client.trace(id=run_id, ...)`에서 트레이스 id를 **우리가 정한 번호로 넘깁니다.** LangFuse가 매긴 번호를 받아 오는 게 아닙니다. 그래서 화면과 DB를 같은 값으로 찾아갈 수 있습니다.

## 5. run_id — 다섯 군데에서 같은 값

| 어디 | 무엇으로 쓰나 |
| --- | --- |
| LangFuse | 트레이스 id |
| `runs` 테이블 | 기본키 PK |
| `usage_logs` 테이블 | 외래키 FK |
| `GET /api/v1/chat/runs/{run_id}` | 경로 파라미터 |
| 감사 로그 | 사람이 화면에서 눈으로 확인하는 값 |

그래서 **번호를 먼저 만들고 그 다음에 트레이스를 붙입니다.** DB의 자동 증가 PK를 쓸 수 없는 이유가 여기 있습니다. INSERT를 해야 번호가 나오는데, 우리는 호출을 시작하기 전에 이미 번호가 필요합니다.

```python
RUN_START = 8821

def next_run_id(session: Session) -> str:
    used = session.scalars(select(Run.id)).all()
    numbers = [RUN_START - 1]                 # 아무 행도 없을 때 max() 가 죽지 않게
    for run_id in used:
        tail = run_id.removeprefix("RUN-")
        if tail.isdigit():                    # "RUN-테스트" 같은 값에서 int() 가 터지지 않게
            numbers.append(int(tail))
    return f"RUN-{max(numbers) + 1:04d}"
```

`:04d`는 21을 `0021`로 채웁니다. 문자열로 정렬해도 순서가 맞습니다.

이 방식의 한계도 분명합니다. **행을 전부 읽어서 최대값을 찾습니다.** 기록이 쌓이면 느려지고, 두 요청이 동시에 들어오면 같은 번호를 받을 수 있습니다. 운영이라면 DB 시퀀스로 바꿀 자리입니다.

## 6. 실행 기록 테이블과 Alembic 리비전

관측 도구가 보는 계층을 우리 DB에 그대로 옮겼습니다. trace는 `runs`, observation은 `run_steps`입니다.

```python
class Run(Base, TimestampMixin):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)     # "RUN-8821"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)   # 나중에 채웁니다
    status: Mapped[str] = mapped_column(String(24), default="완료")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    mode: Mapped[str] = mapped_column(String(8), default="mock")
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)

class RunStep(Base):
    __tablename__ = "run_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    ord: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(64))
    ok: Mapped[bool] = mapped_column(default=True)
    ms: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
```

| 판단 | 이유 |
| --- | --- |
| 관측 도구에만 두지 않고 우리 DB에도 남깁니다 | 그 서비스가 죽거나 무료 한도를 넘으면 기록이 사라집니다. 화면·감사 로그·통계는 우리 힘으로 만들어야 합니다 |
| `answer`가 `nullable` | 호출 **전에** 행을 먼저 넣기 때문에 그때는 답이 없습니다 |
| `mode`를 남깁니다 | 이 답이 mock이었나 live였나. 나중에 기록을 볼 때 이게 없으면 판단이 안 됩니다 |
| `sources`를 JSON 통째로 | "그때 이렇게 답했다"는 스냅샷입니다. 문서가 개정되어도 이 기록의 버전·위치는 그대로 남아야 합니다 |
| `RunStep`에 `ord`를 따로 | `created_at`으로 정렬하면 같은 밀리초에 끝난 단계들의 순서가 뒤집힙니다 |

여기서 놓치기 쉬운 자리가 있었습니다.

```python
from app.models.run import Run, RunStep
```

**Alembic의 autogenerate는 `Base.metadata`에 등록된 테이블만 봅니다.** 모델 파일을 만들어도 `models/__init__.py`에서 import하지 않으면 리비전 파일이 빈 채로 생성됩니다. 에러가 아니라 빈 파일이 나오는 조용한 실패입니다.

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "add runs and run_steps"
alembic -c backend/alembic.ini upgrade head
```

```text
INFO  [alembic.runtime.migration] Running upgrade  -> 1560d57453ab, initial schema
INFO  [alembic.runtime.migration] Running upgrade 1560d57453ab -> 4da9dfda9039, add runs and run_steps
```

```text
 public | run_steps         | table | agent
 public | runs              | table | agent
```

또 하나 걸린 것이 있습니다. **첫 리비전의 `upgrade()`가 `pass`였습니다.** 그 리비전을 만들 때 `users`·`documents`는 이미 `create_all()`로 만들어져 있었고, autogenerate는 모델과 DB의 *차이*만 적기 때문입니다. 빈 파일이라고 지우면 안 됩니다. 다음 리비전의 `down_revision`이 그 번호라서, 기준점이 없으면 이후 리비전을 적용할 수 없습니다.

## 7. 서비스에 붙이고 조회 API 만들기

```python
def ask(*, question: str, run_id: str | None = None, user_id: int = 1) -> AskOut:
    q = check_question(question)
    llm = factory.get_llm()

    from app.integrations.langfuse_client import score, trace
    from app.integrations.llm_claude import _extract_json

    started = time.perf_counter()

    # 1) 호출 전에 먼저 기록을 만듭니다
    with session_scope() as session:
        if run_id is None:
            run_id = next_run_id(session)
        session.add(Run(id=run_id, user_id=user_id, question=q,
                        status="진행중", mode=get_settings().app_mode))

    # 2) 여기서부터가 한 건의 트레이스
    with trace("ask", run_id=run_id, user_id=str(user_id), metadata={"question_len": len(q)}):
        out = None
        hint = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            ...
            out = AskOut(**data, run_id=run_id, attempts=attempt, fallback_used=False)
            break
        if out is None:
            out = _fallback(run_id, MAX_ATTEMPTS)
            score(run_id, "schema_ok", 0.0)

        # 3) 기록 마무리
        with session_scope() as session:
            run = session.get(Run, run_id)
            run.answer = out.answer
            run.status = "완료"
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            run.sources = [s.model_dump() for s in out.sources]
        return out
```

바뀐 점을 하나씩 보면,

**`status="진행중"`으로 먼저 넣습니다.** 답을 받은 다음에 남기면 호출 중에 서버가 죽은 요청은 흔적이 없습니다. 먼저 넣어두면 끝나지 않은 요청도 DB에 보입니다.

**`return`이 `out = ...; break`로 바뀌었습니다.** 전에는 검증을 통과하면 바로 `return`했습니다. 이제는 트레이스 안에서 DB 마무리까지 해야 해서 변수에 담고 루프를 빠져나옵니다. "`for`를 끝까지 돌았다"였던 폴백 조건은 `if out is None`으로 바뀌었습니다.

**`score(run_id, "schema_ok", 0.0)`.** 폴백으로 빠진 것을 점수로도 남깁니다. 로그는 사람이 찾아 읽어야 하지만, 점수는 "폴백 비율"로 집계됩니다.

여기서 계층 규칙과 부딪히는 자리가 나왔습니다. 계층 검사 테스트에는 "services는 `app.integrations.factory`만 본다"는 규칙이 있는데, `langfuse_client`는 팩토리를 거치지 않으니 파일 최상단에서 import하면 이 규칙에 걸립니다. 그래서 **함수 안에서 import했습니다.** 그 검사는 `ast`로 파일 최상단만 읽으므로 함수 안 import는 걸러지지 않습니다.

검사를 피한 셈이지만, 규칙을 우회한 것과 판단이 다른 것은 구별해야 합니다. 팩토리를 거치라는 규칙의 목적은 "공급자 SDK가 서비스 코드에 박히지 않게" 하는 것입니다. 관측은 계층을 타고 흐르는 의존이 아니라 어디서든 껐다 켤 수 있는 부수 기능이고, 껐을 때 `None`만 돌아오면 되므로 Protocol로 감쌀 대상이 아니라고 봤습니다.

```bash
pytest -q backend/tests/test_layers.py
# 5 passed
```

조회 함수는 모델 객체가 아니라 `dict`를 만들어 돌려줍니다.

```python
def get_run(*, run_id: str) -> dict:
    with session_scope() as session:
        run = session.get(Run, run_id)
        if run is None:
            raise NotFound(f"실행 기록을 찾을 수 없습니다: {run_id}")
        return {
            "run_id": run_id, "user_id": run.user_id, "question": run.question,
            "answer": run.answer, "status": run.status, "latency_ms": run.latency_ms,
            "mode": run.mode,
            "sources": run.sources or [],
            "created_at": run.created_at.isoformat(),
        }
```

이유가 네 가지입니다. 세션이 닫힌 뒤에 속성을 읽으면 예외가 납니다. 테이블 컬럼이 늘어날 때 응답이 조용히 같이 늘어납니다. `datetime`은 JSON으로 그대로 못 나가서 문자열로 바꿔야 합니다. `sources`가 아직 `None`이면 빈 목록으로 내보내 화면의 분기를 줄입니다.

라우터는 한 줄입니다.

```python
@router.get("/runs/{run_id}")
def read_run(run_id: str) -> dict:
    return chat_service.get_run(run_id=run_id)
```

라우터에서 `try/except`로 404를 만들지 않습니다. 서비스가 `NotFound`를 던지고 `main.py`의 전역 핸들러가 응답으로 바꿉니다.

실제로 돌려보면 이렇게 나옵니다.

```text
ask() 가 돌려준 run_id : RUN-8830

runs 표에서 찾은 행
  id         : RUN-8830
  status     : 완료
  mode       : mock
  latency_ms : 334
  answer     : 부산 출장 숙박비는 1박 7만...
  sources    : [{'doc_id': 'DOC-HR-014', 'title': '국내출장 여비 규정', 'version': 'v2.0', 'locator': '제12조(숙박비) · p.6'}]
```

```text
GET /api/v1/chat/runs/RUN-8830 → 200
GET /api/v1/chat/runs/RUN-9999 → 404
  {'code': 'not_found', 'message': '실행 기록을 찾을 수 없습니다: RUN-9999', 'detail': None}
```

### 남은 문제

`ask()`가 DB에 쓰게 되면서 골든셋 테스트도 행을 남깁니다. `pytest -q`를 한 번 돌리면 이렇게 쌓입니다.

```text
 RUN-8821 | 완료 |  294 | mock | 부산 출장 숙박비는 1박 7만원 이내입니다.
 RUN-8822 | 완료 |   11 | mock | 국내출장 여비 규정의 현행 판은 v2.0 입니다.
 ...
 RUN-8829 | 완료 |   10 | mock | 정보보안 지침은 대외비 문서라 전문을 그대로 옮겨 드릴
```

테스트는 36건 모두 통과하지만 **돌릴수록 개발 DB가 더러워지고 `run_id`가 앞으로 밀립니다.** 테스트가 자기 DB를 쓰게 하는 것이 다음에 손볼 자리입니다.

## 이날의 소감

14일차는 **기능을 더하는 날이 아니라 들여다보는 장치를 붙이는 날**이었습니다. 코드가 늘었는데 사용자가 받는 답은 하나도 바뀌지 않았습니다.

관측 코드를 짜면서 계속 나온 판단이 "실패해도 조용히 넘어가라"였습니다. 평소에는 예외를 삼키지 말라고 배우는데, 여기서는 삼키는 게 맞습니다. 기준은 **그 실패가 사용자가 받는 답을 바꾸는가**였습니다. 관측이 안 되는 것은 답을 바꾸지 않으니 넘어가고, 대신 로그와 `_warned` 플래그로 사람이 나중에 알 수 있게 남깁니다.

`run_id`를 DB가 아니라 우리가 먼저 만든 것도 같은 성격의 판단이었습니다. 자동 증가 PK가 더 간단한데, 그러면 번호를 알기 위해 INSERT를 기다려야 하고 그 사이 트레이스를 시작할 수 없습니다. **한 값을 다섯 군데에서 쓰기로 정하면 그 값을 언제 만드는지가 설계가 됩니다.**

계층 규칙과 부딪힌 자리도 남습니다. 함수 안 import로 검사를 통과했지만, 검사가 못 보는 방식으로 통과한 것이라 "왜 이건 예외로 둬도 되는가"를 코드 주석에 적어뒀습니다. 이런 것을 적어두지 않으면 나중에는 규칙이 있는지조차 흐려집니다.

다음 포스팅에서는 호출 한 번의 토큰 사용량과 원가를 기록하는 부분을 정리해보겠습니다.

\#한화내일아카데미 \#한화시스템 \#AI개발자 \#K뉴딜아카데미 \#국비지원교육 \#개발자이직 \#부트캠프후기 \#AI에이전트 \#LLM \#백엔드개발 \#API개발

참고 링크 : https://blog.naver.com/dldl8819/224420075761
