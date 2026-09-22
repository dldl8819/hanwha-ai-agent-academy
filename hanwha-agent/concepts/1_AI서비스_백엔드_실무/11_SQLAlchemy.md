# SQLAlchemy

## 1. SQLAlchemy와 SQLite 기초

### SQLAlchemy 개념

파이썬 코드로 데이터베이스를 다룰 수 있게 해주는 라이브러리다(ORM 기능을 갖춘 SQL 툴킷). Python 코드와 실제 DB 사이에서 중간 역할을 한다.

```text
Python ↔ SQLAlchemy ↔ DB
```

같은 조회라도 순수 SQL과 SQLAlchemy로 쓰는 방식이 다르다.

```sql
-- PostgreSQL : 사용자 한 명 조회
SELECT *
FROM users
WHERE id = 1;
```

```python
# SQLAlchemy 사용
user = db.query(User).filter(User.id == 1).first()
user = db.scalar(select(User).where(User.id == 1))
```

#### 용어

| 용어 | 의미 |
| --- | --- |
| Engine | DB와 연결하는 통로 |
| Base | ORM 모델들의 기본 클래스 |
| Model | DB 테이블을 표현하는 파이썬 클래스 |
| Session | DB와 실제로 작업하는 작업 공간 |
| `select()` | 데이터 조회 |
| `add()` | 데이터 추가 |
| `delete()` | 데이터 삭제 |
| `commit()` | 변경 사항 확정 |
| `rollback()` | 작업 취소 |

### 설치

```bash
# 2.0 버전 이상으로 설치
python -m pip install "sqlalchemy>=2.0"
```

### Engine과 DB URL

Engine은 DB 연결 그 자체가 아니라, DB 연결을 관리하는 입구다. 아래 역할을 담당한다.

- DB 연결
- 다 쓴 연결을 커넥션 풀에 반납
- DB 방언(dialect)에 맞게 SQL을 처리
- DB URL을 해석해서 어떤 드라이버·DB를 쓸지 결정

#### SQLite용 DB URL 읽는 법

```text
# sqlite   - sqlite를 사용한다
# :///     - 구분자
# ./practice.db - 실행 중인 프로세스의 작업 디렉터리(cwd) 기준 상대경로
sqlite:///./practice.db

# 절대경로 (Windows는 드라이브 문자가 이미 경로의 시작이라 슬래시 3개로 충분하다)
sqlite:///C:/dev/practice.db

# 인메모리 DB — 프로그램 종료 시 연결도 함께 사라짐
sqlite:///:memory:
```

인메모리 표기는 `:memory:`처럼 앞뒤로 콜론이 있어야 한다. `sqlite:///memory`나 `sqlite:///:memory`처럼 콜론이 빠지면 "memory"라는 이름의 실제 파일 경로로 해석돼버려서, 의도한 인메모리 DB가 아니라 디스크에 그 이름의 파일이 생긴다. `sqlite://`(경로 없이)도 인메모리로 취급되는 축약형이다. 실제로 인메모리를 쓸 일은 거의 없고(테스트에서나 가끔), 위 세 가지 표기 규칙만 기억해두면 된다.

### SQLite 개념

파일 하나가 곧 데이터베이스인 DB다. 설치가 거의 필요 없고 별도 DB 서버를 띄우지 않아도 되며, 파이썬 표준 라이브러리(`sqlite3`)에 기본 포함되어 있다. 지금은 실습용으로 쓰고, 추후 PostgreSQL로 옮길 예정이다.

#### 데이터 타입

| SQLite 타입 | 뜻 | 파이썬으로 치면 |
| --- | --- | --- |
| `INTEGER` | 정수 | `int` |
| `VARCHAR(n)` | 길이 제한이 있는 문자열 | `str` |
| `TEXT` | 길이 제한이 없는 문자열 | `str` |
| `BOOLEAN` | 참/거짓 | `bool` |
| `DATE` | 날짜 | `datetime.date` |
| `TIMESTAMP` | 날짜 + 시각 | `datetime.datetime` |
| `NUMERIC(p, s)` | 자릿수를 정한 소수, 금액에 사용 | `decimal.Decimal` |

### 실습 코드 (sqlite3로 직접 다루기)

#### ROOT 디렉토리 설정

```python
import os
import pathlib

here = pathlib.Path.cwd()
ROOT = here.parents[2] if here.name == "day04" else here  # hanwha-agent

os.chdir(ROOT)  # 앞으로 모든 상대경로는 이 폴더가 기준이 된다
```

#### DB 연결

```python
SANDBOX = ROOT / "sandbox" / "w2" / "day04"

import sqlite3

db_path = SANDBOX / "sql_practice.db"   # 절대경로로 만들어둔다
conn = sqlite3.connect(db_path)          # 파일이 없으면 새로 만들어짐
cur = conn.cursor()                      # DB에 명령을 보내고 결과를 받는 창구

print("연결 완료 : ", db_path)
```

