# 어느 화면을 보여줄지 정하는 함수들
# - 상태(session_state) "page" 값으로 처리 

from __future__ import annotations

import streamlit as st

# 지금 보여줄 화면의 키
def current_page() -> str:
    return st.session_state.get("page", "login")

# 화면 이동
def go(page: str) -> None:
    st.session_state["page"] = page
    # 상태만 바꾸면 이번 실행은 이전 화면을 끝까지 그리고, 다음 클릭에서야 바뀐다
    st.rerun()
