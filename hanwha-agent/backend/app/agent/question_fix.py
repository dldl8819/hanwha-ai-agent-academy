# 질문 고치기 노드
# - 입으로 하는 말을 규정 낱말로 바꾼다 (호텔비 → 숙박비)
# - 검색이 모자라면 고친 질문으로 다시 검색하는 순환 그래프에서 쓴다
from __future__ import annotations

from app.agent.patterns import route_after_search

FIX_WORDS: dict[str, str] = {
    "호텔비": "숙박비",
    "밥값": "식비",
    "기차표": "교통비",
}

# 질문 고치기 상한. 이 횟수를 넘으면 insufficient 로 끝낸다
MAX_FIXES = 2


# 질문을 사전대로 한 번 고친다. 원 질문(question)은 두고 고친 것을 query 에 둔다
def fix_question(state: dict) -> dict:
    q = state.get("query") or state["question"]
    for old, new in FIX_WORDS.items():
        q = q.replace(old, new)
    return {"query": q, "fixes": state.get("fixes", 0) + 1}


# 검색 뒤 갈래 : 찾았으면 found, 못 찾았으면 상한까지 fix, 넘으면 insufficient
# - 고쳐도 질문이 그대로면 fix 로 보내지 않는다. 같은 질문으로 검색을 다시 돌릴 뿐이다
#   (강사님 코드는 「점심 메뉴」에도 같은 검색을 세 번, 약 18초씩 돌렸다)
def route_with_fixes(state: dict) -> str:
    if route_after_search(state) == "found":
        return "found"
    if state.get("fixes", 0) >= MAX_FIXES:
        return "insufficient"
    current = state.get("query") or state["question"]
    return "fix" if fix_question(state)["query"] != current else "insufficient"
