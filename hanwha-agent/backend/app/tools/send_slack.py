# Slack 전송 도구
# - external 등급의 첫 도구. 지금은 구조만 있다. 루프에서 부르면 ApprovalRequired 로 막힌다
# - 실제 전송은 승인(HITL) 단계에서 _execute 를 직접 부르는 길로 붙는다
from __future__ import annotations

from app.tools.registry import SideEffect, Tool, register

SCHEMA = {
    "name": "send_slack",
    "description": "Slack 채널에 메시지를 보낸다. 외부로 나가므로 팀장 승인이 필요하다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "보낼 문구. 초안을 요약한 한두 문장."},
        },
        "required": ["text"],
    },
}


# 승인 서비스 전용. 루프에서 직접 부르지 않는다
def _execute(*, text: str, channel: str = "") -> dict:
    from app.integrations.factory import get_slack

    result = get_slack().post(channel=channel, text=text)
    return {"ok": result.ok, "channel": result.channel, "ts": result.ts,
            "error": result.error, "simulated": result.simulated}


register(Tool(name=SCHEMA["name"], description=SCHEMA["description"],
              side_effect=SideEffect.EXTERNAL, fn=_execute, schema=SCHEMA,
              reversible=False))
