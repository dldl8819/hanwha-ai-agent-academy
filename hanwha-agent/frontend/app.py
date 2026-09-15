from __future__ import annotations

import html
import pathlib
import sys

# frontend/를 모듈 검색 경로에 넣는다.
# - 프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import streamlit as st
from core import router, session
from ui.theme import inject_css
from views import login as login_view
from views import documents as documents_view 

# 가장 먼저 부르는 st 함수여야 한다. 최상위에 배치
st.set_page_config(
    page_title="사내 업무 에이전트",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()  # css 적용

# 사이드바 내비 항목
# - 메뉴 목록
NAV: list[tuple[str, str | None]] = [
    ("AI 업무 도우미", None),
    ("문서 관리", "documents"),
    ("승인함", None),
    ("운영 대시보드", None),
]


# 사이드바 그리는 함수
def render_sidebar() -> None:
    st.sidebar.markdown(
        '<div class="ag-brand"><div class="ag-brand-name">사내 업무 에이전트</div></div>',
        unsafe_allow_html=True,
    )

    # 추가 
    user = session.current_user()
    # 로그인 했으면
    if user is not None:
        # 사용자 이름과 부서명을 화면에 그리기
        st.sidebar.markdown(
            '<div class="ag-user"><div>'
            f'<div class="ag-user-name">{html.escape(user["name"])}</div>'
            f'<div class="ag-user-role">{html.escape(user["dept"])}</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        # 로그아웃 버튼 부착
        # - 버튼 누르면 로그아웃 처리
        if st.sidebar.button("로그아웃", key="nav_logout"):
            session.logout()
            st.rerun()      

    # 메뉴 버튼 그리기
    for label, page_key in NAV:
        if st.sidebar.button(label, key=f"nav_{label}"):
            if page_key is None:
                st.sidebar.info("아직 만들지 않은 화면")
            else:
                # 메뉴 누르면 화면 키값을 state에 추가
                # - 화면 이동 처리
                st.session_state["page"] = page_key


# 메인
def main() -> None:
    # 재실행돼도 유지돼야 하는 값들(page, user, 필터)에 기본값 채우기
    session.init_state()

    # 로그인 안 했으면 사이드바 없이 로그인 화면만 그리고 끝낸다
    if not session.is_authenticated():
        login_view.render()
        return

    render_sidebar()


    # 현재 페이지 키 가져오기 
    page = router.current_page()
    # 현재 페이지 키값이 documents 
    if page == "documents":
        documents_view.render()
    else:
        st.info("아직 만들지 않은 화면입니다.")

main()
