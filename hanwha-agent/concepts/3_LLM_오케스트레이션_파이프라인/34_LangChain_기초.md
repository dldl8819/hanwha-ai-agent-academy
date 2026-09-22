# LangChain 기초 — LCEL과 Runnable

[[33_RAG_개요]]의 그림에서 Orchestration 자리에 들어가는 것이 LangChain이다. 지금까지 SDK를 직접 불러 만든 것과 무엇이 다른지부터 본다.

## SDK를 직접 부르면 손으로 해야 하는 것들

```python
response = client.messages.create(
    model=settings.llm_model,
    max_tokens=settings.max_tokens,
    messages=[{"role": "user", "content": "..."}],
)
print(response.content[0].text)
```

[[25_Claude_API_호출]]에서 만든 코드다. 호출 하나면 이것으로 충분하다. LangChain이 대신해 주는 것은 그 주변이다.

| SDK 직접 | LangChain |
| --- | --- |
| `messages` 리스트를 손으로 조립 | `ChatPromptTemplate`이 만든다 |
| `"".join(b.text for b in ...)` 로 텍스트 꺼내기 | `StrOutputParser`가 꺼낸다 |
| 질문 여러 개를 `for` 문으로 하나씩 | `.batch()` |
| 스트리밍을 직접 처리 | `.stream()` · `.astream()` |
| `try/except`로 재호출 작성 | `.with_retry()` |
| 모델이 죽으면 `if/else`로 다른 모델 | `.with_fallbacks()` |
| 함수를 순서대로 직접 호출 | 파이프(`|`)로 연결 |

오른쪽 항목들은 우리가 이미 손으로 만든 것과 겹친다. [[28_가드와_재시도_폴백]]의 재시도 루프가 `.with_retry()`이고, 폴백이 `.with_fallbacks()`다. **직접 만들어 본 다음에 보면 무엇을 대신해 주는지가 보인다.**

### 설치

```bash
python -m pip install "langchain-core==1.6.2" "langchain-anthropic==1.7.1" "tenacity==9.1.4"
```

| 패키지 | 역할 |
| --- | --- |
| `langchain-core` | LCEL과 Runnable 등 뼈대 |
| `langchain-anthropic` | LCEL 안에서 Claude를 부르는 어댑터 |
| `tenacity` | 재시도 라이브러리. 버전을 고정하려고 명시적으로 적었다 |

버전을 `==`로 박은 것은 LangChain이 버전마다 문법이 꽤 바뀌기 때문이다([[31_관측과_실행_기록]]의 LangFuse v2/v4 차이와 같은 이유).

## ChatAnthropic — 키를 직접 넘겨야 한다

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-haiku-4-5",
    max_tokens=500,
    api_key=settings.anthropic_api_key.get_secret_value(),
)
```

`api_key`를 명시적으로 넘기는 것에 이유가 있다. **`pydantic-settings`는 `.env`를 읽어 `Settings` 객체에만 담고 `os.environ`에는 넣지 않는다.** LangChain은 기본적으로 환경변수에서 키를 찾으므로, 이 줄이 없으면 `.env`에 키가 있어도 못 찾는다.

| 파라미터 | 뜻 |
| --- | --- |
| `model` | 어떤 모델을 부를지 |
| `max_tokens` | 출력 토큰 상한. SDK에서 필수였던 그 값이다 |
| `temperature` | 낮으면 일관된 출력, 높으면 다양한 출력 |

## AIMessage — 돌려받는 것은 문자열이 아니다

```python
response = llm.invoke("RAG가 무엇인지 한 문장으로 설명해주세요.")
print(response)
```

```text
content='# RAG (Retrieval-Augmented Generation)\n\n**외부 데이터베이스에서 관련 정보를 검색해
불러온 후, 이를 바탕으로 AI 모델이 더 정확하고 최신의 답변을 생성하는 기술입니다.**'
additional_kwargs={}
response_metadata={'id': 'msg_011CfHw3qGRDyrDEnGjx6RcF', 'model': 'claude-haiku-4-5-20251001',
                   'stop_reason': 'end_turn', 'usage': {...}, 'model_provider': 'anthropic'}
id='lc_run--01a0c79b-...'
tool_calls=[] invalid_tool_calls=[]
usage_metadata={'input_tokens': 31, 'output_tokens': 89, 'total_tokens': 120,
                'input_token_details': {'cache_read': 0, 'cache_creation': 0, ...}}
