# 환경 변수와 Pydantic Settings

## 환경 변수란

환경 변수(environment variable)는 운영체제가 프로그램에게 넘겨주는 `이름=값` 쌍 형태의 데이터다. API 키처럼 코드에 그대로 넣으면 유출될 수 있는 값들을 코드 바깥에 작성해두고, 코드에서는 이름으로 불러다 쓴다. 프로젝트 루트에 `.env` 파일을 만들고 그 안에 값을 작성한다.

## python-dotenv로 .env 읽기

`.env` 파일의 값을 파이썬에서 조회하는 가장 기본적인 방법이다.

```bash
python -m pip install python-dotenv
```

```python
from dotenv import load_dotenv
import os

# .env를 찾아 읽고 os.environ에 채워 넣는다.
# override=True로 주면 이미 있는 환경변수도 .env 값으로 덮어쓴다.
load_dotenv()

print(os.environ.get("APP_MODE"))
print(os.environ.get("ANTHROPIC_API_KEY"))
```

이 방식은 `os.environ.get()`으로 매번 값을 꺼내야 하고, 타입도 전부 문자열로 온다는 한계가 있다.

## Pydantic Settings

환경 변수를 타입이 있는 설정 객체로 바로 읽어오는 방법이다. 필드에 타입을 지정해두면 자동으로 형변환도 해준다.

```bash
python -m pip install pydantic-settings
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env에 모르는 항목이 있어도 무시
    )

    # 필드명 = 환경변수 이름 (대소문자 구분 안 함)
    app_mode: str = "dev"
    anthropic_api_key: str  # 기본값이 없으면 필수 값
    llm_model: str = "claude-haiku-4-5"

    # 타입이 int라서 "400"이 자동으로 400으로 변환된다.
    max_tokens: int = Field(default=400, ge=1, le=8192)
    daily_call_limit: int = Field(default=200, ge=1)
    max_input_chars: int = Field(default=200, ge=1)

settings = Settings()
print(settings.app_mode, settings.max_tokens)
```

`.env` 파일 예시 (띄어쓰기도 그대로 문자열로 읽히므로 `=` 앞뒤에 공백을 넣지 않는다):

```
APP_MODE=mock
ANTHROPIC_API_KEY=your-claude-api-key
LLM_MODEL=claude-haiku-4-5
MAX_TOKEN=400
DAILY_CALL_LIMIT=200
```

## 설정 관리 시 주의할 점

**설정을 읽는 곳은 한 군데로 모은다.** 여러 파일에서 각자 `os.environ`을 직접 읽으면, 기본값이 파일마다 달라지는 등 값이 흩어진다.

```python
# 나쁜 예 — 파일마다 따로 읽음, 기본값도 제각각
# .../retriever.py
top_k = int(os.environ.get("TOP_K", "3"))
# .../chat_service.py
top_k = int(os.getenv("TOP_K", "5"))
```

```python
# 좋은 예 — app/core/config.py 한 곳에서만 정의하고 다른 곳은 가져다 씀
class Settings(BaseSettings):
    ...

settings = Settings()

def get_settings():
    return settings

# .../retriever.py
from app.core.config import get_settings

settings = get_settings()
top_k = settings.top_k
```

**기본값은 안전한 쪽으로 잡는다.** 예를 들어 `debug: bool = True`처럼 위험한 값을 기본값으로 두지 않고, `debug: bool = False`처럼 꺼진 상태를 기본으로 한다. 필수 값에는 애초에 기본값을 주지 않아서, 값이 없으면 앱이 뜨지 않고 바로 알 수 있게 한다.

**`.env`와 `.env.example`을 함께 관리한다.** `.env`는 실제로 쓰는 값(민감 정보 포함, git에 올리지 않음)이고, `.env.example`은 어떤 키가 필요한지 이름과 설명만 적어둔 샘플(git에 올림)이다.

참고: sandbox/w2/day01/02.환경변수설정.ipynb
