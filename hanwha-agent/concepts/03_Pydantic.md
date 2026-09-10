# Pydantic

## 1. 타입 힌트와 Pydantic 모델

### Pydantic이란

파이썬 데이터의 구조와 타입을 정의하고, 실제 데이터가 그 규칙에 맞는지 검사해주는 라이브러리다. 타입 힌트를 읽어서 들어온 데이터가 그 타입이 맞는지 검사하고, 아니면 어느 필드가 왜 틀렸는지까지 알려준다. 이 검사를 받으려면 필드마다 타입 힌트를 반드시 작성해야 한다.

```bash
python -m pip install pydantic
```

### BaseModel

검사가 필요한 클래스는 `BaseModel`을 상속받아 정의한다. `__init__`을 따로 작성하지 않아도 필드 선언만으로 자동 생성되고, `__repr__`도 자동으로 만들어진다.

```python
from pydantic import BaseModel

class Document(BaseModel):
    doc_id: str
    title: str
    version: str
    security_level: str

doc = Document(
    doc_id="DOC-HR-001",
    title="여비 규정 문서",
    version="1.0",
    security_level="사내 공개",
)

print(doc)
print(doc.title)
```

호환 가능한 타입은 적당히 변환도 해준다 (`"123"` → `123`). 웹 폼이나 쿼리 문자열처럼 서버로 들어오는 데이터는 전부 문자열이기 때문에, 이 자동 변환이 실제로 유용하게 쓰인다.

### Field로 세부 제약 걸기

타입만으로는 부족한 규칙을 `Field`로 추가한다.

| 제약 | 의미 |
| --- | --- |
| `min_length` / `max_length` | 문자열·리스트의 최소/최대 길이 |
| `pattern` | 정규식으로 문자열 값 제약 |
| `default` | 기본값. 지정하면 선택 필드가 된다 |
| `description` | 설명. FastAPI 자동 문서에 그대로 노출됨 |
| `ge`, `gt`, `le`, `lt` | 숫자의 이상/초과/이하/미만 제약 |

```python
from pydantic import Field
from datetime import date

class Document2(BaseModel):
    doc_id: str = Field(
        ...,
        pattern=r"DOC-[A-Z]{2,4}-\d{3}$",
        description="문서 고유 번호",
    )
    title: str = Field(..., min_length=1, max_length=200)
    version: str = Field(..., pattern=r"^\d+\.\d+$")  # 2.0
    security_level: str
    expiry_date: date | None = None  # 선택 필드는 `|`로 여러 타입 지정 + default
    tags: list[str] = Field(default_factory=list)
```

`pattern`에 넘기는 정규식은 문법이 틀리면(괄호/중괄호가 안 맞거나 이스케이프가 빠지면) 클래스를 정의하는 시점에 `SchemaError`가 난다. 예를 들어 `r"DOC-[A-Z]{2,4}, -\d{3$}"`처럼 쉼표·공백이 잘못 들어가거나 `{3}`의 닫는 중괄호가 `$` 안쪽에 있으면 "unclosed counted repetition" 에러로 클래스 자체가 만들어지지 않는다. 정규식 리터럴(`r"..."`)은 눈으로 훑기 어려우니, `re.compile()`로 먼저 검증해보는 습관이 필요하다.

### 값 목록을 고정하기 — Enum

지정된 값들 중 하나만 들어가야 하는 경우 `Enum`으로 코드 차원에서 제약을 준다. `str`과 함께 상속받으면 문자열처럼 다룰 수 있어 JSON 변환이 편하다. 간단한 경우에는 `Literal`로도 같은 효과를 낼 수 있다.

```python
from enum import Enum
from typing import Literal

class SecurityLevel(str, Enum):
    PUBLIC = "공개"
    INTERNAL = "사내공개"
    CONFIDENTIAL = "대외비"
    SECRET = "기밀"

class Document3(BaseModel):
    doc_id: str
    security_level: SecurityLevel        # Enum 타입
    sec_level: Literal["공개", "사내공개", "대외비", "기밀"]  # Literal로 간단히

doc3 = Document3(doc_id="Doc-1", security_level=SecurityLevel.CONFIDENTIAL, sec_level="대외비")
```

### 모델 ↔ 딕셔너리 ↔ JSON

API는 데이터를 JSON으로 주고받기 때문에, 모델과 딕셔너리/JSON 사이를 변환하는 메서드가 자주 쓰인다.

| 메서드 | 방향 |
| --- | --- |
| `model_dump()` | 모델 → 파이썬 딕셔너리 |
| `model_dump_json()` | 모델 → JSON 문자열 |
| `모델클래스.model_validate(dict)` | 딕셔너리 → 모델 |
| `모델클래스.model_validate_json(json)` | JSON 문자열 → 모델 |

