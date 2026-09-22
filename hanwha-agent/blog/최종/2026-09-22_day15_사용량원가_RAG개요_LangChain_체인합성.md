# [한화 내일 아카데미 ICT부문] 15일차 후기 — 사용량·원가 기록, RAG 개요, LangChain과 체인 합성

지난 포스팅에서는 LangFuse로 실행을 관측하고 `run_id`로 실행 기록을 남기는 것까지 다뤘습니다. 15일차에는 그 기록에 **돈**을 붙였습니다. 호출 한 번이 토큰을 얼마나 쓰고 원가가 얼마인지 표에 남기는 작업입니다.

그리고 오후에는 방향이 크게 바뀌었습니다. 지금까지는 모델 하나를 부르는 구조였는데, RAG가 무엇인지 전체 그림을 보고 LangChain으로 체인을 만드는 데까지 들어갔습니다. 한화 내일 아카데미 ICT부문 과정 15일차에 학습한 내용을 순서대로 정리해봅니다.

1. 사용량과 원가를 남기는 표
2. 기록하는 자리 — 검증 전입니다
3. 사람별 집계 — 출력이 비용의 절반을 넘습니다
4. 컬럼 이름 바꾸기 — autogenerate를 쓰면 안 되는 경우
5. RAG 개요 — 준비와 질의는 다른 시간에 돕니다
6. LangChain 기초와 LCEL
7. 가짜 모델로 체인 확인하기
8. 체인 합성 — 갈래 만들기

## 1. 사용량과 원가를 남기는 표

14일차에 만든 `runs` 테이블은 **질문 한 건**을 남깁니다. 오늘 만든 `usage_logs`는 **호출 한 번**을 남깁니다. 같아 보이지만 다릅니다.

| 표 | 단위 | 재시도가 2회 돌면 |
| --- | --- | --- |
| `runs` | 질문 한 건 | 1행 |
| `usage_logs` | 모델 호출 한 번 | 2행 |

재시도가 돌면 한 `run_id`에 사용량 행이 여러 개 붙습니다. 재시도 한 번이 곧 과금 한 번이기 때문입니다.

```python
class UsageLog(Base, TimestampMixin):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    model: Mapped[str] = mapped_column(String(64))

    input_tok: Mapped[int] = mapped_column(Integer, default=0)
    cache_tok: Mapped[int] = mapped_column(Integer, default=0)
    output_tok: Mapped[int] = mapped_column(Integer, default=0)

    cost_krw: Mapped[float] = mapped_column(Float, default=0.0)
    occurred_at: Mapped[datetime] = mapped_column(default=datetime.now)
```

컬럼마다 이유가 있습니다.

| 컬럼 | 왜 남기는가 |
| --- | --- |
| `run_id` | `runs.id`를 가리키는 FK입니다. 질문 한 건에 호출 여러 건을 묶습니다 |
| `model` | 모델마다 단가가 다릅니다. 나중에 모델을 바꿨을 때 비용이 어떻게 변했는지 이 컬럼이 없으면 알 수 없습니다 |
| `input_tok` / `output_tok` | 출력이 입력보다 5배 비싸서 합계만으로는 원가를 설명할 수 없습니다 |
| `cost_krw` | 계산해서 저장합니다. 나중에 단가표가 바뀌어도 그때의 원가가 보존됩니다 |

`cost_krw`를 조회할 때마다 계산하지 않고 저장해 두는 이유가 중요합니다. 단가와 환율은 바뀝니다. 저장해 두지 않으면 작년 사용량을 올해 단가로 다시 계산하게 됩니다. 11일차에 `sources`를 JSON으로 통째로 남긴 것과 같은 판단입니다. **그때 이렇게 됐다는 스냅샷**입니다.

`TimestampMixin`이 `created_at`을 이미 주는데 `occurred_at`을 따로 둔 것도 이유가 있습니다. 기록을 나중에 몰아서 적재하는 경우 "행이 만들어진 시각"과 "호출이 일어난 시각"이 달라지기 때문입니다.

