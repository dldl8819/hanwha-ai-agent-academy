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
MAX_TOKENS=400
DAILY_CALL_LIMIT=200
```

`case_sensitive=False`(기본값)라 대소문자는 안 맞아도 되지만, 철자 자체는 필드명과 정확히 일치해야 한다. `.env`에 `MAX_TOKEN`(S 없음)이라고 적어두면 필드 `max_tokens`(S 있음)와 매칭이 안 돼서, 에러 없이 조용히 기본값만 쓰이고 `.env`에 적어둔 값은 영영 안 읽힌다.

## SecretStr — 값을 로그에 노출하지 않기

API 키처럼 민감한 값은 타입을 `str` 대신 `SecretStr`로 지정한다. `print()`나 로그에 실수로 찍혀도 실제 값 대신 `**********`로 가려진다.

```python
from pydantic import SecretStr

class Settings(BaseSettings):
    anthropic_api_key: SecretStr | None = None  # 필수가 아니면 `| None = None`

settings = Settings()
print(settings.anthropic_api_key)          # **********
print(settings.anthropic_api_key.get_secret_value())  # 실제 값 (필요할 때만 명시적으로 꺼낸다)
```

## 실전 프로젝트 적용 (backend/app/core/config.py)

`Settings` 클래스는 프로젝트에서 한 곳(`backend/app/core/config.py`)에만 정의하고, `get_settings()` 함수로 어디서나 같은 인스턴스를 가져다 쓴다. `@lru_cache`를 붙이면 `Settings()`가 최초 1번만 만들어지고, 이후 호출은 캐시된 같은 객체를 반환한다.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_mode: str = Field(default="mock", pattern=r"^(mock|live)$")
    anthropic_api_key: SecretStr | None = None
    llm_model: str = "claude-haiku-4-5"
    max_tokens: int = Field(default=400, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    daily_call_limit: int = Field(default=200, ge=1)
    max_input_chars: int = Field(default=200, ge=1)
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    allow_external_send: bool = False

    @property
    def is_live(self) -> bool:
        return self.app_mode == "live"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

노트북(`sandbox/`)에서 `backend/app` 모듈을 그대로 가져다 쓰려면, cwd를 프로젝트 루트로 옮긴 뒤 `backend`를 `sys.path`에 추가해야 한다.

```python
import sys

if "backend" not in sys.path:
    sys.path.insert(0, "backend")

from app.core.config import get_settings

settings = get_settings()
print(settings.app_mode, settings.is_live, settings.top_k)
```

## 환경변수 초기화 (테스트할 때)

`.env`나 이전 셀에서 이미 설정된 값을 지우고 다시 테스트하고 싶을 때는 `os.environ.pop()`을 쓴다. 키가 없어도 에러가 나지 않는다(두 번째 인자 `None`이 기본값 역할).

```python
import os

# 1개 삭제
os.environ.pop("APP_MODE", None)

# 여러 개 삭제
keys = ["APP_MODE", "ANTHROPIC_API_KEY"]
for key in keys:
    os.environ.pop(key, None)
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

참고: sandbox/w2/day01/02.환경변수설정.ipynb, sandbox/w2/day02/01.환경변수세팅.ipynb, backend/app/core/config.py