#### 테이블 생성

```python
sql = """
CREATE TABLE documents(
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    version VARCHAR(10) NOT NULL,
    department VARCHAR(15) NOT NULL,
    security_level VARCHAR(10) NOT NULL,
    valid_date DATE NOT NULL,
    expiry_date DATE,
    is_latest BOOLEAN NOT NULL DEFAULT FALSE,
    page_count INTEGER NOT NULL DEFAULT 0,
    create_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
cur.execute(sql)
print("DB 테이블 생성")

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(f"테이블 목록 : {cur.fetchall()}")
```

`CREATE TABLE`은 이미 같은 이름의 테이블이 있으면 `OperationalError: table documents already exists`로 실패한다. `.db` 파일은 커널을 재시작해도 디스크에 그대로 남아있는 파일이라서, 한 번 만든 테이블은 노트북을 다시 실행한다고 없어지지 않는다.

#### 컬럼 수정 — `ALTER TABLE ... RENAME COLUMN`

실습 중 테이블을 처음 만들 때 `expiry_date`를 `expiray_date`로 오타를 냈다. `.db` 파일에는 이미 오타난 이름으로 테이블이 저장돼 있었고, 이후 코드는 `expiry_date`(맞는 철자)를 쓰고 있어서 `INSERT` 시점에 `OperationalError: table documents has no column named expiry_date`가 났다. `CREATE TABLE`을 다시 실행해도 "이미 존재" 에러만 나고 스키마는 안 바뀌기 때문에, 컬럼 이름만 바로잡는 게 더 간단하다.

```python
cur.execute("ALTER TABLE documents RENAME COLUMN expiray_date TO expiry_date;")
conn.commit()
print("컬럼명 수정 완료")

# 확인
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='documents';")
print(cur.fetchone()[0])
```

#### 데이터 삽입

```python
sql = """
INSERT INTO documents(doc_id, title, version, department, security_level, valid_date, expiry_date, is_latest, page_count)
VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);
"""
cur.execute(sql, ("DOC-HR-012", "출장 여비 규정", "1.0", "인사팀", "일반", "2025-01-01", "2025-12-31", False, 28))
print("저장 완료")
conn.commit()
```

`VALUES(...)`의 `?` 개수는 컬럼 개수와 정확히 같아야 하고, 마지막 `?` 뒤에 콤마를 더 붙이면(`?, )`) SQL 문법 오류(`near ")": syntax error`)가 난다 — 실습 중 직접 겪은 오류다.

#### 데이터 조회 — 순수 sqlite3

```python
sql = "SELECT id, doc_id, title, version, department FROM documents;"
cur.execute(sql, ())

result = cur.fetchall()
for r in result:
    id, doc_id, title = r[0], r[1], r[2]
    print(id, doc_id, title)

conn.close()
```

`fetchall()`은 남은 모든 행을 리스트로 반환하고, `fetchone()`은 한 행만(더 없으면 `None`) 반환한다. `cur.fetchone()[0]`처럼 결과가 한 줄뿐이라고 확신할 때는 `fetchone()`이 더 간단하다.

#### 데이터 조회 — SQLAlchemy

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(bind=engine)

# with를 사용하면 close()를 따로 명시하지 않아도 된다
with SessionLocal() as session:
    rows = session.execute(
        text("SELECT id, doc_id, title, version, department FROM documents")
    ).all()
    session.commit()
```

`create_engine("sqlite:///./sql_practice.db")`처럼 상대경로를 쓰면, 그 경로는 노트북이 있는 폴더가 아니라 **현재 프로세스의 작업 디렉터리(cwd)** 기준으로 풀린다. 이 노트북은 맨 위 셀에서 `os.chdir(ROOT)`로 cwd를 `hanwha-agent` 루트로 옮겨뒀기 때문에, `./sql_practice.db`는 `sandbox/w2/day04/`가 아니라 프로젝트 루트를 가리켜서 `no such table: documents`가 났다. sqlite3 쪽에서 이미 절대경로로 만들어둔 `db_path`를 그대로 재사용(`f"sqlite:///{db_path}"`)하면, 같은 파일을 가리키게 되어 정상적으로 조회된다. [[03_Pydantic]]에서 `env_file=".env"`가 cwd 기준으로 풀리던 것과 같은 종류의 문제다.

### 실전 적용: `backend/app/db/session.py`

노트북 실습을 실제 프로젝트에서 쓸 형태로 정리한 모듈이다. 처음에는 `engine`/`SessionLocal`을 모듈 전역 변수로 딱 하나만 만들어뒀는데, 이후 여러 DB URL을 상황에 따라 쓸 수 있도록 `get_engine()`/`get_sessionmaker()` 함수 + 캐시 딕셔너리 구조로 리팩터링했다.

#### Engine 생성 시 옵션

| 옵션 | 의미 |
| --- | --- |
| `connect_args={"check_same_thread": False}` | SQLite는 기본적으로 커넥션을 만든 스레드에서만 쓸 수 있게 막혀 있는데, 여러 스레드(FastAPI의 요청 처리 등)에서 같이 쓸 수 있도록 그 검사를 끈다 |
| `PRAGMA foreign_keys=ON` (연결 시 실행) | SQLite는 외래키 제약 조건 검사가 기본적으로 꺼져 있을 수 있어서, 연결이 새로 생길 때마다 켜준다 |
| `expire_on_commit=False` | 기본값(`True`)이면 `commit()` 이후 ORM 객체의 속성에 접근할 때마다 DB를 다시 조회한다. 꺼두면 그 재조회를 막는다 |

#### 전체 코드

```python
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

