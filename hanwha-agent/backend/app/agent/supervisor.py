# supervisor 의 고르는 규칙
# - 지금은 규칙(코드)으로 고른다. 모델이 고르게 바꿔도 pick_worker 자리만 바뀐다
from __future__ import annotations

# supervisor 가 고르는 횟수 상한
MAX_TURNS = 4

# 질문에 이 낱말이 있으면 검색 뒤 초안까지 만든다
DRAFT_WORDS = ("신청서", "초안")


# 상태를 보고 다음 담당을 고른다
def pick_worker(state: dict) -> str:
    if state.get("turns", 0) >= MAX_TURNS:
        return "finish"
    if "sources" not in state:
        return "search"
    # sources 가 아니라 passed 를 본다
    # - 검색은 임계값 미달이어도 후보를 돌려준다. 「점심 메뉴 신청서」도 sources 가 차 있어 초안이 만들어졌다
    if any(w in state["question"] for w in DRAFT_WORDS) and state.get("passed") and "draft" not in state:
        return "draft"
    return "finish"
