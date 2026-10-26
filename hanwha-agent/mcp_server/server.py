# MCP 서버 (stdio)
# - 표준 입력으로 JSON-RPC 2.0 메시지를 한 줄씩 받고, 표준 출력으로 한 줄씩 답한다
# - stdout 은 프로토콜 전용 통로다. 로그나 print 가 한 글자라도 섞이면 클라이언트가 메시지를 못 읽는다
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.core.logging import setup_logging  # noqa: E402

# 로그를 stderr 로 보낸다
# - 다른 모듈이 get_logger() 를 먼저 부르면 기본값(stdout)으로 설정이 굳으므로 가장 먼저 부른다
setup_logging(stream=sys.stderr)

# 입출력을 UTF-8 로 고정한다
# - 윈도우 기본 콘솔 인코딩은 cp949 라 한글이 cp949 바이트로 나가고, UTF-8 을 기대하는 클라이언트가 깨진 글자를 받는다
# - newline="\n" : 텍스트 모드가 \n 을 \r\n 으로 바꾸지 않게 한다. 메시지 경계가 줄바꿈이다
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(newline="\n")

# 진짜 출구는 따로 쥐고, sys.stdout 은 stderr 로 돌려 둔다 — 실수로 print 해도 프로토콜이 안 깨진다
_PROTOCOL_OUT = sys.stdout
sys.stdout = sys.stderr

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "hanwha-agent", "version": "1.0.0"}
CAPABILITIES: dict = {}


# 응답 한 줄 쓰기. result 와 error 는 둘 중 하나만 실린다
def respond(msg_id, result=None, error=None) -> None:
    payload = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    _PROTOCOL_OUT.write(json.dumps(payload, ensure_ascii=False) + "\n")
    _PROTOCOL_OUT.flush()


# 핸드셰이크. 서버가 쓰는 프로토콜 버전과 제공 기능을 알린다
def on_initialize(msg_id, params: dict) -> None:
    respond(msg_id, {"protocolVersion": PROTOCOL_VERSION,
                     "capabilities": CAPABILITIES, "serverInfo": SERVER_INFO})


def on_ping(msg_id, params: dict) -> None:
    respond(msg_id, {})


METHODS = {"initialize": on_initialize, "ping": on_ping}


# 요청 한 건 처리
# - id 가 없으면 알림(notification)이다. 답하지 않는다 (예: notifications/initialized)
def handle(message: dict) -> None:
    msg_id = message.get("id")
    if msg_id is None:
        return
    fn = METHODS.get(message.get("method"))
    if fn is None:
        respond(msg_id, error={"code": -32601,
                               "message": f"지원하지 않는 메서드: {message.get('method')}"})
        return
    fn(msg_id, message.get("params") or {})


# ----- 도구 -------------------------------------------------------
from app.tools import registry  # noqa: E402

# 사용자 정보(보안등급)가 필요한 도구
USER_TOOLS = ("search_documents",)
CLEARANCE = {"type": "string", "enum": ["일반", "3급", "대외비"], "description": "조회자의 보안등급. 기본값 일반"}


# 밖에 내놓는 도구 : 부작용 none 만
# - internal(초안)·external(Slack) 은 우리 앱 안에서만 쓴다
def _exposed() -> dict:
    registry.load_all()
    return {t.name: t for t in registry.all_tools() if t.side_effect is registry.SideEffect.NONE}


# 등록소의 도구 정의를 MCP 모양(inputSchema)으로 옮긴다
def on_tools_list(msg_id, params: dict) -> None:
    tools = []
    for t in _exposed().values():
        props = dict(t.schema["input_schema"]["properties"])
        if t.name in USER_TOOLS:
            props["clearance"] = CLEARANCE
        schema = {**t.schema["input_schema"], "properties": props}
        tools.append({"name": t.name, "description": t.description, "inputSchema": schema})
    respond(msg_id, {"tools": tools})


# 호출자가 적은 등급을 서버 상한(MCP_MAX_CLEARANCE)까지만 인정한다
# - MCP 에는 인증이 없다. 상한이 없으면 arguments 에 '대외비' 한 줄로 대외비 문서가 검색된다
def _capped(requested: str) -> str:
    from app.core.config import get_settings
    from app.models.org import CLEARANCE

    cap = get_settings().mcp_max_clearance
    req = requested if requested in CLEARANCE else "일반"
    return req if CLEARANCE[req] <= CLEARANCE[cap] else cap


# 결과에 실린 문서 등급이 상한을 넘으면 없는 문서처럼 돌려준다 (존재 자체를 알리지 않는다)
def _visible(out: dict) -> dict:
    from app.core.config import get_settings
    from app.models.org import CLEARANCE

    level = out.get("security_level")
    if level and CLEARANCE.get(level, 1) > CLEARANCE[get_settings().mcp_max_clearance]:
        return {"error": f"문서를 찾을 수 없습니다: {out.get('doc_id')}"}
    return out


# 도구 하나 실행
# - 도구 안의 실패는 JSON-RPC error 가 아니라 결과의 isError 로 돌려준다. 모델이 읽고 대응하게
def on_tools_call(msg_id, params: dict) -> None:
    name = params.get("name")
    args = dict(params.get("arguments") or {})
    tool = _exposed().get(name)
    if tool is None:
        respond(msg_id, error={"code": -32601, "message": f"알 수 없는 도구: {name}"})
        return
    clearance = _capped(args.pop("clearance", "일반"))
    ours = ({"user": {"id": "mcp", "name": "MCP", "clearance": clearance, "dept_id": ""}}
            if name in USER_TOOLS else {})
    try:
        out = _visible(tool.run(**args, **ours))
    except Exception as e:
        respond(msg_id, {"content": [{"type": "text", "text": f"도구 실행 중 오류: {e}"}], "isError": True})
        return
    text = json.dumps(out, ensure_ascii=False, default=str)
    respond(msg_id, {"content": [{"type": "text", "text": text}], "isError": "error" in out})


CAPABILITIES["tools"] = {}
METHODS["tools/list"] = on_tools_list
METHODS["tools/call"] = on_tools_call


def main() -> int:
    print("[hanwha-agent MCP] 메서드 " + " · ".join(METHODS), file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
