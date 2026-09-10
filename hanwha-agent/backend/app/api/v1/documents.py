from fastapi import APIRouter, Query
from typing import Annotated

from app.schemas.document import DocumentOut
from app.api.v1.deps import SettingsDep
from app.core.exceptions import NotFound

# 문서 API를 모아주는 라우터
router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

# DB 사용 전, 임시 데이터 추가 (나중에 없앨 예정)
_DOCS: list[dict] = [
    {
        "doc_id": "DOC-HR-014",
        "title": "2026년 휴가 운영 규정",
        "dept": "인사",
        "version": "v2.0",
        "security_level": "일반",
        "file_format": "docx",
        "status": "active",
        "secret_note":"담당자 메모 - 개정 예고"
    },
    {
        "doc_id": "DOC-HR-021",
        "title": "복리후생 운영 지침",
        "dept": "인사",
        "version": "v2.0",
        "security_level": "일반",
        "file_format": "pdf",
        "status": "active",
        "secret_note":"담당자 메모 - 인사팀 검토중"
    },
    {
        "doc_id": "DOC-SE-011",
        "title": "정보보안 관리 규정",
        "dept": "보안",
        "version": "v2.0",
        "security_level": "3급",
        "file_format": "pdf",
        "status": "active",
        "secret_note":"담당자 메모 - 열람 이력 점검 필요"
    },
    {
        "doc_id": "DOC-PU-007",
        "title": "구매 계약 업무 지침",
        "dept": "구매",
        "version": "v2.0",
        "security_level": "대외비",
        "file_format": "docx",
        "status": "active",
        "secret_note":"담당자 메모 - v4.0 준비중"
    },
]

# 문서 목록 요청
@router.get("", response_model=list[DocumentOut]) # ...:8000/api/v1/documents
def list_documents(
    settings: SettingsDep, # 외존성 주입: 별칭으로 처리
    dept: str | None = None,
    security_level: str | None = None,
    file_format: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict]:
    result = _DOCS.copy()
    if dept is not None:
        result = [doc for doc in result if doc["dept"] == dept]
    if security_level is not None:
        result = [doc for doc in result if doc["security_level"] == security_level]
    if file_format is not None:
        result = [doc for doc in result if doc["file_format"] == file_format]
    return result[:limit]


'''
# 예외 테스트
@router.get("/find")
def find_doc():
    raise NotFound("문서 못 찾음")

'''

# 문서 1개 조회 : ...:8000/api/v1/documents/문서id값
@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str) -> dict:
    for doc in _DOCS:
        if doc["doc_id"] == doc_id:
            return doc

    raise NotFound(f"문서를 찾지 못했습니다.: {doc_id}")