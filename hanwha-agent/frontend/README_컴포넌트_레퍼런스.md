# UI 킷 컴포넌트 레퍼런스

사내 업무 에이전트 화면을 그리는 부품 모음. **공개 이름 27개**가 전부다.
설치와 「어디에 붙이나」는 `README_사용법.md`에 있다. 이 문서는 **부품 하나하나의 인자와 옵션**을 적는다.

> 이 문서는 킷 실물(`ui/*.py` 9모듈 · `assets/*.css` 3파일)에서 뽑았다.
> 문서와 코드가 갈리면 **도는 코드가 기준**이다.

---

## 목차

| 절 | 무엇 |
| --- | --- |
| 0. 한눈에 | 27개 전체 표 |
| 1. 공통 규칙 | tone · `_html` 짝 · 이스케이프 · `ag-` 접두어 |
| 2. theme | `inject_css` `load_css` |
| 3. badge | `badge` `badge_html` `badges` `tone_for` |
| 4. table | `table` `table_html` `kv` `kv_html` |
| 5. card | `card` `card_html` `bordered` `note` `message_block` `log_block` `meta_footer` `inline_md` `page_header` |
| 6. metric | `metrics` |
| 7. status | `steps` `steps_html` `progress` |
| 8. source | `sources` `source_html` |
| 9. chart | `bars` `line` `timeline` |
| 10. 디자인 토큰 | `--ag-*` 35개 |
| 11. CSS 클래스 | 킷이 만드는 클래스 · 직접 쓰는 유틸 |
| 12. 함정 | 조용히 실패하는 자리 |
| 13. 자주 묻는 것 | FAQ |

---

## 0. 한눈에 — 공개 이름 27개

`from ui import ...`로 전부 꺼낼 수 있다. **`metric`(단수) · `status_line` · `mini_bars` 같은 이름은 없다.**

| 이름 | 모듈 | 반환 | 한 줄 |
| --- | --- | --- | --- |
| `inject_css` | theme | 그린다 | CSS 세 개를 화면에 밀어 넣는다 |
| `badge` | badge | 그린다 | 배지 하나 |
| `badge_html` | badge | **문자열** | 표 칸·문장 안에 넣을 배지 |
| `badges` | badge | 그린다 | 배지 여러 개를 한 줄로 |
| `tone_for` | badge | **문자열** | 글자를 보고 색 이름을 돌려준다 |
| `table` | table | 그린다 | HTML 표 |
| `table_html` | table | **문자열** | 같은 표를 문자열로 |
| `kv` | table | 그린다 | 키-값 2열 표 |
| `kv_html` | table | **문자열** | 같은 것을 문자열로 |
| `card` | card | 그린다 | 카드 |
| `card_html` | card | **문자열** | 같은 카드를 문자열로 |
| `bordered` | card | **컨텍스트** | Streamlit 위젯을 담는 테두리 상자 |
| `note` | card | 그린다 | 왼쪽 세로선 안내 블록 |
| `message_block` | card | 그린다 | 그대로 나갈 텍스트(Slack 문구 등) |
| `inline_md` | card | **문자열** | `**굵게**`와 줄바꿈만 HTML로 |
| `log_block` | card | 그린다 | 감사 로그(모노스페이스) |
| `meta_footer` | card | 그린다 | 응답 하단 메타 한 줄 |
| `page_header` | card | 그린다 | 빵부스러기 + 제목 + 배지 + 부제 |
| `sources` | source | 그린다 | 근거 문서 카드 여러 개 |
| `source_html` | source | **문자열** | 근거 문서 하나 |
| `metrics` | metric | 그린다 | 지표 타일 한 줄 |
| `steps` | status | 그린다 | 처리 단계 목록 |
| `steps_html` | status | **문자열** | 같은 것을 문자열로 |
| `progress` | status | 그린다 | 진행률 막대 |
| `bars` | chart | 그린다 | 가로 막대 + 축 |
| `line` | chart | 그린다 | 라인 차트(SVG) |
| `timeline` | chart | 그린다 | 버전 타임라인 |

---

## 1. 공통 규칙

### 1.1 `_html` 짝

이름이 같고 `_html`이 붙은 것은 **그리지 않고 문자열을 돌려준다.** `st.columns` 안에 넣거나, 표 칸에 끼워 넣거나, 문장 중간에 섞을 때 쓴다.

