from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
# from app.api.v1.documents import router as document_router
# from app.api.v1.auth import router as auth_router
from app.api.v1 import auth, documents, chat, ops
from app.core.config import get_settings
from app.core.exceptions import AgentError
from contextlib import asynccontextmanager
from app.core.logging import setup_logging, get_logger
from fastapi.exceptions import RequestValidationError
from app.integrations import factory

log = get_logger(__name__)

# 서버 시작 때 로컬 모델을 미리 열어 둔다
# - 못 열어도 서버는 뜬다. 경고만 남기고 첫 질문 때 다시 연다
def _warm_up_models() -> None:
    settings = get_settings()
    if not settings.warm_up_models:
        return
    started = time.perf_counter()
    try:
        if settings.embed_provider == "local":
            factory.get_embedder()
        if settings.reranker == "cross_encoder":
            factory.get_cross_encoder()
    except AgentError as e:
        log.warning("모델을 미리 열지 못했습니다 - %s (첫 질문에서 다시 엽니다)", e.message)
        return
    log.info("모델 미리 열기 완료: %.1f초", time.perf_counter() - started)

# lifespan 함수 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    _warm_up_models()
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

app.include_router(
    ops.router,
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