# 만든 엔진을 URL별로 담아두는 상자 — 같은 URL이면 새로 안 만들고 재사용
_ENGINES: dict[str, Engine] = {}

def get_engine(url: str | None = None) -> Engine:
    # 인자로 안 주면 환경변수(.env)의 DATABASE_URL을 쓴다
    resolved = url or get_settings().database_url
    if resolved in _ENGINES:
        return _ENGINES[resolved]

    connect_args: dict[str, object] = {}
    is_sqlite = resolved.startswith("sqlite")
    if is_sqlite:
        connect_args["check_same_thread"] = False

    engine = create_engine(resolved, connect_args=connect_args)

    if is_sqlite:
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _ENGINES[resolved] = engine
    return engine

def get_sessionmaker(engine: Engine | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=engine or get_engine(), expire_on_commit=False)

@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_sessionmaker()()  # 1번째 () = 공장(sessionmaker)을 받음, 2번째 () = 그 공장을 호출해 Session 생성
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

- `get_engine()`이 `resolved`(최종 DB URL)를 키로 `_ENGINES`에 캐시해두기 때문에, 같은 URL로 여러 번 호출해도 Engine을 매번 새로 만들지 않고 재사용한다. Engine 하나가 자체적으로 커넥션 풀을 갖고 있어서, 앱 전체에서 하나만 있으면 되기 때문이다.
- `is_sqlite`로 분기해두는 이유는, `check_same_thread`나 `PRAGMA foreign_keys` 설정이 SQLite 전용이기 때문이다. 나중에 `DATABASE_URL`을 PostgreSQL로 바꾸면 이 분기는 자동으로 건너뛰어져서, 코드 수정 없이 DB만 교체할 수 있다.
- `get_sessionmaker()()`처럼 괄호가 두 번 붙는 이유는, `get_sessionmaker()`가 반환하는 값 자체가 "세션을 찍어내는 공장"(`sessionmaker` 객체, 호출 가능)이기 때문이다. 첫 번째 `()`로 그 공장을 받고, 두 번째 `()`로 그 공장을 즉시 호출해서 진짜 `Session` 객체 하나를 만든다.

## 2. ORM 모델 설계

위에서 만든 Engine/Session 위에, 실제 테이블을 파이썬 클래스로 정의하는 부분이다.

### ORM (Object-Relational Mapping) 개념

관계형 DB의 개념을 파이썬 객체로 대응시켜서, SQL을 직접 쓰지 않고도 파이썬 코드로 DB를 다룰 수 있게 해준다.

| 관계형 DB | 파이썬 ORM |
| --- | --- |
| 테이블 | 클래스 |
| 행(row) | 객체(인스턴스) |
| 열(column) | `Mapped[...]` 속성 |
| 기본키 | `primary_key=True` |
| 외래키 | `ForeignKey(...)` |

### `models/base.py` — 공통 기반 클래스

```python
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

# 생성일/수정일은 거의 모든 테이블에 공통으로 들어가는 컬럼이라 믹스인으로 분리
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
```

- `DeclarativeBase`를 상속받은 `Base`가 모든 ORM 모델의 공통 부모가 된다. `Base.metadata`에 정의된 모든 테이블 스키마가 모인다.
- `TimestampMixin`처럼 여러 모델에 공통으로 섞어 넣을 속성은 별도 클래스로 분리해서 다중 상속으로 붙인다(`class Document(Base, TimestampMixin)`). 클래스 이름에 `Mixin`을 붙이는 건 "다른 클래스와 섞어 쓰라고 만든 클래스"라는 뜻을 드러내는 관례다.
- 처음엔 `datetime.utcnow`를 썼는데, 파이썬 3.12부터 deprecated라 `datetime.now`로 바꿨다. 다만 `datetime.now()`는 UTC가 아니라 **서버의 로컬 시간대** 기준이라는 점은 알아두는 게 좋다 — 서버 시간대가 바뀌거나 여러 지역에 서버를 두게 되면 `created_at` 값 해석이 꼬일 수 있어서, 나중에 UTC로 통일하고 싶으면 `lambda: datetime.now(datetime.UTC)`처럼 타임존을 명시하는 방법도 있다.

