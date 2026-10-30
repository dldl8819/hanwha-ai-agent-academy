# 그래프 상태
# - 질문 하나가 그래프를 한 바퀴 도는 동안 노드들이 함께 읽고 쓰는 칸
# - total=False : 처음엔 question·user 만 있고, 나머지는 노드가 채운다
import operator
from typing import Annotated, TypedDict


class WorkflowState(TypedDict, total=False):
    question: str                 # 입력
    user: dict                    # 입력
    sources: list[dict]           # search 가 채운다
    passed: bool                  # 갈래를 고르는 값
    versions: dict                # found / insufficient 가 채운다
    note: str                     # insufficient 가 채운다
    # 리듀서 : 노드가 trace 를 돌려주면 덮어쓰지 않고 이어 붙인다
    trace: Annotated[list[str], operator.add]


# 순환 그래프 상태 : 검색 → (모자라면) 질문 고치기 → 다시 검색
class LoopState(WorkflowState, total=False):
    query: str      # 고친 질문 (원 질문은 question 에 그대로)
    fixes: int      # 몇 번 고쳤는지


# 승인 그래프 상태 : 초안 → 사람 결정(멈춤) → 전송
class ApprovalState(TypedDict, total=False):
    text: str       # 보낼 문구 (draft 가 채운다)
    decision: dict  # 재개할 때 받은 사람의 결정 (gate 가 채운다)
    result: dict    # 전송 결과 (send 가 채운다)
    rewrites: int   # 반려 뒤 다시 쓴 횟수 (rewrite 가 센다)


# Supervisor 그래프 상태 : supervisor 가 고른 담당 → 다시 supervisor → ...
class SupervisorState(WorkflowState, total=False):
    next: str       # supervisor 가 고른 다음 담당
    turns: int      # supervisor 가 고른 횟수
    draft: dict     # draft 담당이 채운다
    run_id: str     # draft 가 만든 실행 기록 번호
