"""문서 업로드 화면

한 화면이 두 가지 상태를 번갈아 그린다.
  - 작업 번호가 없으면 : 등록 폼
  - 작업 번호가 있으면 : 진행 상태

업로드 응답은 "저장했다" 까지만 알려준다. 파싱·청킹은 그 뒤에 배경에서 돌기
때문에, 결과를 보려면 작업 번호로 다시 물어야 한다. 그 묻는 일을 이 화면이 한다.
"""
from __future__ import annotations

import time

import streamlit as st

from core import api_client, router, session
from core.api_client import ApiError
from ui.badge import badge_html
from ui.card import page_header
from ui.status import progress, steps

# 부서 코드 -> 이름
# - 화면에는 이름을 보여주고 서버로는 코드를 보낸다.
#   seed_data.py 의 departments 와 코드가 어긋나면 외래키에서 걸린다.
DEPTS = {
    "HR": "경영지원팀",
    "HRGA": "인사총무",
    "INFRA2": "인프라사업부 2팀",
    "PMO": "PMO",
    "PU": "구매팀",
    "SE": "보안팀",
}
LEVELS = ["일반", "3급", "대외비"]
# 업로드를 받을 확장자
# - 백엔드 documents.py 의 ALLOWED_EXTS 와 맞춰 둔다.
#   여기만 늘리면 파일은 올라가고 서버에서 거절당한다.
ACCEPT = ["docx", "pdf", "txt"]


def render() -> None:
    page_header(
        "문서 업로드",
        crumb="문서 관리 > 업로드",
        subtitle="DOCX · PDF 를 파싱해 조항 단위와 표 단위로 나눠 저장합니다.",
    )
    if st.button("← 문서 관리"):
        router.go("documents")

    # 작업 번호 유무로 화면을 가른다
    job_id = st.session_state.get("upload_job")
    if job_id:
        _render_progress(job_id)
    else:
        _render_form()


# 등록 폼
def _render_form() -> None:
    up = st.file_uploader("파일을 끌어다 놓으세요", type=ACCEPT)
    doc_id = st.text_input("문서번호", value="DOC-FI-009")
    title = st.text_input("문서명", value="법인카드 사용 지침")
    version = st.text_input("버전 번호", value="v1.4")
    effective_from = st.text_input("시행일", value="2025-07-01")
    dept_id = st.selectbox("소관 부서", options=list(DEPTS), format_func=DEPTS.get)
    security_level = st.selectbox("보안등급", options=LEVELS)

    if st.button("등록", type="primary") and up is not None:
        try:
            res = api_client.upload_document(
                doc_id=doc_id, title=title, dept_id=dept_id,
                security_level=security_level, version=version,
                effective_from=effective_from,
                # up.getvalue() 로 바이트를 한 번에 꺼낸다.
                # up 자체를 넘기면 파일 포인터가 소진된 뒤 두 번째 읽기가 빈 바이트가 된다.
                filename=up.name, content=up.getvalue(),
                emp_no=session.emp_no(),
            )
        except ApiError as exc:
            st.error(str(exc))
            return
        # 받은 작업 번호를 세션에 적어 두고 화면을 다시 그린다.
        # - rerun 이 없으면 폼이 그대로 남아 진행 화면으로 넘어가지 않는다.
        st.session_state["upload_job"] = res["job_id"]
        st.rerun()

    st.caption("현행/만료를 고르는 일은 버전 관리 챕터에서 진행합니다.")


# 진행 상태
# - 1초에 한 번 작업을 묻고 다시 그린다(폴링). 끝나면 묻지 않는다.
def _render_progress(job_id: str) -> None:
    try:
        job = api_client.get_job(job_id, emp_no=session.emp_no())
    except ApiError as exc:
        st.error(str(exc))
        job = None

    if job is not None:
        st.markdown(
            badge_html(f"{job['status']} · {job['chunk_count']}청크"),
            unsafe_allow_html=True,
        )
        steps(job["steps"])
        progress(job["progress"])

        if job["status"] == "완료":
            st.markdown(f"**{job['message']}**")
            st.caption("표 1개가 청크 1개로 저장됩니다. 임베딩은 아직 붙지 않아 66% 에서 멈춥니다.")
        elif job["status"] == "실패":
            st.error(job["message"])

        # 끝나지 않았을 때만 다시 묻는다
        # - 이 조건을 빼면 완료된 뒤에도 1초마다 서버를 두드린다.
        if job["status"] not in ("완료", "실패"):
            time.sleep(1)
            st.rerun()

    if st.button("문서 하나 더 올리기"):
        # 작업 번호를 지우면 render() 가 다시 폼을 그린다.
        st.session_state.pop("upload_job", None)
        st.rerun()
