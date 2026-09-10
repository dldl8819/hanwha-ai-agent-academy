from sqlalchemy import Engine
from app.db.session import engine as default_engine
from app.models import Base

def init_db(engine: Engine | None = None) -> None:
    Base.metadata.create_all(engine or default_engine)

def main() -> None:
    init_db()
    print("테이블 생성 완료")

# 이 파일 실행할 때만 테이블 생성
if __name__ == "__main__":
    main()