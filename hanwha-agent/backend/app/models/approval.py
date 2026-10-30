# 승인 요청과 감사 로그
# - 밖으로 나가는 실행(external 등급)은 사람이 승인한 뒤에만 한다
# - 누가 언제 무엇을 했는지는 감사 로그에 한 줄씩 남는다
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# 외부로 나가는 요청 하나
# - thread_id : 멈춘 승인 그래프의 실행 이름. 승인·반려 때 이 이름으로 이어서 실행한다
class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)          # REQ-0148
    thread_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"), nullable=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(16), default="slack")
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="대기중")       # 대기중 / 승인 / 승인·실행 / 반려됨 / 실패 · ...
    requested_at: Mapped[datetime] = mapped_column(default=datetime.now)
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)


# 누가 언제 무엇을 했는지 한 줄
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    approval_id: Mapped[str | None] = mapped_column(ForeignKey("approval_requests.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    at: Mapped[datetime] = mapped_column(default=datetime.now)
    actor: Mapped[str] = mapped_column(String(50))
    event: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, default="")


# 실제로 보낸 Slack 메시지 한 건
# - ts(메시지 식별자)가 있어야 나중에 그 메시지를 지우거나 수정할 수 있다
# - 강사님 코드의 칸 이름은 sent_ad 다. sent_at 의 오타로 보고 고쳐 옮겼다
class SlackMessageLog(Base):
    __tablename__ = "slack_message_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    approval_id: Mapped[str] = mapped_column(ForeignKey("approval_requests.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    ts: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(default=datetime.now)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
