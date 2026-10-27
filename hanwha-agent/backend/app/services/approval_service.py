# 승인 서비스 (HITL)
# - 승인 그래프가 gate 에서 멈추면 요청을 저장하고, 사람이 승인·반려하면 같은 thread_id 로 그래프를 이어서 실행한다
# - send_slack 의 실제 실행(Tool.fn)은 이 서비스의 _send 에서만 부른다. 루프에서는 Tool.run() 이 막는다
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ExternalServiceError, ModeNotAvailable, NotFound, PermissionDenied
from app.db.session import session_scope
from app.models import ApprovalRequest, AuditLog, User
from app.tools import registry

WAITING, APPROVED, DONE, REJECTED = ("대기중", "승인", "승인·실행", "반려됨")

# 첫 요청 번호
REQ_START = 148


def _next_req_id(session: Session) -> str:
    numbers = [REQ_START - 1]
    for req_id in session.scalars(select(ApprovalRequest.id)).all():
        tail = req_id.removeprefix("REQ-")
        if tail.isdigit():
            numbers.append(int(tail))
    return f"REQ-{max(numbers) + 1:04d}"


# 초안 단계 : 받은 문구를 그대로 둔다 (모델 없음)
def _draft(state: dict) -> dict:
    return {"text": state["text"]}


# 전송 단계 : 승인된 뒤에만 온다
# - 실패를 예외로 올리지 않고 result 에 담는다. 그래프는 끝까지 가고 결과로 상태를 정한다
def _send(state: dict) -> dict:
    registry.load_all()
    try:
        return {"result": registry.get("send_slack").fn(text=state["text"])}
    except ModeNotAvailable:
        return {"result": {"ok": False, "error": "전송 꺼짐"}}
    except ExternalServiceError as e:
        return {"result": {"ok": False, "error": e.message}}


def build_graph(checkpointer):
    from app.agent.graph import build_approval_graph
    return build_approval_graph(_draft, _send, checkpointer=checkpointer)


# 멈춘 그래프를 사람의 결정으로 이어서 실행
def _resume(checkpointer, thread_id: str, decision: dict) -> dict:
    from langgraph.types import Command
    return build_graph(checkpointer).invoke(Command(resume=decision), {"configurable": {"thread_id": thread_id}})


# 요청 한 건 + 감사 로그 한 줄을 한 트랜잭션으로
def open_request(*, thread_id: str, requester_id: int, text: str, run_id: str | None = None) -> str:
    with session_scope() as s:
        requester = s.get(User, requester_id)
        if requester is None:
            raise NotFound(f"없는 사용자: {requester_id}")
        req_id = _next_req_id(s)
        s.add(ApprovalRequest(id=req_id, thread_id=thread_id, run_id=run_id, requester_id=requester_id,
                              action_type="slack", payload={"text": text}, status=WAITING))
        s.add(AuditLog(approval_id=req_id, run_id=run_id, actor=requester.name,
                       event="Slack 전송 요청 → 승인 대기", detail=text))
    return req_id


def events(req_id: str) -> list[str]:
    with session_scope() as s:
        return list(s.scalars(select(AuditLog.event).where(AuditLog.approval_id == req_id).order_by(AuditLog.id)))


# 재개 뒤 결과 상태와 로그 한 줄
def _close(req_id: str, status: str, event: str, text: str | None = None) -> None:
    with session_scope() as s:
        row = s.get(ApprovalRequest, req_id)
        row.status = status[:24]
        if text is not None:
            row.payload = {"text": text}
        s.add(AuditLog(approval_id=req_id, run_id=row.run_id, actor="시스템", event=event[:64]))


# 결정 기록 : 대기 중인 요청인지, 결정할 권한이 있는지 본다
def _decide(req_id: str, approver_id: int, status: str, event: str, note: str = "") -> ApprovalRequest:
    with session_scope() as s:
        row, user = s.get(ApprovalRequest, req_id), s.get(User, approver_id)
        if row is None:
            raise NotFound(f"없는 승인 요청: {req_id}")
        if row.status != WAITING:
            raise PermissionDenied(f"이미 처리된 요청: {row.status}")
        if user is None or not user.can_approve:
            raise PermissionDenied("승인 권한이 없습니다")
        # 강사님 코드에 없던 검사. 팀장이 요청자면 자기 요청을 스스로 승인할 수 있었다
        if row.requester_id == approver_id:
            raise PermissionDenied("본인 요청은 승인·반려할 수 없습니다")
        row.status, row.approver_id, row.decided_at = status, approver_id, datetime.now()
        s.add(AuditLog(approval_id=req_id, run_id=row.run_id, actor=user.name, event=event, detail=note))
    return row


def approve(*, req_id: str, approver_id: int, checkpointer) -> dict:
    row = _decide(req_id, approver_id, APPROVED, "승인")
    try:
        out = _resume(checkpointer, row.thread_id, {"approved": True, "note": ""})
    except Exception:
        _close(req_id, "실패 · 재개 오류", "재개 실패")
        raise
    res = out.get("result", {})
    status, event = ((DONE, "Slack 전송 완료") if res.get("ok")
                     else (f"실패 · {res.get('error')}", f"전송 안 됨 · {res.get('error')}"))
    _close(req_id, status, event)
    return {"req_id": req_id, "status": status[:24], "result": res}


# 반려
# - 지금 그래프는 반려하면 END 로 간다. 다시 멈추는 일(again)은 반려 루프가 생기면 쓰인다
def reject(*, req_id: str, approver_id: int, note: str, checkpointer) -> dict:
    row = _decide(req_id, approver_id, REJECTED, "반려", note)
    out = _resume(checkpointer, row.thread_id, {"approved": False, "note": note})
    again = out["__interrupt__"][0].value["text"] if "__interrupt__" in out else None
    if again is not None:
        _close(req_id, WAITING, "재작성", text=again)
    return {"req_id": req_id, "status": REJECTED if again is None else WAITING, "text": again or row.payload["text"]}
