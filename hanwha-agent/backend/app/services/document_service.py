"""
서비스
- 사용자 요청에 대한 로직 처리 하는 곳
- DB 정보가 필요하면 repository 호출
- 트랜잭션을 여닫는 자리
"""
from __future__ import annotations

from datetime import date
from uuid import uuid4

from app.core.exceptions import NotFound, ValidationFailed
# 세션
# - DB 접속을 하기 위한 통로
from app.db.session import session_scope
# 모델 
# - 데이터 넣는 가방
from app.models.document import Chunk, Document, DocumentVersion
# 리포지토리
# - DB 접속 시 필요
from app.repositories import document_repo

# 사용자에게 전달할 데이터를 만들어주는 함수
def _to_out(version: DocumentVersion, document: Document) -> dict:
   # 여러 객체에 나뉘어있는 데이터를 하나로 묶어주는 처리
    return {
        "doc_id": document.id,
        "title": document.title,
        "dept": document.dept.name,
        "version": version.version,
        "security_level": document.security_level,
        "file_format": version.file_format,
        "status": version.status,
        "effective_from": version.effective_from,
        "expires_at": version.expires_at,
        "index_status": version.index_status,
        "index_progress": version.index_progress,
    }

# 문서 목록 조회
def list_documents(
    *,
    dept_id: str | None = None,
    security_level: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> list[dict]:

    # 세션 만들어서 repository 호출해 결과 받기 
    with session_scope() as s:
        # repository(document_repo)의 문석 목록 호출
        rows = document_repo.list_documents(
            s,
            dept_id=dept_id,
            security_level=security_level,
            status=status,
            q=q,
            limit=limit,
        )
        # 위 rows를 _to_out에 문서 버전과 문서를 전달해서 리스트로 전달
        return [_to_out(version, document) for version, document in rows]

# 문서 1개 조회
# - 문서 id값을 외부에서 전달해주면 해당 문서 1개 조회해서 리턴
def get_document(*, doc_id: str) -> dict:
    # 세션 생성해 문서 1개 조회
    with session_scope() as s:
        document = document_repo.get_document(s, doc_id)
        if document is None:
            raise NotFound(f"문서를 찾을 수 없습니다: {doc_id}")
        current = document.current
        if current is None:
            raise NotFound(f"현행 버전이 없습니다: {doc_id}")
        return _to_out(current, document)

# 문서 등록(저장)
def create_document(
    *,
    doc_id: str,
    title: str,
    dept_id: str,
    security_level: str,
    version: str,
    effective_from: date,
    file_path: str,
    file_format: str,
    owner_id: int | None = None,
) -> dict:

    with session_scope() as s:
        document = document_repo.get_document(s, doc_id)
        created = document is None
        # 기존에 없던 문서인지 확인 후 문서 저장 
        if document is None:
            document = Document(
                id=doc_id,
                title=title,
                dept_id=dept_id,
                security_level=security_level,
                owner_id=owner_id,
            )
            s.add(document)
            s.flush()
        # 문서 버전이 이미 존재할 때 예외 처리
        elif any(v.version == version for v in document.versions):
            raise ValidationFailed(
                f"{doc_id} 의 {version} 은(는) 이미 등록되어 있습니다. "
                "판 번호를 올려 다시 올려 주세요."
            )

        # 문서 버전 저장
        document_repo.add_version(
            s,
            document,
            version=version,
            status="현행",
            effective_from=effective_from,
            expires_at=None,
            file_path=file_path,
            file_format=file_format,
            index_status="대기",     
        )
        # 저장 후 화면에 전달할 데이터 리턴
        return {
            "doc_id": document.id,
            "title": document.title,
            "version": version,
            "file_format": file_format,
            "file_path": file_path,
            "created": created,
        }


# 업로드된 파일 하나를 파싱 -> 청킹 -> 저장까지 이어주는 함수
# - 여기까지가 RAG 11단계의 ②파싱 ③청킹이다. ④임베딩은 아직 없다.
def ingest_document(*, doc_id: str, version: str, path: str) -> dict:
    # 함수 안에서 import 하는 이유
    # - app.rag 는 무거운 쪽(파서 라이브러리들)을 끌고 온다.
    #   모듈 맨 위에 두면 서버가 뜰 때마다 전부 읽어 기동이 느려진다.
    from app.rag import chunker, parser

    with session_scope() as s:
        # 어느 판에 붙일 청크인지 먼저 확정한다
        document = document_repo.get_document(s, doc_id)
        dv = next((v for v in document.versions if v.version == version), None) if document else None
        if dv is None:
            raise NotFound(f"문서 버전을 찾을 수 없습니다: {doc_id} {version}")

        parsed = parser.parse(path)
        if parsed is None:
            raise ValidationFailed(f"파일을 읽지 못했습니다: {path}")

        drafts = chunker.chunk(parsed)

        # 같은 판을 다시 올린 경우 — 더하지 않고 갈아끼운다
        # - 지우지 않고 add 만 하면 같은 조항이 두 벌 남아 검색이 같은 근거를 중복으로 집는다.
        # - flush() 로 DELETE 를 먼저 내보낸다. 이게 없으면 SQLAlchemy 가 INSERT 를 먼저 보낼 수 있고
        #   (version_id, ord) 로 유일성을 걸게 되는 순간 충돌한다.
        for old in list(dv.chunks):
            s.delete(old)
        s.flush()

        for i, d in enumerate(drafts):
            s.add(Chunk(version_id=dv.id, ord=i, kind=d.kind, locator=d.locator, text=d.text))

        dv.chunk_count = len(drafts)
        # 주의: 임베딩을 하지 않았는데도 "완료" 로 적는다.
        # - DocumentVersion.is_searchable 은 index_status == "완료" 를 보므로
        #   지금 구조에서는 벡터가 없는 판도 검색 대상으로 판정된다.
        #   ④임베딩을 붙일 때 이 두 줄을 "임베딩까지 끝난 뒤" 로 옮겨야 한다.
        dv.index_status = "완료"
        dv.index_progress = 100
        dv.indexed_at = date.today()
        return {
            "chunks": len(drafts),
            "tables": parsed.table_count,
            "summary": chunker.summarize(drafts),
        }


# ─────────────────────────────────────────────────────────────
# 작업 번호 배부 — 동기 응답을 끊고 진행 상태를 따로 묻게 만드는 자리
# ─────────────────────────────────────────────────────────────

# 작업 상태를 담아두는 곳
# - 프로세스 메모리다. 서버를 재시작하면 전부 사라지고,
#   uvicorn --reload 가 코드 변경으로 다시 뜨면 진행 중이던 작업도 함께 사라진다.
#   워커를 2개 이상 띄우면 요청이 다른 워커로 가 "작업을 찾을 수 없습니다" 가 난다.
#   실제 운영이라면 DB나 Redis 로 옮길 자리다. 지금은 한 프로세스 전제로 둔다.
_JOBS: dict[str, dict] = {}

# 화면에 보여줄 단계 이름
# - 뒤의 2개는 아직 구현이 없다. 목록에 남겨 두어 무엇이 빠졌는지 화면에 드러나게 한다.
_STEP_NAMES = [
    "파일 검증",
    "문서 파싱",
    "표 -> 마크다운 변환",
    "청킹",
    "임베딩",
    "검색 반영 및 현행 버전 지정",
]
# 위 목록에서 지금 실제로 돌아가는 단계 수
_DONE_STEPS = 4


# 작업 하나를 만들어 번호를 돌려주는 함수
def start_ingest_job(*, doc_id: str, version: str, path: str) -> str:
    # uuid4 의 앞 8자만 쓴다. 화면에 띄우고 눈으로 비교하기 위한 길이다.
    # - 32자 중 8자만 남기므로 충돌 가능성이 생긴다. 한 프로세스 안의 임시 작업이라 감수한다.
    job_id = uuid4().hex[:8]
    _JOBS[job_id] = {
        "job_id": job_id, "doc_id": doc_id, "version": version, "path": path,
        "status": "대기", "progress": 0,
        "steps": [{"name": n, "state": "todo"} for n in _STEP_NAMES],
        "chunk_count": 0, "message": "",
    }
    return job_id


# 작업을 실제로 돌리는 함수
# - BackgroundTasks 가 응답을 보낸 뒤에 호출한다.
# - async 가 아니라 평범한 def 다. BackgroundTasks 는 동기 함수를 스레드풀에서 돌린다.
#   async def 로 쓰면서 안에서 블로킹 파싱을 하면 이벤트 루프를 잡아 서버 전체가 멈춘다.
def run_ingest_job(job_id: str) -> None:
    job = _JOBS.get(job_id)
    if job is None:
        return
    try:
        job["status"] = "진행 중"
        steps = job["steps"]
        result = ingest_document(doc_id=job["doc_id"], version=job["version"], path=job["path"])

        # 단계별 중간 보고를 하지 않는다
        # - ingest_document() 는 파싱·청킹을 한 번에 끝내고 결과만 돌려준다.
        #   그래서 "진행 중"에서 바로 4단계가 함께 ok 로 바뀐다.
        #   단계마다 갱신하려면 ingest_document 가 콜백을 받아야 한다.
        for i in range(_DONE_STEPS):
            steps[i]["state"] = "ok"
        steps[1]["time"] = f"표 {result['tables']}개 인식"
        steps[2]["time"] = f"표 {result['tables']}개"
        steps[3]["time"] = f"{result['chunks']}청크"

        # 진행률은 구현된 단계 기준이다. 4/6 이라 완료해도 66% 에서 멈춘다.
        # - 100% 로 적으면 임베딩이 끝난 것처럼 보인다. 덜 된 것을 덜 됐다고 두는 쪽을 택했다.
        job["progress"] = int(_DONE_STEPS / len(steps) * 100)
        job["chunk_count"] = result["chunks"]
        job["message"] = result["summary"]
        job["status"] = "완료"
    except Exception as exc:
        # 배경 작업의 예외는 요청 쪽으로 돌아갈 길이 없다
        # - 응답은 이미 201 로 나갔다. 여기서 잡아 작업에 적어 두지 않으면
        #   화면은 "진행 중" 에 영원히 머물고 원인은 아무 데도 남지 않는다.
        job["status"] = "실패"
        job["message"] = str(exc)
        for st in job["steps"]:
            if st["state"] == "todo":
                st["state"] = "no"
                break


# 작업 하나의 진행 상태를 돌려주는 함수
def get_job(job_id: str) -> dict:
    job = _JOBS.get(job_id)
    if job is None:
        raise NotFound(f"작업을 찾을 수 없습니다: {job_id}")
    return job
