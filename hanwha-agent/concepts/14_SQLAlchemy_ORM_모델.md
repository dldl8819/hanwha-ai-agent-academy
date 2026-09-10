# ORM 모델 설계

[[13_SQLAlchemy와_SQLite]]에서 다룬 Engine/Session 위에, 실제 테이블을 파이썬 클래스로 정의하는 부분이다.

## ORM (Object-Relational Mapping) 개념

관계형 DB의 개념을 파이썬 객체로 대응시켜서, SQL을 직접 쓰지 않고도 파이썬 코드로 DB를 다룰 수 있게 해준다.

| 관계형 DB | 파이썬 ORM |
| --- | --- |
| 테이블 | 클래스 |
| 행(row) | 객체(인스턴스) |
| 열(column) | `Mapped[...]` 속성 |
| 기본키 | `primary_key=True` |
| 외래키 | `ForeignKey(...)` |

## `models/base.py` — 공통 기반 클래스

```python
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

# 생성일/수정일은 거의 모든 테이블에 공통으로 들어가는 컬럼이라 믹스인으로 분리
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
```

- `DeclarativeBase`를 상속받은 `Base`가 모든 ORM 모델의 공통 부모가 된다. `Base.metadata`에 정의된 모든 테이블 스키마가 모인다.
- `TimestampMixin`처럼 여러 모델에 공통으로 섞어 넣을 속성은 별도 클래스로 분리해서 다중 상속으로 붙인다(`class Document(Base, TimestampMixin)`). 클래스 이름에 `Mixin`을 붙이는 건 "다른 클래스와 섞어 쓰라고 만든 클래스"라는 뜻을 드러내는 관례다.
- `datetime.utcnow`는 파이썬 3.12부터 deprecated다. 지금 당장 에러는 아니지만 `DeprecationWarning`이 뜨고, 나중에 `lambda: datetime.now(datetime.UTC)` 같은 형태로 바꿔야 할 수 있다.

## `models/documents.py` — 실제 테이블 3개

```python
from __future__ import annotations

from datetime import date
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Department(Base, TimestampMixin):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    documents: Mapped[list["Document"]] = relationship(back_populates="department")

class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    security_level: Mapped[str] = mapped_column(String(20), default="일반", index=True)
    department: Mapped[Department] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("doc_id", "version", name="uq_document_version"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="현행", index=True)
    valid_date: Mapped[date | None]
    file_path: Mapped[str] = mapped_column(String(500))
    page_count: Mapped[int] = mapped_column(default=0)
    document: Mapped[Document] = relationship(back_populates="versions")

# Department 1:N Document
# Document 1:N DocumentVersion
```

- `relationship(back_populates=...)`으로 양쪽 클래스에서 서로를 오갈 수 있게 연결한다. `document.department`로 부서에 접근하고, `department.documents`로 그 부서의 문서 목록에 접근하는 식이다. 두 클래스에 각각 선언해야 하고, `back_populates`에 넘기는 문자열은 **상대편 클래스에서 자기 자신을 가리키는 속성 이름**이어야 한다.
- `cascade="all, delete-orphan"`: `Document`가 삭제되면 그 문서에 딸린 `DocumentVersion`들도 같이 삭제된다.
- `UniqueConstraint("doc_id", "version", ...)`: 같은 문서(`doc_id`)에 같은 버전(`version`)이 중복 저장되지 않도록 두 컬럼을 묶어서 유니크 제약을 건다(각 컬럼을 따로 unique로 걸면 안 되는 경우).
- `Mapped[date | None]`처럼 컬럼 전용 옵션(`String(길이)` 등)이 필요 없으면 `mapped_column()` 없이 타입 힌트만으로도 컬럼이 만들어진다.

## 모델을 한곳에 모으기 — `models/__init__.py`

```python
from app.models.base import Base, TimestampMixin
from app.models.documents import Department, Document, DocumentVersion

__all__ = "Base", "TimestampMixin", "Department", "Document", "DocumentVersion"
```

여기서 `documents.py`의 모델들을 import해두는 게 핵심이다 — SQLAlchemy는 어떤 모델 클래스가 실제로 "import돼서 파이썬에 로드된 적 있는" 것만 `Base.metadata`에 등록한다. `init_db.py`가 `app.models`를 import할 때 이 `__init__.py`가 실행되면서 `Department`/`Document`/`DocumentVersion`이 전부 로드되고, 그래야 다음 단계의 `create_all()`이 세 테이블을 다 만들어준다.

## 테이블 생성 — `db/init_db.py`

```python
from sqlalchemy import Engine
from app.db.session import engine as default_engine
from app.models import Base

def init_db(engine: Engine | None = None) -> None:
    Base.metadata.create_all(engine or default_engine)

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

## 폴더 구조

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
                documents.py
    sandbox/
        w2/
            ...
```

참고: sandbox/w2/day04/sqlalchemy_practice/03_model.py, backend/app/models/, backend/app/db/init_db.py
