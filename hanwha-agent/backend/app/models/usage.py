from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

# LLM 호출 1번의 사용량과 원가 정보를 저장할 테이블(모델)
class UsageLog(Base, TimestampMixin):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    model: Mapped[str] = mapped_column(String(64))

    input_tok: Mapped[int] = mapped_column(Integer, default=0)
    cache_tok: Mapped[int] = mapped_column(Integer, default=0)
    output_tok: Mapped[int] = mapped_column(Integer, default=0)

    # 환율에 따라 달라질 수 있기 때문에 달러도 추가하는 게 좋다.
    cost_krw: Mapped[float] = mapped_column(Float, default=0.0)
    # TimestampMixin 이 주는 created_at 과 따로 두는 이유
    # - created_at : 이 행이 DB 에 들어간 시각
    # - occurred_at : 호출이 실제로 일어난 시각
    #   기록을 나중에 몰아서 적재하게 되면 둘이 달라진다
    occurred_at: Mapped[datetime] = mapped_column(default=datetime.now)

