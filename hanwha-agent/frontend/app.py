from __future__ import annotations

import html
import pathlib
import sys

# frontend/를 모듈 검색 경로에 넣는다.
# - 프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import streamlit as st
from core import api_client, router, session
from ui.theme import inject_css
from views import login as login_view
from views import documents as documents_view 
from views import chat as chat_view
from views import document_upload as document_upload_view
from views import document_detail as document_detail_view
from views import approvals as approvals_view

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
    ("AI 업무 도우미", "chat"),
    ("문서 관리", "documents"),
    ("승인함", "approvals"),
    ("운영 대시보드", None),
]


# 승인함 메뉴 옆에 대기 건수를 붙인다
def _nav_label(label: str, waiting: int | None) -> str:
    if label == "승인함" and waiting is not None:
        return f"{label}  {waiting}"
    return label


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
            '<div class="ag-user">'
            f'<div class="ag-avatar">{html.escape(user["name"][:1])}</div>'
            '<div>'
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

    # 대기 건수. 백엔드가 꺼져 있어도 메뉴는 그린다
    # - 화면이 다시 그려질 때마다 한 번씩 요청이 나간다
    waiting: int | None = None
    try:
        waiting = api_client.list_approvals(session.emp_no())["summary"]["waiting"]
    except Exception:
        pass

    # 메뉴 버튼 그리기
    for label, page_key in NAV:
        if st.sidebar.button(_nav_label(label, waiting), key=f"nav_{label}"):
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
    # 현재 페이지 키값이 chat, documents 
    if page == "chat":
        chat_view.render()
    elif page == "documents":
        documents_view.render()
    elif page == "document_upload":
        document_upload_view.render()
    elif page == "document_detail":
        document_detail_view.render()
    elif page == "approvals":
        approvals_view.render()
    else:
        st.info("아직 만들지 않은 화면입니다.")

main()