```python
table(headers, rows)                                              # 화면에 그린다
st.markdown(table_html(headers, rows), unsafe_allow_html=True)    # 같은 결과
```

### 1.2 `tone` — 색 이름

| tone | 쓰는 곳 | 색 |
| --- | --- | --- |
| `"ok"` | 승인·완료·현행 | `--ag-ok` `#2C6E45` |
| `"wait"` | 대기·진행중·재임베딩 | `--ag-wait` `#9B5E0B` |
| `"no"` | 반려·만료·위험·실패 | `--ag-no` `#9E2B2B` |
| `"accent"` | 강조 (배지 전용) | `--ag-accent` `#0E6E62` |
| `"neutral"` | 그 밖 (배지 전용) | 회색 |
| `"count"` | 개수 (배지 전용) | 회색 계열 |
| `""` | 기본 | 지정 없음 |

- **`badge` 계열만 여섯을 다 받는다.** `note` · `metrics`는 `'' | ok | wait | no` 넷, `steps`는 `ok | wait | no | todo` 넷이다.
- 목록에 없는 값을 주면 `badge`는 **`neutral`로 떨어뜨리고**, 나머지는 **그 이름을 클래스로 그냥 붙인다**(= CSS에 없으니 아무 일도 일어나지 않는다).

### 1.3 이스케이프 — 어디까지 HTML이 살아 있나

| 함수 | 그대로 HTML로 들어가는 자리 | 글자로 바뀌는 자리 |
| --- | --- | --- |
| `table` / `table_html` | **셀 값**(`raw_html=True` 기본) | 헤더는 **항상** 글자 |
| `kv` / `kv_html` | **값**(`raw_html=True` 기본) | 키는 **항상** 글자 |
| `card` / `card_html` | **본문 `body`** | `label` · `title` |
| `note` | **`text`** (`markdown=False`일 때) | — |
| `timeline` | **`items` 전부** | — |
| `badge` · `message_block` · `log_block` · `meta_footer` · `page_header` · `metrics` · `steps` · `source_html` | — | 전부 글자 |

> ⚠️ **사용자가 친 글을 그대로 넣지 않는다.** 위 왼쪽 칸은 HTML이 살아 있어서 업로드한 문서 제목 같은 외부 값을 그대로 넣으면 화면이 깨지거나 스크립트가 섞인다.
> 외부 값을 넣을 때는 `raw_html=False`를 주거나 `html.escape()`를 먼저 건다.

### 1.4 `ag-` 접두어

우리가 새로 만드는 클래스에는 **반드시 `ag-`**를 붙인다. 접두어 없이 `.sel`을 만들었다가 킷 표의 선택 행 규칙과 부딪혀 표가 통째로 무너진 적이 있다.
Streamlit 내부 클래스(`.st-emotion-cache-…`)는 **쓰지 않는다** — 버전이 오르면 이름이 바뀐다.
`[data-testid="stSidebar"]` 같은 **속성 선택자**까지만 허용한다.

---

## 2. theme — CSS 주입

```python
inject_css() -> None
load_css()   -> str
```

`assets/`의 CSS 세 개를 **이 순서로** 읽어 `<style>`로 밀어 넣는다 — `tokens.css` → `base.css` → `components.css`.
순서가 바뀌면 변수가 정의되기 전에 규칙이 나와서 색이 빠진다.

| 옵션 | 값 | 설명 |
| --- | --- | --- |
| — | 없음 | 인자가 없다 |

```python
from ui.theme import inject_css
inject_css()          # app.py 맨 위, st.set_page_config 다음
```

- **매 실행마다 부른다.** `session_state`로 「한 번만」 하게 막으면 버튼을 한 번 누른 뒤 스타일이 통째로 사라진다. 비싼 것은 파일 읽기이고 그건 `load_css()`가 `@lru_cache`로 이미 잡아 둔다.
- `assets/`는 `ui/`의 **형제 폴더**여야 한다(`ui/theme.py` 기준 `../assets`). 둘 중 하나만 옮기면 CSS가 조용히 빠진다 — 파일이 없어도 앱은 죽지 않고 주석만 남는다.
- ⚠️ **CSS 파일을 고쳐도 서버가 떠 있는 동안에는 반영되지 않는다.** `load_css()`가 캐시한다. 고쳤으면 `Ctrl+C` 후 다시 띄운다.

