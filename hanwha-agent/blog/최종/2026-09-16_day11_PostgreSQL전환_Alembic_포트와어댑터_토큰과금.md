# [한화 내일 아카데미 ICT부문] 11일차 후기 — PostgreSQL 전환, Alembic, 포트와 어댑터, 토큰 과금

지난 포스팅에서는 로그인과 화면-API 연동, 그리고 Docker로 PostgreSQL을 띄우는 것까지 다뤘습니다. 오늘은 한화 내일 아카데미 ICT부문 과정 11일차로, 그 컨테이너를 실제 프로젝트가 바라보게 바꾸고 스키마 변경을 관리하는 도구까지 붙였습니다. 오후에는 LLM을 붙이기 전에 필요한 설계 원칙과 비용 계산을 다뤘습니다.

오늘 학습한 내용을 순서대로 정리해봅니다.

1. SQLite에서 PostgreSQL로 전환
2. Alembic — 스키마 변경 이력 관리
3. AI-Native 애플리케이션
4. 포트와 어댑터
5. pytest 심화 — fixture, TestClient, 계층 검사
6. API 토큰과 과금

## 1. SQLite에서 PostgreSQL로 전환

코드는 고치지 않고 `.env`의 URL 한 줄만 바꿉니다.

```bash
# DATABASE_URL=sqlite:///./app.db
DATABASE_URL=postgresql+psycopg://agent:agent@localhost:5432/agent
```

그런데 노트북에서는 이것만으로 반영되지 않습니다.

```python
get_settings.cache_clear()      # @lru_cache 로 붙잡고 있던 Settings 버리기
db_session._ENGINES.clear()     # URL 별로 만들어 둔 엔진 캐시 비우기
```

`get_settings`에는 `@lru_cache`가 걸려 있어서 한 번 읽은 `.env` 값을 계속 돌려주고, `get_engine`은 URL별로 만든 엔진을 딕셔너리에 담아둡니다. 둘 다 프로세스가 살아 있는 동안 유지되는 캐시라, 커널을 켜 둔 채 `.env`만 바꾸면 예전 SQLite 설정이 그대로 쓰입니다. 서버는 다시 띄우면 해결되지만 노트북에서는 직접 비워야 합니다.

바뀐 뒤에는 SQLite 전용 설정이 안 타는지 확인합니다.

```python
is_sqlite = resolved.startswith("sqlite")
if is_sqlite:
    connect_args["check_same_thread"] = False   # sqlite3 드라이버 전용 인자
...
    cursor.execute("PRAGMA foreign_keys=ON")    # SQLite 전용 SQL
```

`check_same_thread`는 파이썬 `sqlite3` 드라이버에만 있는 인자라 psycopg에 넘기면 접속이 실패하고, `PRAGMA`는 SQLite 전용 SQL이라 PostgreSQL에서는 문법 오류가 납니다. PostgreSQL은 외래 키를 원래 항상 검사하므로 이 설정 자체가 필요 없습니다. URL 앞부분으로 갈라놨기 때문에 URL만 바꾸면 분기도 알아서 맞춰집니다.

표를 만들고 시드를 넣은 뒤, 같은 함수를 두 번 불러 결과가 같은지 확인했습니다.

```python
print("seed_all()      →", seed_all())
print("seed_all() 다시 →", seed_all())      # 멱등성 검사
```

`_seed`는 맨 앞에서 문서 개수를 세고 0이 아니면 아무것도 넣지 않고 현재 개수만 돌려줍니다. 이 검사가 없으면 셀을 다시 실행할 때마다 같은 데이터가 중복으로 쌓입니다.

## 2. Alembic — 스키마 변경 이력 관리

앞서 `User`에 컬럼을 추가했을 때는 DB 파일을 지우고 다시 만들었습니다. `create_all()`이 **표가 없으면 만들고 이미 있으면 아무것도 하지 않기** 때문입니다. 실습용 파일은 지우면 그만이지만 실제 서버 DB는 지울 수 없습니다. Alembic은 변경 내용을 파일로 남기고, 순서를 기억하고, 어디까지 적용했는지를 DB에 적어둡니다.

```bash
cd backend
alembic init app/db/migrations
```

