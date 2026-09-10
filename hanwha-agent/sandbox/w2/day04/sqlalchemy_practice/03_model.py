# ORM 설계
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 연습용 부모 모델
class Base(DeclarativeBase):
    pass

# memos 테이블과 연결되는 ORM 모델을 정의
# - DB 테이블과 동일한 구조로 클래스 작성
class Memo(Base):
    # 실제 DB 테이블 이름 지정
    __tablename__ = "memos"

    # 기본키 컬럼 지정
    id: Mapped[int] = mapped_column(primary_key=True)

    # 일반 컬럼
    # 최대 100자의 필수 컬럼 설정
    title: Mapped[str] = mapped_column(String(100))

# 모델 등록 + 테이블 생성
def main() -> None:
    engine = create_engine("sqlite:///./sandbox/w2/day04/sqlalchemy_practice/practice.db")

    # 테이블 생성
    Base.metadata.create_all(engine)
    print(Base.metadata.tables.keys())

if __name__ == "__main__":
    main()