---

## 3. badge — 상태 배지

```python
tone_for(text: str) -> str
badge_html(text: str, tone: str | None = None) -> str
badge(text: str, tone: str | None = None) -> None
badges(items: list[tuple[str, str | None]]) -> None
```

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `text` | `str` | 필수 | 배지에 쓸 글자. **글자로 이스케이프된다** |
| `tone` | `str \| None` | `None` | 안 주면 `tone_for(text)`로 **자동 판정**. 여섯 값 밖이면 `neutral` |
| `items` | `list[tuple[str, str \| None]]` | 필수 | `badges` 전용. `[("현행", None), ("대외비", "no")]` |

### 자동 색 판정 — 「그 말로 **시작하면**」

`tone_for`는 아래 낱말로 **시작하는지**만 본다. 들어 있기만 해서는 걸리지 않는다.

| tone | 시작 낱말 |
| --- | --- |
| `ok` | `현행` `완료` `승인` `승인·실행` `유효` `정상` |
| `wait` | `대기` `대기중` `진행 중` `진행중` `재임베딩` |
| `no` | `만료` `반려` `반려됨` `차단` `위험` `실패` |
| `neutral` | `보관` · **그 밖 전부** |

```python
badge_html("재임베딩 62%")     # ok  wait  — '재임베딩'으로 시작한다
badge_html("색인 완료")        # neutral — '완료'가 뒤에 있다
badge_html("색인 완료", "ok")  # 직접 지정하면 된다
```

**상태 낱말을 앞에 둔다.** 이것이 이 킷에서 가장 자주 걸리는 자리다.

나오는 HTML — `<span class="ag-badge ag-badge--ok">현행</span>`

---

## 4. table — 표와 키-값

```python
table_html(headers, rows, *, row_classes=None, align=None, raw_html=True) -> str
table(headers, rows, **kwargs) -> None
kv_html(pairs, *, raw_html=True) -> str
kv(pairs, **kwargs) -> None
```

`st.dataframe`을 쓰지 않는 이유는 하나다 — **칸 안에 배지가 들어가야 하기 때문이다.** `st.dataframe`에 배지 HTML을 넣으면 태그가 글자 그대로 보인다.

### `table` / `table_html`

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `headers` | `Sequence[str]` | 필수 | 헤더. **항상 글자로 이스케이프**된다 |
| `rows` | `Iterable[Sequence[Cell]]` | 필수 | 행. `Cell = str \| int \| float \| None`. `None`은 빈 칸 |
| `row_classes` | `Sequence[str] \| None` | `None` | **행마다** 클래스 하나 |
| `align` | `Sequence[str] \| None` | `None` | **열마다** 클래스 하나 |
| `raw_html` | `bool` | `True` | 셀 값을 HTML로 살릴지. `False`면 전부 글자 |

**`align`에 쓸 수 있는 값 — 셋뿐이다.** 여기 적는 것은 CSS 클래스 이름 그대로다.

| 값 | 효과 |
| --- | --- |
| `""` | 기본(좌측) |
| `"ag-num"` | **우측 정렬** · 숫자용 |
| `"ag-nowrap"` | **줄바꿈 금지** · 문서번호·날짜처럼 폭이 일정한 열 |

> ⚠️ `"left"` · `"center"` · `"right"`는 **킷 CSS에 없는 이름**이라 클래스만 붙고 아무 일도 일어나지 않는다. 에러도 경고도 없다.

**`row_classes`에 쓸 수 있는 값**

| 값 | 효과 |
| --- | --- |
| `""` | 기본 |
| `"ag-row-sel"` | 선택된 행 — 액센트 배경 |
| `"ag-row-muted"` | 흐린 행 — 만료·비활성 |
| `"ag-row-total"` | 합계 행 — 굵게 · 윗선 |

```python
table(
    headers=["문서번호", "문서명", "버전", "상태", "청크"],
    rows=[
        ["DOC-HR-014", "국내출장 여비 규정", "v2.0", badge_html("현행"), 70],
        ["DOC-HR-014", "국내출장 여비 규정", "v1.1", badge_html("만료"), 64],
    ],
    row_classes=["ag-row-sel", "ag-row-muted"],
    align=["ag-nowrap", "", "ag-nowrap", "", "ag-num"],
)
```