설정에서 두 군데를 고쳤습니다.

```ini
prepend_sys_path = %(here)s     # 기본값 "." 에서 수정
sqlalchemy.url =                # = 뒤 값을 지운다
```

`prepend_sys_path`는 Alembic이 `env.py`를 실행할 때 모듈 검색 경로에 넣을 폴더입니다. `%(here)s`가 `backend/`를 가리켜서 `env.py`에서 `from app.core.config import ...`가 됩니다. `sqlalchemy.url`을 비우는 이유는 접속 정보를 `.env` 한 곳에서만 관리하기 위해서입니다. 여기에 URL을 적으면 **비밀번호가 ini 파일에 남아 커밋됩니다.**

```python
config.set_main_option("sqlalchemy.url", get_settings().database_url)

import app.models                    # 모델을 전부 불러와 Base에 등록시킨다
target_metadata = Base.metadata
```

`import app.models`가 꼭 필요합니다. `--autogenerate`는 `Base.metadata`에 등록된 표를 기준으로 비교하는데, 모델 모듈을 한 번도 import 하지 않으면 등록이 안 돼서 Alembic이 "표가 하나도 없다"고 판단하고 **전부 삭제하는 마이그레이션을 만듭니다.**

첫 적용은 `upgrade`가 아니라 `stamp`입니다.

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "initial schema"
alembic -c backend/alembic.ini stamp head
```

이미 `create_all`로 만들어 둔 표가 있는 상태라, "표를 만들라"는 첫 마이그레이션을 실행하면 이미 있는 표를 또 만들려다 실패합니다. `stamp`는 실행하지 않고 "여기까지 적용됨"만 기록해서 이력의 시작점을 맞춥니다.

## 3. AI-Native 애플리케이션

**핵심 기능의 일부를 같은 입력에 같은 출력을 보장하지 않는 구성요소(LLM)에 맡기고, 그 전제 위에서 설계된 애플리케이션**을 말합니다. LLM을 붙였다고 전부 해당하는 것은 아니고, 기존 기능 옆에 챗봇을 하나 다는 것과 핵심 동작 자체를 모델이 수행하는 것은 설계가 다릅니다.

기존 애플리케이션과 가장 다른 점은 실패 방식입니다. 코드 오류는 예외로 드러나지만, 모델이 없는 근거를 지어내면 형식은 멀쩡한 응답이 나옵니다.

원칙으로 정리하면 이렇습니다.

- **LLM은 아키텍처가 아니라 부품 하나다.** 뼈대(권한, 상태, 트랜잭션)는 코드로 짜고 모델은 가장 바깥으로 민다
- **순서**: 단일 호출 → 체인 → 라우팅 → 에이전트. 처음부터 에이전트를 만들지 않는다
- **출력은 스키마로 강제하고 검증한다.** 자연어를 그대로 다음 단계로 넘기지 않는다
- **무엇을 얼마나 어떤 순서로 넣을지가 설계의 본체다** (컨텍스트 엔지니어링)
- **같은 값이 안 나와서 단위 테스트로 회귀를 못 잡는다.** 골든셋 정확도가 빌드 통과 기준이 된다
- **"나중에 최적화"가 안 통한다.** 호출 한 번에 돈과 시간이 들어서 처음부터 상한과 계측을 건다
- **외부에서 들어온 텍스트는 데이터이지 명령이 아니다.** 도구에는 최소 권한만 주고, 되돌릴 수 없는 행위 앞에는 사람을 세운다

API 키는 `.env`에만 두고 `.gitignore`에 `.env`가 들어 있는지 먼저 확인했습니다. 키가 커밋되면 파일을 지워도 과거 커밋에 남습니다. 확인용으로는 앞 8자와 글자 수만 보여주는 함수를 만들었습니다.

```python
def mask(secret: str | None, keep: int = 8) -> str:
    if not secret:
        return "(없음)"
    return f"{secret[:keep]}...({len(secret)}자)"
```

그리고 실제 API를 부르기 전에, 같은 질문에 다른 답이 오는 상황을 가짜 객체로 재현했습니다.

```python
llm = FlakyLLM(ANSWERS)     # 답 세 개를 순서대로 돌려준다
for i in range(1, 4):
    answer = llm.ask(QUESTION)
    assert answer == EXPECTED
