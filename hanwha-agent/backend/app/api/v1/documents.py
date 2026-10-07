from fastapi import APIRouter, BackgroundTasks, Query, File, Form, UploadFile
from typing import Annotated

import shutil
from datetime import date 
from pathlib import Path

from app.schemas.document import DocumentOut, DocumentCreateOut, JobOut
from app.api.v1.deps import SettingsDep, LoggerDep
from app.core.exceptions import NotFound, ValidationFailed
from app.services import document_service

# 문서 API를 모아주는 라우터
router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

# 파일 업로드될 경로 지정
UPLOAD_DIR = Path("uploads")

ALLOWED_EXTS = {".docx", ".pdf", ".txt"}


# 문서 목록 요청
@router.get("", response_model=list[DocumentOut]) # ...:8000/api/v1/documents
def list_documents(
    dept_id: str | None = None,
    security_level: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict]:

    # 서비스 함수와 연결
    # 임시 데이터가 아닌 DB와 연결
    # service -> repository -> DB 데이터 조회
    return document_service.list_documents(
        dept_id=dept_id,
        security_level=security_level,
        status=status,
        q=q,
        limit=limit
    )

# 문서 등록 
@router.post("", response_model=DocumentCreateOut, status_code=201)
def upload_document(
    doc_id: Annotated[str, Form()],
    title: Annotated[str, Form()],
    dept_id: Annotated[str, Form()],
    security_level: Annotated[str, Form()],
    version: Annotated[str, Form()],
    effective_from: Annotated[date, Form()],
    file: Annotated[UploadFile, File()],
    # BackgroundTasks
    # - 타입만 적어 두면 FastAPI 가 넣어 준다. 요청 본문에서 받는 값이 아니다.
    # - Form/File 뒤에 와도 되지만 기본값이 없는 인자이므로 logger(=Depends) 보다 앞에 둔다.
    background: BackgroundTasks,
    logger: LoggerDep,
) -> dict:
    safe_name = Path(file.filename or "").name
    ext = Path(safe_name).suffix.lower()

    # docx/pdf/txt 아니면 업로드 예외 처리
    if ext not in ALLOWED_EXTS:
        
        raise ValidationFailed(
            f"{ext or '확장자 없는'} 파일은 등록할 수 없습니다. "
            "DOCX 또는 PDF, TXT 로 변환해 다시 올려 주세요."
        )

    # 업로드 폴더 없으면 생성
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # 경로/파일명.확장자
    # uuid로 지정하는 것을 추천
    # 저장할 파일명은 doc_id_version
    dest = UPLOAD_DIR / f"{doc_id}_{version}{ext}"

    # 파일을 조금씩 나눠서 업로드
    with dest.open("wb") as out:
        # 파일을 dest(저장위치+파일명)으로 복사
        shutil.copyfileobj(file.file, out)

    logger.info("문서 파일 저장: %s (%s)", dest, security_level)

    # DB에 파일정보 저장
    result = document_service.create_document(
        doc_id=doc_id,
        title=title,
        dept_id=dept_id,
        security_level=security_level,
        version=version,
        effective_from=effective_from,
        file_path=dest.as_posix(),
        file_format=ext.lstrip("."),
    )

    # 파싱·청킹을 여기서 바로 부르지 않는다
    # - 동기로 부르면(= document_service.ingest_document(...)) 응답이 그만큼 늦는다.
    #   재료 문서는 0.2초 안이지만 수백 쪽 PDF 가 들어오면 요청이 그 시간만큼 매달린다.
    # - 작업 번호만 먼저 끊어 주고, 실제 처리는 응답을 보낸 뒤 배경에서 돌린다.
    job_id = document_service.start_ingest_job(
        doc_id=doc_id, version=version, path=dest.as_posix()
    )
    background.add_task(document_service.run_ingest_job, job_id)

    # 호출이 아니라 등록이다. 괄호를 붙여 run_ingest_job(job_id) 로 쓰면
    # 지금 당장 실행되고 그 반환값(None)이 배경 작업으로 등록된다.
    return {**result, "job_id": job_id}


# 업로드 작업 하나의 진행 상태 조회
# - 화면이 1초에 한 번 두드린다. 선언 위치가 중요하다.
#   아래 "/{doc_id}" 보다 뒤에 두면 "jobs" 가 doc_id 로 잡혀 404 가 난다.
@router.get("/jobs/{job_id}", response_model=JobOut)
def read_job(job_id: str) -> dict:
    return document_service.get_job(job_id)


# 문서 1개 조회 : ...:8000/api/v1/documents/문서id값
@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str) -> dict:
    return document_service.get_document(doc_id=doc_id)