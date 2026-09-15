# 비밀번호 해싱 — bcrypt

## 왜 비밀번호를 그대로 저장하면 안 되는가

로그인 기능을 만들려면 사용자가 입력한 비밀번호를 DB에 저장된 값과 비교해야 한다. 이때 원문 비밀번호를 그대로 저장하면, DB가 유출되는 순간 모든 사용자의 비밀번호가 그대로 노출된다. 그래서 **암호화(정확히는 해싱)를 거친 값만 저장**하고, 로그인 시에는 입력값을 같은 방식으로 해싱해서 저장된 해시와 비교한다.

## bcrypt

비밀번호 해싱에 널리 쓰이는 해시 함수다.

```bash
python -m pip install bcrypt
```

```python
import bcrypt

hashed = bcrypt.hashpw("비밀번호".encode("utf-8"), bcrypt.gensalt())  # 암호화
matched = bcrypt.checkpw("비밀번호".encode("utf-8"), hashed)          # True / False
```

- `bcrypt.gensalt()`가 매번 다른 salt를 붙이기 때문에, 같은 비밀번호를 두 번 해싱해도 결과 문자열이 다르다. 그래서 비교는 문자열 `==`이 아니라 반드시 `bcrypt.checkpw`로 해야 한다.
- `hashpw`/`checkpw`는 `bytes`를 받는다. 문자열을 그대로 넘기면 안 되고 `.encode("utf-8")`을 거쳐야 한다.

### 직접 확인해본 것

```python
import bcrypt

RAW = "hanwha2026!"

first = bcrypt.hashpw(RAW.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
second = bcrypt.hashpw(RAW.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

print("first  : ", first)
print("second : ", second)
print("해시 길이 : ", len(first), "자")

print("해시 검증 : ", bcrypt.checkpw(RAW.encode("utf-8"), first.encode("utf-8")))    # True
print("해시 검증 : ", bcrypt.checkpw(RAW.encode("utf-8"), second.encode("utf-8")))   # True
print("틀린 비번 : ", bcrypt.checkpw("한화2026!".encode("utf-8"), first.encode("utf-8")))  # False
```

`first`와 `second`는 **서로 다른 문자열인데 둘 다 검증에 통과한다.** salt가 해시 문자열 안에 같이 들어 있어서, `checkpw`가 저장된 해시에서 salt를 꺼내 같은 방식으로 다시 계산해 비교하기 때문이다. 길이는 항상 60자로 나온다.

## agent-app에 적용 — `backend/app/core/security.py`

DB에는 `bytes`가 아니라 문자열 컬럼으로 저장하므로, 앱 코드에서는 인코딩/디코딩을 감싼 함수 두 개로 정리했다.

```python
from __future__ import annotations

import bcrypt

# 암호화: raw 문자열을 주면 암호화된 문자열로 변환하여 리턴
def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# 검증: raw 문자열과 암호화된 문자열을 주면, 두 개가 일치하는지 True/False 돌려주는 함수
def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
```

`verify_password`에서 `try/except`로 감싼 이유는, DB에 저장된 `hashed` 값이 bcrypt 형식이 아니거나(예: 빈 문자열 기본값) 인코딩 중 문제가 생겨도 예외를 그대로 터뜨리지 않고 "일치하지 않음"으로 처리하기 위해서다. 로그인 실패는 흔한 케이스이므로 예외가 아니라 `False` 반환으로 다루는 게 맞다.

## 로그인 실패 예외 — `backend/app/core/exceptions.py`

[[05_예외_계층_설계]]에서 만든 `AgentError` 계층에 로그인 전용 예외를 추가했다.

```python
# 로그인 실패
# - 누구인지 확인이 안 되었을 때
class AuthFailed(AgentError):
    status_code = 401
    code = "auth_failed"

    def __init__(self, message: str = "사번 또는 비밀번호가 올바르지 않습니다.", *, detail: str | None = None):
        super().__init__(message, detail=detail)
```

사번이 없는 경우와 비밀번호가 틀린 경우를 **같은 메시지**로 돌려준다. "사번이 존재하지 않습니다"처럼 따로 나누면, 공격자가 그 응답만으로 어떤 사번이 실제로 등록돼 있는지 알아낼 수 있기 때문이다.