### 실제 테이블 — `models/org.py`, `models/document.py`

처음엔 `models/documents.py` 하나에 `Department`/`Document`/`DocumentVersion`만 넣었는데, 이후 "부서·사용자"와 "문서"로 파일을 나누고 `User` 모델과 업무 로직(권한, 보안 등급, 색인 상태)을 추가했다.

`models/org.py` — 부서와 사용자:

```python
from __future__ import annotations
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

# 보안 등급을 숫자 크기로도 비교할 수 있게 매핑
CLEARANCE: dict[str, int] = {"일반": 1, "3급": 2, "대외비": 3}

class Department(Base, TimestampMixin):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    users: Mapped[list["User"]] = relationship(back_populates="dept")
    documents: Mapped[list["Document"]] = relationship(back_populates="dept")

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    emp_no: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(50))
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    role: Mapped[str] = mapped_column(String(10))
    clearance: Mapped[str] = mapped_column(String(10))

    dept: Mapped["Department"] = relationship(back_populates="users")
    documents: Mapped[list["Document"]] = relationship(back_populates="owner")

    # 보안등급을 숫자로 변환 (모르는 값이면 가장 낮은 1로 취급)
    @property
    def clearance_level(self) -> int:
        return CLEARANCE.get(self.clearance, 1)

    # 팀장·관리자에게만 승인 권한 부여
    @property
    def can_approve(self) -> bool:
        return self.role in {"팀장", "관리자"}
```

`models/document.py` — 문서와 문서 버전:

```python
from __future__ import annotations

from datetime import date
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # 자연키
    title: Mapped[str] = mapped_column(String(200))
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    security_level: Mapped[str] = mapped_column(String(10), index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    dept: Mapped["Department"] = relationship(back_populates="documents")
    owner: Mapped["User | None"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        order_by="DocumentVersion.version",
    )

    # 여러 버전 중 지금 "현행"인 것만 골라준다
    @property
    def current(self) -> "DocumentVersion | None":
        for v in self.versions:
            if v.status == "현행":
                return v
        return None

class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("doc_id", "version", name="uq_doc_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10))

    effective_from: Mapped[date]
    expires_at: Mapped[date | None]

    file_path: Mapped[str | None] = mapped_column(String(300))  # 파일은 디스크에, DB엔 경로만
    file_format: Mapped[str] = mapped_column(String(10))

    # 색인(파싱/임베딩) 관련 필드
    chunk_count: Mapped[int] = mapped_column(default=0)
    embed_model: Mapped[str | None] = mapped_column(String(50))
    index_status: Mapped[str] = mapped_column(String(10), default="대기")
    index_progress: Mapped[int] = mapped_column(default=0)
    indexed_at: Mapped[date | None]

    document: Mapped["Document"] = relationship(back_populates="versions")

    @property
    def period(self) -> str:
        if self.expires_at is None:
            return f"{self.effective_from} ~"
        return f"{self.effective_from} ~ {self.expires_at}"

    # 현행이면서 색인까지 끝난 버전만 검색 결과로 내보내도 된다고 판단
    @property
    def is_searchable(self) -> bool:
        return self.status == "현행" and self.index_status == "완료"

# Department 1:N User, Department 1:N Document
# User 1:N Document (owner)
# Document 1:N DocumentVersion
```

- `relationship(back_populates=...)`으로 양쪽 클래스에서 서로를 오갈 수 있게 연결한다. 두 클래스에 각각 선언해야 하고, `back_populates`에 넘기는 문자열은 **상대편 클래스에서 자기 자신을 가리키는 속성 이름**이어야 한다.
- `owner: Mapped["User | None"]`처럼 옵션 관계(문서에 담당자가 없을 수도 있음)는 `| None`으로 표시한다. `ForeignKey`도 `owner_id: Mapped[int | None]`으로 NULL을 허용해둬야 짝이 맞는다.
- `@property`로 만든 `clearance_level`, `can_approve`, `current`, `period`, `is_searchable`은 전부 **DB 컬럼이 아니라 파이썬에서만 계산되는 값**이다. 매번 SQL로 계산하기보다, 이미 로드된 객체의 속성들을 조합해서 판단하는 업무 로직을 모델에 바로 붙여둔 것이다.
- `UniqueConstraint("doc_id", "version", ...)`: 같은 문서(`doc_id`)에 같은 버전(`version`)이 중복 저장되지 않도록 두 컬럼을 묶어서 유니크 제약을 건다.

### 모델을 한곳에 모으기 — `models/__init__.py`

