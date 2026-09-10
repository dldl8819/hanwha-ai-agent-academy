# SQLAlchemy와 SQLite

## SQLAlchemy 개념

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

### 용어

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

## Engine과 DB URL

Engine은 DB 연결 그 자체가 아니라, DB 연결을 관리하는 입구다. 아래 역할을 담당한다.

- DB 연결
- 다 쓴 연결을 커넥션 풀에 반납
- DB 방언(dialect)에 맞게 SQL을 처리
- DB URL을 해석해서 어떤 드라이버·DB를 쓸지 결정

### SQLite용 DB URL 읽는 법

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

## SQLite 개념

파일 하나가 곧 데이터베이스인 DB다. 설치가 거의 필요 없고 별도 DB 서버를 띄우지 않아도 되며, 파이썬 표준 라이브러리(`sqlite3`)에 기본 포함되어 있다. 지금은 실습용으로 쓰고, 추후 PostgreSQL로 옮길 예정이다.

### 데이터 타입

| SQLite 타입 | 뜻 | 파이썬으로 치면 |
| --- | --- | --- |
| `INTEGER` | 정수 | `int` |
| `VARCHAR(n)` | 길이 제한이 있는 문자열 | `str` |
| `TEXT` | 길이 제한이 없는 문자열 | `str` |
| `BOOLEAN` | 참/거짓 | `bool` |
| `DATE` | 날짜 | `datetime.date` |
| `TIMESTAMP` | 날짜 + 시각 | `datetime.datetime` |
| `NUMERIC(p, s)` | 자릿수를 정한 소수, 금액에 사용 | `decimal.Decimal` |

## 실습 코드 (sqlite3로 직접 다루기)

### ROOT 디렉토리 설정

```python
import os
import pathlib

here = pathlib.Path.cwd()
ROOT = here.parents[2] if here.name == "day04" else here  # hanwha-agent

os.chdir(ROOT)  # 앞으로 모든 상대경로는 이 폴더가 기준이 된다
```

### DB 연결

```python
SANDBOX = ROOT / "sandbox" / "w2" / "day04"

import sqlite3

db_path = SANDBOX / "sql_practice.db"   # 절대경로로 만들어둔다
conn = sqlite3.connect(db_path)          # 파일이 없으면 새로 만들어짐
cur = conn.cursor()                      # DB에 명령을 보내고 결과를 받는 창구

print("연결 완료 : ", db_path)
```

### 테이블 생성

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

### 컬럼 수정 — `ALTER TABLE ... RENAME COLUMN`

실습 중 테이블을 처음 만들 때 `expiry_date`를 `expiray_date`로 오타를 냈다. `.db` 파일에는 이미 오타난 이름으로 테이블이 저장돼 있었고, 이후 코드는 `expiry_date`(맞는 철자)를 쓰고 있어서 `INSERT` 시점에 `OperationalError: table documents has no column named expiry_date`가 났다. `CREATE TABLE`을 다시 실행해도 "이미 존재" 에러만 나고 스키마는 안 바뀌기 때문에, 컬럼 이름만 바로잡는 게 더 간단하다.

```python
cur.execute("ALTER TABLE documents RENAME COLUMN expiray_date TO expiry_date;")
conn.commit()
print("컬럼명 수정 완료")

# 확인
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='documents';")
print(cur.fetchone()[0])
```

### 데이터 삽입

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

### 데이터 조회 — 순수 sqlite3

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

### 데이터 조회 — SQLAlchemy

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

`create_engine("sqlite:///./sql_practice.db")`처럼 상대경로를 쓰면, 그 경로는 노트북이 있는 폴더가 아니라 **현재 프로세스의 작업 디렉터리(cwd)** 기준으로 풀린다. 이 노트북은 맨 위 셀에서 `os.chdir(ROOT)`로 cwd를 `hanwha-agent` 루트로 옮겨뒀기 때문에, `./sql_practice.db`는 `sandbox/w2/day04/`가 아니라 프로젝트 루트를 가리켜서 `no such table: documents`가 났다. sqlite3 쪽에서 이미 절대경로로 만들어둔 `db_path`를 그대로 재사용(`f"sqlite:///{db_path}"`)하면, 같은 파일을 가리키게 되어 정상적으로 조회된다. [[04_환경변수와_Pydantic_Settings]]에서 `env_file=".env"`가 cwd 기준으로 풀리던 것과 같은 종류의 문제다.

## 실전 적용: `backend/app/db/session.py`

노트북 실습을 실제 프로젝트에서 쓸 형태로 정리한 모듈이다. Engine과 Session을 앱 전체에서 하나씩만 만들어두고, 어디서든 `session_scope()`로 가져다 쓰는 구조다.

### Engine 생성 시 옵션

| 옵션 | 의미 |
| --- | --- |
| `connect_args={"check_same_thread": False}` | SQLite는 기본적으로 커넥션을 만든 스레드에서만 쓸 수 있게 막혀 있는데, 여러 스레드(FastAPI의 요청 처리 등)에서 같이 쓸 수 있도록 그 검사를 끈다 |
| `pool_pre_ping=True` | 커넥션 풀에서 커넥션을 꺼내 쓰기 전에 아직 살아있는지 ping으로 확인한다 |
| `PRAGMA foreign_keys=ON` (연결 시 실행) | SQLite는 외래키 제약 조건 검사가 기본적으로 꺼져 있을 수 있어서, 연결이 새로 생길 때마다 켜준다 |
| `expire_on_commit=False` | 기본값(`True`)이면 `commit()` 이후 ORM 객체의 속성에 접근할 때마다 DB를 다시 조회한다. 꺼두면 그 재조회를 막는다 |

### 전체 코드

```python
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

# DB 경로 — 환경변수를 참고하고, 없으면 app.db 사용
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

def build_engine() -> Engine:
    options: dict = {"pool_pre_ping": True}

    if DATABASE_URL.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}

    db_engine = create_engine(DATABASE_URL, **options)

    if DATABASE_URL.startswith("sqlite"):
        @event.listens_for(db_engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return db_engine

# 애플리케이션 전체에서 Engine/세션 공장은 하나만 만들면 된다
engine = build_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# 세션의 시작·성공·실패·종료 규칙을 한곳에 모은 편의 함수
@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def main() -> None:
    print(f"DB URL : {engine.url}")
    print(f"DB 종류 : {engine.dialect.name}")

    with session_scope() as session:
        print(f"select 결과 : {session.execute(text('SELECT 1')).scalar_one()}")

if __name__ == "__main__":
    main()
```

`db.startswith("sqlite")`로 분기해두는 이유는, `check_same_thread`나 `PRAGMA foreign_keys` 설정이 SQLite 전용이기 때문이다. 나중에 `DATABASE_URL`을 PostgreSQL로 바꾸면 이 분기는 자동으로 건너뛰어져서, 코드 수정 없이 DB만 교체할 수 있다.

### 폴더 배치

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
            db/                     # 데이터베이스
                __init__.py
                session.py
    sandbox/
        w2/
            ...
```

참고: sandbox/w2/day04/01.sqlalchemy와sqlite.ipynb, sandbox/w2/day04/sqlalchemy_practice/02_session.py, backend/app/db/session.py
