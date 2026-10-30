# run_workflow 와 같은 흐름을 LangGraph 로
#
#   START -> search -> pick(state) --- "found"        -> found        -> END
#                                   └-- "insufficient" -> insufficient -> END
#
# - 노드 함수는 patterns.Step 그대로 쓴다 (state 를 받아 바뀐 키만 돌려준다)
from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from app.agent.patterns import Step
from app.agent.state import WorkflowState


def build_graph(search: Step, routes: dict[str, Step], pick: Callable[[dict], str]):
    g = StateGraph(WorkflowState)
    g.add_node("search", search)
    for name, step in routes.items():
        g.add_node(name, step)
        g.add_edge(name, END)
    g.add_edge(START, "search")
    # pick 이 돌려준 이름 → 같은 이름의 노드
    g.add_conditional_edges("search", pick, {name: name for name in routes})
    return g.compile()


# ----- 순환 그래프 ---------------------------------------------------
#   START -> search -> pick --- found        -> END
#              ^          ├-- insufficient -> END
#              └── fix <──┘ "fix"
from langgraph.types import RetryPolicy, interrupt  # noqa: E402

from app.agent.state import ApprovalState, LoopState  # noqa: E402


# - retry_policy : 노드 안에서 정해진 예외가 나면 그 노드만 다시 부른다
# - checkpointer : 노드가 끝날 때마다 상태를 저장한다. 있으면 thread_id 로 이어서 실행할 수 있다
def build_loop_graph(search: Step, fix: Step, routes: dict[str, Step], pick: Callable[[dict], str], *,
                     search_retry: RetryPolicy | None = None, fix_retry: RetryPolicy | None = None,
                     checkpointer=None):
    g = StateGraph(LoopState)
    g.add_node("search", search, retry_policy=search_retry)
    g.add_node("fix", fix, retry_policy=fix_retry)
    for name, step in routes.items():
        g.add_node(name, step)
        g.add_edge(name, END)
    g.add_edge(START, "search")
    g.add_conditional_edges("search", pick, {"fix": "fix", **{name: name for name in routes}})
    g.add_edge("fix", "search")          # 되돌아가는 선
    return g.compile(checkpointer=checkpointer)


# ----- 승인 그래프 ---------------------------------------------------
#   START -> draft -> gate (멈춤) --(승인)-------------------------> send -> END
#                       ^  └-(반려 · 다시 쓴 횟수 < MAX_REWRITES)--> rewrite --+
#                       └-----------------------------------------------------+
#                          └-(반려 · 상한)-------------------------------------> END
MAX_REWRITES = 2

# 사람의 결정을 기다린다
# - interrupt() 는 여기서 그래프를 멈추고 값을 바깥에 보인다
# - Command(resume=결정) 으로 다시 부르면 이 노드를 처음부터 다시 실행하고, 이번엔 interrupt() 가 결정을 돌려준다
def _gate(state: dict) -> dict:
    return {"decision": interrupt({"text": state["text"]})}


def build_approval_graph(draft: Step, send: Step, *, checkpointer, rewrite: Step | None = None):
    # 멈춘 자리를 저장할 곳이 없으면 재개할 수 없다
    if checkpointer is None:
        raise ValueError("승인 그래프는 저장소가 있어야 멈췄다 이어 간다. checkpointer를 넘기세요.")

    g = StateGraph(ApprovalState)
    g.add_node("draft", draft)
    g.add_node("gate", _gate)
    g.add_node("send", send)
    g.add_edge(START, "draft")
    g.add_edge("draft", "gate")

    def pick(state: dict) -> str:
        if state["decision"].get("approved"):
            return "send"
        return "rewrite" if rewrite is not None and state.get("rewrites", 0) < MAX_REWRITES else "end"

    routes = {"send": "send", "end": END}
    # rewrite 를 넘기면 반려 → 다시 쓰기 → gate(다시 멈춤) 순환이 생긴다
    if rewrite is not None:
        g.add_node("rewrite", rewrite)
        g.add_edge("rewrite", "gate")
        routes["rewrite"] = "rewrite"
    g.add_conditional_edges("gate", pick, routes)
    g.add_edge("send", END)
    return g.compile(checkpointer=checkpointer)


# ----- supervisor 그래프 ---------------------------------------------
#   START -> supervisor --(pick 이 고른 이름)--> search / draft --+
#                ^                                              |
#                └──────────────── 끝나면 돌아온다 ──────────────┘
#                └── "finish" -> END
from app.agent.state import SupervisorState  # noqa: E402


def build_supervisor_graph(workers: dict[str, Step], pick: Callable[[dict], str]):
    # 고르기만 하고 일은 하지 않는다. 몇 번 골랐는지 센다
    def supervisor(state: dict) -> dict:
        return {"next": pick(state), "turns": state.get("turns", 0) + 1}

    g = StateGraph(SupervisorState)
    g.add_node("supervisor", supervisor)
    for name, step in workers.items():
        g.add_node(name, step)
        g.add_edge(name, "supervisor")      # 담당이 끝나면 supervisor 로 돌아간다
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", lambda s: s["next"], {**{n: n for n in workers}, "finish": END})
    return g.compile()