## 2. 기록하는 자리 — 검증 전입니다

여기가 오늘 배운 것 중에 가장 중요한 자리였습니다.

```python
result = llm.answer(question=prompt, contexts=NO_CONTEXTS, user=DEFAULT_USER)

_record_usage(run_id, result)      # ← 검증하기 전에 기록합니다

try:
    data = _extract_json(result.text)
    AnswerOut.model_validate(data)
except ValidationError as e:
    ...
    continue
```

**이 순서가 전부입니다.** 응답이 형식을 어겨서 버려지더라도 그 호출의 토큰은 이미 과금됐습니다. 통과한 호출만 기록하면 재시도로 나간 비용이 장부에서 통째로 빠집니다.

실제로 확인해보면 `attempts`와 행 수가 정확히 같습니다.

```text
① 한 번에 성공        RUN-8882  attempts=1  usage_logs 1건
   WARNING  app.services.chat_service 스키마 위반 1/3회 : sources: Field required
② 한 번 실패 후 성공  RUN-8883  attempts=2  usage_logs 2건
```

기록 함수는 실패해도 조용히 넘어가게 만들었습니다.

```python
def _record_usage(run_id: str, result) -> None:
    try:
        with session_scope() as session:
            session.add(UsageLog(...))
    except Exception as e:
        log.warning("사용 기록 실패(무시하고 계속): %s", e)
```

14일차의 관측 어댑터와 같은 판단입니다. **기록에 실패해도 답변은 나가야 합니다.** 다만 조용히 넘어가는 데는 대가가 있었습니다. 리비전을 적용하기 전에는 이 경고만 찍히고 테스트가 전부 통과했습니다. 통과하는데 행이 안 쌓이면 이 자리를 먼저 봐야 한다는 것을 알게 됐습니다.

## 3. 사람별 집계 — 출력이 비용의 절반을 넘습니다

`runs`와 `users`까지 조인하면 사람별로 얼마를 썼는지 나옵니다.

```python
per_person = session.execute(
    select(User.name, User.emp_no, func.count(UsageLog.id), func.sum(UsageLog.cost_krw))
    .join(Run, UsageLog.run_id == Run.id)
    .join(User, Run.user_id == User.id)
    .group_by(User.name, User.emp_no)
).all()
```

```text
***사람별 결과***
 김민준 (2019-0412) : 51건 135.3원
***토큰 비중***
 입력 61200, 출력 15300
 출력 비중 : 20.0 %
```

조인이 두 단계인 이유는 **`usage_logs`에 `user_id`가 없기 때문**입니다. 호출은 질문에 속하고 질문은 사람에 속합니다. 사용량 표에 사람을 직접 달아두면 조회는 빨라지지만, 같은 사실이 두 곳에 적혀 어긋날 수 있습니다. 지금 규모에서는 조인이 맞다고 배웠습니다.

출력 비중을 따로 보는 이유는 단가 때문입니다. 토큰 수로는 출력이 20%지만 단가가 5배라 **비용으로는 절반 이상**이 출력에서 나옵니다. 비용을 줄이려면 `max_tokens`를 조이거나 "짧게 답하라"를 프롬프트에 넣는 쪽이, 입력을 줄이는 것보다 효과가 큽니다.

## 4. 컬럼 이름 바꾸기 — autogenerate를 쓰면 안 되는 경우

컬럼 이름을 `occured_at`(r 한 개)으로 잘못 적었던 것을 발견했습니다. 동작에는 문제가 없었습니다. 모델·리비전·실제 테이블이 **모두 같은 철자로 틀려 있었기 때문**입니다. 이런 오타는 에러로 드러나지 않고, 나중에 쿼리를 짜는 사람이 바른 철자로 적었다가 걸립니다.

고칠 때 `--autogenerate`를 쓰면 안 됩니다.

