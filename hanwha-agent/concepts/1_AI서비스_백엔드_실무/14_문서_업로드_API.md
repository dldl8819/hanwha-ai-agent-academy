# 스키마와 문서 업로드 API

## 모델과 스키마

| | 모델 `app/models/document.py` | 스키마 `app/schemas/document.py` |
| --- | --- | --- |
| 개념 | DB 테이블의 한 행을 담는 객체 | 데이터를 외부로 전달할 때 쓰는 객체 |
| 구성 요소 | `Mapped`, `mapped_column` | `BaseModel` |
| 읽는 주체 | 데이터베이스(내부) | 브라우저 등 외부(화면) |
| 값 구성 | 옵션 없음 — DB 테이블에 저장되는 모든 데이터를 그대로 가짐 | 화면에 안 띄울 정보는 제외 가능, 옵션(기본값 등)이 많을 수 있음 |

**모델은 절대로 화면에 그대로 전달하지 않는다.** 브라우저 개발자 도구에 그대로 노출되면 보안에 취약해진다 — [[10_FastAPI]]에서 `secret_note`를 `DocumentOut`에서 뺀 것과 같은 이유다.

## 스키마 — `app/schemas/document.py`

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date

class DocumentOut(BaseModel):
    doc_id: str
    title: str
    dept: str
    version: str
    security_level: Literal["일반", "3급", "대외비"]
    file_format: Literal["docx", "pdf"]
    status: Literal["현행", "만료"]
    effective_from: date
    expires_at: date | None = None
    index_status: Literal["대기", "재임베딩", "완료", "보관"] = "대기"
    index_progress: int = Field(default=0, ge=0, le=100)

# 업로드 응답 — 무엇이 어디에 저장됐는지만 알려주는 객체
class DocumentCreateOut(BaseModel):
    doc_id: str = Field(examples=["DOC-HR-014"])
    title: str
    version: str = Field(examples=["v2.0"])
    file_format: Literal["docx", "pdf"]
    file_path: str = Field(examples=["uploads/DOC-HR-014_v2.0.docx"])
    created: bool = Field(
        description="문서 자체가 이번에 새로 생겼으면 True, 버전만 더했으면 False"
    )
```

`Field(examples=[...])`은 Swagger UI(`/docs`)에서 그 필드의 예시 값으로 보여준다. `DocumentCreateOut.created`처럼 `Field(description=...)`만 있고 `examples`가 없으면 필드 설명만 문서에 노출된다.

## `app/api/v1/deps.py` 확장 — 요청 단위 의존성

[[10_FastAPI]]에서 만든 `SettingsDep`에 이어, 요청마다 새로 만들어야 하는 것들을 의존성으로 추가했다.

```python
import uuid
import logging
from typing import Annotated
from fastapi import Depends, Request
from collections.abc import Iterator
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_sessionmaker

SettingsDep = Annotated[Settings, Depends(get_settings)]

# 요청 하나를 로그에서 따라갈 수 있게 하는 식별자
def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or uuid.uuid4().hex[:8]

RequestIdDep = Annotated[str, Depends(get_request_id)]

# 요청 ID가 붙은 로거
def get_request_logger(request_id: RequestIdDep) -> logging.Logger:
    return get_logger(f"api.req.{request_id}")

LoggerDep = Annotated[logging.Logger, Depends(get_request_logger)]

# 요청 하나가 사용할 DB 세션
def get_db() -> Iterator[Session]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()

SessionDep = Annotated[Session, Depends(get_db)]
```

- `get_request_id`는 클라이언트가 `X-Request-ID` 헤더를 보냈으면 그걸 쓰고, 없으면 `uuid4` 앞 8자리로 새로 만든다. 같은 요청 하나가 여러 로그 줄에 걸쳐 찍힐 때, 이 id로 "이게 같은 요청이구나"를 묶어서 추적할 수 있다.
- `LoggerDep`은 의존성 안에서 또 다른 의존성(`RequestIdDep`)을 요구하는 **중첩 의존성**이다([[10_FastAPI]] 참고). `get_request_logger`가 실행되기 전에 FastAPI가 `get_request_id`부터 먼저 해결해서 넣어준다.
- `get_db()`는 `yield`를 쓰는 의존성이다 — 응답을 만들고 나면(`yield` 이후) `finally`에서 `db.close()`가 실행되어, 요청이 끝나면 세션이 자동으로 정리된다. 다만 지금 라우터들은 `SessionDep` 대신 서비스 계층의 `session_scope()`를 쓰고 있어서, 이 의존성은 서비스를 거치지 않고 라우터에서 세션이 바로 필요한 경우를 위해 준비해둔 것이다.

## 문서 업로드

### 왜 JSON이 아닌가

파일 자체는 JSON에 담을 수 없다. 브라우저는 파일을 보낼 때 **멀티파트(multipart)**라는 별도 형식을 쓴다 — 일반 글자 칸과 파일 칸을 구역으로 나눠서 하나의 요청에 같이 담아 보내는 방식이다. 이때 HTTP 요청의 `Content-Type` 헤더는 `multipart/form-data`가 된다.

### 설치

```bash
python -m pip install python-multipart==0.0.32
```

FastAPI가 `multipart/form-data`를 파싱하려면 이 라이브러리가 필요하다.

### 업로드 연습 코드

```python
from fastapi import FastAPI, File, UploadFile
from typing import Annotated

app = FastAPI()

@app.post("/upload")
async def receive(file: Annotated[UploadFile, File()]) -> dict:
    """올라온 파일의 겉모습만 찍어본다. 저장하지 않는다."""
    head = await file.read(8)
    return {
        "이름": file.filename,
        "MIME": file.content_type,
        "크기(바이트)": file.size,
        "앞 8바이트": repr(head),
    }
