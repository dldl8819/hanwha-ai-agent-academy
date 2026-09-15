# 비동기(async/await)와 asyncio

## 왜 비동기가 필요한가

보통 함수(동기 함수)는 "한번 시작하면 끝까지 달린다." 그 함수가 뭔가를 기다리는 동안(파일 읽기, 네트워크 응답 대기 등) 프로그램 전체가 멈춰서 다른 일을 못 한다. **비동기(async)**는 "기다리는 시간 동안 다른 일을 하자"는 아이디어다 — 기다리는 동안 제어권을 다른 작업에 넘겨주고, 기다림이 끝나면 다시 이어서 하던 일을 계속한다.

## 코루틴 (coroutine)

**나중에 다시 실행할 수 있는 함수, 즉 중간에 일시정지가 가능한 함수**다. `async def`로 정의한 함수가 코루틴 함수(비동기 함수)이고, 이걸 호출하면 코루틴 객체가 만들어진다.

핵심 특징 세 가지:

1. **호출해도 바로 실행되지 않는다.** `do_work()`처럼 그냥 호출만 하면 코드가 실행되는 게 아니라, "실행할 준비가 된 코루틴 객체"만 하나 돌려받는다.
2. **내부에서 `await`를 만나면 그 자리에서 즉시 멈춘다(suspend).**
3. **나중에 이벤트 루프가 다시 깨워준다(resume).**

```python
import asyncio

async def do_work():
    print("작업 시작")
    await asyncio.sleep(1)  # 1초 대기 (이 순간 제어권을 넘긴다)
    print("작업 재개")
    return "완료"

coro = do_work()
print("호출 결과 :", coro)  # 아직 실행 안 됨 — <coroutine object do_work at 0x...>

result = await coro  # 여기서 실제로 실행되고, 끝날 때까지 기다린다
print("돌려받은 값 :", result)
```

**실습 중 만난 오류**: `result = await coro`를 `reulst = await coro`로 오타 내고, 그다음 줄은 `result`(원래 의도한 철자)를 그대로 참조해서 `NameError: name 'result' is not defined`가 났다. 변수 이름 오타는 파이썬이 문법 단계에서는 못 잡아내고, 그 변수를 실제로 쓰는 시점에서야 에러로 드러난다는 걸 다시 확인한 사례다.

### `await`의 의미

"여기서 잠깐 멈출게 — 이벤트 루프야, 제어권 가져가. 내 연산이 끝나면 다시 깨워줘"라는 뜻이다. `await`는 코루틴 함수 안에서만 쓸 수 있다.

## Task와 asyncio, event loop

코루틴은 그 자체로는 그냥 "정지 가능한 함수"일 뿐이다. 이걸 실제로 이벤트 루프가 실행하도록 등록한 것이 **Task**다.

```python
asyncio.create_task(coro)  # coro를 이벤트 루프에게 "이것도 실행 목록에 넣어줘"라고 요청
```

- **asyncio**: 파이썬 표준 라이브러리로, 비동기 프로그래밍(코루틴·Task·이벤트 루프)을 다루는 도구 모음이다.
- **event loop**: asyncio의 두뇌이자 스케줄러다. 여러 코루틴/Task 중 지금 실행 가능한 걸 계속 돌아가며 실행해준다.

주피터 노트북에서는 이벤트 루프가 이미 돌아가고 있어서 `await`를 셀에 바로 써도 된다. 반대로 `.py` 파일에서는 이벤트 루프를 직접 만들거나 `asyncio.run()`으로 시작해야 한다.

```python
# 방법 1: 이벤트 루프를 직접 다룸
loop = asyncio.get_event_loop()
loop.run_until_complete(main_test())
loop.close()

# 방법 2: 파이썬 3.7 이상 권장 방식 — 한 번에 실행하고 정리까지 해줌
asyncio.run(main_test())
```

### 비동기 함수 호출

```python
async def test():
    return "test"

async def main_test():
    await test()  # 비동기 함수는 다른 비동기 함수 안에서 await로 호출한다
```

### 비동기 병렬 처리 — `asyncio.gather` / `create_task`

