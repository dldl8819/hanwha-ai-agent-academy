from __future__ import annotations
from sqlalchemy import Engine
from app.db.session import get_engine

# 테이블 초기화 함수 
# - 이미 있으면 아무것도 안하고 없으면 생성
def init_db(engine: Engine | None = None) -> None:
    from app.models import Base
    Base.metadata.create_all(engine or get_engine())

# 테이블 생성용
def main() -> None:
    init_db()
    print("테이블 생성 완료")

if __name__ == "__main__":
    main()