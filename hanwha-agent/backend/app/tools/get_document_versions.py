# 문서 버전 이력 조회 도구 (읽기 전용, none 등급)
# - import 될 때 등록소에 스스로 등록한다 (send_slack 과 같은 방식)
from __future__ import annotations

from app.tools.registry import SideEffect, Tool, register

SCHEMA = {
    "name": "get_document_versions",
    "description": "문서번호로 문서 버전 이력을 조회한다. 어느 버전이 현행이고 언제부터 언제까지였는지 알려 준다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "doc_id": {"type": "string", "description": "문서번호. 예: DOC-HR-014"},
        },
        "required": ["doc_id"],
    },
}


# 문서 하나의 버전 이력을 최신 버전부터 돌려준다
def _run(*, doc_id: str) -> dict:
    from app.db.session import session_scope
    from app.repositories import document_repo

    with session_scope() as s:
        doc = document_repo.get_document(s, doc_id)
        if doc is None:
            return {"error": f"문서를 찾을 수 없습니다: {doc_id}"}

        # 주의 : 버전 문자열 정렬이라 v10.0 이 v2.0 보다 뒤로 간다. 지금 문서는 한 자리 판뿐이다
        versions = sorted(doc.versions, key=lambda v: v.version, reverse=True)
        return {"doc_id": doc.id, "title": doc.title, "dept": doc.dept.name,
                "security_level": doc.security_level,
                "versions": [{"version": v.version, "status": v.status, "period": v.period,
                              "chunk_count": v.chunk_count, "searchable": v.is_searchable}
                             for v in versions]}


register(Tool(name=SCHEMA["name"], description=SCHEMA["description"],
              side_effect=SideEffect.NONE, fn=_run, schema=SCHEMA))
