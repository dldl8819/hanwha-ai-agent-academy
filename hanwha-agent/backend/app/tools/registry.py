# 도구 등록소
# - 도구 연결을 한 곳에 모은다. 서비스는 도구 이름을 몰라도 목록을 받아 모델에게 넘긴다
# - 부작용 등급을 여기서 강제한다. external 도구는 run() 으로 실행되지 않는다
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from app.core.exceptions import ApprovalRequired


class SideEffect(str, Enum):
    NONE = "none"               # 조회
    INTERNAL = "internal"       # 내부 쓰기 (우리 DB 만 바뀐다)
    EXTERNAL = "external"       # 외부 실행. 되돌릴 수 없다. 승인 필요


@dataclass
class Tool:
    name: str
    description: str
    side_effect: SideEffect
    fn: Callable
    schema: dict
    reversible: bool = True

    # 루프가 부르는 실행 입구
    # - external 은 여기서 막는다. 실제 실행은 승인 서비스가 fn 을 직접 부르는 길로만 한다
    def run(self, **kwargs) -> dict:
        if self.side_effect is SideEffect.EXTERNAL:
            raise ApprovalRequired(f"'{self.name}'은(는) 승인 없이 실행할 수 없습니다.",
                                   detail="approval_service.approve() 를 통해서만 실행됩니다.")
        return self.fn(**kwargs)


_REGISTRY: dict[str, Tool] = {}


# 도구를 목록에 올린다. 문자열 등급("none")도 SideEffect 로 바꿔 둔다
def register(tool: Tool) -> Tool:
    tool.side_effect = SideEffect(tool.side_effect)
    _REGISTRY[tool.name] = tool
    return tool


def get(name: str) -> Tool:
    if name not in _REGISTRY:
        raise KeyError(f"등록되지 않은 도구: {name}")
    return _REGISTRY[name]


def all_tools() -> list[Tool]:
    return list(_REGISTRY.values())


# 도구 모듈을 등록한다
# - 검색·초안은 모듈 상수(NAME·SCHEMA·SIDE_EFFECT·run)로 감싸 등록하고
#   send_slack 은 모듈이 import 될 때 스스로 등록한다
def load_all() -> None:
    from app.tools import create_draft, search_documents

    for m in (search_documents, create_draft):
        register(Tool(name=m.NAME, description=m.SCHEMA["description"],
                      side_effect=m.SIDE_EFFECT, fn=m.run, schema=m.SCHEMA))

    from app.tools import get_document_versions, send_slack  # noqa: F401  import 시 등록
