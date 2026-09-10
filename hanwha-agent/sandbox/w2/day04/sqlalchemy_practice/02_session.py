# commit, rollback 자동 처리
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

# Engine 생성
engine = create_engine(
    "sqlite:///./sandbox/w2/day04/sqlalchemy_practice/practice.db",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# 새 SQLite 연결이 생길 때마다 외래키 검사하기
@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    # sqlite3 연결 커서 가져오기
    cursor = dbapi_connection.cursor()
    # 제약 조건 검사 활성화
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# 요청마다 작업마다 새 Session을 만들 공장 준비
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# 세션의 시작, 성공, 실패, 종료 규칙 한 곳에 모으기
@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
def main() -> None:
    # session을 통해 실제 DB 연결을 사용한다.
    with session_scope() as session:
        result = session.execute(text("SELECT 1")).scalar_one()
        print("select 결과 ", result)

# VS Code에 이 파일을 직접 run할 때만 실행되도록 만들기
if __name__ == "__main__":
    main()