```python
op.drop_column("usage_logs", "occured_at")
op.add_column("usage_logs", sa.Column("occurred_at", sa.DateTime(), nullable=False))
```

autogenerate는 **이름이 바뀐 것을 알아보지 못합니다.** 없어진 컬럼 하나와 새로 생긴 컬럼 하나로 볼 뿐이라, 그대로 실행하면 기존 행의 값이 전부 사라집니다. 이름만 바꾸려면 손으로 적습니다.

```python
def upgrade() -> None:
    op.alter_column(
        "usage_logs", "occured_at",
        new_column_name="occurred_at",
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
```

`existing_type`과 `existing_nullable`은 바꾸려는 값이 아니라 **지금 그대로인 값**을 알려주는 인자입니다. 일부 DB는 컬럼을 고칠 때 전체 정의를 다시 써야 해서, Alembic이 문장을 만들려면 이 정보가 필요합니다.

적용 전후로 행 수가 35건 그대로였습니다. 이름만 바뀌고 값은 남았습니다. 그리고 **먼저 만든 리비전의 `occured_at`은 고치지 않았습니다.** 이미 적용한 사람의 DB는 그 이름으로 만들어져 있어서, 과거 리비전을 고쳐 쓰면 기록과 실제가 어긋납니다. 마이그레이션 이력은 무엇이 있었는지를 남기는 기록이지 현재 상태를 적는 문서가 아니라고 배웠습니다.

## 5. RAG 개요 — 준비와 질의는 다른 시간에 돕니다

오후부터 방향이 바뀌었습니다. RAG는 **R**etrieval, **A**ugmented, **G**eneration의 약자입니다. 검색해서 가져오고, 가져온 것을 프롬프트에 붙여서, 모델이 그것을 근거로 답하게 하는 방식입니다.

모델은 사내 규정을 학습한 적이 없습니다. 그런데도 물어보면 답합니다. 시키지 않으면 그럴듯한 숫자를 만들어 냅니다. 이게 할루시네이션이고, **모델을 바꾸거나 프롬프트를 다듬는 것으로는 없앨 수 없습니다.** 모델에게 없는 정보이기 때문입니다.

RAG는 문제를 다르게 풉니다. 모델에게 규정을 외우게 하는 대신, 물어볼 때마다 찾아서 보여줍니다. 모델을 다시 학습시키지 않아도 **문서만 바꾸면 답이 바뀝니다.** 규정이 개정되면 파일을 갈아 끼우면 됩니다.

전체는 11단계입니다.

```text
                  [ 원본 데이터 ]
           PDF / DOCX / HWP / HTML / DB / API
                        │
                 ① Document Loading      문서를 읽어 들인다
                        │
                 ② Parsing / Cleaning    머리글·바닥글을 걷어낸다
                        │
                    ③ Chunking           검색 단위로 자른다
                        │
                   ④ Embedding           텍스트를 벡터로 바꾼다
                        │
                ⑤ Vector Database        PostgreSQL + pgvector
                        │
════════════════════════╪══════════════════════════════════
       여기까지가 문서를 미리 준비하는 과정
════════════════════════╪══════════════════════════════════
                        │
사용자 질문              │
       │                │
  ⑥ Query Processing    │   질문도 같은 방식으로 벡터로 바꾼다
       │                │
       └───────────────▶│
                   ⑦ Retrieval           가까운 벡터를 찾는다
                        │
               ⑧ Filter / Reranking      권한·최신성으로 거른다
                        │
                  ⑨ Prompt 구성          질문 + 검색 문서
                        │
                     ⑩ LLM
                        │
                 ⑪ Answer + Citation     답 + 출처
```

**①~⑤와 ⑥~⑪은 다른 시간에 돕니다.** 앞쪽은 문서를 올릴 때 한 번, 뒤쪽은 질문할 때마다입니다. 이 경계를 놓치면 질문할 때마다 PDF를 파싱하는 느리고 비싼 구조가 됩니다.

단계마다 잘못됐을 때 어떻게 되는지도 정리했습니다.