- 표는 **`<div class="ag-tbl-wrap">`로 감싸여** 나온다(`overflow-x: auto`). 화면이 좁으면 표만 가로로 스크롤되고 페이지는 밀리지 않는다.
- 한국어 열은 `word-break: keep-all`이 이미 걸려 있어 낱말 단위로만 끊긴다. **폭이 일정한 열을 `ag-nowrap`으로 고정하고 남는 폭을 문서명이 가져가게** 두면 표가 흔들리지 않는다.
- `align` · `row_classes`는 길이가 모자라면 그 뒤는 기본값으로 둔다. 남는 것은 무시된다.

### `kv` / `kv_html`

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `pairs` | `Iterable[tuple[str, Cell]]` | 필수 | `[(키, 값), …]`. 키는 **항상 글자**, 값은 `raw_html`을 따른다 |
| `raw_html` | `bool` | `True` | 값에 배지 같은 HTML을 넣을 수 있다 |

```python
kv([
    ("성명 / 소속", "김민준 / 인프라사업부 2팀"),
    ("예상 여비", "424,600원"),
    ("상태", badge_html("승인 대기")),
])
```

---

## 5. card — 카드 · 안내 · 블록 · 헤더

```python
card_html(body, *, label=None, title=None) -> str
card(body, *, label=None, title=None) -> None
bordered(label=None)                      # with 문과 함께 쓴다
note(text, tone="", *, markdown=False) -> None
message_block(text) -> None
log_block(lines) -> None
meta_footer(text) -> None
inline_md(text) -> str
page_header(title, *, crumb=None, subtitle=None, badges=None) -> None
```

### `card` / `card_html`

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `body` | `str` | 필수 | 카드 본문. **HTML이 그대로 살아 있다** — 다른 부품의 `_html`을 넣을 수 있다 |
| `label` | `str \| None` | `None` | 맨 위 작은 라벨(대문자 느낌의 분류) |
| `title` | `str \| None` | `None` | 제목 줄 |

```python
card(kv_html([("예상 여비", "424,600원")]), label="초안", title="국내출장 신청서")
```

### `bordered` — 위젯을 담는 상자

카드는 HTML이라 **안에 Streamlit 위젯을 넣을 수 없다.** 버튼·입력칸을 테두리 안에 넣어야 하면 이것을 쓴다.

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `label` | `str \| None` | `None` | 상자 맨 위 라벨 |

```python
with bordered("승인 처리"):
    st.text_area("의견")
    st.button("승인")
```

### `note` — 왼쪽 세로선 안내 블록

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `text` | `str` | 필수 | 문구 |
| `tone` | `str` | `""` | `"" \| "ok" \| "wait" \| "no"` |
| `markdown` | `bool` | `False` | `True`면 `**굵게**`와 줄바꿈을 해석한다 |

```python
note("적재가 끝났습니다. 청크 70개.", tone="ok")
note("v1.1은 2025-06-30자로 만료되어 검색에서 제외되었습니다.", tone="wait")
note("근거를 찾지 못했습니다.", tone="no")
note("**굵게**도 되고\n줄바꿈도 된다", markdown=True)
```

### `message_block` · `log_block` · `meta_footer`

| 함수 | 인자 | 무엇 |
| --- | --- | --- |
| `message_block(text)` | `str` | **그대로 나갈 텍스트**. Slack 전송 문구 미리보기 |
| `log_block(lines)` | `list[str]` | 감사 로그. 줄 목록을 모노스페이스로. 내부에서 `"\n".join` |
| `meta_footer(text)` | `str` | 응답 하단 한 줄 — `3.1s · 입력 4,120 tok · 42원 · haiku-4.5` |

셋 다 내용이 **글자로 이스케이프**된다. HTML을 넣어도 태그가 그대로 보인다.

### `inline_md`

`ag-note` 같은 **HTML 블록 안**에서는 Streamlit이 마크다운을 처리해 주지 않는다.
전체 마크다운 파서를 넣을 일은 아니라서 **두 가지만** 바꾼다 — `**굵게**`와 줄바꿈(`\n` → `<br>`).
나머지는 전부 이스케이프된다.