```python
async def job(name, t):
    print(f"{name} 시작")
    await asyncio.sleep(t)
    print(f"{name} 완료")

async def main():
    # create_task = "이벤트 루프야, 이것도 돌릴 목록에 넣어줘" (등록만 하고 바로 다음 줄로 진행)
    t1 = asyncio.create_task(job("A", 1))
    t2 = asyncio.create_task(job("B", 2))
    t3 = asyncio.create_task(job("C", 3))

    await t1
    await t2
    await t3

asyncio.run(main())
```

세 작업을 각각 `create_task`로 먼저 등록해두면, `await t1`에서 기다리는 동안에도 B·C 작업이 이미 백그라운드에서 같이 진행되고 있다. 그래서 1+2+3=6초가 아니라 가장 오래 걸리는 작업(3초) 정도로 전체가 끝난다 — 이게 비동기의 핵심 이점이다. (비슷한 일을 `asyncio.gather(job("A",1), job("B",2), job("C",3))` 한 줄로도 할 수 있다.)

## 주의점 — 코루틴 안에서 동기 함수를 부르면 안 된다

`async def` 함수 안에서 시간이 걸리는 **동기(블로킹) 함수**를 그냥 호출하면, 그 순간 이벤트 루프 전체가 멈춰버린다. `await`가 붙어 있어도 그 함수 자체가 동기 함수면 소용없다 — 이벤트 루프에 제어권을 안 넘기고 자기가 끝날 때까지 꽉 붙잡고 있기 때문이다.

문제가 되는 대표적인 경우:

- `time.sleep(...)` (→ `asyncio.sleep(...)`을 써야 한다)
- 무거운 CPU 연산
- 대용량 JSON 파싱
- 동기 방식 파일 읽기/쓰기
- `requests` 라이브러리(동기 HTTP) — 비동기가 필요하면 `httpx.AsyncClient` 등을 쓴다
- pandas로 대량 데이터 처리

## FastAPI에서 `def`와 `async def`의 차이

| | `def 라우터(...)` | `async def 라우터(...)` |
| --- | --- | --- |
| 실행 위치 | 스레드 풀로 보냄 | 이벤트 루프에서 직접 돌림 |
| 안에서 블로킹 코드를 써도 | 다른 요청은 멀쩡함 | 서버 전체가 멈춘다 |

**우리가 `async def`를 붙여야 하는 경우**:

- Claude 같은 LLM 호출(비동기 클라이언트로 부를 때)
- LangChain LCEL의 `astream` 같은 비동기 API
- 백그라운드 태스크가 있을 때

**프레임워크가 강제로 `async def`를 요구하는 경우**도 있다.

- `main.py`의 `lifespan` — FastAPI가 `async def`를 요구한다.
- `main.py`의 예외 핸들러(`@app.exception_handler`) — Starlette 규약상 `async def`로 작성해야 한다.

### 프로젝트에서 async def 개수 확인해보기

```python
import pathlib

APP = pathlib.Path("backend/app")
hits, plain = [], 0

for path in sorted(APP.rglob("*.py")):
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("async def "):
            hits.append((path.as_posix(), no, line.strip()))
        elif line.startswith("def "):
            plain += 1

for path, no, line in hits:
    print(f"{path}:{no}  {line}")
print(f"async def : {len(hits)}자리 / def : {plain}자리")
```

실제로 돌려보니 `backend/app`에는 `async def`가 3곳이었다.

```text
backend/app/api/v1/documents.py:92  async def upload_document(
backend/app/main.py:10  async def lifespan(app: FastAPI):
backend/app/main.py:33  async def handle_agent_error(
```

`lifespan`과 `handle_agent_error`는 프레임워크가 요구해서 필요하지만, **`upload_document`는 다르다.** 안을 들여다보면 `shutil.copyfileobj(file.file, out)`로 파일을 저장하는데, 이건 완전히 동기(블로킹) 파일 쓰기다 — `await`가 단 한 번도 안 쓰인다. 즉 "이벤트 루프에서 돌리겠다"고 `async def`를 선언해놓고, 정작 안에서는 이벤트 루프에 제어권을 한 번도 안 넘기는 블로킹 코드를 실행하는 셈이라, 위에서 정리한 "코루틴 안에서 동기 함수 호출" 문제에 그대로 해당한다. 이 엔드포인트는 `async def` 대신 그냥 `def`로 선언해서, FastAPI가 스레드 풀로 돌리게 두는 게 맞다.

참고: sandbox/w3/day01/00.async.ipynb, backend/app/api/v1/documents.py, backend/app/main.py
