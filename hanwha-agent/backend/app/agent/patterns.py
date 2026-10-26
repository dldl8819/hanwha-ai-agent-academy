# 에이전트 패턴 세 가지 — 순서(체이닝), 갈래(라우팅), 동시(병렬)
# - 모두 "다음 단계를 우리가 정한다"는 공통점이 있다. 모델이 정하는 것은 에이전트 루프(ask_with_tools)다
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

# 단계 = state 를 받아 바뀐 키만 돌려주는 함수
Step = Callable[[dict], dict]


# ------ 체이닝 ----------------------------------------
# 단계를 순서대로 부르고, 바뀐 키를 state 에 합친다
# - 단계가 error 를 돌려주면 다음 단계는 부르지 않는다
def run_chain(steps: list[Step], state: dict) -> dict:
    trace = state.setdefault("trace", [])
    for step in steps:
        changed = step(state)
        trace.append(step.__name__)
        state.update(changed)
        if "error" in changed:
            break
    return state


# ------ 라우팅 ----------------------------------------
# 검색 뒤 갈래 : 근거가 임계값을 넘었는가
def route_after_search(state: dict) -> str:
    return "found" if state.get("passed") else "insufficient"


# pick 이 고른 이름으로 갈래 표에서 단계를 찾아 부른다
# - 표에 없는 이름이면 조용히 넘어가지 않고 KeyError. 갈래가 빠진 것을 바로 알게 한다
def route(state: dict, pick: Callable[[dict], str], routes: dict[str, Step]) -> dict:
    name = pick(state)
    if name not in routes:
        raise KeyError(f"작업 갈래 표에 없는 이름: {name!r} - 존재하는 이름: {sorted(routes)}")
    return {"route": name, **routes[name](state)}


# ------ 병렬 ------------------------------------------
# 서로 기다릴 이유가 없는 호출을 동시에 돌리고 이름별로 모은다
# - 스레드라서 DB·네트워크·LLM 처럼 기다리는 일에서만 빨라진다. 순수 계산은 GIL 때문에 이득이 없다
# - 하나가 터져도 나머지 결과는 살린다. 터진 자리에는 error 를 담는다
def run_parallel(calls: dict[str, tuple[Callable[..., dict], dict]], max_workers: int = 4) -> dict[str, dict]:
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {name: ex.submit(fn, **kwargs) for name, (fn, kwargs) in calls.items()}
    out: dict[str, dict] = {}
    for name, f in futures.items():
        try:
            out[name] = f.result()
        except Exception as e:
            out[name] = {"error": f"{type(e).__name__}: {e}"}
    return out