### `page_header`

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `title` | `str` | 필수 | 제목(`<h1>`) |
| `crumb` | `str \| None` | `None` | 위 빵부스러기 — `문서 관리 › 상세` |
| `subtitle` | `str \| None` | `None` | 제목 아래 보조 줄 |
| `badges` | `list[tuple[str, str \| None]] \| None` | `None` | 제목 옆 배지들. `tone`이 `None`이면 자동 판정 |

```python
page_header(
    "국내출장 여비 규정",
    crumb="문서 관리 › 상세",
    subtitle="DOC-HR-014 · 인사총무 · 최종 개정 2025-07-01",
    badges=[("현행", None), ("대외비", "no")],
)
```

---

## 6. metric — 지표 타일

```python
metrics(items: list[dict]) -> None
```

| 키 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `label` | `str` | **필수** | 타일 이름. 없으면 `KeyError` |
| `value` | `str \| int` | **필수** | 큰 숫자 |
| `delta` | `str` | 선택 | 값 아래 작은 줄. 항상 회색(`--ag-muted`) |
| `tone` | `str` | 선택 | `"" \| "ok" \| "wait" \| "no"` — **숫자 색만** 바뀐다 |

```python
metrics([
    {"label": "전체 문서", "value": "42"},
    {"label": "현행", "value": "34", "tone": "ok"},
    {"label": "재임베딩 필요", "value": "2", "delta": "+1", "tone": "wait"},
    {"label": "만료", "value": "8", "tone": "no"},
])
```

> ⚠️ **`st.columns()`로 나누지 않는다.** `metrics`가 한 줄을 통째로 그린다.
> 이 킷에서 **배치를 가져가는 유일한 부품**이다. 나머지는 전부 Streamlit이 자리를 잡는다.

---

## 7. status — 처리 단계와 진행률

```python
steps_html(items: list[dict]) -> str
steps(items: list[dict]) -> None
progress(pct: int) -> None
```

### `steps`

| 키 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `name` | `str` | **필수** | 단계 이름 |
| `state` | `str` | 선택 | `ok` · `wait` · `no` · `todo`. 기본 `todo` |
| `time` | `str` | 선택 | 오른쪽 소요 시간. 없고 `state`가 `no`·`todo`면 **자동으로 `—`** |

| state | 표시 | 뜻 |
| --- | --- | --- |
| `ok` | `✓` | 끝났다 |
| `wait` | `◐` | 하는 중 |
| `no` | `✕` | 실패 |
| `todo` | `·` | 아직 |

```python
steps([
    {"name": "문서 파싱", "state": "ok", "time": "3.8s"},
    {"name": "임베딩", "state": "wait"},
    {"name": "색인", "state": "todo"},
])
```

### `progress`

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `pct` | `int` | 필수 | 0~100. **범위를 벗어나면 잘라서 맞춘다**(`-5` → 0, `120` → 100) |

막대 아래 오른쪽에 `83%`가 함께 찍힌다.

---

## 8. source — 근거 문서 블록

```python
source_html(*, title, version, locator, score, quote=None, extra_badge=None, weak=False) -> str
sources(items: list[dict], *, weak=False) -> None
```

**전부 키워드 인자다.** 위치 인자로 넘기면 `TypeError`가 난다.

| 인자 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `title` | `str` | **필수** | 문서명 |
| `version` | `str` | **필수** | 판 번호. `accent` 배지로 나간다 |
| `locator` | `str` | **필수** | 어디인지 — `제14조(숙박비)` · `표2` |
| `score` | `float` | **필수** | 유사도. `0.71`처럼 **소수 둘째 자리**로 찍힌다 |
| `quote` | `str \| None` | 선택 | 인용문. 주면 왼쪽 세로선 블록이 붙는다 |
| `extra_badge` | `tuple[str, str] \| None` | 선택 | 배지 하나 더 — `("시행 2025-07-01", "neutral")` |
| `weak` | `bool` | `False` | `True`면 **임계값 미달** — 점수 배지가 빨갛고 인용이 흐려진다 |

