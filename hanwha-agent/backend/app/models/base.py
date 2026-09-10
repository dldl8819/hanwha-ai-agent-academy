from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

# DB 테이블 또는 공통 기반 클래스 정의
# 생성일, 수정일은 거의 모든 테이블에 공통적으로 들어가는 컬럼
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