| 단계 | 여기서 잘못되면 |
| --- | --- |
| ② Parsing | 표가 뭉개지거나 머리글이 섞여, 검색은 맞는데 답이 이상해집니다 |
| ③ Chunking | 크면 관계없는 내용까지 실려 비싸지고, 작으면 문맥이 끊깁니다 |
| ⑦ Retrieval | 엉뚱한 문서를 가져오면 그 뒤가 아무리 좋아도 답이 틀립니다 |
| ⑧ Filter | 권한이 없는 문서가 통과하면 보안 사고가 됩니다 |
| ⑪ Citation | 출처가 없으면 사용자가 답을 확인할 방법이 없습니다 |

⑧과 ⑪은 이미 만든 것과 이어집니다. 12일차에 `doc_id`를 `Literal`로 묶어 등록된 문서만 인용하게 한 것이 ⑧의 화이트리스트에 해당하고, `sources`에 `version`과 `locator`를 담게 한 것이 ⑪입니다. 모르고 만든 게 아니라 RAG의 자리를 미리 채워둔 것이었습니다.

## 6. LangChain 기초와 LCEL

LangChain은 LLM API 하나만 부르면 필요하지 않습니다. 중간 단계가 늘어날 때 필요해집니다. 먼저 모델을 직접 만들어 불러봤습니다.

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-haiku-4-5",
    max_tokens=500,
    api_key=settings.anthropic_api_key.get_secret_value(),
)
```

`api_key`를 직접 넘기는 부분에서 걸렸습니다. **pydantic-settings는 `.env`를 읽어 `Settings` 객체에만 담고 `os.environ`에는 넣지 않습니다.** 라이브러리가 환경변수에서 키를 알아서 찾을 거라고 생각하면 인증 오류가 납니다.

돌아오는 것은 문자열이 아니라 `AIMessage` 객체입니다. 본문 말고도 토큰 사용량 같은 정보가 같이 들어 있습니다. 오전에 만든 `usage_logs`가 받는 값이 이 자리에서 나옵니다.

프롬프트에서 반복되는 부분은 템플릿으로 뺍니다.

```python
prompt = ChatPromptTemplate.from_template(
    "{topic}에 대해 비전공자도 이해할 수 있도록 쉽게 설명해주세요."
)
chain = prompt | llm | StrOutputParser()
response = chain.invoke({"topic": "RAG"})
```

`|`로 잇는 방식을 LCEL(LangChain Expression Language)이라고 부릅니다. 손으로 쓰면 중간 변수가 세 개 생기는데, 파이프로 이으면 **흐름이 한 줄로 보입니다.**

여기서 실수를 하나 했습니다.

```python
response = chain.invoke(
    "topic": "RAG"
)
```

```text
SyntaxError: invalid syntax
```

`invoke`에 넘기는 것은 **딕셔너리 하나**입니다. 중괄호를 빼면 파이썬 문법 자체가 성립하지 않습니다. 템플릿의 `{topic}`만 보고 중괄호를 이미 쓴 것으로 착각하기 쉬운 자리였습니다.

## 7. 가짜 모델로 체인 확인하기

체인 모양만 확인하려는데 매번 진짜 모델을 부르면 돈이 나갑니다. `langchain-core`가 테스트용 모델을 공식으로 줍니다.

| 모델 | 용도 |
| --- | --- |
| `FakeListChatModel(responses=[...])` | 답 목록을 돌려가며 내놓습니다 |
| `GenericFakeChatModel(messages=iter([...]))` | `AIMessage` 이터레이터. 스트리밍 확인 |
| `ParrotFakeChatModel()` | 받은 것을 그대로 돌려줍니다 |

13일차에 골든셋을 만들면서 손으로 짰던 `StubLLM`과 같은 역할인데, 이쪽은 이미 만들어져 있습니다. 써보면서 알게 된 것이 몇 가지 있습니다.

```text
invoke : 두 번째 답
batch  : ['첫 번째 답', '두 번째 답', '첫 번째 답']
```

**`FakeListChatModel`은 목록을 순환합니다.** 답이 2개인데 3건을 물으면 첫 번째로 돌아갑니다. 실제 모델처럼 매번 다른 답이 오는 것으로 착각하면 안 됩니다.

파서가 있고 없고의 차이도 확인했습니다.

```text
파서 없음 : AIMessage → '두 번째 답'
파서 있음 : TextAccessor → '첫 번째 답'
str 인가   : True
```

`type()`에 `TextAccessor`라고 찍히지만 **`str`의 하위 클래스**라 문자열처럼 그대로 쓰면 됩니다. 여기서 놀라서 `str()`로 다시 감쌀 필요가 없습니다.

## 8. 체인 합성 — 갈래 만들기

여기까지 만든 체인은 전부 한 줄로 늘어서 있었습니다. 그런데 실제 RAG는 이 모양이 안 됩니다. **갈래가 필요합니다.**

```text
                    "부산 출장 숙박비?"
                              │
                   ┌──────────┴──────────┐
                   ▼                     ▼
              Retriever        RunnablePassthrough
                   │                     │
                   ▼                     ▼
           출장비규정 제8조       "부산 출장 숙박비?"
                   │                     │
                   ▼                     ▼
                context               question
                   └──────────┬──────────┘
                              ▼
         dict {"context": [...], "question": "부산 출장 숙박비?"}
