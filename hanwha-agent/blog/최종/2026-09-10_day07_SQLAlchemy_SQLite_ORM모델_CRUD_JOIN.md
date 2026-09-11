[한화 내일 아카데미 ICT부문] 7일차 후기 — SQLAlchemy, ORM 모델, CRUD, JOIN

어제(2026-09-09) 포스팅에서는 FastAPI로 APIRouter와 의존성 주입, 예외 처리 구조를 다뤘습니다. 오늘은 한화 내일 아카데미 ICT부문 과정 7일차로, 지금까지 만든 백엔드 구조에 실제 데이터베이스를 연결하는 SQLAlchemy를 배웠습니다. 어제까지는 API 구조만 있고 데이터는 메모리에만 있었다면, 오늘부터는 SQLite에 데이터를 실제로 저장하고 조회하는 단계로 넘어갔습니다.

오늘 배운 내용은 아래 순서로 정리합니다.

1. SQLite와 SQLAlchemy 기초
2. ORM 모델 설계
3. CRUD 흐름 (add, flush, commit, rollback, delete)
4. SELECT 문법
5. JOIN

## 1. SQLite와 SQLAlchemy 기초

SQLAlchemy는 파이썬 코드로 데이터베이스를 다룰 수 있게 해주는 ORM 툴킷입니다. Python 코드와 실제 DB 사이에서 중간 역할을 담당합니다.

같은 조회라도 순수 SQL과 SQLAlchemy로 작성하는 방식은 다릅니다.

```sql
SELECT * FROM users WHERE id = 1;
```

```python
user = db.scalar(select(User).where(User.id == 1))
```

SQLite는 파일 하나가 곧 데이터베이스인 경량 DB로, 별도 서버 설치 없이 파이썬 표준 라이브러리(sqlite3)에 기본 포함되어 있어서 실습용으로 사용했습니다. DB URL은 아래 형식을 따릅니다.

```text
sqlite:///./practice.db      # 실행 중인 프로세스의 작업 디렉터리 기준 상대경로
sqlite:///C:/dev/practice.db # 절대경로
sqlite:///:memory:           # 인메모리 DB
```

Engine은 DB 연결 자체가 아니라 연결을 관리하는 입구로, DB 연결·커넥션 풀 반납·DB 방언 처리를 담당합니다. SQLite를 여러 스레드(FastAPI 요청 처리 등)에서 같이 쓰려면 아래처럼 옵션을 켜야 합니다.

```python
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

## 2. ORM 모델 설계

ORM(Object-Relational Mapping)은 관계형 DB의 개념을 파이썬 객체로 대응시켜, SQL을 직접 쓰지 않고도 DB를 다룰 수 있게 해줍니다.

| 관계형 DB | 파이썬 ORM |
| --- | --- |
| 테이블 | 클래스 |
| 행(row) | 객체(인스턴스) |
| 열(column) | Mapped[...] 속성 |
| 기본키 | primary_key=True |
| 외래키 | ForeignKey(...) |

실습에서는 부서(Department)와 문서(Document)를 1:N 관계로 모델링했습니다.

```python
class Department(Base):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    documents: Mapped[list["Document"]] = relationship(back_populates="department")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    security_level: Mapped[str] = mapped_column(String(20), default="일반")
    department: Mapped[Department] = relationship(back_populates="documents")