```python
from app.models.base import Base, TimestampMixin
from app.models.document import Document, DocumentVersion
from app.models.org import CLEARANCE, Department, User

__all__ = [
    "Base",
    "TimestampMixin",
    "Department",
    "User",
    "Document",
    "DocumentVersion",
    "CLEARANCE",
]
```

여기서 `document.py`/`org.py`의 모델들을 import해두는 게 핵심이다 — SQLAlchemy는 어떤 모델 클래스가 실제로 "import돼서 파이썬에 로드된 적 있는" 것만 `Base.metadata`에 등록한다. `init_db.py`가 `app.models`를 import할 때 이 `__init__.py`가 실행되면서 네 모델이 전부 로드되고, 그래야 다음 단계의 `create_all()`이 네 테이블을 다 만들어준다.

`__all__`은 `from app.models import *`(와일드카드 import)를 할 때 뭘 내보낼지 정하는 목록이다. 여기 이름을 빠뜨리거나(`Document`가 빠져있던 실수) 오타를 내면(`Base` 대신 `base`), 직접 이름을 콕 집어 import(`from app.models import Base`)하는 코드는 멀쩡히 동작하지만 `import *`를 쓰는 코드에서만 조용히 잘못된 값이 들어가는 버그가 된다 — 실습 중 겪은 오류다.

### 테이블 생성 — `db/init_db.py`

```python
from __future__ import annotations
from sqlalchemy import Engine
from app.db.session import get_engine

def init_db(engine: Engine | None = None) -> None:
    from app.models import Base
    Base.metadata.create_all(engine or get_engine())

def main() -> None:
    init_db()
    print("테이블 생성 완료")

if __name__ == "__main__":
    main()
```

```bash
# 모듈 경로로 실행 (backend/ 에서)
python -m app.db.init_db
```

`-m`은 파일 경로가 아니라 점(`.`)으로 구분한 모듈 경로를 받는다. `python -m app.db.init_db.py`처럼 확장자 `.py`를 붙이면, `init_db`(모듈)에 또 `py`라는 서브모듈이 있는 것처럼 찾으려다 실패한다(`__path__ attribute not found` 에러) — 실습 중 겪은 오류다.

`Base.metadata.create_all(engine)`은 아직 없는 테이블만 새로 만들고, 이미 있는 테이블은 건드리지 않는다. `engine: Engine | None = None` 매개변수를 열어둔 이유는, 테스트 코드에서 실제 DB 대신 임시 엔진(예: 인메모리 SQLite)을 넣어 검증할 수 있게 하기 위해서다.

**루트(`hanwha-agent`)에서 실행하려면 `PYTHONPATH`가 필요하다.** `backend/` 안으로 `cd`하지 않고 실행하면 `app` 패키지가 안 보여서 `ModuleNotFoundError: No module named 'app'`이 난다. 이때 PowerShell에서 `set PYTHONPATH=backend`처럼 cmd 문법을 그대로 쓰면 안 된다 — PowerShell의 `set`(`Set-Variable`의 별칭)은 `VAR=VALUE` 형태를 통째로 하나의 변수 이름으로 인식해버려서, 환경변수는 전혀 설정되지 않고 `PYTHONPATH=backend`라는 이상한 이름의 PowerShell 변수만 하나 생긴다. PowerShell에서 환경변수를 설정하는 올바른 문법은 `$env:PYTHONPATH = "backend"`다. 또는 그냥 `cd backend`부터 하고 실행하는 게 더 간단하다.

### 폴더 구조

```text
hanwha-agent/
    backend/
        app/
            __init__.py
            main.py
            core/
                __init__.py
                config.py
                exceptions.py
                logging.py
            schemas/
                ...
            api/
                ...
            db/
                __init__.py
                session.py
                init_db.py
            models/
                __init__.py
                base.py
                org.py
                document.py
    sandbox/
        w2/
            ...
```

## 3. CRUD

Create, Read, Update, Delete — 데이터를 다루는 네 가지 기본 동작이다.

```text
DB 연결 → 테이블(Model) 정의 → Session 생성
        → Insert, Select, Update, Delete
```

### 연습용 모델 — `sandbox/w2/day04/demo_models.py`

다른 예제 파일들이 가져다 쓰는 모델·엔진 모음이다. 이 파일 자체는 직접 실행하지 않는다.

```python
from __future__ import annotations
from datetime import date
from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = "sqlite:///./demo.db"

class Base(DeclarativeBase):
    pass

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # 자연키
    name: Mapped[str] = mapped_column(String(100), unique=True)
    documents: Mapped[list["Document"]] = relationship(back_populates="department")

    def __repr__(self) -> str:
        return f"<Department {self.id} {self.name}>"

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    security_level: Mapped[str] = mapped_column(String(20), default="일반")
    page_count: Mapped[int] = mapped_column(default=0)
    effective_date: Mapped[date | None]  # None 허용 → NULL 가능
    department: Mapped[Department] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document {self.id} {self.title}>"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def reset_db() -> None:
    # 예제를 몇 번 돌려도 같은 결과가 나오도록 지우고 다시 만든다
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def seed() -> None:
    with SessionLocal() as session:
        session.add_all([Department(id="HRGA", name="인사총무"), ...])
        session.add_all([Document(id="DOC-HR-014", title="국내출장 여비 규정", dept_id="HRGA", ...), ...])
        session.commit()
```

