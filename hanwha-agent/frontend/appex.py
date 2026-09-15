import pathlib
import sys

# frontend/를 모듈 검색 경로에 넣는다.
# - 프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import streamlit as st
from ui import (page_header, metrics, table, badge_html, kv, card, card_html, bordered, note, meta_footer, log_block, message_block)

from ui.theme import inject_css

# 가장먼저 부르는 st 함수여야 한다. 최상위에 배치
st.set_page_config(
    page_title="화면 그리기 연습",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

page_header(
    "국내 출장 여비 규정", crumb="문서 관리 > 상세",
    subtitle="DOC-HR-012 - 인사 총무 - 최종개정 2025-07-01",
    badges=[("현행", None), ("대외비", "no"), ("재임베딩 62%", None)]
)

st.divider()

# 작은 카드들
metrics(
    [
        {"label": "전체 문서", "value": "42"},
        {"label": "현행", "value": "34", "tone": "ok"},
        {"label": "재임베딩 필요", "value": "2", "delta": "+1", "tone": "wait"},
        {"label": "만료", "value": "8", "tone": "no"},
    ]
)

st.divider()

# 테이블
table(
    headers=["문서번호", "문서명", "버전", "상태", "청크"],
    rows=[
        ["DOC-HR-014", "국내출장 여비 규정", "v2.0", badge_html("현행"), "70"],
        ["DOC-HR-014", "국내출장 여비 규정", "v1.1", badge_html("만료"), "64"],
        ["DOC-SE-003", "정보보안 지침", "v2.2", badge_html("재임베딩 62%"), "38"],
    ],
    row_classes=["ag-row-sel", "", ""],                    # 선택된 행
    align=["ag-nowrap", "", "ag-nowrap", "", "ag-num"],    # 킷이 가진 이름만 쓴다
)

st.divider()

# 표
kv(
    [
        ("성명 / 소속", "김민준 / 인프라사업부 2팀"),
        ("출장지 / 기간", "부산 / 2025-08-12 ~ 08-14 (2박 3일)"),
        ("예상 여비", "424,600원"),
        ("상태", badge_html("승인 대기")),
    ]
)
st.divider()

# 컬럼
left, right = st.columns([2, 1])
with left:
    card(
        "이번 프로젝트 출장비 기준을 찾아 부산 출장 신청서를 작성했습니다.",
        label="초안",
        title="국내출장 신청서",
    )
with right:
    st.markdown(card_html("3건", title="오늘 처리"), unsafe_allow_html=True) # streamlit
with bordered("Streamlit 위젯은 이 안에 넣는다"):
    st.button("승인 요청 보내기")

st.divider()

# 노트
note("적재가 끝났습니다. 청크 70개.", tone="ok")
note("v1.1 은 2025-06-30 자로 만료되어 검색에서 제외되었습니다.", tone="wait")
note("근거를 찾지 못했습니다. 해외출장 규정은 아직 등록되지 않았습니다.", tone="no")
note("기본 톤입니다.")
note("**굵게** 와 줄바꿈만 살리는 markdown=True", tone="", markdown=True)

# 메세지 블럭
message_block(
    "[승인 요청] 김민준 님의 부산 출장 신청서(424,600원)입니다.\n"
    "근거: DOC-HR-014 v2.0 제14조(숙박비)"
)
log_block(
    [
        "2025-08-12 09:14:02  ask        run=RUN-8f2a  user=E2024007",
        "2025-08-12 09:14:05  tool_call  search_documents  q='부산 출장 숙박비'",
        "2025-08-12 09:14:07  answer     score=0.71  sources=3",
    ]
)
meta_footer("3.1s · 입력 4,120 tok · 출력 512 tok · 42원 · haiku-4.5")
