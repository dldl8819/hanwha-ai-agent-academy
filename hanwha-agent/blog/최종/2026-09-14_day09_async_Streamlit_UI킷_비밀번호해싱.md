# [한화 내일 아카데미 ICT부문] 9일차 후기 — async/await, Streamlit, UI 킷, 비밀번호 해싱

지난 포스팅에서는 스키마와 파일 업로드 API, 검색 키워드 확장까지 백엔드 쪽을 정리했었습니다. 9일차에는 그렇게 만들어 둔 API를 실제로 보여줄 화면 쪽으로 넘어갔습니다. 한화 내일 아카데미 ICT부문 과정에서 처음으로 프론트엔드를 다룬 날이고, 그 전에 백엔드에서 계속 써 왔던 `async def`가 정확히 무슨 의미인지도 짚고 넘어갔습니다.

9일차에 학습한 내용을 순서대로 정리해봅니다.

1. async/await와 이벤트 루프
2. Streamlit 기초와 재실행 모델
3. Streamlit 애드온 — shadcn, AgGrid, ECharts
4. UI 킷으로 화면 통일하기
5. 비밀번호 해싱(bcrypt)

## 1. async/await와 이벤트 루프

동기 함수는 한번 시작하면 끝까지 달립니다. 그래서 파일을 읽거나 네트워크 응답을 기다리는 동안 프로그램 전체가 멈춥니다. 비동기는 그 기다리는 시간에 다른 일을 하자는 접근입니다.

`async def`로 정의한 함수를 코루틴 함수라고 하는데, 특징이 세 가지입니다.

- 호출해도 바로 실행되지 않고 코루틴 객체만 돌려받는다
- 내부에서 `await`를 만나면 그 자리에서 멈춘다
- 나중에 이벤트 루프가 다시 깨워준다

```python
import asyncio

async def do_work():
    print("작업 시작")
    await asyncio.sleep(1)
    print("작업 재개")
    return "완료"

coro = do_work()
print("호출 결과 :", coro)   # <coroutine object do_work at 0x...>

result = await coro          # 여기서 실제로 실행된다
```

`await`는 "여기서 잠깐 멈출 테니 이벤트 루프가 제어권을 가져가고, 내 연산이 끝나면 다시 깨워달라"는 뜻입니다. 여러 작업을 `create_task`로 먼저 등록해두면 동시에 진행됩니다.

```python
async def main():
    t1 = asyncio.create_task(job("A", 1))
    t2 = asyncio.create_task(job("B", 2))
    t3 = asyncio.create_task(job("C", 3))
    await t1
    await t2
    await t3
```

1초, 2초, 3초짜리 작업 세 개를 합쳐도 6초가 아니라 가장 오래 걸리는 3초 정도에 끝납니다.

반대로 코루틴 안에서 동기 함수를 부르면 그 순간 이벤트 루프 전체가 멈춥니다. `time.sleep`, 무거운 CPU 연산, 동기 방식 파일 입출력, `requests` 같은 동기 HTTP 라이브러리가 여기 해당합니다.

```python
async def handle_request():
    await asyncio.sleep(0.1)   # 제어권을 넘긴다
    time.sleep(2)              # 이벤트 루프가 2초간 멈춘다
    return "OK"
```

FastAPI에서는 `def`로 선언하면 스레드 풀로 보내고 `async def`로 선언하면 이벤트 루프에서 직접 돌립니다. 그래서 `async def` 안에 블로킹 코드가 있으면 서버 전체가 영향을 받습니다. 실제로 프로젝트에서 `async def`가 몇 군데인지 세어봤더니 세 곳이었는데, 그중 파일 업로드 엔드포인트는 안에서 `shutil.copyfileobj`로 동기 파일 쓰기만 하고 `await`가 한 번도 없었습니다. 이런 자리는 `async def` 대신 `def`로 두고 FastAPI가 스레드 풀로 돌리게 하는 편이 맞습니다.

## 2. Streamlit 기초와 재실행 모델

Streamlit은 파이썬 스크립트를 웹 페이지로 바꿔주는 도구입니다. HTML/CSS/JS 없이 파이썬 함수 호출만으로 화면을 만들 수 있습니다.

가장 중요한 개념은 재실행 모델입니다. **버튼 클릭이나 입력 같은 이벤트가 일어날 때마다 `.py` 파일 전체가 처음부터 다시 실행됩니다.** 특정 함수만 실행되는 구조가 아닙니다.

```python
# 이렇게 하면 숫자가 절대 안 늘어난다 — 매번 count = 0으로 되돌아간다
count = 0
if st.button("문서 1건 추가"):
    count = count + 1
st.write("추가한 문서 수 : ", count)
```