`__repr__`는 DB와는 무관하고, `print(doc)`처럼 객체를 찍었을 때 보기 좋으라고 붙이는 것이다.

### 테이블 미리보기 — `01_model.py`

```python
from sqlalchemy.schema import CreateTable
from demo_models import Base, Document, engine, reset_db

def main() -> None:
    print("등록된 테이블 목록", list(Base.metadata.tables.keys()))

    # 실제로 실행하지 않고, 생성될 CREATE TABLE SQL만 미리 본다
    print(CreateTable(Document.__table__).compile(engine))

    for column in Document.__table__.columns:
        print(f"{column.name} / {column.type} / nullable={column.nullable} / pk={column.primary_key}")

    reset_db()

if __name__ == "__main__":
    main()
```

`column.nullable`을 `column.nulable`로 오타 냈을 때 에러 메시지가 `AttributeError: Neither 'Column' object nor 'Comparator' object has an attribute 'nulable'. Did you mean: 'nullable'?`처럼 정확히 뭘 의도했는지까지 짚어줬다 — SQLAlchemy 객체들은 존재하지 않는 속성에 접근하면 비슷한 이름을 제안해주는 경우가 많다.

### 실습 중 겪은 이슈: `python -m`은 cwd를 기준으로 모듈을 찾는다

같은 파일을 실행 위치만 바꿔가며 시도했는데, 결과가 매번 달랐다.

```powershell
# 1) backend/ 에서 실행 — sandbox 패키지 자체를 못 찾음
PS backend> python -m sandbox.w2.day04.01_model
# ModuleNotFoundError: No module named 'sandbox'

# 2) hanwha-agent 루트에서 실행 — 01_model은 찾았지만, 그 안의 demo_models를 못 찾음
PS hanwha-agent> python -m sandbox.w2.day04.01_model
# ModuleNotFoundError: No module named 'demo_models'

# 3) day04 폴더 안으로 직접 이동해서 실행 — 성공
PS day04> python -m 01_model
```

`python -m <모듈>`은 실행 파일이 어디 있는지가 아니라, **명령을 실행한 시점의 현재 작업 디렉터리(cwd)**를 `sys.path`에 넣고 그 안에서 모듈을 찾는다.

- 1번: cwd가 `backend/`라서 그 안에 `sandbox`라는 이름의 패키지/폴더가 없다.
- 2번: cwd가 `hanwha-agent`라서 `sandbox.w2.day04.01_model`까지는 정상적으로 찾아서 실행됐다. 하지만 `01_model.py` 안의 `from demo_models import ...`는 "같은 폴더의 파일을 가져오는" 평범한(상대 import가 아닌) import라서, `sys.path`에 들어간 게 `hanwha-agent`뿐이라 그 안에 `demo_models`라는 최상위 모듈이 없다며 실패했다.
- 3번: cwd 자체를 `day04` 폴더로 옮기면, `-m`이 그 폴더를 `sys.path`에 넣어주기 때문에 같은 폴더의 `demo_models.py`도 바로 찾아진다.

정리하면, `python 파일.py`(스크립트 방식)는 **그 파일이 있는 폴더**를 `sys.path`에 넣어주지만, `python -m 모듈`(모듈 방식)은 **명령을 실행한 cwd**를 넣어준다는 점이 다르다. sandbox 예제처럼 같은 폴더의 파일끼리 평범한 import로 서로를 참조하는 구조라면, 그 폴더 안으로 직접 이동해서 `python -m 파일이름`(확장자 없이)으로 실행하는 게 맞다.

### 그 밖의 사소한 이슈

`01_model.py` 하단의 실행 방법 안내를 적어둔 `'''...'''` 문자열 안에 `.\sandbox\w2\day04\`처럼 백슬래시 경로가 들어있으면, 파이썬이 `\s`를 이스케이프 시퀀스로 잘못 해석하려다 `SyntaxWarning: invalid escape sequence '\s'`를 띄운다. 에러는 아니고 경고라 실행 자체는 되지만, 문자열 앞에 `r`을 붙여 raw string(`r'''...'''`)으로 만들거나 슬래시(`/`)를 쓰면 경고가 사라진다.

### Session 주요 메서드

| 메서드 | 하는 일 |
| --- | --- |
| `session.add(obj)` | "저장 대상으로 등록"만 한다. 아직 DB에 안 갔다(`session.new`에 들어감) |
| `session.add_all([...])` | 여러 건을 한 번에 등록 |
| `session.flush()` | 등록해둔 것을 SQL로 내보낸다. 자동 발급 id·제약 위반을 여기서 확인할 수 있다. 아직 확정은 아니다 |
| `session.commit()` | 확정. 이게 없으면 DB 파일에 안 남는다 |
| `session.rollback()` | 확정 전 변경을 전부 되돌린다 |
| `session.get(모델, 키)` | 기본키로 한 건 조회. 없으면 `None` |
| `session.delete(obj)` | 객체 단위 삭제 |
| `session.refresh(obj)` | DB에서 다시 읽어 객체를 갱신 |
| `session.close()` | 연결을 풀에 반납 (`with`를 쓰면 자동으로 호출됨) |

### `02_session_crud.py` — add/flush/commit/rollback/delete 흐름

```python
from demo_models import Department, Document, SessionLocal, reset_db

