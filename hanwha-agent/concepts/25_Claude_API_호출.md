# Claude API 호출

[[22_AI_Native_애플리케이션]]에서 가짜 LLM으로 구조를 잡고, [[24_API_토큰과_과금]]에서 비용을 어림했다. 여기서 처음으로 **실제 API를 호출**한다.

## 설치

```bash
python -m pip install anthropic
```

실습 환경에서는 `anthropic 1.6.0`이 설치됐다.

## 필수 파라미터부터 확인

문서를 읽기 전에 SDK 코드에서 직접 뽑아볼 수 있다.

```python
import inspect
from anthropic.resources.messages import Messages

params = inspect.signature(Messages.create).parameters
required = [name for name, p in params.items()
            if p.default is inspect.Parameter.empty and name != "self"]
print(required)
```

```text
['max_tokens', 'messages', 'model']
```

`inspect.signature`는 함수의 인자 목록을 객체로 돌려준다. 기본값이 없는(`inspect.Parameter.empty`) 인자만 걸러내면 필수값이다. 일부러 `max_tokens`를 빼고 호출하면 이렇게 막힌다.

```text
TypeError
Missing required arguments; Expected either ('max_tokens', 'messages' and 'model')
or ('max_tokens', 'messages', 'model' and 'stream') arguments to be given
```

**`max_tokens`가 필수라는 점이 중요하다.** 출력 토큰 상한을 반드시 정해야 호출이 된다. 출력이 입력보다 5배 비싸다는 점([[24_API_토큰과_과금]])을 생각하면, SDK가 상한을 강제하는 것은 합리적이다.

## 첫 호출 — `sandbox/w3/day04/first_call.py`

```python
import sys
from pathlib import Path

# 이 파일 기준 3단계 위(hanwha-agent)의 backend 를 모듈 검색 경로에 넣는다
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

import anthropic
from app.core.config import get_settings

settings = get_settings()
key = settings.anthropic_api_key
if key is None:
    print(".env 의 anthropic_api_key 가 비어있습니다. 확인해주세요.")
    sys.exit(1)

client = anthropic.Anthropic(api_key=key.get_secret_value())

response = client.messages.create(
    model=settings.llm_model,
    max_tokens=settings.max_tokens,
    system="너는 사내 규정 질의 응답 도우미다. 근거가 없으면 없다고 말해야해.",
    messages=[
        {"role": "user", "content": "제주도 출장 숙박비 한도가 얼마인가요?"}
    ],
)

print("".join(b.text for b in response.content if b.type == "text"))
print("입력 토큰:", response.usage.input_tokens, ", 출력 토큰:", response.usage.output_tokens)
```

- `parents[3]`(복수)여야 한다. `parent`(단수)는 바로 위 폴더 하나를 돌려주는 속성이라 `parent[3]`은 `TypeError: 'WindowsPath' object is not subscriptable`이 난다.
- `.py` 파일은 `__file__`을 기준으로 경로를 잡는다. 노트북에는 `__file__`이 없어서 `Path.cwd()`를 썼다. 이 줄이 있으면 `set PYTHONPATH=backend`는 따로 필요 없다.
- 모델명, `max_tokens`를 코드에 적지 않고 설정에서 가져온다. 모델이 바뀌어도 `.env` 한 줄만 고치면 된다.
- `settings = get_settings()` — 괄호를 빼면 설정 객체가 아니라 **함수 자체**가 들어가서 다음 줄에서 `AttributeError`가 난다.
- 키는 `SecretStr`로 들고 있다가 SDK에 넘기는 그 순간에만 `.get_secret_value()`로 꺼낸다.

## 응답 구조

```text
Message(
  id='msg_...',
  content=[TextBlock(text='죄송하지만, 저는 귀사의 사내 규정에 대한 정보를 가지고 있지 않습니다. ...', type='text')],
  model='claude-haiku-4-5-20251001',
  role='assistant',
  stop_reason='end_turn',
  usage=Usage(input_tokens=67, output_tokens=176,
              cache_creation_input_tokens=0, cache_read_input_tokens=0, ...)
)
```

| 필드 | 뜻 |
| --- | --- |
| `content` | **블록의 리스트**. 텍스트 외에 도구 호출 블록 등이 섞일 수 있다 |
| `model` | 실제로 응답한 모델. `claude-haiku-4-5`로 보냈는데 날짜가 붙은 정식 버전명으로 돌아온다 |
| `stop_reason` | 멈춘 이유. `end_turn`은 스스로 답을 끝냈다는 뜻, `max_tokens`면 상한에 걸려 잘린 것 |
| `usage` | 입력·출력·캐시 토큰 수. **정확한 토큰 수는 여기서만 알 수 있다** |

