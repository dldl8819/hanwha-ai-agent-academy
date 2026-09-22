# Streamlit

## 개념

파이썬 스크립트를 웹 페이지로 바꿔주는 도구다. HTML/CSS/JS를 몰라도 파이썬 함수 호출만으로 화면을 만들 수 있다.

```bash
python -m pip install "streamlit==1.63.0"
```

```bash
# 파일이 있는 경로로 이동한 뒤
streamlit run 파일명.py
```

### 재실행 모델 — 이게 제일 중요한 개념이다

**Streamlit은 화면에서 뭔가 이벤트가 일어날 때마다(버튼 클릭, 입력 등) 스크립트 파일을 처음부터 끝까지 다시 실행한다.** 일반적인 웹 프레임워크처럼 "이 버튼을 누르면 이 함수만 실행"하는 게 아니라, 매번 `.py` 파일 전체가 위에서 아래로 다시 돌아간다.

```python
# 이렇게 하면 절대 안 늘어난다 — 매번 count = 0 으로 되돌아가기 때문
count = 0
if st.button("문서 1건 추가"):
    count = count + 1
st.write("추가한 문서 수 : ", count)
```

재실행돼도 값이 유지돼야 하는 건 **`session_state`**에 저장해야 하고, 매번 다시 계산하기 아까운 무거운 작업(파일 읽기 등)은 **캐시**(`@st.cache_data`, `@lru_cache` 등)로 피한다.

## 기본 함수

| 함수 | 역할 |
| --- | --- |
| `title()` | 화면 맨 위 제목 |
| `header()` / `subheader()` | 제목 / 소제목 |
| `write()` | 텍스트·표·그림 등 뭐든 알아서 그려주는 범용 출력 |
| `markdown()` | 마크다운 텍스트 |
| `divider()` | 가로 구분선 |
| `selectbox()` | 선택 상자 |
| `text_input()` | 입력란 |
| `checkbox()` | 체크박스 |
| `json()` | JSON 형태로 보기 좋게 출력 |
| `columns(n)` | 가로로 n칸 나누기. `columns([2, 1])`처럼 비율도 지정 가능 |
| `container(border=True)` | 테두리 있는 묶음 |
| `tabs([...])` | 같은 자리에 탭으로 여러 화면 겹치기 |

### 기본 예제 — `hello.py`

```python
st.set_page_config(page_title="사내 업무 에이전트")

st.title("사내 업무 에이전트")
st.write("write는 화면에 텍스트를 출력하는 함수입니다.")

st.header("제목")
st.subheader("소 제목")

st.markdown(
    "- python\n"
    "- fastAPI\n"
    "- streamlit\n"
)

st.divider()
st.caption("출처 - streamlit 공식 문서")
```

### 레이아웃 예제 — `layout.py`

```python
c1, c2, c3 = st.columns(3)
c1.metric("전체 문서", "44")
c2.metric("python", "33")
c3.metric("fastapi", "22")

with st.container(border=True):
    st.subheader("컨테이너 내부")
    st.caption("컨테이너 끝")

t1, t2 = st.tabs(["python", "streamlit"])
t1.write("python tab")
t2.write("streamlit tab")
```

`st.columns(3)`은 언패킹해서 각 칸(`c1`, `c2`, `c3`)에 `.metric()`처럼 위젯을 바로 붙여 쓸 수 있다. `container(border=True)`는 그냥 `with` 블록으로 묶어서 그 안 내용에 테두리를 두른다.

### 위젯과 `session_state` 연결 — `widgets.py`

```python
st.selectbox("상태", ["python", "FastAPI", "streamlit"], key="f_status")
st.text_input("입력란", key="f_query")
st.checkbox("체크하십쇼", key="f_check")

st.json({
    "status": st.session_state.f_status,
    "query": st.session_state.f_query,
    "check": st.session_state.f_check,
})
```

위젯을 만들 때 `key="..."`를 주면, 그 위젯의 현재 값이 자동으로 `st.session_state["그 key"]`에 들어간다. 별도로 이벤트 핸들러를 안 만들어도, 재실행될 때마다 `st.session_state.f_status`로 최신 선택값을 바로 읽을 수 있다.

