# 타입 힌트와 Pydantic

## Pydantic이란

파이썬 데이터의 구조와 타입을 정의하고, 실제 데이터가 그 규칙에 맞는지 검사해주는 라이브러리다. 타입 힌트를 읽어서 들어온 데이터가 그 타입이 맞는지 검사하고, 아니면 어느 필드가 왜 틀렸는지까지 알려준다. 이 검사를 받으려면 필드마다 타입 힌트를 반드시 작성해야 한다.

```bash
python -m pip install pydantic
```

## BaseModel

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

## Field로 세부 제약 걸기

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

## 값 목록을 고정하기 — Enum

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

## 모델 ↔ 딕셔너리 ↔ JSON

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

## 실전 패턴: 요청 모델과 응답 모델 분리

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

## field_validator로 커스텀 검증/가공

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

참고: sandbox/w2/day01/01.타입힌트와_Pydantic.ipynb