```

| 필드 | 무엇 |
| --- | --- |
| `content` | 실제 답변 본문 |
| `usage_metadata` | 입력·출력 토큰. **[[32_사용량과_원가_기록]]의 `UsageLog`에 그대로 들어갈 값이다** |
| `response_metadata` | 모델명·중단 이유 등 원본 응답 정보 |
| `tool_calls` | 도구 호출 정보 (아직 안 쓴다) |

`model`에 `claude-haiku-4-5`를 넣었는데 `response_metadata`에는 `claude-haiku-4-5-20251001`이 찍힌다. 별칭으로 부르면 **그 시점의 실제 버전**이 응답에 담겨 온다. 기록에 남겨야 할 것은 이쪽이다.

## ChatPromptTemplate

같은 문장에서 주제만 바뀌는 질문이 반복되면 템플릿으로 뺀다.

```python
prompt = ChatPromptTemplate.from_template(
    "{topic}에 대해 비전공자도 이해할 수 있도록 쉽게 설명해주세요."
)
```

역할과 질문을 나누려면 메시지 목록으로 만든다.

```python
prompt2 = ChatPromptTemplate.from_messages([
    ("system", "너는 IT 박사님이야. 초보자가 이해하기 쉽게 설명해줘"),
    ("human", "{question}"),
])
```

`system`은 매 요청 같은 것(역할·규칙), `human`은 매 요청 달라지는 것이다. [[26_프롬프트_설계와_컨텍스트]]에서 `answer_system.md`를 파일로 빼고 사용자 메시지만 매번 조립한 것과 같은 구분이다.

조립 결과가 궁금하면 **프롬프트만 `invoke`한다.** 모델을 부르지 않으므로 돈이 들지 않는다.

```python
msgs = prompt2.invoke({"question": "RAG가 뭔가요?"})
for m in msgs.messages:
    print(f"  {m.type:<7} {m.content}")
```

```text
  system  너는 IT 박사님이야. 초보자가 이해하기 쉽게 설명해줘
  human   RAG가 뭔가요?
```

## LCEL — 파이프로 잇는다

```python
chain = prompt | llm | parser
```

`prompt`의 결과를 `llm`에 넘기고, 그 결과를 `parser`에 넘긴다는 뜻이다. 손으로 쓰면 이렇게 된다.

```python
msgs = prompt.invoke({"question": "RAG가 무엇인가요?"})
response = llm.invoke(msgs)
text = parser.invoke(response)
```

`|`로 이으면 중간 변수가 사라지고 **흐름이 한 줄로 보인다.** LCEL(LangChain Expression Language)이라고 부른다.

파이프로 이을 수 있는 것은 LangChain 부품만이 아니다. 내가 만든 평범한 함수도 들어가는데, 조건이 하나 있다 — [[35_체인_합성]]에 정리했다.

### 실습에서 만난 오류

```python
response = chain.invoke(
    "topic": "RAG"
)
```

```text
SyntaxError: invalid syntax
```

`invoke`에 넘기는 것은 **딕셔너리 하나**다. 중괄호를 빼면 파이썬 문법 자체가 성립하지 않는다.

```python
response = chain.invoke({"topic": "RAG"})
```

템플릿의 `{topic}`만 보고 중괄호를 이미 쓴 것으로 착각하기 쉬운 자리다.

## Output Parser

파서가 없으면 `AIMessage`가, 있으면 문자열이 나온다.

```python
chain_raw = prompt | fake                       # AIMessage
chain_str = prompt | fake | StrOutputParser()   # 본문만
```

```text
파서 없음 : AIMessage → '두 번째 답'
파서 있음 : TextAccessor → '첫 번째 답'
str 인가   : True
```

`type()`에 `TextAccessor`라고 찍히지만 **`str`의 하위 클래스**라 문자열처럼 그대로 쓰면 된다. 여기서 놀라서 `str()`로 다시 감쌀 필요가 없다.

## Runnable — 부품이 모두 같은 방식으로 실행된다

LangChain의 핵심 부품들은 Runnable이라는 공통 규약을 따른다. 그래서 `|`로 이어 붙일 수 있고, 무엇이든 같은 메서드로 실행된다.

| 메서드 | 하는 일 |
| --- | --- |
| `invoke()` | 입력 하나 → 출력 하나 |
| `batch()` | 입력 여러 개 → 출력 여러 개 |
| `stream()` / `astream()` | 생성되는 대로 조각으로 받는다 |

[[23_포트와_어댑터]]의 `LLMPort`와 성격이 같다. **같은 모양으로 부를 수 있으면 갈아 끼울 수 있다.**

```python
print("invoke :", chain_fake.invoke({"topic": "RAG"}))
print("batch  :", chain_fake.batch([
    {"topic": "RAG"}, {"topic": "Embedding"}, {"topic": "Vector DB"},
]))
```

```text
invoke : 두 번째 답
batch  : ['첫 번째 답', '두 번째 답', '첫 번째 답']
```

### 스트리밍

답이 길면 다 만들어질 때까지 기다리는 대신 오는 대로 보여준다.

```python
for chunk in chain.stream({"topic": "RAG"}):
    print(chunk, end="", flush=True)