## 멀티페이지 — `st.Page` + `st.navigation`

함수 하나가 화면(페이지) 하나가 된다.

```python
def page_chat():
    st.title("AI 업무 도우미 채팅창")
    st.write("채팅 화면")

def page_doc():
    st.title("문서 관리 페이지")
    st.write("문서 목록")

pages = [
    st.Page(page_chat, title="AI Chat"),
    st.Page(page_doc, title="문서 관리"),
]

st.navigation(pages).run()
```

`st.navigation(pages)`가 사이드바 메뉴를 자동으로 만들어주고, `.run()`이 현재 선택된 페이지의 함수를 실행한다.

## 채팅 UI와 파일 업로드

```python
if "messages" not in st.session_state:
    st.session_state.messages = []

up = st.file_uploader("파일 업로드", type=["docx", "pdf"])
if up is not None:
    st.success(f"업로드 파일명 - {up.name} 사이즈 - ({up.size:,} bytes)")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["text"])

q = st.chat_input("문의 내용")
if q:
    st.session_state.messages.append({"role": "user", "text": q})
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write("기능 구현은 추후에 진행")
```

- `file_uploader(type=[...])`로 허용 확장자를 제한할 수 있다 — [[14_문서_업로드_API]]에서 서버 쪽 `ALLOWED_EXTS`로 하던 걸 화면 쪽에서도 1차로 걸러준다.
- 대화 이력은 재실행돼도 사라지면 안 되니 `session_state.messages`에 쌓는다. `chat_message(role)`로 감싸면 사용자/어시스턴트 말풍선 모양이 자동으로 나온다.
- 대화가 길어지면 이력을 전부 LLM에 넘기기보다 최근 몇 턴만 잘라 쓰는 게 일반적이다.

```python
def trim_history(messages, max_turn=2):
    keep = max_turn * 2  # 한 턴 = 질문 1 + 답변 1
    if len(messages) <= keep:
        return messages
    return messages[-keep:]
```

## Streamlit add-ons — 외부 부품 가져다 쓰기

```bash
# shadcn은 streamlit 1.60 이상을 요구한다
python -m pip install streamlit-shadcn-ui streamlit-aggrid streamlit-echarts
```

### shadcn — `streamlit_shadcn_ui`

```python
import streamlit_shadcn_ui as ui

ui.card(title="첫 카드", description="카드 설명", content="실제 내용", key="first_card")
ui.badge("뱃지1", key="b_first")
ui.badge("뱃지2", key="b_second", variant="secondary")
ui.metric_card("전체 문서", "44", description="지난 주 대비 +3", key="m1")

if ui.button("문서 열기", key="open_btn"):
    st.write("문서 열기 버튼 클릭했습니다.")
```

표에 배지를 넣어보는 실습도 했다.

```python
rows = [{"문서ID": "DOC-HR-014", "문서명": "국내출장 여비 규정", "상태": "현행", "청크": 70}, ...]
cols = [
    {"key": "문서ID", "label": "문서 ID"},
    {"key": "상태", "label": "상태"},
    {"key": "청크", "label": "청크", "align": "right"},  # 정렬 옵션은 된다
]
ui.table(data=rows, columns=cols, key="doc_table")
```

**여기서 막힌 부분**: `ui.table`의 칸에는 순수 글자만 들어가고, "상태" 칸에 색깔 있는 배지(뱃지)를 넣을 방법이 없다. `align` 같은 옵션은 지원해도 셀 안에 HTML/커스텀 컴포넌트를 넣는 건 이 테이블 컴포넌트의 한계다 — 그래서 아래 `frontend/ui/badge.py`처럼 직접 HTML 문자열(`st.markdown(..., unsafe_allow_html=True)`)로 배지를 그리는 방식을 따로 쓰는 이유이기도 하다.

### AgGrid — `streamlit_aggrid`

