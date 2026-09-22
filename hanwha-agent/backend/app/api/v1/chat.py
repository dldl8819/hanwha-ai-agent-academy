from __future__ import annotations

# 채팅 라우터
# - 하는 일은 "받아서 서비스에 넘기고, 돌려준다" 뿐이다
# - 가드·재시도·폴백은 전부 chat_service 안에 있고, 라우터는 그 판단에 끼어들지 않는다
#   (계층 규칙은 backend/tests/test_layers.py 가 import 목록으로 검사한다)

from fastapi import APIRouter

from app.schemas.chat import AskOut, ChatRequest
from app.services import chat_service

# prefix 는 main.py 의 "/api/v1" 뒤에 이어 붙는다 → 최종 경로 /api/v1/chat/messages
# tags 는 /docs 화면에서 이 라우터의 묶음 제목이 된다
router = APIRouter(prefix="/chat", tags=["chat"])


# 질문 한 건을 받아 답변을 돌려준다
# - response_model=AskOut : 돌려주는 객체를 AskOut 으로 한 번 더 걸러서 내보낸다
#   서비스가 필드를 더 담아 보내도 스키마에 없는 값은 응답에 나가지 않는다
@router.post("/messages", response_model=AskOut)
def create_message(payload: ChatRequest) -> AskOut:
    # ChatRequest 가 길이(2~2000자)를 이미 걸렀지만 여기서 멈추지 않는다
    # - 화면을 거치지 않는 호출도 있어서, 실제 상한은 서비스 안의 가드(check_question)가 다시 본다
    return chat_service.ask(question=payload.question)


# 실행 기록 한 건 조회
# - response_model 을 두지 않았다. 서비스가 만든 dict 를 그대로 내보낸다
#   기록 조회는 화면에서 그때그때 필드를 더 보고 싶어지는 자리라 스키마로 굳히지 않았다
#   (대신 무엇이 나가는지는 chat_service.get_run() 의 dict 한 곳에서만 정한다)
@router.get("/runs/{run_id}")
def read_run(run_id: str) -> dict:
    # 없는 번호면 서비스가 NotFound 를 던지고, main.py 의 전역 핸들러가 404 로 바꿔 내보낸다
    # - 라우터에서 try/except 로 404 를 만들지 않는다. 그 판단은 계층마다 흩어지면 안 된다
    return chat_service.get_run(run_id=run_id)
