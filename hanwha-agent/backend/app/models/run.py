# 실행 기록 — 질문 한 건이 행(레코드) 하나로 남는다
# - 관측 도구(LangFuse)가 보는 trace / observation 계층을 우리 DB 에 그대로 옮긴 것이다
#     trace       → runs       (질문 1건)
#     observation → run_steps  (그 안의 단계들)
# - 관측 도구에만 기록을 두면 그 서비스가 죽거나 무료 한도를 넘으면 기록이 사라진다
#   우리 DB 에도 남겨두면 화면·감사 로그·통계를 우리 힘으로 만들 수 있다
from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


# 질문 한 건의 실행 기록을 담을 테이블(모델)
class Run(Base, TimestampMixin):
    __tablename__ = "runs"

    # PK 가 자동 증가 정수가 아니라 문자열이다
    # - run_id("RUN-8821")를 LangFuse 트레이스 id·URL 경로·로그에서 같은 값으로 쓰려면
    #   DB 가 번호를 매겨 주기를 기다릴 수 없다. 우리가 먼저 만들어서 넣는다 (services/ids.py)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    # 답은 나중에 채운다 → 처음 넣을 때는 비어 있어야 하므로 nullable
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="완료")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    # 이 답이 mock 이었나 live 였나. 나중에 기록을 볼 때 이게 없으면 판단이 안 된다
    mode: Mapped[str] = mapped_column(String(8), default="mock")
    # 근거 목록을 통째로 담는다
    # - 별도 테이블로 나누지 않은 이유는 "그때 이렇게 답했다"는 스냅샷이기 때문이다
    #   문서가 나중에 개정되어도 이 기록의 버전·위치는 그대로 남아야 한다
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)


# 실행 하나 안의 단계 하나를 담을 테이블(모델)
# - TimestampMixin 을 붙이지 않았다. 단계는 ord 로 순서를 세우고 ms 로 시간을 재므로
#   등록일·수정일이 따로 필요하지 않다
class RunStep(Base):
    __tablename__ = "run_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    # 몇 번째 단계인가
    # - created_at 으로 정렬하지 않는다. 같은 밀리초에 여러 단계가 끝나면 순서가 뒤집힌다
    ord: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(64))
    ok: Mapped[bool] = mapped_column(default=True)
    ms: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
