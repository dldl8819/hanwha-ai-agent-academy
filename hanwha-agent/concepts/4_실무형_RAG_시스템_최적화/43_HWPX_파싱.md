# HWPX 파싱

[[39_문서_파싱]]에서 PDF 와 DOCX 를 읽었다. 남은 것이 한글 문서인데, **`.hwp` 와 `.hwpx` 는 다른 형식**이고 한쪽만 읽을 수 있다.

| | HWPX | HWP |
| --- | --- | --- |
| 무엇인가 | **ZIP 안의 XML** | 한컴 독자 바이너리 |
| 표준 | **KS 국가 표준** | 공개 표준이 아니다 |
| 파이썬 | **표준 라이브러리만으로 읽는다** | 유일한 파서가 5년 넘게 릴리즈 없음 |
| 우리 처리 | 읽는다 | 안내하고 막는다([[44_파일_형식_분기와_차단]]) |

`.hwpx` 는 라이브러리를 새로 들이지 않아도 된다. `zipfile` 과 `xml.etree` 가 표준 라이브러리다 — [[41_기술_스택_지도]]의 "스택에 무엇이 하나 더 늘어나는가" 기준에서 0 이다.

## ZIP 안을 들여다본다

```text
연습 재료 1 : 앞 4바이트 b'PK\x03\x04'  →  ZIP 인가 True
세 건 모두 ZIP : True
```

DOCX 와 같은 표식이다([[39_문서_파싱]]). 안에 든 것은 열 개다.

```text
항목 수 : 10
  mimetype                   application/hwp+zip (19바이트)
  version.xml
  META-INF/container.xml
  META-INF/container.rdf
  META-INF/manifest.xml
  Contents/content.hpf       본문 파일의 순서
  Contents/header.xml        서식
  Contents/section0.xml      ← 본문
  settings.xml               커서 위치
  Preview/PrvText.txt        미리보기용 짧은 글자
```

```text
압축 방식 : 0 (압축한 것이 아니라 그대로 넣었다)
열 개 전체의 압축 방식 : {0}
```

**열 개 전부 압축되어 있지 않다.** ZIP 은 담는 그릇으로만 쓰고 내용은 그대로 둔 것이다.

본문은 `Contents/section0.xml` 이고, 문서가 길면 `section1`, `section2` 로 이어진다. 그래서 하나만 읽지 않고 전부 찾는다.

```python
sections = sorted(n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml$", n))
```

```text
본문 파일 : ['Contents/section0.xml']
길이 : 190,833 바이트
```

## XML 을 읽는다 — ElementTree

`xml.etree.ElementTree` 가 표준 라이브러리다. **악의적으로 만든 XML 에 취약**하므로 남이 올린 파일에 바로 쓰면 안 된다. 여기서는 연습이라 그대로 쓴다.

| | 어디를 보나 |
| --- | --- |
| `요소.find("태그")` | 바로 아래 자식 중 첫 하나 |
| `요소.findall("태그")` | 바로 아래 자식 전부 |
| `요소.iter("태그")` | 자기 아래 **모든 깊이** |
| `요소.find(".//태그")` | 모든 깊이에서 첫 하나 |

작은 예로 차이를 보면 분명하다.

```python
MINI = '<sec><p>제12조(식비)</p><p><tbl><tc><p>구분</p></tc><tc><p>금액</p></tc></tbl></p></sec>'
```

```text
findall('p') : 2 개  ← 바로 아래 자식만
iter('p')    : 4 개  ← 모든 깊이

findall 이 찾은 것 : ['제12조(식비)', None]
iter    가 찾은 것 : ['제12조(식비)', None, '구분', '금액']
```

표 안의 `p` 두 개가 `iter` 에만 딸려 온다. **이 차이가 오늘의 핵심이다.**

### 네임스페이스 — 없이 찾으면 조용히 0

```python
root.findall('p')
```

```text
findall('p') 결과 : []
찾은 개수         : 0

에러가 났습니까?  → 아니요. 조용히 빈 목록이 돌아왔습니다.
```

HWPX 의 태그는 이름 앞에 주소가 붙어 있다.

```text
뿌리 태그 : {http://www.hancom.co.kr/hwpml/2011/section}sec
```

주소를 붙여야 찾아진다.

```python
NS_P = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
root.findall(f"{NS_P}p")
```

```text
최상위 문단 수 : 237
```

**0 과 237 사이에 예외가 없다.** 어제 본 "에러가 나지 않는 실패"([[39_문서_파싱]])가 여기서도 나온다. XML 을 다룰 때 결과가 0이면 네임스페이스부터 본다.

