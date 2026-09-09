from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI(
    title="사내 업무 에이전트 연습",
    version="0.1.0"
)

# --- 사용자 요청을 처리해줄 uri 매핑 함수들 ---

# 요청 함수
# GET /health
@app.get("/health")
def health() -> dict:
    # 리턴값
    # 요청에 응답해줄 데이터
    return {"status": "ok"} 

# * 쿼리 파라미터 *
# ex. 문서 목록 조회 함수 : http://127.0.0.1:8000/documents?dept=hr&limit=20
@app.get("/documents")
def list_documents(
    dept: str | None = None,
    limit: int = 20
) -> dict:
    return {
        "dept" : dept,
        "limit" : limit
    }

# * 요청 범위 제한 *
# ex. 문서 목록 조회 시 범위 제한 주기
@app.get("/document-limited")
def list_document_limited(
    dept: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> dict:
    return {
        "dept" : dept,
        "limit" : limit
    }

# * 경로 변수 *
# 고정 경로를 위에 배치

# ex. 최근 문서를 조회하는 함수
@app.get("/documents/latest")
def get_document() -> dict:
    return {
        "doc_id" : "latest",
        "title" : "latest 문서 제목"
    }

# 경로 변수를 아래에 배치
# ex. 특정 문서를 조회하는 함수
@app.get("/documents/{doc_id}")
def get_document(doc_id: str) -> dict:
    return {
        "doc_id" : doc_id,
        "title" : f"{doc_id} 문서 제목"
    }


# ex. 타입 검증 - 레벨 조회
@app.get("/levels/{level}")
def get_level(level: int) -> dict:
    return {"level": level}