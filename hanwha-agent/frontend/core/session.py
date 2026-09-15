from __future__ import annotations

import streamlit as st

# 상태 초기값 설정
DEFAULTS: dict = {
    "page": "login",
    "user": None,
    "f_dept": "전체",
    "f_level": "전체",
    "f_status": "전체",
    "f_q": "",
}

# 상태에 초기값 채우기
def init_state() -> None:
    for key, value in DEFAULTS.items():
        # 화면을 다시 실행해도 데이터 유지되는 변수들 초기화
        st.session_state.setdefault(key, value)

# 현재 사용자 정보 조회 
# - 로그인 -> 사용자 정보
# - 비로그인 -> None
def current_user() -> dict | None:
    return st.session_state.get("user")
    

# 로그인 여부 확인
def is_authenticated() -> bool:
    return current_user() is not None

# 로그인
# - 로그인 상태로 만들기
# - 문서 목록 화면으로 이동
def login(user: dict) -> None:
    st.session_state["user"] = user
    st.session_state["page"] = "documents"
    
# 로그아웃 
# - 사용자 정보 삭제
# - 로그인 화면으로 이동
# - 부서, ... 필터 초기화
def logout() -> None:
    st.session_state["user"] = None
    st.session_state["page"] = "login"
    for key in ("f_dept", "f_level", "f_status", "f_q"):
        st.session_state[key] = DEFAULTS[key]

# 사용자 사번 조회
# - 비로그인 시 None 리턴
def emp_no() -> str | None:
    user = current_user()
    return user["emp_no"] if user else None