재실행돼도 값이 유지돼야 하는 것은 `session_state`에 저장해야 합니다. 위젯을 만들 때 `key="..."`를 주면 그 값이 자동으로 `st.session_state["그 key"]`에 들어가서, 별도 이벤트 핸들러 없이도 최신 값을 읽을 수 있습니다.

```python
st.selectbox("상태", ["python", "FastAPI", "streamlit"], key="f_status")
st.text_input("입력란", key="f_query")

st.json({"status": st.session_state.f_status, "query": st.session_state.f_query})
```

이 밖에 `st.columns`로 가로 분할, `st.container(border=True)`로 묶기, `st.tabs`로 탭 구성, `st.Page` + `st.navigation`으로 멀티페이지 구성을 실습했습니다. 채팅 UI는 `chat_message`와 `chat_input`으로 만들고, 대화 이력은 재실행에 사라지면 안 되니 `session_state.messages`에 쌓는 방식으로 처리했습니다.

## 3. Streamlit 애드온 — shadcn, AgGrid, ECharts

기본 위젯만으로 부족한 부분은 외부 컴포넌트를 붙여봤습니다.

| 라이브러리 | 쓰임 |
| --- | --- |
| `streamlit-shadcn-ui` | 카드, 배지, 지표 카드 같은 부품 |
| `streamlit-aggrid` | 정렬·필터가 되는 표 |
| `streamlit-echarts` | 게이지 등 차트 |

여기서 한 가지 한계를 만났습니다. shadcn의 `ui.table`은 칸 값을 전부 글자로 처리해서, "상태" 칸에 색깔 있는 배지를 넣을 방법이 없습니다. `align` 같은 옵션은 지원해도 셀 안에 HTML을 넣는 것은 안 됩니다. 뒤에 나오는 UI 킷이 배지를 직접 HTML로 그리는 이유가 여기에 있습니다.

ECharts에서는 `detail.formatter`를 `"{vale}%"`로 오타 내는 실수를 했습니다. ECharts는 `{value}`라는 정확한 이름만 치환해주기 때문에, 오타가 나면 게이지에 `{vale}%`라는 글자가 그대로 찍힙니다. 에러가 나지 않고 화면에만 이상하게 보이는 종류의 오타라서 로그로는 찾을 수 없습니다.

## 4. UI 킷으로 화면 통일하기

수업에서 만드는 화면들의 디자인을 통일하기 위해 `frontend/` 폴더에 UI 킷을 받아 붙였습니다.

```text
frontend/
    app.py                 # 실행 시작점
    assets/
        tokens.css          # 색상·간격 등 디자인 토큰
        base.css
        components.css
    ui/
        theme.py            # CSS 주입
        badge.py            # 상태 배지
        card.py, chart.py, metric.py, source.py, status.py, table.py
```

`tokens.css`는 값만 모아둔 파일이라 한 줄만 바꾸면 화면 전체 색이 따라 바뀝니다. 규칙 파일들은 `var(--ag-accent)`처럼 이름을 부르기만 합니다. CSS는 `tokens.css` → `base.css` → `components.css` 순서로 주입해야 하고, 순서가 바뀌면 변수가 정의되기 전에 규칙이 나와서 색이 빠집니다.

`theme.py`에는 실습 중 겪은 함정이 그대로 반영되어 있었습니다.

```python
@lru_cache(maxsize=1)
def load_css() -> str:
    # 파일을 읽어 문자열로 합치는, 비용이 드는 부분만 캐시
    ...

def inject_css() -> None:
    # <style>로 꽂는 부분은 매번 실행돼야 한다
    st.markdown(f"<style>\n{load_css()}\n</style>", unsafe_allow_html=True)
```

"한 번만 주입"하려고 `session_state`로 막으면 버튼을 한 번 누른 뒤부터 스타일이 통째로 사라집니다. 앞에서 정리한 재실행 모델과 정확히 같은 원리로, **결과가 항상 같은 순수 계산은 캐시해도 되지만 화면에 실제로 뭔가를 그리는 동작은 매번 실행돼야 한다**는 구분입니다.

배지는 상태 문자열을 보고 색을 자동으로 정하는데, 판정 기준이 "그 말로 시작하는지"입니다.

```python
badge_html("재임베딩 62%")     # 주황색 — '재임베딩'으로 시작한다
badge_html("색인 완료")        # 회색 — '완료'가 뒤에 있어서 걸리지 않는다
badge_html("색인 완료", "ok")  # 직접 지정하면 된다
```

표의 열 정렬도 킷이 가진 클래스 이름(`ag-num`, `ag-nowrap`)만 동작하고, `"left"`나 `"center"`를 적으면 클래스만 붙고 아무 일도 일어나지 않습니다. 에러도 경고도 없이 화면만 안 바뀌는 자리가 여러 곳이라, 값을 넘길 때 이름을 정확히 맞추는 것이 중요했습니다.

## 5. 비밀번호 해싱(bcrypt)

