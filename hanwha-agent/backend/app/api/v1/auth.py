from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header

from app.core.exceptions import AuthFailed
from app.schemas.auth import LoginIn, UserOut
from app.services import auth_service

# 인증 관련 요청 처리
router = APIRouter(prefix="/auth", tags=["auth"])

# 로그인 요청 처리
@router.post("/login", response_model=UserOut) # 응답 데이터 타입 : UserOut
def login(body: LoginIn) -> dict: # 사용자가 요청한 데이터는 LoginIn 타입으로 취합
    # 서비스에서 로직 처리
    # - 사용자가 보내준 사번과 비밀번호로 검증
    # - DB와 일치하는 값인지 확인 후 회원정보 리턴
    return auth_service.authenticate(body.emp_no, body.password)

# 사용자 정보 요청 처리 
@router.get("/me", response_model=UserOut)
# 헤더 정보로 넘어오는 x_emp_no 인증키 검증 
# - 추후 JWT 토큰으로 변경 예정
def me(x_emp_no: Annotated[str | None, Header()] = None) -> dict: 
    # 사번이 존재하지 않으면 예외 발생
    if x_emp_no is None:
        raise AuthFailed("로그인이 필요합니다.")
    # 사번이 존재하면 회원 정보 리턴
    return auth_service.get_me(x_emp_no) 

