# AI-Native 애플리케이션

## 정의

**핵심 기능의 일부를 같은 입력에 같은 출력을 보장하지 않는 구성요소(LLM)에 맡기고, 그 전제 위에서 설계된 애플리케이션.**

LLM을 붙였다고 전부 AI-Native는 아니다. 기존 기능은 그대로 두고 챗봇 하나를 옆에 달아둔 것과, 문서 검색·요약·판단 같은 **핵심 동작 자체를 LLM이 수행하는 것**은 설계가 다르다. 후자는 "결과가 매번 달라질 수 있다"를 버그가 아니라 전제로 깔고 시작한다.

## 기존 애플리케이션과 무엇이 다른가

| | 기존 | AI-Native |
| --- | --- | --- |
| 같은 입력 | 항상 같은 출력 | 다를 수 있다 |
| 테스트 | 기댓값과 정확히 비교 | 정확히 비교하기 어렵다 |
| 실패 | 예외로 드러난다 | 그럴듯한 오답으로 조용히 지나간다 |
| 비용 | 대체로 일정 | 호출마다 토큰만큼 든다 |

가장 다루기 어려운 것은 세 번째다. 코드 오류는 예외가 나서 알 수 있지만, LLM이 없는 근거를 지어내면 형식은 멀쩡한 응답이 나온다. 그래서 **답을 만들어내는 부분과, 그 답을 검증·제한하는 부분을 따로 설계해야 한다.**

## 지금 프로젝트에 이미 들어 있는 장치들

수업 프로젝트에는 LLM을 붙이기 전인데도 이 전제를 염두에 둔 구조가 먼저 들어와 있다.

| 장치 | 위치 | 하는 일 |
| --- | --- | --- |
| `APP_MODE` (`mock` / `live`) | `.env`, `core/config.py` | 실제 호출 없이 정해진 응답으로 동작을 확인하는 모드 |
| `ALLOW_EXTERNAL_SEND` | `.env` | 외부(Slack 등)로 실제 전송할지 여부 |
| `DAILY_CALL_LIMIT`, `MAX_INPUT_CHARS` | `.env` | 호출 횟수·입력 길이 제한 |
| `GuardTripped`, `RateLimited` | `core/exceptions.py` | 입력 가드와 호출 한도를 예외로 다룬다 |
| `ApprovalRequired` | `core/exceptions.py` | 승인 없이 외부 실행을 시도하면 막는다 |
| 근거 문서 표시 | UI 킷 `source` 부품 | 답과 함께 어떤 문서의 어느 부분을 근거로 삼았는지 보여준다 |

[[05_예외_계층_설계]]에서 만들어 둔 `GuardTripped`·`RateLimited`·`ApprovalRequired`는 일반적인 웹 애플리케이션에는 잘 없는 예외다. LLM이 무엇을 만들어낼지 모른다는 전제에서 **"모델이 시킨 대로 바로 실행하지 않는다"**는 규칙을 코드 구조로 먼저 잡아둔 것이다.

UI 킷에 근거 문서(`source_html`)와 임계값 미달 표시(`weak=True`)가 부품으로 들어 있는 것도 같은 맥락이다([[16_Streamlit]]). 답이 틀릴 수 있으니 **사용자가 근거를 직접 확인할 수 있게** 화면을 설계한다.

## LLM API 키 다루기

### 키는 `.env`에만 둔다

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

`.gitignore`에 `.env`가 들어 있는지 **먼저** 확인한다. 이게 빠진 상태로 커밋하면 키가 저장소 이력에 남고, 나중에 파일을 지워도 과거 커밋에는 그대로 남는다. 공개 저장소라면 그 시점에 키를 폐기하고 다시 발급받는 것 말고는 방법이 없다.

### 키가 정상인지 확인

```bash
# Windows (cmd) — 본문 JSON의 따옴표를 \" 로 이스케이프한다
curl -s -w "\nHTTP %{http_code}\n" https://api.anthropic.com/v1/messages -H "x-api-key: 키" -H "anthropic-version: 2023-06-01" -H "content-type: application/json" -d "{\"model\":\"claude-haiku-4-5\",\"max_tokens\":16,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}"
```

```bash
# macOS — 작은따옴표로 감싸면 이스케이프가 필요 없다
curl -s -w "\nHTTP %{http_code}\n" https://api.anthropic.com/v1/messages -H "x-api-key: 키" -H "anthropic-version: 2023-06-01" -H "content-type: application/json" -d '{"model":"claude-haiku-4-5","max_tokens":16,"messages":[{"role":"user","content":"hi"}]}'
```