```python
from st_aggrid import AgGrid, GridOptionsBuilder

df = pd.DataFrame([
    {"문서ID": "DOC-HR-014", "문서명": "국내출장 여비 규정", "상태": "현행", "청크": 70},
    ...
])
```

정렬·필터가 되는 진짜 엑셀 느낌의 테이블을 만들어주는 컴포넌트다. 이 실습 코드는 데이터프레임까지만 준비된 상태이고 `GridOptionsBuilder`로 옵션을 만들어 `AgGrid(df, ...)`를 실제로 호출하는 부분은 아직 이어서 작성해야 한다.

### ECharts — `streamlit_echarts`

```python
from streamlit_echarts import st_echarts

options = {
    "series": [{
        "type": "gauge",
        "min": 0, "max": 100,
        "detail": {"formatter": "{value}%"},
        "data": [{"value": 84, "name": "정확도"}],
    }]
}
st_echarts(options=options, height="320px")
```

검색 정확도 같은 지표를 게이지 차트로 보여줄 때 쓴다. `detail.formatter`의 `{value}`는 ECharts가 실제 값(`84`)으로 바꿔서 채워주는 자리표시자다.

**실습 중 만난 오류**: `formatter`를 `"{vale}%"`로 오타 냈다(`value`가 아니라 `vale`). ECharts는 `{value}`라는 정확한 이름만 인식해서, 오타가 나면 치환이 안 되고 게이지에 `{vale}%`라는 글자가 그대로 찍힌다. 에러가 나는 종류의 오타가 아니라 **화면에 이상하게 보이기만 하는** 오타라서, 콘솔 로그로는 못 찾고 직접 화면을 보고서야 알 수 있다.

## UI-Kit — 화면 디자인 통일하기

수업에서 만든 화면 디자인을 통일하기 위한 세트를 `hanwha-agent/frontend/` 폴더 안에 받아서 붙였다.

```text
frontend/
    app.py                 # 실행 시작점, frontend를 sys.path에 등록
    .streamlit/config.toml
    assets/
        tokens.css          # 색상·간격 등 디자인 토큰
        base.css
        components.css
    ui/
        __init__.py
        theme.py            # CSS 주입
        badge.py            # 배지(상태 표시)
        card.py, chart.py, metric.py, source.py, status.py, table.py
```

`ui/badge.py`는 위에서 shadcn 테이블이 못 하던 "표 안에 색깔 있는 배지"를 직접 HTML로 만들어 해결한 버전이다 — 상태 문자열("현행", "만료" 등)을 미리 정해둔 톤(`ok`/`wait`/`no`/`neutral`)에 매핑해서 `<span class="ag-badge ag-badge--톤">`으로 렌더링한다.

`ui/theme.py`의 주석에 실습 중 겪은 함정이 그대로 남아 있다.

> Streamlit은 재실행할 때마다 화면을 처음부터 다시 그린다. "한 번만 주입"하려고 `session_state`로 막으면, 두 번째 실행부터 스타일이 통째로 사라진다. 그래서 **매 실행마다 주입하고, 파일 읽기만 캐시한다.**

```python
@lru_cache(maxsize=1)
def load_css() -> str:
    # CSS 파일들을 읽어서 이어붙이는, 비용이 드는 부분만 캐시
    ...

def inject_css() -> None:
    # <style> 태그로 화면에 꽂는 부분은 매번 실행돼야 한다 (캐시하면 안 됨)
    st.markdown(f"<style>\n{load_css()}\n</style>", unsafe_allow_html=True)
```

"재실행마다 스크립트 전체가 다시 돈다"는 이 문서 맨 위의 Streamlit 재실행 모델과 정확히 같은 원리다 — 파일을 읽어서 문자열로 합치는 것처럼 **결과가 항상 같은 순수 계산**은 캐시해도 되지만, **화면에 실제로 뭔가를 그리는 동작**(`st.markdown`으로 `<style>` 주입)은 매번 실행돼야 한다는 구분을 보여주는 사례다.

참고: sandbox/streamlit/01_basic/, sandbox/streamlit/02_shadcn/, frontend/