```

`end=""`로 줄바꿈을 막고 `flush=True`로 버퍼를 바로 비워야 조각이 실시간으로 보인다. 둘 중 하나만 빠져도 한 번에 몰려서 출력된다.

## 가짜 모델 — 돈을 쓰지 않고 체인을 확인한다

`langchain-core`가 테스트용 모델을 공식으로 준다. [[29_골든셋_회귀테스트]]에서 손으로 만든 `StubLLM`과 같은 역할인데, 이쪽은 만들어져 있다.

| 모델 | 용도 |
| --- | --- |
| `FakeListChatModel(responses=[...])` | 답 목록을 **돌려가며** 내놓는다. `invoke` · `batch` 확인 |
| `GenericFakeChatModel(messages=iter([...]))` | `AIMessage` 이터레이터. 스트리밍 확인 |
| `ParrotFakeChatModel()` | 받은 것을 그대로 돌려준다 |

```python
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel, GenericFakeChatModel, ParrotFakeChatModel,
)
```

세 가지를 직접 써 보고 알게 된 것.

- **`FakeListChatModel`은 목록을 순환한다.** 답이 2개인데 3건을 물으면 첫 번째로 돌아간다. 위 `batch` 출력에서 `['첫 번째 답', '두 번째 답', '첫 번째 답']`이 나온 이유다. 실제 모델처럼 매번 다른 답이 오는 것으로 착각하면 안 된다
- **`ParrotFakeChatModel`은 마지막 메시지만 돌려준다.** 전체 프롬프트가 아니라 `human` 메시지만 나온다. 조립된 프롬프트 전체를 보려면 앞서처럼 프롬프트만 `invoke`한다
- 가짜 모델도 돌려주는 것은 **진짜 `AIMessage`**다. 그래서 파서와 체인이 그대로 붙는다

## RunnableLambda — 내 함수를 체인에 끼운다

직접 만든 함수는 Runnable이 아니라 `|`로 못 잇는다. `RunnableLambda`로 감싸면 된다.

```python
def lookup(payload: dict) -> str:
    known = {"DOC-HR-014", "DOC-PU-007", "DOC-SE-003"}
    if payload["doc_id"] not in known:
        raise ValueError("모르는 문서...")
    return f"{payload['doc_id']} 조회 완료"

lookup_chain = RunnableLambda(lookup)
```

데코레이터로도 쓸 수 있다.

```python
from langchain_core.runnables import chain

@chain
def tag_grade(d: dict) -> dict:
    return {**d, "grade": "일반"}
```

## RunnablePassthrough — RAG로 이어지는 자리

RAG에서는 질문 하나를 두 갈래로 쓴다. 한쪽은 검색에 넣고, 다른 한쪽은 프롬프트에 그대로 넣는다.

```text
	Question
       ├───────────────┐
       ▼               ▼
  Retriever        원래 질문
       │               │
    Context            │
       └───────┬───────┘
               ▼
             Prompt ──▶ Claude ──▶ Parser
```

딕셔너리로 묶으면 두 갈래가 동시에 실행되고 결과가 하나의 딕셔너리로 합쳐진다.

```python
{
    "context": retriever,               # 질문을 받아 검색 결과를 낸다
    "question": RunnablePassthrough(),  # 받은 값을 그대로 흘려보낸다
}
```

```text
context  : [검색결과] 부산 출장 숙박비 → 국내출장 여비 규정 제12조
question : 부산 출장 숙박비
```

이 딕셔너리가 그대로 `ChatPromptTemplate`의 `{context}` · `{question}` 자리에 들어간다. 다음은 `retriever` 자리에 진짜 검색을 넣는 일이다.

갈래를 만드는 도구는 `RunnablePassthrough()` 하나가 아니다. 받은 딕셔너리에 키를 더하는 `.assign()`, 갈래를 모으는 `RunnableParallel`까지 세 가지를 [[35_체인_합성]]에 정리했다.

참고: sandbox/w4/day02/01.langchain기초.ipynb, sandbox/w4/day02/api_01.py
