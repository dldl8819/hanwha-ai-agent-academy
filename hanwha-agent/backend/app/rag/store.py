from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.document import Chunk, Document, DocumentVersion

log = get_logger(__name__)

# ───── 적재 ─────

# 문서 버전의 청크를 모두 재저장하는 함수 (재 임베딩시에도 사용)
def save_chunks(session: Session, version: DocumentVersion, 
                drafts: list, vectors: list[list[float]]) -> int:
    
    # 기존에 저장된 chunks 삭제 
    for old in list(version.chunks):
        session.delete(old)
    session.flush() 

    # 새 청크와 임베딩 벡터 저장 
    for i, (d, vec) in enumerate(zip(drafts, vectors, strict=False)):
        session.add(Chunk(version_id=version.id, ord=i, kind=d.kind,
                          locator=d.locator, text=d.text, embedding=vec))
    version.chunk_count = len(drafts)
    session.flush() 
    log.info("청크 적재 : %s %s - %d청크 - %d벡터", version.doc_id, version.version, len(drafts), len(vectors))
    
    return len(drafts)


# ───── 검색 ─────

# 검색 결과 한 건을 화면이 그대로 쓸 수 있는 딕셔너리로 바꿔 주는 함수
# - 화면에 필요한 값이 테이블 셋에 흩어져 있다.
#   chunks(본문·출처) · document_versions(판·현행 여부) · documents(제목·부서·보안등급)
# - score 는 DB 가 준 거리를 뒤집은 값이다. 거리는 작을수록 가깝고 점수는 클수록 가깝다.
def _row(chunk: Chunk, version: DocumentVersion, doc: Document, score: float) -> dict:
    return {
        "chunk_id": chunk.id,
        "doc_id": doc.id,
        "title": doc.title,
        "dept_id": doc.dept_id,
        "security_level": doc.security_level,
        "version": version.version,
        "version_status": version.status,
        "locator": chunk.locator,
        "kind": chunk.kind,
        "text": chunk.text,
        "score": round(float(score), 4),
    }


# 질문 벡터에 가까운 청크를 가까운 순서로 돌려주는 함수
def vector_search(session: Session, query_vec: list[float], *, limit: int = 12) -> list[dict]:
    if not query_vec:
        return []
    # <=> 코사인 거리. 0 이면 같은 방향이다.
    distance = Chunk.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(Chunk, DocumentVersion, Document, distance)
        .join(DocumentVersion, Chunk.version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.doc_id == Document.id)
        # 벡터가 없는 청크는 거리를 잴 수 없다. 빼지 않으면 NULL 이 섞여 정렬이 흐트러진다.
        .where(Chunk.embedding.is_not(None))
        .order_by("distance")
        .limit(limit)
    )
    return [
        _row(chunk, version, doc, 1.0 - float(dist))
        for chunk, version, doc, dist in session.execute(stmt)
    ]


# ----- 키워드 검색 ------------------------------------------------
# 글자로 찾는 함수
# - 벡터 검색은 뜻이 비슷한 것을 찾는다. 고유명사나 금액처럼 글자 자체가 중요한 것은
#   뜻이 비슷한 이웃이 없어서 벡터로는 잘 안 걸린다. 그 구멍을 메우는 자리다.
def keyword_search(session: Session, query: str, *, limit: int = 12) -> list[dict]:
    stmt = (select(Chunk, DocumentVersion, Document)
            .join(DocumentVersion, Chunk.version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.doc_id == Document.id))
    rows = list(session.execute(stmt))
    if not rows:
        log.warning("키워드 검색: 청크가 한 건도 없습니다 - 적재를 먼저 하세요.")
        return []

    # BM25 가 없어도 검색 자체는 돌아가야 한다. 빈 목록을 돌려주면 하이브리드가
    # 벡터 단독으로 내려앉는다.
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        log.warning("키워드 검색이 꺼져 있습니다 - rank_bm25 미설치.")
        return []

    scores = BM25Okapi([_tokenize(c.text) for c, _, _ in rows]).get_scores(_tokenize(query))
    # 최고점으로 나눠 0~1 로 맞춘다. BM25 점수는 상한이 없어서 그대로 두면
    # 코사인 유사도와 자리를 나란히 놓을 수 없다.
    top = max(scores) if len(scores) else 0.0
    out = [
        _row(chunk, version, doc, (s / top) if top else 0.0)
        for (chunk, version, doc), s in zip(rows, scores, strict=False)
    ]
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:limit]


# 본문과 질의를 같은 규칙으로 낱말로 쪼개는 함수
# - 한 글자는 버린다. 조사와 토씨가 전부 걸려 점수를 흐린다.
def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[가-힣A-Za-z0-9]+", text or "") if len(t) > 1]


# RRF : 점수의 척도가 다른 두 결과를 *순위*로 합친다
# - 0.7*벡터 + 0.3*BM25 같은 가중합은 값의 범위가 큰 쪽이 결과를 좌우한다.
#   순위로 바꿔 합치면 두 검색이 같은 무게를 갖는다.
def fuse(vector_rows: list[dict], keyword_rows: list[dict], *, k: int = 60) -> list[dict]:
    ranks: dict[int, dict] = {}
    for source, rows in (("vector", vector_rows), ("keyword", keyword_rows)):
        for rank, row in enumerate(rows, 1):
            if row["chunk_id"] not in ranks:
                # 벡터에서 처음 본 것은 그 유사도를 그대로 들고 온다.
                # 키워드에서만 나온 것은 벡터 점수가 없으므로 0 으로 둔다.
                first = row["score"] if source == "vector" else 0.0
                ranks[row["chunk_id"]] = {**row, "score": first, "keyword_score": 0.0, "_rrf": 0.0}
            entry = ranks[row["chunk_id"]]
            entry["_rrf"] += 1.0 / (k + rank)
            if source == "keyword":
                entry["keyword_score"] = row["score"]

    merged = list(ranks.values())
    merged.sort(key=lambda r: r["_rrf"], reverse=True)
    for r in merged:
        r.pop("_rrf", None)
    return merged


# 정해진 청크들과 질문 벡터의 유사도를 재는 함수
# - 키워드에서만 올라온 청크는 벡터 점수가 비어 있다. 임계값은 코사인 유사도로
#   그은 선이므로(concepts 63) 후보 전체의 점수를 같은 자로 다시 재야 한다.
def vector_scores(session: Session, query_vec: list[float], chunk_ids: list[int]) -> dict[int, float]:
    if not query_vec or not chunk_ids:
        return {}
    distance = Chunk.embedding.cosine_distance(query_vec)
    stmt = (select(Chunk.id, distance)
            .where(Chunk.id.in_(chunk_ids))
            .where(Chunk.embedding.is_not(None)))
    return {cid: round(1.0 - float(dist), 4) for cid, dist in session.execute(stmt)}
