# 문서 관련 쿼리문들 모아두는 공간 
# DB에 요청
from __future__ import annotations
from sqlalchemy import Row, desc, or_, select
from sqlalchemy.orm import Session, joinedload
from app.models.document import Document, DocumentVersion

# 문서 목록 조회
def list_documents(
    # DB 세션
    session: Session, # 서비스가 전달해주는 session
    *,
    dept_id: str | None = None,
    security_level: str | None = None,
    status: str | None = None,
    # 문서명, 문서 번호에 이 글자만 들어간 것만 조회
    # - 검색 기능에 사용
    q: str | None = None, 
    limit: int = 50,
) -> list[Row]:

    # 쿼리문
    stmt = select(DocumentVersion, Document).join(
        Document, DocumentVersion.doc_id == Document.id
    )
    # 조건값 여부에 따라 쿼리문에 조건식 추가 
    if dept_id:
        stmt = stmt.where(Document.dept_id == dept_id)
    if security_level:
        stmt = stmt.where(Document.security_level == security_level)
    if status:
        stmt = stmt.where(DocumentVersion.status == status)
    if q:
        stmt = stmt.where(
            or_(Document.title.ilike(f"%{q}%"), Document.id.ilike(f"%{q}%"))
        )
    # - 즉시 로딩
    # - 부서 테이블도 조인해서 함께 가져오기
    stmt = stmt.options(joinedload(Document.dept))
    # 정렬(order_by), 개수 제한(limit)
    stmt = stmt.order_by(Document.id, desc(DocumentVersion.version)).limit(limit)
    # 최종 결과를 리스트로 만들어서 리턴
    return list(session.execute(stmt).all())
    
# 문서_id로 문서 1개 조회
def get_document(session: Session, doc_id: str) -> Document | None:
    return session.get(Document, doc_id)

# 특정 문서에 버전 1개 추가
def add_version(session: Session, doc: Document, **fields) -> DocumentVersion:
    version = DocumentVersion(doc_id=doc.id, **fields)
    session.add(version)
    session.flush()
    return version