with SessionLocal() as session:
    hr = Department(id="HR", name="인사")
    session.add(hr)
    print(f"add 후 new : {session.new}")

    session.flush()  # SQL로 내보내지만 아직 commit 전
    print(f"DB에서 조회는 가능 : {session.get(Department, 'HR')}")

    session.add_all([
        Document(id="DOC-HR-012", title="출장 여비 규정", dept_id="HR", page_count=18),
        Document(id="DOC-HR-013", title="재택근무 운영 지침", dept_id="HR", page_count=9),
    ])
    session.commit()

with SessionLocal() as session:
    document = session.get(Document, "DOC-HR-012")
    document.page_count = 20          # 속성만 바꾸면 UPDATE 없이도 변경 감지됨
    print(f"update - dirty : {session.dirty}")
    session.commit()

with SessionLocal() as session:
    session.add(Document(id="DOC-TMP-001", title="실수", dept_id="HR"))
    session.flush()
    print("rollback 전 : ", session.get(Document, "DOC-TMP-001"))
    session.rollback()                # flush까지는 됐어도 commit 전이면 되돌릴 수 있다
    print("rollback 후 : ", session.get(Document, "DOC-TMP-001"))  # None

    doc = session.get(Document, "DOC-HR-013")
    session.delete(doc)
    session.commit()
    print(f"삭제 후 조회(재조회) : {session.get(Document, 'DOC-HR-013')}")  # None
```

**실습 중 겪은 이슈**: 삭제 직후 `session.get()`으로 다시 조회하지 않고, 삭제 전에 이미 변수에 담아둔 `doc` 객체를 그대로 다시 `print(doc)`했더니 삭제 전과 똑같은 내용이 출력됐다. `demo_models.py`의 `SessionLocal`이 `expire_on_commit=False`로 만들어져 있어서, `commit()` 후에도 `doc` 객체가 DB를 다시 조회하지 않고 메모리에 있던 예전 값을 그대로 들고 있었기 때문이다. 기본값(`expire_on_commit=True`)이었다면 `commit()` 후 속성에 접근하는 순간 다시 조회하려다 `ObjectDeletedError`가 나서 바로 알아챌 수 있었을 것이다. **삭제·수정 여부를 눈으로 확인하려면 들고 있던 객체를 다시 찍지 말고, `session.get(...)`처럼 DB에 새로 질의해야 한다.**

### SELECT 문법

| 도구 | 예 | 뜻 |
| --- | --- | --- |
| `select(모델)` | `select(Document)` | `SELECT * FROM documents` |
| `select(열, 열)` | `select(Document.id, Document.title)` | 필요한 열만 |
| `.where(...)` | `.where(Document.page_count >= 20)` | 조건. 여러 번 이어 쓰면 AND |
| `and_()` / `or_()` | `.where(or_(A == 1, B < 10))` | 조건을 묶어서 결합 |
| `.in_([...])` | `Document.dept_id.in_(["SE", "PMO"])` | IN |
| `.like("%규정%")` / `.ilike(...)` | | 부분 일치 (`ilike`는 대소문자 무시) |
| `.is_(None)` | `Document.effective_date.is_(None)` | IS NULL (`== None`이 아니다) |
| `.between(a, b)` | | 범위 |
| `.order_by(...)` / `desc(...)` | `.order_by(desc(Document.page_count))` | 정렬 |
| `.limit(n)` / `.offset(n)` | | 개수 제한 · 건너뛰기 |
| `func.count()` `func.sum()` `func.avg()` | `select(func.sum(Document.page_count))` | 집계 |
| `.group_by(...)` / `.having(...)` | | 묶기 / 집계 결과 거르기 |
| `.label("cnt")` | | 결과 열 이름 붙이기 |
| `print(stmt)` | | 만들어진 SQL을 그대로 출력 — 막혔을 때 제일 먼저 해볼 것 |

```python
from sqlalchemy import and_, desc, func, or_, select
from demo_models import Document, SessionLocal, reset_db, seed

