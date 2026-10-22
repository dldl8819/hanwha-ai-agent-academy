# 도구가 만든 문서 초안
# - run_id 로 어느 질문에서 만들어졌는지 남긴다. internal 등급 도구의 기록 자리
from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Draft(Base, TimestampMixin):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(32))
    fields: Mapped[dict] = mapped_column(JSON)
    body: Mapped[str] = mapped_column(Text)
