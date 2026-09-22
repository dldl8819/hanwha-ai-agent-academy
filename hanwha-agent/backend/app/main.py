from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
# from app.api.v1.documents import router as document_router
# from app.api.v1.auth import router as auth_router
from app.api.v1 import auth, chat, documents
from app.core.exceptions import AgentError
from contextlib import asynccontextmanager
from app.core.logging import setup_logging
from fastapi.exceptions import RequestValidationError

# lifespan 함수 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

# FastAPI 앱 생성
app = FastAPI(
    title="사내 AI 에이전트",
    version="0.1.0",
    lifespan=lifespan
)

# 서버 상태 확인용 API
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# 라우터 연결

app.include_router(
    # document_router,
    documents.router,
    prefix="/api/v1" # 옵션이라 없어도 된다.
)

app.include_router(
    # auth_router
    auth.router,
    prefix="/api/v1"
)

# 채팅 라우터 (/api/v1/chat/messages)
# - 라우터마다 한 번씩 부른다. 한 번에 여러 개를 넘길 수는 없다
#   (include_router 의 첫 인자는 router 하나이고, 나머지는 prefix 같은 옵션 자리다)
app.include_router(
    chat.router,
    prefix="/api/v1"
)

# 예외 핸들러
@app.exception_handler(AgentError)
async def handle_agent_error(
    request: Request,
    exc: AgentError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": str(exc),
            "detail": None
        }
    )

# 예외 처리
# - 사번 입력 없이 로그인 시 비밀번호 로그에 노출
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # exc.errors() 에는 사용자가 보낸 값이 통째로 들어 있다. 필드 이름만 돌려주고 값은 감춘다.
    fields = ", ".join(
        ".".join(str(p) for p in e["loc"][1:]) or "요청 본문" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"code": "validation_failed", "message": f"입력값을 확인하세요 — {fields}", "detail": None},
    )