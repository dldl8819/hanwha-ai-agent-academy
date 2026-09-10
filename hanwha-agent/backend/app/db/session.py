from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

# DB 경로
# - 환경변수 참고, 없으면 app.db 사용
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# 엔진 생성
def build_engine() -> Engine:

    # 연결 확인 옵션
    options: dict = {"pool_pre_ping": True}

    # sqlite라면
    if DATABASE_URL.startswith("sqlite"):
        # 스레드 체크 옵션 추가
        options["connect_args"] = {"check_same_thread": False}
    # 엔진 생성 
    # - 옵션 풀어서 주기
    db_engine = create_engine(DATABASE_URL, **options)
    # sqlite라면
    if DATABASE_URL.startswith("sqlite"):
        # 연결 시작 시 
        @event.listens_for(db_engine, "connect")
        # 외래키 검사 설정 추가
        def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return db_engine

# 엔진 공장 생성
# - 애플리케이션 전체에서 하나만 만들면 된다.
engine = build_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# 편의 함수 
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
        print(f"select 결과 : {session.execute(text("SELECT 1")).scalar_one()}")

if __name__ == "__main__":
    main()