```

```text
1회차: 통과              | 숙박비는 1박 7만원입니다.
2회차: 실패 — 기대와 다름 | 국내출장 숙박비 한도는 1박당 7만원입니다.
3회차: 실패 — 기대와 다름 | 1박 기준 숙박비는 7만원까지 인정됩니다.
```

세 답은 전부 내용이 맞습니다. 틀린 것은 답이 아니라 `assert answer == EXPECTED`라는 검사 방식입니다.

## 4. 포트와 어댑터

mock과 실제 호출을 함께 지원해야 하는데, 함수마다 모드를 확인하면 기능 수만큼 분기가 늘어납니다. 모델이 6~12개월마다 바뀐다는 전제와 정면으로 부딪히는 구조입니다. 그래서 역할을 셋으로 나눕니다.

| 이름 | 무엇 |
| --- | --- |
| 포트(Port) | 주고받을 내용을 정한 규약. 구현을 담지 않는다 |
| 어댑터(Adapter) | 포트를 실제 기술로 구현한 것 (MockLLM, ClaudeLLM) |
| 팩토리(Factory) | 어떤 어댑터를 쓸지 고르는 단 한 곳 |

이렇게 안쪽 업무 규칙을 가운데 두고 바깥 기술을 갈아 끼우는 구조를 헥사고날 아키텍처라고 하며, 원래 **테스트를 위해** 고안된 방식입니다.

규약은 `typing.Protocol`로 만들었습니다.

```python
@runtime_checkable
class LLMPort(Protocol):
    def answer(self, *, question: str, contexts: list[dict], user: dict) -> LLMResult: ...

class FixedLLM:                       # LLMPort 를 상속하지 않았다
    def answer(self, *, question, contexts, user) -> LLMResult: ...
```

```text
LLMPort in FixedLLM.__mro__     : False   ← 상속 관계가 아니다
isinstance(FixedLLM(), LLMPort) : True    ← 그런데 통과한다
```

상속하지 않았는데 통과합니다. Protocol은 "이 클래스를 물려받았는가"가 아니라 **"약속한 메서드를 갖고 있는가"**로 판단하기 때문입니다. 반대로 `abc.ABC`는 상속을 요구하고, 메서드를 구현하지 않으면 인스턴스를 만들 때 `TypeError`로 막습니다.

다만 한계가 있습니다.

```python
class WrongSignature:
    def answer(self, x): ...          # 인자 이름도 타입도 다르다

isinstance(WrongSignature(), LLMPort)   # → True
```

`runtime_checkable`의 `isinstance`는 **메서드 이름만 봅니다.** 서명까지 확인하려면 정적 타입 검사기를 돌려야 합니다.

## 5. pytest 심화 — fixture, TestClient, 계층 검사

같은 준비 데이터를 테스트마다 복사하지 않고 fixture로 뺐습니다. 함수 인자 이름을 fixture 이름과 맞추면 pytest가 알아서 넣어줍니다. `conftest.py`에 두면 그 폴더 아래 모든 테스트 파일이 import 없이 씁니다.

예외 8개가 각각 맞는 상태 코드를 갖는지는 `parametrize`로 확인했습니다. 테스트 하나가 아니라 **8개로 세어져서** 어느 것이 깨졌는지 결과에 그대로 나옵니다.

API는 `TestClient`로 서버를 띄우지 않고 앱을 직접 호출합니다.

```python
def test_documents_list_returns_rows(client) -> None:
    r = client.get("/api/v1/documents")
    assert 문서들[0]["security_level"] in ("일반", "3급", "대외비")
    # secret_note 는 응답 모델에 없으므로 밖으로 나가면 안 된다
    assert "secret_note" not in 문서들[0]
```

여기서 확인하는 것이 성공 여부가 아니라 **응답 스키마가 내부 필드를 실제로 걸러내는지**라는 점이 중요합니다. 404 테스트에서도 상태 코드만 보면 예외 핸들러가 빠져도 통과하기 때문에 본문의 `code`와 `message`까지 확인합니다.

계층 의존 방향을 검사하는 테스트도 만들었습니다.

```python
def test_api_does_not_import_repositories_or_models() -> None:
    offenders = _violations("api/v1", forbidden=("app.repositories", "app.models"))
    assert not offenders, "라우터가 repositories/models 를 직접 import 합니다. ..."
