"""검색 정책

기본 검색은 지금 효력이 있는 최신본만 대상으로 한다.

벡터 검색은 "가장 가까운 k 개"를 돌려줄 뿐 맞는 답이 있는지, 보여 줘도 되는지는
가리지 않는다. 그 판단을 여기서 한다. 거르는 기준이 코드 여기저기 흩어지면
무엇이 왜 빠졌는지 설명할 수 없게 되므로 한 자리에 모은다.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.org import CLEARANCE

CURRENT = "현행"


@dataclass
class SearchPolicy:
    current_only: bool = True           # 현행 버전만 검색 대상에 넣는다
    allow_past_on_request: bool = True  # 사용자가 명시하면 이전 버전도 본다
    respect_clearance: bool = True      # 보안 등급으로 문서를 거른다
    threshold: float = 0.55             # 이 점수에 못 미치면 '근거 부족'


# 아무 조건이 없으면 쓰는 기본 정책
DEFAULT = SearchPolicy()


# 질문이 이전 버전을 가리키는지 본다
# - 공백을 지우고 찾는다. "이전 버전" 과 "이전버전" 을 따로 적지 않기 위해서다.
# - 글자만 보는 방식이라 "예전에는 몰랐는데 지금 숙박비가" 같은 문장도 과거로 읽는다.
#   놓치는 쪽보다 넓게 잡는 쪽이 낫다고 보고 두지만, 정확한 판정은 아니다.
def wants_past_version(question: str) -> bool:
    q = (question or "").replace(" ", "")
    hints = ("예전", "이전버전", "과거버전", "개정전", "구버전", "예전규정")
    return any(hint in q for hint in hints) or "v1." in q


# 이 버전을 검색 대상에 넣어도 되는지
def version_allowed(version_status: str, *, policy: SearchPolicy, question: str) -> bool:
    if not policy.current_only:
        return True
    if version_status == CURRENT:
        return True
    return policy.allow_past_on_request and wants_past_version(question)


# 이 등급의 문서를 이 사용자가 봐도 되는지
# - CLEARANCE 는 등급 이름을 숫자로 바꾼 표다. 사용자 등급이 문서 등급 이상이어야 한다.
# - 모르는 이름은 1(가장 낮음)로 본다. 오타가 나면 더 보이는 게 아니라 덜 보이는 쪽으로 틀린다.
def clearance_allowed(user_clearance: str, doc_level: str, *, policy: SearchPolicy) -> bool:
    if not policy.respect_clearance:
        return True
    return CLEARANCE.get(user_clearance, 1) >= CLEARANCE.get(doc_level, 1)


# 검색 결과를 정책으로 거른다.
# 통과한 것과 '왜 걸렀는지' 를 함께 돌려준다 — 조용히 빼면 답이 왜 부실한지 알 수 없다.
def filter_candidates(
    rows: list[dict], *, user: dict, question: str, policy: SearchPolicy = DEFAULT
) -> tuple[list[dict], list[str]]:
    kept: list[dict] = []
    reason: list[str] = []

    for row in rows:
        if not version_allowed(row.get("version_status", CURRENT), policy=policy, question=question):
            reason.append(f"{row['title']} {row['version']} - 만료 버전")
            continue
        if not clearance_allowed(
            user.get("clearance", "일반"), row.get("security_level", "일반"), policy=policy
        ):
            # 사유에 문서 제목이 남는다. 등급 때문에 가린 문서의 이름이
            # 사유를 통해 드러나므로, 사용자에게 보일 때는 제목을 빼야 한다.
            reason.append(f"{row['title']} - 보안등급({row.get('security_level')}) 차단")
            continue
        kept.append(row)

    return kept, reason