`HTTP 200`이면 키가 살아 있다. `401`이면 키 문제, `400`이면 본문 형식 문제다.

### 화면과 로그에 키가 찍히지 않게 — `mask`

설정에서 키는 `SecretStr`로 받는다([[03_Pydantic]]). `SecretStr`은 `print`하면 `**********`로 나와서 실수로 로그에 남는 것을 막아주고, 실제 값은 `.get_secret_value()`로만 꺼낼 수 있다. 확인용으로 앞 몇 글자만 보고 싶을 때를 위해 `core/config.py`에 함수를 하나 뒀다.

```python
def mask(secret: str | None, keep: int = 8) -> str:
    if not secret:
        return "(없음)"
    return f"{secret[:keep]}...({len(secret)}자)"
```

```python
settings = get_settings()
api_key = settings.anthropic_api_key
print("anthropic_api_key:", mask(api_key.get_secret_value() if api_key else None))
# anthropic_api_key: sk-ant-a...(108자)
```

앞 8자는 모든 키가 공유하는 접두어라 노출돼도 문제가 없고, **글자 수**를 같이 보여줘서 키가 잘렸는지 아닌지를 구분할 수 있다.

### 이렇게 쓰면 안 된다

```python
@router.get("/{doc_id}/summary")
def summ(doc_id: str):
    doc = ...  # DB 조회
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])   # 키가 코드에 박힌다
    resp = client.messages.create(model="claude-haiku-4-5", max_tokens=400,
                                  messages=[{"role": "user", "content": doc.text}])
    print("summary:", resp.content[0].text)                        # 응답을 print로 흘린다
```

- 키를 라우터에서 직접 꺼내면 설정 계층([[01_개발환경설정]])을 건너뛰게 되고, 키를 쓰는 자리가 코드 곳곳에 흩어진다
- 라우터가 LLM을 직접 부르면 서비스 계층이 비어버린다([[13_서비스_계층]]). 호출 한도·입력 가드·승인 같은 규칙을 걸 자리가 사라진다
- `print`로 응답을 흘리면 로그에 그대로 남는다. 로거를 쓴다([[06_로깅]])

## 비결정성을 눈으로 보기 — FlakyLLM

API를 실제로 부르기 전에, **같은 질문에 다른 답이 오는 상황**을 가짜 객체로 재현했다.

```python
import itertools

class FlakyLLM:
    def __init__(self, answers: list[str]) -> None:
        self._answers = list(answers)
        self._cycle = itertools.cycle(self._answers)   # 답 목록을 무한히 돌린다
        self.calls = 0

    def ask(self, question: str) -> str:
        self.calls += 1
        return next(self._cycle)
```

`itertools.cycle`은 리스트를 끝까지 쓰면 처음으로 돌아가며 무한히 반복하는 반복자다. 질문을 받아도 무시하고 답을 순서대로 하나씩 돌려준다.

```python
ANSWERS = [
    "숙박비는 1박 7만원입니다.",
    "국내출장 숙박비 한도는 1박당 7만원입니다.",
    "1박 기준 숙박비는 7만원까지 인정됩니다.",
]
EXPECTED = "숙박비는 1박 7만원입니다."

llm = FlakyLLM(ANSWERS)
for i in range(1, 4):
    answer = llm.ask("국내출장 숙박비 한도가 얼마인가요?")
    try:
        assert answer == EXPECTED
        print(f"{i}회차: 통과              | {answer}")
    except AssertionError:
        print(f"{i}회차: 실패 — 기대와 다름 | {answer}")
```

```text
1회차: 통과              | 숙박비는 1박 7만원입니다.
2회차: 실패 — 기대와 다름 | 국내출장 숙박비 한도는 1박당 7만원입니다.
3회차: 실패 — 기대와 다름 | 1박 기준 숙박비는 7만원까지 인정됩니다.

호출 횟수   : 3회 — 질문은 한 글자도 바뀌지 않았다
```

세 답은 **전부 내용이 맞다.** 틀린 것은 답이 아니라 `assert answer == EXPECTED`라는 검사 방식이다. 문장이 조금만 달라져도 실패하기 때문에, 지금까지 [[07_pytest]]에서 쓰던 "기댓값과 정확히 같은지" 방식은 LLM 응답에 그대로 쓸 수 없다.