```

`ast`로 각 파일의 최상단 import 문만 읽어서 금지된 방향으로 부르는 자리를 모읍니다. "각 계층은 자기 바로 아래만 호출한다"는 규칙은 지키지 않아도 기능은 잘 돌기 때문에, 사람이 코드 리뷰로만 막으면 시간이 지나며 새어 나갑니다. 규칙을 테스트로 바꿔두면 빌드가 대신 잡아줍니다.

## 6. API 토큰과 과금

과금 단위는 호출 횟수가 아니라 토큰 수입니다. 공백, 줄바꿈, 문장부호도 전부 토큰입니다.

```text
한국어 · 글자  19자 · 어림 토큰  16 · 글자당 0.84 토큰
영어   · 글자  46자 · 어림 토큰  12 · 글자당 0.26 토큰
```

글자 수는 영어가 2배 이상 많은데 토큰은 더 적습니다. 한국어가 토큰을 많이 먹는다는 뜻이고, 프롬프트를 한국어로 길게 쓰면 비용이 빨리 올라갑니다. 다만 이 값은 어림이고, 정확한 수는 응답에 오는 `usage`로만 알 수 있습니다.

가격은 100만 토큰당 달러로 매겨지고, **출력이 입력보다 5배 비쌉니다.** 답을 길게 쓰게 만드는 프롬프트가 비용에 더 크게 작용합니다.

```text
1회 질의 :  3.92 원
하루 요청 횟수를 모두 사용하면 : 784.0원
600이 캐시 읽기 :  3.16 원
절감 :  19.39 %
```

한 번에 4원이 안 되지만 하루 한도인 200회를 다 쓰면 784원이고, 사용자가 늘면 그대로 곱해집니다. 매번 똑같이 들어가는 부분을 캐시에 올려두면 그 몫은 1/10 값으로 계산됩니다.

한도는 두 가지를 구분합니다. `spend limit`은 누적 금액이라 다 쓰면 멈추고, `rate limit`은 분당 속도 제한이라 돈을 막지는 않습니다. 한도에 걸린 요청은 HTTP `429`로 돌아오는데, 앞서 예외 계층을 설계할 때 만들어 둔 `RateLimited`가 바로 이 자리에 쓰입니다.

## 오늘의 소감

한화 내일 아카데미 ICT부문 과정에서 지금까지는 기능을 만드는 쪽에 시간을 썼는데, 오늘은 **만든 것이 무너지지 않게 붙잡아두는 장치**를 여러 개 배웠습니다. 스키마 변경 이력을 파일로 남기는 Alembic, 계층 규칙을 검사하는 테스트, 어댑터를 팩토리 한 곳으로만 들어오게 막는 규칙이 모두 같은 성격입니다.

공통점은 **지키지 않아도 당장은 잘 돌아간다**는 것입니다. 라우터가 리포지토리를 직접 불러도 화면은 정상으로 보이고, 서비스가 SDK를 직접 import 해도 기능은 동작합니다. 그래서 사람이 기억으로 지키는 대신 규칙 자체를 테스트로 옮겨 둡니다.

비용 계산도 같은 맥락입니다. 호출 한 번이 4원이라 작아 보이지만 상한과 계측을 나중에 붙이려면 모든 호출 자리를 다시 고쳐야 합니다. `LLMResult`에 응답 문자열뿐 아니라 토큰 수와 비용, 지연 시간까지 함께 담아두는 이유를 이해하게 됐습니다.

다음 포스팅에서는 이어서 배울 내용을 정리해보겠습니다.

\#한화내일아카데미 \#한화시스템 \#AI개발자 \#K뉴딜아카데미 \#국비지원교육 \#개발자이직 \#부트캠프후기 \#AI에이전트 \#백엔드개발 \#파이썬프로젝트

참고 링크 : https://blog.naver.com/dldl8819/224413930997
