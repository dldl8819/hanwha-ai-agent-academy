# UI 킷 사용법

설치 방법과 컴포넌트별 인자는 `README_컴포넌트_레퍼런스.md`를 본다. 이 문서는 **어디에 어떻게 붙이는지**만 적는다.

## 화면 하나 그려보기 — 전 부품 예시

```python
import pathlib
import sys

# 프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기
sys.path.insert(0, str(pathlib.Path(__file__).parent))  # frontend/를 모듈 검색 경로에 넣는다.

import streamlit as st
from ui import (page_header, metrics, table, badge_html)

from ui.theme import inject_css

inject_css()

page_header(
    "국내 출장 여비 규정",
    crumb="문서 관리 > 상세",
    subtitle="DOC-HR-012 - 인사 총무 - 최종개정 2025-07-01",
    badges=[("현행", None), ("대외비", "no"), ("재임베딩 62%", None)],
)

st.divider()

metrics(
    [
        {"label": "전체 문서", "value": "42"},
        {"label": "현행", "value": "34", "tone": "ok"},
        {"label": "재임베딩 필요", "value": "2", "delta": "+1", "tone": "wait"},
        {"label": "만료", "value": "8", "tone": "no"},
    ]
)

table(
    headers=["문서번호", "문서명", "버전", "상태", "청크"],
    rows=[
        ["DOC-HR-014", "국내출장 여비 규정", "v2.0", badge_html("현행"), "70"],
        ["DOC-HR-014", "국내출장 여비 규정", "v1.1", badge_html("만료"), "64"],
        ["DOC-SE-003", "정보보안 지침", "v2.2", badge_html("재임베딩 62%"), "38"],
    ],
    row_classes=["ag-row-sel", "", ""],                  # 선택된 행
    align=["ag-nowrap", "", "ag-nowrap", "", "ag-num"],  # 킷이 가진 이름만 쓴다
)

st.divider()

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
    st.markdown(card_html("3건", title="오늘 처리"), unsafe_allow_html=True)
with bordered("Streamlit 위젯은 이 안에 넣는다"):
    st.button("승인 요청 보내기")
st.divider()

# 노트
note("적재가 끝났습니다. 청크 70개.", tone="ok")
note("v1.1은 2025-06-30자로 만료되어 검색에서 제외되었습니다.", tone="wait")
note("근거를 찾지 못했습니다. 해외출장 규정은 아직 등록되지 않았습니다.", tone="no")
note("기본 톤입니다.")
note("**굵게**와 줄바꿈만 살리는 markdown=True", tone="", markdown=True)
st.divider()

# 메시지 블록, 로그 블록, 푸터
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
st.divider()

# 소스
sources(
    [
        {
            "title": "국내출장 여비 규정",
            "version": "v2.0",
            "locator": "제14조(숙박비)",
            "score": 0.71,
            "quote": "광역시의 숙박비는 1박당 70,000원을 상한으로 한다.",
            "extra_badge": ("현행", "ok"),
        },
        {"title": "복무 규정", "version": "v3.1", "locator": "표2", "score": 0.55},
    ]
)
st.caption("weak=True — 임계값 미달")
sources(
    [{"title": "구매·계약 규정", "version": "v4.0", "locator": "제16조", "score": 0.38}],
    weak=True,
)
st.markdown(
    source_html(title="정보보안 지침", version="v2.2", locator="제5조", score=0.64),
    unsafe_allow_html=True,
)

# 스텝, 프로그레스
steps(
    [
        {"name": "업로드", "state": "ok", "time": "0.2s"},
        {"name": "문서 파싱", "state": "ok", "time": "3.8s"},
        {"name": "청킹", "state": "ok", "time": "0.4s"},
        {"name": "임베딩", "state": "wait"},
        {"name": "색인 및 현행 버전 지정", "state": "todo"},
        {"name": "실패 예시", "state": "no"},
    ]
)
progress(83)
st.divider()

# bar, line, timeline
bars(
    [("기본 검색", 62), ("+ Multi-Query", 71), ("+ 하이브리드", 78), ("+ 리랭킹", 84)],
    max_value=100,
    unit="%",
)
line(
    [12, 18, 15, 24, 31, 28, 37],
    ["월", "화", "수", "목", "금", "토", "일"],
    y_ticks=[0, 10, 20, 30, 40],
    last_label="37건",
)
timeline(
    [
        f"<b>v2.0</b> 2025-07-01 개정 {badge_html('현행')}",
        f"<b>v1.1</b> 2024-03-02 개정 {badge_html('만료')}",
        "<b>v1.0</b> 2023-01-10 제정",
    ]
)
```

## agent-app 화면 그리기 — 진입점 + 사이드바

```python
import pathlib
import sys

# 프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기
sys.path.insert(0, str(pathlib.Path(__file__).parent))  # frontend/를 모듈 검색 경로에 넣는다.

import streamlit as st
from ui.theme import inject_css

# 가장 먼저 부르는 st 함수여야 한다. 최상위에 배치
st.set_page_config(
    page_title="사내 업무 에이전트",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()  # css 적용

# 사이드바 내비 항목
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

    for label, page_key in NAV:
        if st.sidebar.button(label, key=f"nav_{label}"):
            if page_key is None:
                st.sidebar.info("아직 만들지 않은 화면")
            else:
                st.session_state["page"] = page_key


# 메인
def main() -> None:
    st.session_state.setdefault("page", "documents")

    render_sidebar()

    page = st.session_state["page"]
    if page == "documents":
        st.info("문서 목록 화면은 다음 시간에 만들겠습니다.")
    else:
        st.info("아직 만들지 않은 페이지와 서버입니다.")


main()
```

- `st.set_page_config`는 스크립트에서 **가장 먼저 실행되는 `st.*` 호출**이어야 한다 — `inject_css()`나 다른 위젯보다 앞에 둔다.
- `NAV`에서 `page_key`가 `None`인 항목은 아직 만들지 않은 화면이라는 뜻으로, 클릭하면 `st.sidebar.info`로만 안내하고 페이지 전환은 하지 않는다.
- **현재 페이지는 `st.session_state["page"]`에 담는다.** Streamlit은 버튼을 누를 때마다 스크립트를 처음부터 다시 돌리므로, 지역 변수에 담아두면 다음 실행에서 사라진다. `setdefault`는 첫 실행에만 기본값(`"documents"`)을 넣고, 이후 재실행에서는 이미 들어있는 값을 건드리지 않는다.
- 사이드바를 먼저 그리고 나서 `page`를 읽는 순서가 중요하다. 버튼 클릭으로 바뀐 값이 같은 실행 안에서 바로 반영돼, 한 번 더 클릭해야 넘어가는 현상이 생기지 않는다.

## 연습은 `appex.py`에서

`app.py`는 실제 앱 골격(사이드바 + 페이지 라우팅)이라, 부품을 이것저것 찍어보는 연습은 같은 폴더의 별도 파일에서 한다.

```python
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import streamlit as st
from ui.theme import inject_css

st.set_page_config(
    page_title="화면 그리기 연습",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# 여기서부터 부품을 하나씩 붙여본다
```

```bash
streamlit run frontend/appex.py
```