```python
sources([
    {
        "title": "국내출장 여비 규정",
        "version": "v2.0",
        "locator": "제14조(숙박비)",
        "score": 0.71,
        "quote": "광역시의 숙박비는 1박당 70,000원을 상한으로 한다.",
        "extra_badge": ("현행", "ok"),
    },
])
```

> ⚠️ **`sources`는 딕셔너리 키를 그대로 인자로 넘긴다**(`source_html(**item)`).
> 키 이름이 하나라도 다르면 그 자리에서 `TypeError`다. API 응답을 그대로 넘기지 말고 **위 여섯 키로 맞춰서** 넘긴다.

---

## 9. chart — 막대 · 라인 · 타임라인

```python
bars(items, *, max_value=100, unit="%", strong_last=True, ticks=None) -> None
line(values, labels, *, y_ticks, last_label=None, height=190) -> None
timeline(items: list[str]) -> None
```

### `bars` — 가로 막대

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `items` | `list[tuple[str, float]]` | 필수 | `[(라벨, 값), …]` |
| `max_value` | `float` | `100` | 축 최대값. **막대 폭 = 값 / max_value** |
| `unit` | `str` | `"%"` | 값과 눈금 뒤에 붙는 단위 |
| `strong_last` | `bool` | `True` | 마지막 막대만 진하게 + 굵은 글씨 |
| `ticks` | `list[float] \| None` | `None` | 눈금 값. 기본은 `max_value` **4등분**(0·25·50·75·100) |

```python
bars([("기본 검색", 62), ("+ 하이브리드", 78), ("+ 리랭킹", 84)], max_value=100, unit="%")
bars([("파싱", 3.8), ("임베딩", 1.2)], max_value=5, unit="s", ticks=[0, 2.5, 5])
```

- 값은 0~100%로 잘려서 그려진다. **축 눈금과 막대 길이가 정확히 일치한다** — 이게 이 부품의 존재 이유다.
- 숫자는 `:g`로 찍혀 `62` · `3.8`처럼 불필요한 0이 붙지 않는다.

### `line` — 라인 차트(SVG)

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `values` | `list[float]` | 필수 | 값. 비어 있으면 **아무것도 그리지 않고 끝난다** |
| `labels` | `list[str]` | 필수 | x축 라벨 |
| `y_ticks` | `list[float]` | **필수(키워드)** | y축 눈금. **최대값이 축 상한**이 된다 |
| `last_label` | `str \| None` | `None` | 마지막 점 옆 라벨 |
| `height` | `int` | `190` | 높이(px). 폭은 100% |

```python
line([12, 18, 15, 24, 31], ["월", "화", "수", "목", "금"], y_ticks=[0, 10, 20, 30], last_label="31건")
```

- **`y_ticks`의 최대값을 넘는 값은 잘린다.** 데이터 최대보다 크게 잡는다.
- x 라벨은 너무 많으면 솎아서 **7~8개**만 찍는다. 마지막은 항상 찍는다.
- ⚠️ **이 차트의 색은 토큰이 아니라 파일에 박혀 있다**(`#0E6E62` 등). `tokens.css`를 바꿔도 라인 차트 색은 따라오지 않는다.

### `timeline` — 버전 타임라인

| 인자 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `items` | `list[str]` | 필수 | **이미 만들어진 HTML 조각**들. 이스케이프하지 않는다 |

**첫 항목이 「현행」**으로 강조된다. 순서는 최신부터 넣는다.

```python
timeline([
    f"<b>v2.0</b> 2025-07-01 개정{badge_html('현행')}",
    f"<b>v1.1</b> 2024-03-02 개정{badge_html('만료')}",
    "<b>v1.0</b> 2023-01-10 제정",
])
```

---

## 10. 디자인 토큰 (`tokens.css`)

값만 모아 둔 파일이다. 규칙은 없고 변수뿐이라 **한 줄을 바꾸면 화면 전체가 따라 바뀐다.** `base.css` · `components.css`는 이 이름을 부르기만 한다.

> **학생은 이 파일을 고치지 않는다.** 각자 색을 바꾸면 화면마다 「현행」 색이 달라진다.
> 바꿀 자리는 캡스톤이다.

### 색