`content`가 리스트라서 응답 텍스트는 `response.content[0].text`로 바로 꺼내지 않고, `type == "text"`인 블록만 모아 이어 붙인다. 첫 블록이 텍스트가 아닌 경우를 대비하는 것이다.

## 실제 결과에서 확인한 것

### 1. 근거가 없으면 없다고 답했다

시스템 프롬프트에 "근거가 없으면 없다고 말해야 해"를 넣었더니, 제주도 숙박비 한도를 지어내지 않고 "사내 규정 정보를 가지고 있지 않다"고 답했다. 아직 문서를 하나도 넘기지 않았으니 맞는 동작이다.

### 2. 같은 질문인데 답이 달랐다

같은 파일을 두 번 실행했다.

| | 입력 토큰 | 출력 토큰 | 답 |
| --- | --- | --- | --- |
| 1회차 | 67 | 176 | "…인사/재무 부서에 직접 문의하시기를 권장합니다." |
| 2회차 | 67 | 236 | "…인사/경영관리팀, 사내 출장 규정 문서, 전자결재 시스템…" |

**입력은 한 글자도 안 바뀌었는데 출력 길이도, 문장도 달랐다.** [[22_AI_Native_애플리케이션]]의 FlakyLLM 실습에서 가짜로 재현했던 비결정성이 실제로 나온 것이다. 출력 토큰 수가 달라지니 **비용도 매번 달라진다.**

### 3. 어림값보다 실제가 쌌다

```text
수요일에 어림한 값 : 3.9 원   (입력 800 · 출력 400 토큰)
오늘 실제 호출     : 1.7 원   (입력 67 · 출력 236 토큰)
차이               : 2.2 원
```

근거 문서 없이 질문만 보내서 입력이 67토큰뿐이었다. 문서를 붙이기 시작하면 입력이 크게 늘어나므로, 이 값을 기준으로 하루 비용을 잡으면 안 된다.

## 요청이 실패할 때

| 예외 / 상태 코드 | 원인 | 대응 |
| --- | --- | --- |
| `AuthenticationError` / 401 | API 키 문제 | `.env` 확인 |
| `RateLimitError` / 429 | 분당 한도 또는 금액 소진 | **무작정 다시 누르지 않는다** — 재시도가 한도를 더 소모한다 |
| `APIConnectionError` | 방화벽, 프록시, 오프라인 | 네트워크 확인 |
| `OverloadedError` / 529 | 공급자 쪽 과부하. 우리 잘못이 아니다 | 몇 분 기다렸다가 재시도 |

설치된 SDK에서 확인해보면 연결·타임아웃·인증·한도 오류가 전부 `anthropic.APIError` 하위다. 그래서 어댑터에서는 `except Exception`보다 **`except anthropic.APIError`로 좁게 잡는 편이 낫다.** `Exception`으로 넓게 잡으면 우리 코드의 오타(`AttributeError`, `NameError`)까지 "Claude 호출 실패"로 둔갑한다.

잡은 예외는 우리 예외로 바꿔 던지되 원인을 잃지 않게 `from exc`로 연결한다([[05_예외_계층_설계]]).

```python
except anthropic.APIError as exc:
    log.exception("Claude 호출 실패")
    raise ExternalServiceError("Claude 호출에 실패했습니다.", detail=str(exc)) from exc
```

| 방식 | 트레이스백에 나오는 문장 | 의미 |
| --- | --- | --- |
| `raise ... from exc` | The above exception was the **direct cause** of the following exception | 의도적으로 바꿔 던졌다 |
| `from` 없이 `raise` | **During handling** of the above exception, another exception occurred | except 블록 안에서 사고가 난 것처럼 읽힌다 |
| `raise ... from None` | (원래 예외가 안 보인다) | 원인을 숨긴다 |

SDK의 원문 에러를 `message`에 넣으면 `main.py`의 예외 핸들러가 `message`를 그대로 응답하기 때문에 **화면까지 전달된다.** 원문은 `detail`로 보내고 사용자에게는 일반 문구만 보여준다.

참고: sandbox/w3/day04/00.api호출.ipynb, sandbox/w3/day04/first_call.py, sandbox/w3/day04/first_call_responses.md
