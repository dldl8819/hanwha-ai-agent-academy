
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

# 대기 중인 요청 한건 
class ApprovalOut(BaseModel):
    req_id: str
    text: str
    requester: str
    action_type: str
    status: str
    requested_at: datetime
    events: list[str]

# 화면에 지표 네 개 띄울때 필요한 데이터 
class ApprovalSummaryOut(BaseModel):
    waiting: int
    approved_today: int
    rejected_today: int
    avg_minutes: int | None

# 지표와 목록을 함께 주는 데이터 형태 
class ApprovalListOut(BaseModel):
    summary: ApprovalSummaryOut
    items: list[ApprovalOut]

# 승인,반려 한번의 결과를 담는 형태 
class DecisionOut(BaseModel):
    req_id: str
    status: str
    message: str

# 반려 요청 본문 담아줄 형태 
class RejectIn(BaseModel):
    note: str = Field(min_length=1)