| 토큰 | 값 | 쓰는 곳 |
| --- | --- | --- |
| `--ag-bg` | `#F6F8F7` | 페이지 바탕 |
| `--ag-surface` | `#FFFFFF` | 카드 |
| `--ag-sb` | `#EEF3F1` | 사이드바 · 표 헤더 |
| `--ag-sb-ink` | `#3A4A47` | 사이드바 글씨 |
| `--ag-ink` | `#14201E` | 본문 글자 |
| `--ag-muted` | `#66766F` | 보조 텍스트 · `delta` |
| `--ag-line` | `#DCE4E1` | 선 |
| `--ag-line-2` | `#C6D2CE` | 진한 선 |
| `--ag-accent` | `#0E6E62` | 버튼 · 선택 |
| `--ag-accent-soft` | `#E0EFEB` | 선택 행 배경 |
| `--ag-accent-ink` | `#0A544A` | 액센트 글자 |
| `--ag-ok` / `--ag-ok-soft` | `#2C6E45` / `#E2F0E7` | 승인 · 완료 · 현행 |
| `--ag-wait` / `--ag-wait-soft` | `#9B5E0B` / `#F7ECD9` | 대기 · 진행중 |
| `--ag-no` / `--ag-no-soft` | `#9E2B2B` / `#F8E5E4` | 반려 · 위험 · 만료 |

**상태 3종은 액센트와 절대 섞지 않는다.** 「승인됨」과 「선택됨」이 같은 색이면 화면을 읽을 수 없다.
어두운 배경은 어디에도 쓰지 않는다.

### 형태 · 간격 · 글자

| 토큰 | 값 | 쓰는 곳 |
| --- | --- | --- |
| `--ag-radius` / `--ag-radius-sm` | `4px` / `3px` | 모서리 (Streamlit 기본보다 각지게) |
| `--ag-s1` … `--ag-s6` | `4` `9` `16` `22` `32` `46` px | 간격 |
| `--ag-row-y` / `--ag-row-x` | `13px` / `14px` | 표 행 · 단계 목록의 안쪽 여백 |
| `--ag-fs-xs` … `--ag-fs-2xl` | `12.5` `14` `15` `17.5` `21.5` `27` px | 글자 크기 |
| `--ag-lh` | `1.8` | 줄 간격 |
| `--ag-mono` | `ui-monospace, …` | 메타 푸터 · 감사 로그 |

```css
/* 규칙 파일은 이렇게 부른다 */
.ag-card { background: var(--ag-surface); border-radius: var(--ag-radius); padding: var(--ag-s3); }
```

> `.streamlit/config.toml`은 **Streamlit이 직접 그리는 위젯**(버튼·입력창)의 색이고, `tokens.css`는 **우리가 만든 마크업**의 색이다.
> 두 축이 따로 있고 값은 같게 맞춰 두었다. **한쪽만 바꾸면 화면이 반쯤 어긋난다.**

---

## 11. CSS 클래스 전체

### 직접 쓰는 유틸 (인자로 넘기는 이름)

| 클래스 | 어디에 | 효과 |
| --- | --- | --- |
| `ag-num` | `table(align=…)` | 우측 정렬 |
| `ag-nowrap` | `table(align=…)` | 줄바꿈 금지 |
| `ag-row-sel` | `table(row_classes=…)` | 선택된 행 |
| `ag-row-muted` | `table(row_classes=…)` | 흐린 행 |
| `ag-row-total` | `table(row_classes=…)` | 합계 행 |

### 직접 마크업으로 쓰는 것 (사이드바 등)

| 클래스 | 무엇 |
| --- | --- |
| `ag-brand` / `ag-brand-name` / `ag-brand-sub` | 사이드바 브랜드. **글자 스타일은 `-name`·`-sub`에 있다** |
| `ag-user` / `ag-user-name` / `ag-user-role` | 사이드바 사용자. **래퍼로만 감싸면 기본 글꼴로 뜬다** |
| `ag-avatar` | 사용자 아바타 자리 (W3 예정) |
| `ag-chip` / `ag-chip--on` | 「자주 하는 질문」 칩 · 필터 칩 |
| `ag-mode` | 실행 모드 표시 |

### 부품이 알아서 만드는 것

