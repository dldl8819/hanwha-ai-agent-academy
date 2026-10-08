from __future__ import annotations

import os
from typing import Any
import httpx2

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

TIMEOUT = 60.0

# 백엔드 호출 실패 시 예외 클래스
class ApiError(RuntimeError):
    pass

# 모든 호출이 지나가는 내부 공용 함수 
# - `_` : 내부 함수 - 이 파일 안에서만 사용 
def _request(
    method: str, # GET, POST 전송 방식
    path: str,   # BASE_URL 뒤에 붙는 경로 ex. /api/v1/documents
    *,
    params: dict | None = None, # 쿼리스트링 ?a=10
    json: dict | None = None,   # 요청 본문으로 보낼 dict 타입 데이터
    # 파일 업로드용 두 칸
    # - 파일은 json 으로 못 보낸다. multipart/form-data 로 나가야 하고
    #   그 형식에서는 텍스트 칸(data)과 파일 칸(files)이 따로 실린다.
    # - json 과 같이 쓰면 안 된다. 본문 형식이 하나뿐이라 뒤에 오는 쪽이 이긴다.
    data: dict | None = None,   # 멀티파트 텍스트 필드
    files: dict | None = None,  # 멀티파트 파일 필드
    emp_no: str | None = None,  # 사번. X-Emp-No 헤더 값
) -> Any:

    clean_params = None
    if params is not None: # 파라미터가 있으면
        # (None, "" 빈 문자열, 전체) 값이 아닌 파라미터 값들만 파라미터로 취합
        clean_params = {k: v for k, v in params.items() if v not in (None, "", "전체")}
    # emp_no가 넘어오면 헤더 정보로 추가
    headers = {"X-Emp-No": emp_no} if emp_no else None
    # 요청할 URL 완성
    url = f"{BASE_URL}{path}"

    try:
        # 백엔드에 요청
        response = httpx2.request(
            method, url, params=clean_params, json=json, data=data, files=files,
            headers=headers, timeout=TIMEOUT
        )
    except httpx2.ConnectError as exc:
        raise ApiError(
            f"백엔드에 연결하지 못했습니다. 터미널에서 서버가 떠 있는지 확인하세요 ({BASE_URL})."
        ) from exc
    except httpx2.TimeoutException as exc:
        raise ApiError("응답이 너무 늦습니다. 서버가 멎었는지 확인하세요.") from exc

    # 4xx, 5xx 에러 발생 예외 처리 
    if response.status_code >= 400:
        try:
            message = response.json().get("message") or response.text
        except ValueError:
            message = response.text
        raise ApiError(message)

    # 응답 데이터 리턴
    return response.json()

# 로그인 요청
def login(emp_no: str, password: str) -> dict:
    return _request(
        "POST",
        "/api/v1/auth/login",
        json={
            "emp_no": emp_no,
            "password": password
        }
    )

# 현재 사용자 검증 (백엔드 확인)
def me(emp_no: str) -> dict:
    return _request(
        "GET",
        "/api/v1/auth/me",
        emp_no=emp_no
    )

# 문서 목록 요청 
def list_documents(
    *,
    dept_id: str | None = None,
    security_level: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 20,
    emp_no: str | None = None, # 신원 확인
) -> list[dict]:
    params = {
        "dept_id": dept_id,
        "security_level": security_level,
        "status": status,
        "q": q,
        "limit": limit
    }
    return _request("GET", "/api/v1/documents", params=params, emp_no=emp_no) # 백엔드에 요청

# 문서 1건 요청
def get_document(doc_id: str, *, emp_no: str | None = None) -> dict:
    return _request("GET", f"/api/v1/documents/{doc_id}", emp_no=emp_no)

# 문서 상태 화면에 뿌려줄 데이터 요청
def stats(*, emp_no: str | None = None) -> dict:
    # 100건이 되지 않는 문서라서 limit=100
    rows = list_documents(limit=100, emp_no=emp_no)
    return {
        "total": len(rows),
        "current": sum(1 for row in rows if row["status"] == "현행"),
        "expired": sum(1 for row in rows if row["status"] == "만료"),
        "reindexing": sum(1 for row in rows if row["index_status"] == "재임베딩"),
    }

# 질문 하나 백엔드에 보내면 답변을 받아오는 함수
def ask(question: str) -> dict:
    # question: 사용자가 입력창에 입력한 질문
    return _request("POST", "/api/v1/chat/messages", json={"question": question})
# 파일 하나를 백엔드로 보내 업로드를 요청하고 작업 번호를 받는 함수
# - files 의 값은 (파일명, 바이트) 튜플이다. 파일명을 빼고 바이트만 주면
#   서버가 확장자를 알 수 없어 ALLOWED_EXTS 검사에서 걸린다.
# - effective_from 은 문자열로 보낸다. 날짜 변환은 FastAPI 쪽 Form(date) 이 한다.
def upload_document(
    *, doc_id: str, title: str, dept_id: str, security_level: str,
    version: str, effective_from: str, filename: str, content: bytes,
    emp_no: str | None = None,
) -> dict:
    return _request(
        "POST", "/api/v1/documents",
        data={
            "doc_id": doc_id, "title": title, "dept_id": dept_id,
            "security_level": security_level, "version": version,
            "effective_from": effective_from,
        },
        files={"file": (filename, content)},
        emp_no=emp_no,
    )

# 업로드 작업 하나의 진행 상태 요청
def get_job(job_id: str, *, emp_no: str | None = None) -> dict:
    return _request("GET", f"/api/v1/documents/jobs/{job_id}", emp_no=emp_no)