## `.text` 가 None 일 수 있다

글자를 모으다 터졌다.

```python
texts = ["".join(t.text for t in para.iter(f"{NS_P}t")).strip() for para in tops]
```

```text
TypeError: sequence item 0: expected str instance, NoneType found
```

빈 태그(`<hp:t/>`)의 `.text` 는 빈 문자열이 아니라 `None` 이다.

```text
글자 태그     : 450 개
.text 가 None : 41 개
```

450개 중 41개다. **한 개만 있어도 전체가 멈춘다** — 237개 문단을 훑다 중간에서 끊기면 그 뒤는 시도조차 못 한다.

```python
"".join(t.text or "" for t in para.iter(f"{NS_P}t")).strip()
```

`or ""` 한 조각으로 끝난다. 짧지만 **없는 것과 비어 있는 것을 같게 다루겠다**는 결정이다.

## findall 과 iter — 같은 글이 두 번 들어온다

문단을 모으는 데 어느 쪽을 쓰느냐로 결과가 갈린다.

```text
findall 로 모은 블록 : 233
iter    로 모은 블록 : 416
차이                 : +183
```

늘어난 183개가 무엇인지 확인했다.

```text
늘어난 블록 : 183 개
표 안에 있던 문단 : 133 종류
늘어난 것이 전부 표 안 문장인가 : True

  중복된 예 : v2.0
  중복된 예 : 버전
  중복된 예 : 구분
```

**표 안의 문단이 두 번씩 들어온 것이다.** 표를 담은 문단을 한 번 세고, 그 안의 문단을 또 센다.

중복은 에러가 아니라서 그대로 지나간다. 그런데 이 블록들이 청킹을 거쳐 검색에 들어가면 **같은 내용이 여러 조각으로 앉는다.** 검색 결과 상위가 같은 말로 채워지고, 프롬프트에 중복이 실려 토큰만 늘어난다([[32_사용량과_원가_기록]]).

### 어디에 무엇을 쓰는가

| 찾는 것 | 어디 | 쓰는 것 | 왜 |
| --- | --- | --- | --- |
| 문서의 문단 | `sec` 바로 아래 | `root.findall(f"{ns_p}p")` | 같은 내용이 두 번 들어오지 않게 |
| 문단 안의 표 | 문단 아래 아무 깊이 | `para.find(f".//{ns_p}tbl")` | 표가 `run` 안에 들어 있다 |
| 표의 행 | `tbl` 바로 아래 | `table_el.findall(f"{ns_p}tr")` | 표 안의 표가 딸려오지 않게 |
| 행의 칸 | `tr` 바로 아래 | `tr.findall(f"{ns_p}tc")` | 같은 이유 |
| 한 문단의 글자 | 문단 아래 모든 깊이 | `para.iter(f"{ns_p}t")` | 글자는 깊이 박혀 있다 |
| 한 칸의 글자 | 칸 아래 모든 깊이 | `tc.iter(f"{ns_p}t")` | 같은 이유 |

**규칙이 하나다. 구조를 훑을 때는 `findall`(직계), 글자를 긁을 때는 `iter`(모든 깊이).** 구조에 `iter` 를 쓰면 중복되고, 글자에 `findall` 을 쓰면 빠진다.

## 표

표가 들어 있는 자리는 이렇게 생겼다.

```text
hp:p                          ← 표를 "담은" 문단
└── hp:run
    └── hp:tbl  rowCnt="4" colCnt="7"
        ├── hp:sz / hp:pos / hp:inMargin      크기·위치 (글자 없음)
        └── hp:tr                             행
            └── hp:tc  header="1"             칸
                ├── hp:cellAddr  rowAddr colAddr
                ├── hp:cellSpan  rowSpan colSpan
                └── hp:subList
                    └── hp:p → hp:run → hp:t  ← 실제 글자
```

```text
tbl 직계 : ['sz', 'pos', 'outMargin', 'inMargin', 'tr'] …
tr  직계 : ['tc']
tc  직계 : ['cellAddr', 'cellSpan', 'cellSz', 'cellMargin', 'subList']
```

표가 `hp:p` 아래 `hp:run` 안에 들어 있어서, 문단에서 표를 찾을 때는 `.//` 로 깊이를 건너뛴다.

```text
최상위 문단 237개
그중 표를 담은 문단 7개
```

### 그냥 이으면 칸이 사라진다