with SessionLocal() as session:
    # SELECT * FROM documents — session.scalars()로 ORM 객체를 바로 뽑는다
    stmt = select(Document)
    print("전체 : ", len(session.scalars(stmt).all()), "건")

    # 만들어질 SQL을 실행 전에 미리 확인
    print(select(Document.id, Document.title).where(Document.dept_id == "HRGA"))

    # where를 이어 쓰면 AND, and_()/or_()로 명시적으로 묶을 수도 있다
    stmt = select(Document).where(Document.dept_id == "HRGA").where(Document.page_count >= 10)
    stmt = select(Document).where(and_(Document.dept_id == "HRGA", Document.page_count >= 10))
    stmt = select(Document).where(or_(Document.dept_id == "HRGA", Document.page_count >= 10))

    print("in : ", [d.id for d in session.scalars(select(Document).where(Document.dept_id.in_(["SE", "PMO"])))])
    print("like : ", [d.id for d in session.scalars(select(Document).where(Document.title.like("%규정%")))])

    stmt = select(Document).order_by(desc(Document.page_count)).limit(3)
    print("페이지 수 많은 top 3 : ", [(d.id, d.page_count) for d in session.scalars(stmt)])

    # 집계는 select_from()으로 대상 테이블을 지정하거나, 집계할 열을 넣는다
    total = session.scalar(select(func.count()).select_from(Document))
    page_sum = session.scalar(select(func.sum(Document.page_count)))
```

`session.scalars(stmt)`는 결과를 ORM 객체(`Document` 인스턴스)로 바로 돌려주고, `session.scalar(stmt)`(단수)는 결과가 값 하나(집계 결과 등)일 때 그 값 자체를 돌려준다.

## 4. JOIN

두 테이블을 하나로 묶어서 조회하는 것이 JOIN이다. `documents.dept_id`와 `departments.id`처럼 외래키로 연결된 테이블 사이에서, "문서 id와 그 문서가 속한 부서명을 같이 보고 싶다"처럼 한쪽 테이블만으로는 답할 수 없는 질문에 쓴다.

### `.join(모델.관계속성)` — relationship을 그대로 넘기기

`demo_models.py`에는 이미 `Document.department`(다대일)와 `Department.documents`(일대다) 관계가 `relationship(back_populates=...)`로 정의돼 있다. `.join()`에 이 관계 속성을 그대로 넘기면, SQLAlchemy가 `ForeignKey`를 보고 ON 조건을 알아서 만들어준다.

```python
from sqlalchemy import select
from demo_models import Department, Document, SessionLocal, seed, reset_db

with SessionLocal() as session:
    stmt = select(Document.id, Department.name).join(Document.department)
    print(stmt)
    # SELECT documents.id, departments.name
    # FROM documents JOIN departments ON departments.id = documents.dept_id

    for doc_id, dept_name in session.execute(stmt):
        print(doc_id, dept_name)

    # join 뒤에도 where는 그대로 붙는다 — 부서명으로 필터링
    stmt = (
        select(Document.id, Department.name)
        .join(Document.department)
        .where(Department.name == "보안팀")
    )
```

`select(Document.id, Department.name)`처럼 두 테이블의 열을 함께 지정했을 때, `session.execute(stmt)`는 `session.scalars(stmt)`(단일 열/객체용)가 아니라 각 행이 `(doc_id, dept_name)` 튜플로 묶여 나온다. `session.scalars()`를 쓰면 첫 번째 열만 뽑혀서 두 번째 열(`Department.name`)이 사라진다 — 열이 두 개 이상이면 `execute()`를 써야 한다.

### `.join(대상모델, ON조건)` — 관계 없이 직접 지정

`relationship`이 정의돼 있지 않거나 조인 조건을 명시적으로 쓰고 싶을 때는 아래처럼 직접 지정할 수도 있다. 결과는 위 방식과 동일하다.

```python
stmt = select(Document.id, Department.name).join(
    Department, Document.dept_id == Department.id
)
```

### 실습 — `04_excrud.py`

"문서의 id와 부서명을 모두 출력", "보안팀의 문서 id와 부서명을 출력" 두 문제를 위 두 가지 방식으로 풀어본 파일이다. `reset_db()` + `seed()`로 매번 같은 데이터에서 시작해서, `session.execute(stmt)`로 결과를 순회하며 `(doc_id, dept_name)` 튜플을 언패킹해 출력한다.

참고: sandbox/w2/day04/01.sqlalchemy와sqlite.ipynb, sandbox/w2/day04/sqlalchemy_practice/02_session.py, sandbox/w2/day04/demo_models.py, sandbox/w2/day04/01_model.py, sandbox/w2/day04/02_session_crud.py, sandbox/w2/day04/03_select.py, sandbox/w2/day04/04_excrud.py, backend/app/db/session.py, backend/app/db/init_db.py, backend/app/models/
