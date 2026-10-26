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