표를 문단처럼 처리하면 [[40_표_추출과_마크다운]]에서 본 일이 그대로 일어난다.

```text
표 자리의 블록 : 버전구분시행일주요 내용작성검토승인v2.0개정2025-07-01일비 인상(25,000→30,000) · 광역시 …
```

DOCX 때 만든 `_table_to_markdown` 을 그대로 쓴다. **형식이 달라도 표를 담는 모양은 하나**라 함수를 다시 만들지 않는다.

```text
5행 × 5열
| 직급 | 일비 | 숙박비(광역시) | 숙박비(그 밖의 지역) | 식비 |
|---|---|---|---|---|
| 1~2급 | 40,000 | 100,000 | 80,000 | 30,000 |
```

### `continue` 한 줄

```python
if table_el is not None:
    ...
    blocks.append(ParsedBlock("표", f"표{tables}", _table_to_markdown(rows[0], rows[1:])))
    continue          # ← 이 줄

text = "".join(t.text or "" for t in para.iter(f"{ns_p}t")).strip()
```

```text
continue 있음 : 233
continue 없음 : 240
차이           : 7
```

`continue` 가 없으면 **표 하나가 블록 두 개**가 된다 — 마크다운 표 하나와, 같은 내용을 이어 붙인 문단 하나. 표가 7개라 정확히 7이 늘었다.

## 결과

```text
블록 233 · page_count 1 · table_count 7
표 블록 : ['표1', '표2', '표3', '표4', '표5', '표6', '표7']
첫 표 블록의 첫 줄 : | 버전 | 구분 | 시행일 | 주요 내용 | 작성 | 검토 | 승인 |
```

같은 문서를 세 형식으로 읽어 견줘 보면 이렇다.

```text
형식        블록    표    쪽수
HWPX     233    7     1
DOCX     233    7     1
PDF       16    0    16
```

**HWPX 와 DOCX 가 완전히 같다.** 둘 다 ZIP + XML 이고 문단과 표가 구조로 남아 있어서, 원문 순서대로 훑으면 같은 결과가 나온다. PDF 만 다른 세계다([[40_표_추출과_마크다운]]).

이 일치를 테스트로 박아 두었다.

```python
assert (len(hwpx_doc.blocks), hwpx_doc.table_count, hwpx_doc.page_count) == \
       (len(docx_doc.blocks), docx_doc.table_count, docx_doc.page_count)
```

숫자 233·7 을 따로 적어 두는 것보다 **두 파서가 서로를 검산하게 하는 쪽**이 낫다. 한쪽을 고쳐서 결과가 달라지면 바로 걸린다.

## 짚어둘 것

`parse_hwpx` 안에서 `import` 를 한다.

```python
def parse_hwpx(path: Path) -> ParsedDoc:
    import re
    import zipfile
    from xml.etree import ElementTree as ET
```

`parse_pdf` 가 `pypdf` 를 함수 안에서 import 한 것과 같은 모양인데([[39_문서_파싱]]), **이유는 다르다.** 저쪽은 안 쓰는 경로에서 무거운 라이브러리를 안 올리려는 것이고, 여기는 전부 표준 라이브러리라 그 이득이 없다. 모양을 맞춘 것에 가깝다.

### 같은 표인데 이름이 달랐다

실습에서 두 형식의 `locator` 를 나란히 찍어 보고 알았다.

```text
hwpx   표 1 · 표 2      ← 띄어쓰기 있음
docx   표1 · 표2        ← 없음
```

`parse_hwpx` 가 `f"표 {tables}"`, `parse_docx` 가 `f"표{tables}"` 였다. **같은 문서를 어느 형식으로 올렸느냐에 따라 인용 문구가 달라진다.**

블록 수·표 수를 맞춰 보는 테스트는 이걸 못 잡는다. 세는 것만 보고 **이름은 안 봤기 때문**이다.

```python
assert (len(hwpx_doc.blocks), hwpx_doc.table_count, ...) == (len(docx_doc.blocks), ...)
```

`표{tables}` 쪽으로 맞췄다. 먼저 만든 쪽이고 `tables_DOC-HR-014_v2.0.md` 에 이미 그 형태로 저장돼 있어서다.

**두 곳에서 같은 개념을 각자 문자열로 만들면 언젠가 갈라진다.** 지금은 두 군데지만 상용 파서를 붙이면 세 군데가 된다.

참고: backend/app/rag/local_parsers.py, sandbox/w5/day02/00.hwpx파싱.ipynb, sandbox/w5/day02/02.문서파싱실습.ipynb
