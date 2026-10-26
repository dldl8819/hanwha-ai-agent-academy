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