```

검색기에는 질문을 넣어야 답이 나옵니다. 그런데 프롬프트에도 질문 원문이 그대로 있어야 합니다. `{context}`만 넘기면 모델은 **무엇을 묻는지 모른 채** 문서만 받습니다.

갈래를 만드는 도구가 세 가지입니다.

| 도구 | 하는 일 |
| --- | --- |
| `RunnablePassthrough()` | 받은 값을 그대로 흘려보냅니다 |
| `RunnablePassthrough.assign(키=단계)` | 받은 딕셔너리는 두고 키를 더합니다 |
| `RunnableParallel(a=…, b=…)` | 갈래를 동시에 돌려 딕셔너리로 모읍니다 |

이름이 비슷해서 헷갈리는데 앞의 둘은 다른 것입니다. `RunnablePassthrough()`는 값을 통과시키고, `.assign()`은 값을 불립니다.

```python
enrich = RunnablePassthrough.assign(
    doc_id=lambda d: "DOC-HR-011",
    grade=lambda d: "일반",
)
print(enrich.invoke({"question": "부산 출장 일비는?"}))
```

```text
{'question': '부산 출장 일비는?', 'doc_id': 'DOC-HR-011', 'grade': '일반'}
```

넘긴 것은 `question` 하나뿐인데 결과에는 셋이 다 있습니다. **`question`이 살아 있다**는 게 핵심입니다. 그래서 뒤에서 그대로 쓸 수 있습니다.

```python
line = enrich | RunnableLambda(lambda d: f"[{d['doc_id']}/{d['grade']}] {d['question']}")
print(line.invoke({"question": "부산 출장 일비는?"}))
```

```text
[DOC-HR-011/일반] 부산 출장 일비는?
```

파이프에 대해서도 규칙을 하나 확인했습니다. 평범한 함수끼리는 이어지지 않습니다.

```text
함수끼리 : unsupported operand type(s) for |: 'function' and 'function'
```

`|`는 **왼쪽 객체의 `__or__`가 처리합니다.** 평범한 함수에는 `__or__`가 없으니 파이썬이 할 수 있는 게 없습니다. 그런데 맨 앞 하나만 감싸면 나머지는 그대로 들어갑니다.

```python
pipeline = RunnableLambda(build_prompt) | call_llm | parser
print(pipeline.invoke("부산 출장 일비는?"))
```

```text
{'answer': '출장 일비는 1일 3만원입니다.', 'doc_id': 'DOC-HR-012'}
```

`call_llm`과 `parser`는 감싸지 않았는데 들어갔습니다. **사슬의 첫 고리만 Runnable이면 됩니다.**

마지막으로 `batch`의 기본값을 확인했습니다. 입력 4건 중 하나가 잘못된 문서 번호일 때입니다.

```text
기본값 : 모르는 문서... → 결과를 하나도 못 받는다
```

**한 건이 실패하면 전체가 실패합니다.** 3건은 멀쩡한데 하나도 못 받습니다. `return_exceptions=True`를 주면 실패한 자리에 예외 객체가 담긴 채로 전부 돌아옵니다.

```text
  성공  DOC-HR-012   DOC-HR-012 조회 완료
  실패  DOC-XX-999   모르는 문서...
  성공  DOC-PU-007   DOC-PU-007 조회 완료
  성공  DOC-SE-002   DOC-SE-002 조회 완료