`ag-badge`(+`--ok/wait/no/accent/neutral/count`) · `ag-tbl` · `ag-tbl-wrap` · `ag-kv`(`-k`/`-v`) ·
`ag-card`(`-label`/`-title`) · `ag-note`(+`--ok/wait/no`) · `ag-msg` · `ag-log` · `ag-meta` ·
`ag-crumb` · `ag-head` · `ag-sub` · `ag-metrics` · `ag-metric`(+tone, `-label`/`-value`/`-delta`) ·
`ag-steps` · `ag-step`(+state, `-mark`/`-name`/`-time`) · `ag-progress`(`-fill`) ·
`ag-src`(+`--no`, `-meta`) · `ag-bars` · `ag-bar-row`(`-label`/`-track`/`-fill`/`-value`/`-tick`) ·
`ag-tl` · `ag-tl-item`(+`--now`)

이 이름들은 **직접 쓰지 않는다.** 부품을 부르면 알아서 붙는다.

---

## 12. 함정 — 틀려도 에러가 안 난다

여기 넷은 **예외도 경고도 나지 않는다.** 화면만 조용히 안 바뀐다.

| # | 무엇 | 증상 | 고치는 법 |
| --- | --- | --- | --- |
| ① | `align`에 `"left"`·`"center"`를 적었다 | 정렬이 안 먹는다 | 쓸 수 있는 이름은 `""`·`ag-num`·`ag-nowrap` 셋뿐 |
| ② | `badge_html("색인 완료")` | 초록이 아니라 회색 | 색은 **「그 말로 시작하면」**으로 정해진다 → `완료 — 색인` 또는 `tone="ok"` |
| ③ | `<div class="ag-user">이름</div>` | 기본 글꼴로 뜬다 | `.ag-user`는 래퍼다. 글자는 `.ag-user-name`·`.ag-user-role`에 |
| ④ | `config.toml`을 `frontend/`에만 뒀다 | CSS는 맞는데 **버튼만 빨갛다** | 루트에도 한 벌 — Streamlit은 **명령을 친 폴더** 기준으로 찾는다 |

에러가 나는 쪽은 이렇다.

| 무엇 | 어떻게 터지나 |
| --- | --- |
| `metrics` 항목에 `label`·`value`가 없다 | `KeyError` |
| `sources` 항목의 키 이름이 다르다 | `TypeError` (`**item`으로 넘긴다) |
| `source_html`을 위치 인자로 불렀다 | `TypeError` (전부 키워드 전용) |
| `line(y_ticks=…)`를 빠뜨렸다 | `TypeError` (키워드 필수) |
| `ui/`와 `assets/`가 형제가 아니다 | 에러는 없고 **CSS만 통째로 빠진다** |

---

## 13. 자주 묻는 것

**Q. `st.dataframe` 쓰면 안 되나요?**
표 안에 색 배지를 넣어야 해서 안 씁니다. `st.dataframe`은 칸 값을 전부 글자로 바꿔서 `<span class="ag-badge">`가 태그 그대로 보입니다. 정렬·필터가 필요하고 배지가 없는 표라면 써도 됩니다.

**Q. 레이아웃 함수(`row`·`grid`)는 왜 없나요?**
자리는 Streamlit이 잡고(`st.columns`·`st.container`·`st.tabs`), 내용은 킷이 그립니다. 둘을 나눠 두면 Streamlit이 버전업으로 배치를 바꿔도 킷은 그대로입니다. 예외는 `metrics` 하나입니다.

**Q. 새 부품이 필요하면?**
① 27개 중에 되는 게 없는지 먼저 봅니다 → ② `card_html` + `inline_md` 조합으로 되는지 봅니다 → ③ 그래도 없으면 **`ag-` 접두어를 붙여** 직접 만듭니다. `components.css`에 규칙을 더하고 색은 반드시 `var(--ag-…)` 토큰으로 씁니다.

**Q. 색을 바꾸고 싶은데요.**
수업 중에는 바꾸지 않습니다(통일이 깨집니다). 연습은 연습 폴더에 **복사본**을 만들어 거기서 `--ag-accent`를 바꿔 보세요 — 규칙을 한 줄도 안 고쳤는데 버튼·선택·강조가 한꺼번에 바뀝니다. 그게 **디자인 토큰**입니다.

**Q. 전부 한 화면에서 보고 싶어요.**
`ui_kit_demo.py`를 킷 폴더에서 띄우면 됩니다 — `streamlit run ui_kit_demo.py`.
