# 사내 규정 검색 도구
# - 도구 하나 = NAME · SIDE_EFFECT · SCHEMA · run() 네 가지
# - SCHEMA 는 모델에게 보내는 설명서, run() 은 우리 코드가 실행하는 본체
from __future__ import annotations

NAME = "search_documents"

# 부작용 등급 : none(조회) / internal(내부 쓰기) / external(외부 실행, 승인 필요)
SIDE_EFFECT = "none"

# 모델에게 돌려줄 근거 필드
# - text 가 근거 원문이다. quote 는 화면용으로 220자에서 잘린 것이라 모델에게는 모자라다
SOURCE_KEYS = ("doc_id", "title", "version", "locator", "score", "quote", "text")

SCHEMA = {
    "name": NAME,
    "description": "사내 규정 문서를 검색해 근거 문단을 돌려준다. 현행 버전, 보안 등급 필터가 적용된다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "찾을 내용. 질문을 그대로 넣어도 된다."},
        },
        "required": ["query"],
    },
}

# 검색어 하나로 사내 문서를 검색해 근거를 리턴
# - user 는 모델이 아니라 서비스가 넣는다. 스키마에 user 가 없으니 모델은 보안등급을 바꿀 수 없다
def run(*, query: str, user: dict) -> dict:
    from app.db.session import session_scope
    from app.rag.retriever import LiveRetriever

    with session_scope() as session:
        found = LiveRetriever().search(question=query, user=user, session=session)
    return {
        "sources": [{k: s.get(k) for k in SOURCE_KEYS} for s in found.sources],
        "steps": found.steps,
        "best_score": found.best_score,
        "passed": found.passed,
        "version_note": found.version_note,
        "threshold": found.threshold,
    }