```

relationship(back_populates=...)로 양쪽 클래스에서 서로를 오갈 수 있게 연결하면, document.department로 부서에 접근하고 department.documents로 그 부서의 문서 목록에 접근할 수 있습니다. 두 클래스에 각각 선언해야 하고, back_populates에 넘기는 문자열은 상대편 클래스에서 자기 자신을 가리키는 속성 이름이어야 한다는 점을 실습하며 확인했습니다.

## 3. CRUD 흐름

Create, Read, Update, Delete는 데이터를 다루는 네 가지 기본 동작입니다. Session의 주요 메서드는 아래와 같이 정리했습니다.

| 메서드 | 하는 일 |
| --- | --- |
| session.add(obj) | 저장 대상으로 등록(아직 DB에 안 감) |
| session.flush() | 등록해둔 것을 SQL로 내보냄(아직 commit 전) |
| session.commit() | 변경 확정 |
| session.rollback() | 확정 전 변경을 전부 되돌림 |
| session.get(모델, 키) | 기본키로 한 건 조회 |
| session.delete(obj) | 객체 단위 삭제 |

```python
with SessionLocal() as session:
    hr = Department(id="HR", name="인사")
    session.add(hr)
    session.flush()  # SQL로 내보내지만 아직 commit 전

    document = session.get(Document, "DOC-HR-012")
    document.page_count = 20  # 속성만 바꾸면 UPDATE 없이도 변경 감지됨
    session.commit()
```

실습 중 삭제 직후 다시 조회하지 않고 이전에 담아둔 객체를 그대로 출력했더니 삭제 전 값이 그대로 나온 경우가 있었습니다. Session이 expire_on_commit=False로 만들어져 있으면 commit 후에도 객체가 메모리의 예전 값을 그대로 들고 있기 때문으로, 변경 여부를 확인하려면 session.get(...)으로 DB에 새로 질의해야 한다는 점을 정리했습니다.

## 4. SELECT 문법

SQLAlchemy 2.0 스타일은 select() 함수를 기준으로 쿼리를 조립합니다.

```python
from sqlalchemy import and_, desc, func, or_, select

stmt = select(Document).where(Document.dept_id == "HRGA").where(Document.page_count >= 10)
stmt = select(Document).where(Document.dept_id.in_(["SE", "PMO"]))
stmt = select(Document).where(Document.title.like("%규정%"))
stmt = select(Document).order_by(desc(Document.page_count)).limit(3)

total = session.scalar(select(func.count()).select_from(Document))
```

where를 이어 쓰면 AND로 묶이고, and_()/or_()로 조건을 명시적으로 묶을 수도 있습니다. print(stmt)로 실제 생성되는 SQL을 미리 확인할 수 있어서, 원하는 쿼리가 맞는지 실행 전에 검증하는 습관을 들였습니다.

## 5. JOIN

두 테이블을 외래키로 묶어서 함께 조회하는 것이 JOIN입니다. Document.department처럼 relationship 속성을 join()에 그대로 넘기면 SQLAlchemy가 ON 조건을 알아서 만들어줍니다.

```python
stmt = select(Document.id, Department.name).join(Document.department)
# SELECT documents.id, departments.name
# FROM documents JOIN departments ON departments.id = documents.dept_id

stmt = (
    select(Document.id, Department.name)
    .join(Document.department)
    .where(Department.name == "보안팀")
)
```

열을 두 개 이상 select()에 넣으면 결과가 (doc_id, dept_name) 튜플로 묶여 나오기 때문에, session.scalars() 대신 session.execute()로 순회해야 한다는 점을 직접 실행해보며 확인했습니다.

## 오늘의 소감

1주차 파이썬 기초와 2주차 초반 FastAPI 구조 실습에 이어, 오늘부터는 실제 데이터가 DB에 저장되고 조회되는 흐름을 다뤘습니다. session.add()가 바로 DB에 반영되는 게 아니라 flush/commit 단계를 거친다는 점, expire_on_commit 옵션에 따라 객체가 메모리 값을 들고 있을 수 있다는 점은 코드만 읽어서는 알기 어렵고 직접 실행 결과를 비교해봐야 체감되는 부분이었습니다. 다음 실습에서는 오늘 만든 ORM 모델을 실제 backend/app/models 구조에 반영해볼 예정입니다.

다음 포스팅에서는 이어서 배울 내용을 정리해보겠습니다.

\#한화내일아카데미 \#한화시스템 \#AI개발자 \#K뉴딜아카데미 \#국비지원교육 \#개발자이직 \#부트캠프후기 \#백엔드개발 \#파이썬프로젝트 \#API개발

참고 링크 : https://blog.naver.com/dldl8819/224407392783
