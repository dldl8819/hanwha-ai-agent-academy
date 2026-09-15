from __future__ import annotations

from html import escape

import streamlit as st

from core import api_client, session
from ui.badge import badge_html
from ui.metric import metrics
from ui.table import table


DEPTS: dict[str, str | None] = {
    "전체": None,
    "인사총무": "HRGA",
    "구매팀": "PU",
    "보안팀": "SE",
    "PMO": "PMO",
}

LEVELS = ["전체", "일반", "3급", "대외비"]

STATUSES = ["전체", "현행", "만료"]

HEADERS = ["문서 ID", "문서명", "버전", "시행 ~ 만료", "상태", "부서", "등급", "색인"]

ALIGNS = ["ag-nowrap", "", "", "ag-nowrap", "", "", "", "ag-nowrap"]


def _metrics_row() -> None:
    # 문서 지표 생성
    try:
        counts = api_client.stats(emp_no=session.emp_no())
    except api_client.ApiError as exc:
        st.caption(f"지표를 불러오지 못했습니다: {exc}")
        return

    metrics([
        {"label": "전체", "value": counts["total"], "delta": "문서 버전 기준"},
        {"label": "현행", "value": counts["current"], "delta": "지금 유효한 판",
         "tone": "ok"},
        {"label": "만료", "value": counts["expired"], "delta": "지난 판",
         "tone": "no"},
        {"label": "재임베딩", "value": counts["reindexing"], "delta": "색인을 다시 만드는 중",
         "tone": "wait"},
    ])

# 필터 그리기
def _filter_row() -> dict:
    # 화면 세로로 분할
    left, middle, right, search = st.columns([1, 1, 1, 2]) # 비율
    # 각 분할된 화면에 selectbox와 입력란 배치
    with left:
        dept_name = st.selectbox("부서", list(DEPTS), key="f_dept")
    with middle:
        level = st.selectbox("보안등급", LEVELS, key="f_level")
    with right:
        status = st.selectbox("상태", STATUSES, key="f_status")
    with search:
        keyword = st.text_input("검색어", key="f_q", placeholder="문서명 또는 문서 ID")

    # 사용자가 선택한 값 리턴
    # - 사용자가 "전체"로 놔두면 None값 리턴
    return {
        "dept_id": DEPTS[dept_name],
        "security_level": None if level == "전체" else level,
        "status": None if status == "전체" else status,
        "q": keyword or None,
    }

# 받은 문서 목록을 표로 그리기
def _table(documents: list[dict]) -> None:
    rows = []
    # 문서 개수만큼 반복해서 화면에 출력될 문서 목록 세팅
    for document in documents:
        period = f"{document['effective_from']} ~ {document['expires_at'] or '현행'}"
        index_label = f"{document['index_status']} {document['index_progress']}%"
        # 화면에 출력될 데이터 컴포넌트들 추가
        rows.append([
            # escape : 문자열
            escape(document["doc_id"]),
            escape(document["title"]),
            escape(document["version"]),
            escape(period),
            badge_html(document["status"]),
            escape(document["dept"]),
            escape(document["security_level"]),
            badge_html(index_label),
        ])

    # 테이블에 컬럼과 로우 추가
    table(HEADERS, rows, align=ALIGNS)

# 실제 화면 구현 함수
def render() -> None:
    st.title("문서 관리")
    st.caption("상태 필터가 「전체」라 지난 판까지 함께 보입니다. "
               "「현행」으로 좁히면 현재 유효한 최신본만 남습니다.")

    _metrics_row() # 지표 그리는 함수

    filters = _filter_row() # 필터

    if st.button("새 문서 업로드"): # 업로드 버튼 생성
        st.info("업로드 화면은 추후에 만듭니다.") # 버튼 클릭 시 정보 출력
    # 로딩 화면
    with st.spinner("문서를 불러오는 중입니다..."):
        try:
            # 백엔드에 문서 요청
            documents = api_client.list_documents(**filters, limit=100,
                                                  emp_no=session.emp_no())
        except api_client.ApiError as exc:
            st.error(str(exc))
            return

    if not documents:
        st.info("조건에 맞는 문서가 없습니다. 필터를 바꿔 보세요.")
        return

    st.caption(f"{len(documents)}건")
    _table(documents)
