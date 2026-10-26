# LangGraph

[[90_에이전트_패턴_셋]]의 `run_workflow` 를 LangGraph 로 같은 흐름 그대로 다시 만들었다. 직접 만든 것과
라이브러리로 만든 것을 나란히 놓고 무엇이 같고 무엇이 빠지는지 본다.

## 무엇인가

LangChain 쪽에서 내는 **상태 기반(stateful) 워크플로우·에이전트 오케스트레이션** 프레임워크다.
[[34_LangChain_기초]]의 체인이 한 줄로 흐르는 파이프였다면, LangGraph 는 갈래와 되돌아가기가 있는 그래프다.

| 구성 | 뜻 | 우리 코드에서 |
| --- | --- | --- |
| State | 실행 중 공유되는 정보 | `run_chain` 의 `state` dict |
| Node | 작업 (LLM 호출, 도구 실행, 코드) | `Step` 함수 |
| Edge | 다음에 실행할 노드를 정한다 | `steps` 목록의 순서, `route` 의 갈래 표 |

```bash
python -m pip install "langgraph==1.2.11"
```

## 상태

```python
class WorkflowState(TypedDict, total=False):
    question: str
    user: dict
    sources: list[dict]
    passed: bool
    versions: dict
    note: str
    trace: Annotated[list[str], operator.add]
```

- `TypedDict` — 상태의 칸을 미리 선언한다. 노드는 **바뀐 칸만** 돌려주고 LangGraph 가 합친다.
  [[90_에이전트_패턴_셋]]의 `Step` 약속과 같다. 그래서 노드 함수를 그대로 가져다 쓸 수 있었다.
- `total=False` — 처음엔 `question`·`user` 만 있고 나머지는 노드가 채운다.
- `Annotated[..., operator.add]` — **리듀서**. 같은 칸을 두 노드가 돌려주면 덮어쓰지 않고 이어 붙인다.
  `run_chain` 이 `trace.append()` 로 하던 일을 선언으로 한다.

## 그래프

```python
def build_graph(search, routes, pick):
    g = StateGraph(WorkflowState)
    g.add_node("search", search)
    for name, step in routes.items():
        g.add_node(name, step)
        g.add_edge(name, END)
    g.add_edge(START, "search")
    g.add_conditional_edges("search", pick, {name: name for name in routes})
    return g.compile()
```

```text
START -> search -> pick(state) --- "found"        -> found        -> END
                                └-- "insufficient" -> insufficient -> END
```

| 직접 만든 것 | LangGraph |
| --- | --- |
| `run_chain([_wf_search, _wf_route], state)` | `add_edge(START, "search")` … |
| `_wf_route` 가 `route(state, pick, 표)` 를 부른다 | `add_conditional_edges("search", pick, 표)` |
| 갈래 함수가 `_wf_route` 안에서 불린다 | 갈래가 **노드**가 된다 |
| 표에 없는 이름 → `KeyError` | 표에 없는 이름 → 그래프 실행 중 오류 |

`_wf_route` 노드가 사라졌다. 라우팅이 함수가 아니라 **선(edge)** 이 됐기 때문이다. `pick` 함수
(`route_after_search`)는 그대로 쓴다.

`compile()` 이 그래프를 실행 가능한 객체로 만든다. 이때 끊긴 노드나 END 로 못 가는 노드를 검사한다.
`run_chain` 은 목록을 그냥 돌기 때문에 이런 검사가 없다.

## 같은 답, 빠진 것

```text
                          run_workflow                      run_graph
국내 출장 ... 몇 버전      found  versions={HR-014}           versions={HR-014}  (같다)
점심 메뉴 추천             insufficient  note 있음             note 있음           (같다)
trace                      ['_wf_search', '_wf_route']        []
route                      found / insufficient               (없음)
```

결과 값은 같다. 그런데 **그래프 쪽에는 어디를 지났는지가 남지 않았다.**

- `trace` 는 리듀서까지 선언했는데 빈 목록이다. 노드 함수가 `trace` 를 돌려주지 않기 때문이다.
  `run_chain` 은 바깥에서 `step.__name__` 을 붙여 줬는데 그래프에는 그 일을 하는 자리가 없다.
- `route` 는 상태 선언에 칸이 없다. 갈래가 함수에서 선으로 바뀌면서 「어느 갈래로 갔다」를 적던
  `route()` 의 `{"route": name}` 이 사라졌다.

수업 노트북이 갈래를 `passed` 로 거꾸로 추정한 이유가 이것이다.

```python
branch = "found" if out["passed"] else "insufficient"
pair = ("note" in out) == (not out["passed"])
```

결과에서 지나온 길을 되짚는 것은 갈래가 둘일 때만 된다. 갈래가 늘거나 같은 값으로 다른 갈래에 갈 수 있게
되면 추정이 안 된다. [[31_관측과_실행_기록]]에서 `run_steps` 를 둔 것과 같은 이유로, 노드마다
`{"trace": ["search"]}` 를 돌려주게 하면 리듀서가 이어 붙인다.

## 언제 LangGraph 인가

지금 흐름(검색 → 갈래 둘 → 끝)은 직접 만든 `run_chain` + `route` 로 충분했고 결과도 같았다.
LangGraph 가 값을 하는 것은 이 흐름에 없는 것들이다.

- **되돌아가는 선** — 「답변 검증이 불충분하면 재검색」처럼 노드가 앞 노드로 돌아가는 것.
  수업의 예시 흐름(생성 → 검증 → 불충분하면 재검색, 횟수 제한)이 그것이다. `run_chain` 의 목록으로는 못 그린다.
- **멀티 에이전트** — 노드 하나가 에이전트 하나가 되고, 상태가 에이전트 사이의 메모가 된다. 과목 이름이
  「멀티 에이전트 제어」인 이유다.
- 중간 상태 저장과 이어서 실행, 사람 승인 대기 — [[87_외부_전송과_승인_경계]]의 승인 단계가 붙을 자리다.

참고: backend/app/agent/state.py, backend/app/agent/graph.py, backend/app/services/chat_service.py