가짜 LLM부터 만드는 이유는 두 가지다. 실제 API를 부르지 않으니 **비용과 네트워크 없이** 구조를 먼저 잡을 수 있고, 답이 항상 정해져 있어서 **테스트가 실패하면 원인이 우리 코드에만 있다.** `.env`의 `APP_MODE=mock`도 같은 목적이다.

## 아키텍처 원칙

### 구조 — LLM은 아키텍처가 아니라 부품 하나다

시스템의 뼈대(권한, 상태, 트랜잭션)는 코드로 짜고, **모델은 가장 바깥으로 밀어둔다.** 모델이 중심이 되면 모델이 바뀔 때 시스템 전체가 흔들린다.

모델은 6~12개월마다 바뀐다. 그래서 **공급자 SDK를 서비스 코드에 직접 박지 않고 인터페이스 뒤에 둔다.** 앞의 "이렇게 쓰면 안 된다" 예시에서 라우터가 `Anthropic(...)`을 직접 만든 것이 정확히 이 원칙을 어긴 형태다. `.env`에 `LLM_MODEL`을 빼 둔 것도 같은 이유로, 모델 이름이 코드에 흩어지지 않게 하기 위해서다.

### 순서 — 단일 호출 → 체인 → 라우팅 → 에이전트

처음부터 에이전트를 만들지 않는다. 호출 한 번이 제대로 도는 것을 확인하고, 여러 단계를 잇고(체인), 조건에 따라 갈래를 나누고(라우팅), 그다음에 모델이 스스로 도구를 고르는 단계(에이전트)로 간다. 뒤로 갈수록 실패 지점이 늘어나서, 앞 단계가 안정되지 않으면 원인을 짚을 수 없다.

### 규칙 — 자연어를 그대로 흘리지 않는다

- **출력은 스키마로 강제하고 파싱·검증한다.** 모델이 준 문자열을 그대로 믿지 않고 [[03_Pydantic]]으로 형태를 확인한다.
- **자연어를 그대로 다음 단계로 넘기지 않는다.** 중간 산출물은 구조화된 값이어야 한다. 문장을 문장으로 넘기면 오류가 조용히 누적된다.
- **모델이 보는 것은 프롬프트와 컨텍스트뿐이다.** 모델은 DB도 코드도 직접 보지 못한다. 넣어준 것만으로 답한다.

### 컨텍스트 엔지니어링

**무엇을, 얼마나, 어떤 순서로 넣을지가 설계의 본체다.** 모델이 가진 능력보다 무엇을 보여줬는지가 결과를 좌우한다. 문서 검색에서 어떤 청크를 몇 개나 어떤 순서로 붙일지가 곧 품질이다.

### 운영

- **단위 테스트로 회귀를 못 잡는다.** 같은 입력에 같은 값이 안 나오기 때문이다([[07_pytest]]의 정확 일치 방식이 통하지 않는 자리). 대신 **골든셋 정확도**가 빌드 통과 기준이 된다.
- **실행한 것을 재현할 수 없으므로 기록이 유일한 증거다.** 어떤 프롬프트로 무엇을 받았는지 남겨야 나중에 따질 수 있다([[06_로깅]]).
- **"나중에 최적화"가 안 통한다.** 호출 한 번마다 돈과 시간이 든다. 상한과 계측을 **처음부터** 걸어야 한다. `.env`의 `DAILY_CALL_LIMIT`·`MAX_INPUT_CHARS`, UI 킷의 `meta_footer`(소요 시간·토큰·비용 표시)가 그 자리다.

### 안전

- **외부에서 들어온 텍스트는 데이터이지 명령이 아니다.** 업로드된 문서나 사용자 입력에 "지금까지의 지시를 무시하라" 같은 문장이 들어 있어도 명령으로 취급하면 안 된다(프롬프트 인젝션).
- **도구에는 최소 권한만 준다.** 모델이 쓰는 도구가 할 수 있는 일의 범위를 좁힌다.
- **되돌릴 수 없는 행위 앞에는 사람을 세운다(HITL).** 메일 발송, 결재 상신, 외부 전송처럼 취소가 안 되는 동작은 승인 단계를 거친다. `ApprovalRequired` 예외와 `.env`의 `ALLOW_EXTERNAL_SEND`가 이 원칙을 코드로 옮겨둔 것이다.

참고: .env, backend/app/core/config.py, backend/app/core/exceptions.py, sandbox/w3/day03/00.api테스트.ipynb