```python
class Document4(BaseModel):
    doc_id: str
    title: str
    valid_date: date
    tags: list[str] = Field(default_factory=list)

doc4 = Document4(
    doc_id="DOC-HR-004",
    title="국내 출장 여비",
    valid_date=date(2026, 9, 7),
    tags=["인사", "출장", "여비"],
)

d = doc4.model_dump()
j = doc4.model_dump_json(indent=2)  # indent: 들여쓰기 옵션

data = {
    "doc_id": "DOC-SEC-002",
    "title": "정보 보안 지침",
    "valid_date": "2026-09-07",
    "tags": ["보안"],
}
doc_data = Document4.model_validate(data)
```

### 실전 패턴: 요청 모델과 응답 모델 분리

요청과 응답을 같은 모델 하나로 쓰면, 응답에서만 필요한 값(서버 내부 id 등)까지 요청에서 받아버리거나 그 반대의 문제가 생긴다. 용도별로 모델을 나눈다.

```python
# 나쁜 예: 요청/응답을 하나로 사용
class Document(BaseModel):
    doc_id: str
    title: str
    ...

# 좋은 예
# 요청용: 서버로 들어오는 데이터를 취합
class DocumentCreate(BaseModel):
    doc_id: str
    title: str

# 응답용: 서버가 요청자에게 내보내는 데이터
class DocumentOut(BaseModel):
    doc_id: str
    title: str
    version: str
```

그 밖에 지켜야 할 것들:

- 딕셔너리로 직접 응답하지 않는다. `return {"doc_id": ...}`처럼 반환하지 말고, 응답 모델 인스턴스를 반환해서 타입 검사를 받는다.
- `str | None`을 남발하지 않는다. 전부 선택 필드로 만들면 값이 있다는 걸 코드로 보장할 수 없다.

### field_validator로 커스텀 검증/가공

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from enum import Enum

class SecurityLevel(str, Enum):
    PUBLIC = "공개"
    INTERNAL = "사내공개"
    CONFIDENTIAL = "대외비"
    SECRET = "기밀"

class DocumentCreate(BaseModel):
    doc_id: str = Field(..., pattern=r"DOC-[A-Z]{2,4}-\d{3}$", description="문서 고유 번호(예:DOC-HR-001)")
    title: str = Field(..., min_length=1, max_length=200)
    version: str = Field(..., pattern=r"^\d+\.\d+$", description="예: 1.0")
    department: str = Field(..., min_length=1, max_length=50)
    security_level: SecurityLevel
    valid_date: date
    expiry_date: date | None = None

    # doc_id가 소문자로 들어와도 대문자로 저장 (mode="before": 검증 전에 값을 먼저 가공)
    @field_validator("doc_id", mode="before")
    @classmethod
    def upper_doc_id(cls, v):
        return v.upper() if isinstance(v, str) else v

    # title, department 양쪽 다 앞뒤 공백 제거 (필드 여러 개 동시 지정 가능)
    @field_validator("title", "department")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

class DocumentOut(BaseModel):
    id: int                        # 서버에서 사용하는 고유 번호
    doc_id: str
    title: str
    version: str
    department: str
    security_level: str
    valid_date: date
    expiry_date: date | None = None
    is_latest: bool                # 최신본 여부
    chunk_count: int = Field(ge=0) # 임베딩된 조각 수
    created_at: datetime           # 문서 저장 날짜
```

## 2. 환경변수와 Pydantic Settings

### 환경 변수란

환경 변수(environment variable)는 운영체제가 프로그램에게 넘겨주는 `이름=값` 쌍 형태의 데이터다. API 키처럼 코드에 그대로 넣으면 유출될 수 있는 값들을 코드 바깥에 작성해두고, 코드에서는 이름으로 불러다 쓴다. 프로젝트 루트에 `.env` 파일을 만들고 그 안에 값을 작성한다.

### python-dotenv로 .env 읽기

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

### Pydantic Settings

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

### SecretStr — 값을 로그에 노출하지 않기

API 키처럼 민감한 값은 타입을 `str` 대신 `SecretStr`로 지정한다. `print()`나 로그에 실수로 찍혀도 실제 값 대신 `**********`로 가려진다.

```python
from pydantic import SecretStr

class Settings(BaseSettings):
    anthropic_api_key: SecretStr | None = None  # 필수가 아니면 `| None = None`

settings = Settings()
print(settings.anthropic_api_key)          # **********
print(settings.anthropic_api_key.get_secret_value())  # 실제 값 (필요할 때만 명시적으로 꺼낸다)
```

### 실전 프로젝트 적용 (backend/app/core/config.py)

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

### 환경변수 초기화 (테스트할 때)

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

### 설정 관리 시 주의할 점

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

참고: sandbox/w2/day01/01.타입힌트와_Pydantic.ipynb, sandbox/w2/day01/02.환경변수설정.ipynb, sandbox/w2/day02/01.환경변수세팅.ipynb, backend/app/core/config.py