로그인 기능을 만들려면 입력한 비밀번호를 저장된 값과 비교해야 하는데, 원문을 그대로 저장하면 DB가 유출되는 순간 전부 노출됩니다. 그래서 해싱한 값만 저장하고, 로그인 시에는 같은 방식으로 해싱해서 비교합니다.

```python
import bcrypt

RAW = "hanwha2026!"

first = bcrypt.hashpw(RAW.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
second = bcrypt.hashpw(RAW.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

print(len(first))                                                  # 60
print(bcrypt.checkpw(RAW.encode("utf-8"), first.encode("utf-8")))   # True
print(bcrypt.checkpw(RAW.encode("utf-8"), second.encode("utf-8")))  # True
```

같은 비밀번호를 두 번 해싱하면 `gensalt()`가 매번 다른 salt를 붙이기 때문에 결과 문자열이 서로 다릅니다. 그런데도 둘 다 검증에 통과합니다. salt가 해시 문자열 안에 함께 들어 있어서 `checkpw`가 저장된 해시에서 salt를 꺼내 같은 방식으로 다시 계산하기 때문입니다. 그래서 비교는 문자열 `==`이 아니라 반드시 `checkpw`로 해야 합니다.

프로젝트에는 `core/security.py`를 만들어 인코딩/디코딩을 감싼 함수 두 개로 정리했습니다.

```python
def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
```

로그인 실패용 예외(`AuthFailed`, 401)도 기존 예외 계층에 추가했는데, 사번이 없는 경우와 비밀번호가 틀린 경우를 같은 메시지로 돌려줍니다. 응답을 나누면 어떤 사번이 실제로 등록돼 있는지 알아낼 수 있기 때문입니다.

`User` 모델에는 `password_hash` 컬럼을 추가했습니다. 여기서 한 가지 걸리는 부분이 있었는데, 모델에 컬럼을 추가해도 이미 만들어진 SQLite 파일에는 반영되지 않는다는 점입니다. `create_all()`이 테이블이 없으면 만들고 이미 있으면 아무것도 하지 않기 때문입니다.

```python
get_engine().dispose()           # 풀에 남아있는 커넥션 먼저 닫기
DB_FILE.unlink(missing_ok=True)  # 파일 삭제
init_db()                        # 테이블 다시 생성

columns = [c["name"] for c in inspect(get_engine()).get_columns("users")]
print("password_hash 들어갔나 :", "password_hash" in columns)
```

`dispose()`를 먼저 부르는 이유는 엔진이 커넥션 풀로 파일을 붙잡고 있으면 윈도우에서 삭제가 막히기 때문입니다. 모델 코드만 보고 넘어가면 DB를 안 지웠을 때 조용히 예전 스키마를 쓰게 되므로, `inspect`로 실제 컬럼을 확인하는 단계까지 거쳤습니다. 마지막으로 시드 데이터에도 임시 비밀번호를 해싱해서 채워 넣었습니다.

## 이날의 소감

지금까지는 터미널과 `/docs` 화면으로만 결과를 확인했는데, 9일차부터는 만든 API가 실제 화면으로 연결되는 단계로 넘어갔습니다. 한화 내일 아카데미 ICT부문 과정에서 백엔드 구조를 여덟 번에 걸쳐 쌓아온 뒤에 화면을 붙이는 순서라, 화면에 무엇을 보여줘야 하는지는 이미 정해져 있는 상태에서 시작했습니다. Streamlit의 재실행 모델은 기존에 알던 웹 프레임워크의 요청-응답 방식과 동작이 달라서, 처음에는 변수 값이 왜 초기화되는지 이해하는 데 시간이 걸렸습니다. CSS 주입을 캐시하면 안 되는 이유도 결국 같은 원리에서 나온다는 점을 확인하면서 정리가 됐습니다.

이날 다룬 내용 중 절반 정도는 틀려도 에러가 나지 않는 종류였습니다. 배지 색이 안 바뀌거나, 정렬 클래스가 안 먹거나, 차트 라벨에 치환되지 않은 글자가 찍히는 식입니다. 백엔드에서는 예외와 로그로 문제를 잡을 수 있었지만 화면 쪽은 직접 띄워서 눈으로 확인해야 한다는 차이를 다루게 됐습니다. 비동기와 비밀번호 해싱은 그동안 코드에 써 오기만 했던 부분의 근거를 채우는 시간이었습니다.

다음 포스팅에서는 이어서 진행한 로그인 화면과 비밀번호 검증, 문서 목록 화면과 API 연동을 정리해보겠습니다.

\#한화내일아카데미 \#한화시스템 \#AI개발자 \#K뉴딜아카데미 \#국비지원교육 \#개발자이직 \#부트캠프후기 \#프론트엔드개발 \#파이썬프로젝트 \#AI에이전트

참고 링크 : https://blog.naver.com/dldl8819/224412170740