```

`async def` 함수 안에서 `await file.read(...)`로 읽는다. 파일을 읽는 건 디스크 입출력을 기다리는 일이라, 기다리는 동안 서버가 다른 요청을 처리할 수 있도록 제어권을 넘겨준다는 뜻이 `await`다.

### 실전 라우터 — `app/api/v1/documents.py`

```python
from fastapi import APIRouter, Query, File, Form, UploadFile
from typing import Annotated
import shutil
from datetime import date
from pathlib import Path

from app.schemas.document import DocumentOut, DocumentCreateOut
from app.api.v1.deps import LoggerDep
from app.core.exceptions import ValidationFailed
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTS = {".docx", ".pdf"}

# 문서 목록 (검색 키워드 포함)
@router.get("", response_model=list[DocumentOut])
def list_documents(
    dept_id: str | None = None,
    security_level: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict]:
    # service -> repository -> DB 데이터 조회
    return document_service.list_documents(
        dept_id=dept_id, security_level=security_level, status=status, q=q, limit=limit
    )

# 문서 등록 (업로드)
@router.post("", response_model=DocumentCreateOut, status_code=201)
async def upload_document(
    doc_id: Annotated[str, Form()],
    title: Annotated[str, Form()],
    dept_id: Annotated[str, Form()],
    security_level: Annotated[str, Form()],
    version: Annotated[str, Form()],
    effective_from: Annotated[date, Form()],
    file: Annotated[UploadFile, File()],
    logger: LoggerDep,
) -> dict:
    safe_name = Path(file.filename or "").name
    ext = Path(safe_name).suffix.lower()

    if ext not in ALLOWED_EXTS:
        raise ValidationFailed(
            f"{ext or '확장자 없는'} 파일은 등록할 수 없습니다. "
            "DOCX 또는 PDF 로 변환해 다시 올려 주세요."
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # 저장 파일명: doc_id_version.확장자 (충돌 방지엔 uuid 방식도 고려할 만하다)
    dest = UPLOAD_DIR / f"{doc_id}_{version}{ext}"

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    logger.info("문서 파일 저장: %s (%s)", dest, security_level)

    return document_service.create_document(
        doc_id=doc_id, title=title, dept_id=dept_id, security_level=security_level,
        version=version, effective_from=effective_from,
        file_path=dest.as_posix(), file_format=ext.lstrip("."),
    )

@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str) -> dict:
    return document_service.get_document(doc_id=doc_id)
```

- 요청 본문의 텍스트 필드는 `Annotated[str, Form()]`으로, 파일은 `Annotated[UploadFile, File()]`로 받는다. 요청 하나에 텍스트와 파일이 섞여 들어오는 멀티파트 구조를 그대로 반영한 시그니처다.
- 확장자 검사는 `ALLOWED_EXTS`(집합)에 없으면 [[05_예외_계층_설계]]의 `ValidationFailed`를 던진다. 전역 예외 핸들러([[10_FastAPI]])가 이걸 잡아서 422 응답으로 바꿔준다.
- `.gitignore`에 `uploads/`도 추가해둔다 — 업로드된 실제 파일은 저장소에 커밋할 대상이 아니다(`*.db`와 같은 이유).

### 실습: 허용 확장자 추가/제거 테스트

`ALLOWED_EXTS`에 `.txt`를 임시로 넣고 실제 업로드가 되는지, 뺐을 때 거부되는지 확인하는 실습이다. 서버를 직접 띄워서 `curl`로 재현해봤다.

```bash
# .txt를 ALLOWED_EXTS에 포함한 상태
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -F "doc_id=DOC-TEST-001" -F "title=테스트" -F "dept_id=HRGA" \
  -F "security_level=일반" -F "version=v1.0" -F "effective_from=2026-01-01" \
  -F "file=@test.txt;type=text/plain"
# -> HTTP 201, 정상 저장됨

# .txt를 ALLOWED_EXTS에서 뺀 상태
# (같은 요청) -> HTTP 422
# {"code":"validation_failed","message":".txt 파일은 등록할 수 없습니다. ..."}
```

두 경우 다 코드 그대로 정상 동작했다. 만약 `.txt`를 뺐는데도 계속 업로드가 성공한다면, `--reload` 없이 띄운 서버가 옛날 `ALLOWED_EXTS`를 그대로 물고 있거나(파일을 고쳐도 서버를 재시작 안 함), 이전에 띄워둔 서버 프로세스가 남아서 새 서버와 포트가 겹친 상태일 가능성이 크다 — 서버를 완전히 재시작하고 다시 확인해야 한다.

**실습 중 발견한 별개의 이슈**: 지금 `Document`↔`DocumentVersion` 관계에는 [[11_SQLAlchemy]]의 연습 모델(`demo_models.py`)에 있던 `cascade="all, delete-orphan"`이 빠져 있다. 그래서 버전이 딸린 `Document`를 그냥 `session.delete(document)`로 지우려 하면 `IntegrityError: NOT NULL constraint failed: document_versions.doc_id`가 난다(자식 행의 `doc_id`를 `NULL`로 만들려다 실패). 지금 라우터에는 문서 삭제 기능이 없어서 당장 문제는 아니지만, 나중에 삭제 API를 추가할 때는 `versions` 관계에 `cascade` 옵션을 다시 넣거나 자식부터 명시적으로 지우는 처리가 필요하다.

참고: backend/app/api/v1/documents.py, backend/app/api/v1/deps.py, backend/app/schemas/document.py, sandbox/w2/day05/00.리포지토리.ipynb