## User 모델에 컬럼 추가 — `backend/app/models/org.py`

```python
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    emp_no: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(50))
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    role: Mapped[str] = mapped_column(String(10))
    clearance: Mapped[str] = mapped_column(String(10))
    password_hash: Mapped[str] = mapped_column(String(100), default="")  # 추가
    ...
```

bcrypt 해시 결과 문자열은 항상 60자 고정 길이라, `String(100)`이면 여유 있게 담긴다. 기존 시드 데이터에는 비밀번호 값이 없으므로 `default=""`를 줬다.

## 컬럼을 추가했으면 DB를 다시 만들어야 한다

모델에 컬럼을 추가해도 이미 만들어진 SQLite 파일에는 반영되지 않는다. `init_db()`가 부르는 `Base.metadata.create_all()`은 **테이블이 없으면 만들고, 이미 있으면 아무것도 하지 않기** 때문이다. 실제 마이그레이션 도구(Alembic 등)를 붙이기 전까지는 DB 파일을 지우고 다시 만드는 방식으로 처리한다.

```python
from sqlalchemy import inspect

from app.db.init_db import init_db
from app.db.session import get_engine

DB_FILE = ROOT / "app.db"

get_engine().dispose()           # 풀에 남아있는 커넥션 먼저 닫기
DB_FILE.unlink(missing_ok=True)  # 파일 삭제
init_db()                        # 테이블 다시 생성

columns = [c["name"] for c in inspect(get_engine()).get_columns("users")]
print("users 컬럼 :", columns)
print("password_hash 들어갔나 :", "password_hash" in columns)
```

- `get_engine().dispose()`를 먼저 부르는 이유는, 엔진이 커넥션 풀로 SQLite 파일을 붙잡고 있으면 윈도우에서 파일 삭제가 막히기 때문이다.
- `inspect(engine).get_columns("users")`로 **실제 테이블에 컬럼이 생겼는지**를 확인한다. 모델 코드만 보고 넘어가면, DB를 안 지웠을 때 조용히 옛 스키마로 돌아간다.

## 시드 데이터에 임시 비밀번호 넣기 — `backend/app/db/seed.py`

DB를 다시 만들었으니 시드도 다시 넣는데, 이때 사용자마다 임시 비밀번호를 해싱해서 채운다.

```python
from app.core.security import hash_password
from app.db.seed_data import DEPARTMENTS, DOCUMENTS, TEMP_PASSWORD, USERS

...
    # 임시 비밀번호 추가
    temp_hash = hash_password(TEMP_PASSWORD)
    session.add_all(User(**row, password_hash=temp_hash) for row in USERS)
```

`TEMP_PASSWORD = "passwd1234!"`는 `seed_data.py`에 상수로 두고, 해싱은 시드를 넣는 시점에 한 번만 한다. 사용자 수만큼 `hash_password`를 부르지 않고 `temp_hash` 하나를 재사용하는데, bcrypt는 해싱 자체가 일부러 느리게 설계된 함수라 반복 호출하면 시드 적재가 눈에 띄게 느려지기 때문이다. 실습용 계정이라 전원이 같은 해시를 가져도 상관없다.

## 노트북에서 실행할 때 — 경로 문제

`sandbox/w3/day01/`처럼 루트가 아닌 폴더에서 노트북을 실행하면 `backend.app...` import가 프로젝트 루트를 기준으로 하기 때문에 실패한다. 노트북 맨 위에서 현재 작업 폴더를 프로젝트 루트로 옮겨준다.

```python
import os
import pathlib
import sys

here = pathlib.Path.cwd()

ROOT = here.parents[2] if here.name == "day01" else here
os.chdir(ROOT)

print("프로젝트 루트 : ", ROOT)
```

`here.name == "day01"`로 방어한 이유는, 이 셀을 실수로 두 번 실행해도(이미 루트로 옮겨간 상태) `parents[2]`를 또 타고 엉뚱한 상위 폴더로 올라가지 않게 하기 위해서다.

참고: `frontend/README_컴포넌트_레퍼런스.md`(UI 킷), sandbox/w3/day01/01.로그인화면과_비밀번호.ipynb