```

이 예제는 사전 조회라 실패해도 잃는 게 없지만, 모델을 부르는 체인이었다면 터지기 전에 나간 호출은 **이미 과금된 뒤**입니다. 결과를 못 받는다고 돈이 돌아오지는 않습니다. 오전에 배운 "검증 전에 기록한다"와 같은 이야기입니다.

## 이날의 소감

15일차는 오전과 오후가 다른 날이었습니다. 오전에는 만든 것에 계량기를 달았고, 오후에는 앞으로 만들 것의 지도를 봤습니다.

오전 내용에서 계속 나온 기준은 **"그때 이렇게 됐다"를 어떻게 남기는가**였습니다. 원가를 계산해서 저장하는 것, 검증 전에 기록하는 것, 과거 리비전을 고치지 않는 것이 전부 같은 이야기였습니다. 나중에 다시 계산하면 그때의 사실이 아니라 지금의 값이 나옵니다. 기록은 현재 상태를 적는 게 아니라 과거를 보존하는 것이라는 점을 세 번 다른 모양으로 배웠습니다.

오타 하나를 고치는 데 리비전을 손으로 적어야 했던 것도 남습니다. `--autogenerate`가 알아서 해줄 것 같은 자리인데, 오히려 그걸 믿으면 데이터가 날아갑니다. 도구가 무엇을 못 보는지 아는 것이 도구를 쓸 줄 아는 것과 같다는 생각을 했습니다.

오후의 RAG 11단계에서는 지금까지 만든 것들이 어디에 놓이는지가 보였습니다. `doc_id`를 `Literal`로 묶은 것이 ⑧ Filter였고, `sources`에 `locator`를 담은 것이 ⑪ Citation이었습니다. 어댑터의 `contexts` 인자를 처음부터 빈 리스트로 두고 만든 것도 여기서 이유가 드러났습니다. Retriever가 생기면 그 자리에 검색 결과를 넣기만 하면 됩니다.

LangChain은 문법이 낯설었지만 내용 자체는 새롭지 않았습니다. Runnable이 같은 방식으로 실행되는 것은 11일차 포트와 어댑터에서 배운 것과 같고, 가짜 모델은 13일차 골든셋의 `StubLLM`과 같습니다. **같은 모양으로 부를 수 있으면 갈아 끼울 수 있다**는 원칙이 라이브러리 안에도 그대로 있었습니다.

아직 체인은 틀만 있습니다. Retriever 자리에는 문자열을 만들어 내는 가짜 함수가 들어가 있습니다. 국비지원교육 과정이 절반을 지나면서 만드는 것보다 **자리를 정해두는 일**이 더 많아지고 있습니다.

다음 포스팅에서는 비어 있는 Retriever 자리를 채우는 내용을 정리해보겠습니다.

\#한화내일아카데미 \#한화시스템 \#AI개발자 \#K뉴딜아카데미 \#국비지원교육 \#개발자이직 \#부트캠프후기 \#RAG \#LLM \#AI에이전트 \#백엔드개발

참고 링크 : https://blog.naver.com/dldl8819/224420079457
