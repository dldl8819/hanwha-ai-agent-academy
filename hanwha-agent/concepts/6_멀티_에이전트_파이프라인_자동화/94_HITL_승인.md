# HITL 승인

HITL(Human In The Loop)은 에이전트가 일하는 도중에 사람이 결정해야 하는 자리를 끼워 넣는 것이다.
[[87_외부_전송과_승인_경계]]에서 Slack 도구는 「승인 서비스가 `_execute` 를 직접 부르는 길로만 실행된다」고 했다.
그 승인 서비스를 만들었다.

## 멈춤과 재개

| | 하는 일 |
| --- | --- |
| `interrupt(값)` | 그래프를 멈추고 값을 바깥에 보인다 |
| `Command(resume=결정)` | 사람의 결정을 들고 멈춘 자리에서 재개한다 |
| 체크포인터 | 멈춘 자리를 저장한다. **없으면 재개할 수 없다** ([[93_체크포인트]]) |

```python
def _gate(state: dict) -> dict:
    return {"decision": interrupt({"text": state["text"]})}
```

`interrupt()` 를 처음 만나면 그래프가 멈추고 결과에 `__interrupt__` 가 실린다. `Command(resume=...)` 로 다시
부르면 LangGraph 는 `_gate` 를 **처음부터 다시 실행**하고, 이번에는 `interrupt()` 가 멈추지 않고 결정값을 돌려준다.
그래서 `interrupt()` 앞에 부작용(DB 쓰기, 전송)이 있으면 재개할 때 한 번 더 일어난다. gate 노드는 `interrupt` 한 줄만 둔다.

## 승인 그래프

```text
START -> draft -> gate (멈춤) --- 승인 -> send -> END
                              └── 반려 ----------> END
```

```python
def build_approval_graph(draft, send, *, checkpointer):
    if checkpointer is None:
        raise ValueError("승인 그래프는 저장소가 있어야 멈췄다 이어 간다. checkpointer를 넘기세요.")
    ...
    def pick(state):
        return "send" if state["decision"].get("approved") else "end"
```

체크포인터 없이 만들려 하면 바로 `ValueError` 다. 만들어지긴 하는데 멈춘 뒤 영영 이어 갈 수 없는 그래프를
애초에 못 만들게 막았다.

## 요청과 감사 로그

| 표 | 칸 |
| --- | --- |
| `approval_requests` | `id`(REQ-0148) · `thread_id`(unique) · `run_id` · `requester_id` · `approver_id` · `payload` · `status` · `requested_at` · `decided_at` |
| `audit_logs` | `approval_id` · `run_id` · `at` · `actor` · `event` · `detail` |

`thread_id` 가 요청과 멈춘 그래프를 잇는다. 승인 버튼을 누르면 요청 행에서 `thread_id` 를 꺼내 그 이름으로
그래프를 재개한다. [[84_초안_도구와_쓰기_등급]]에서 「감사 로그 테이블은 따로 없다」고 적었는데 이제 생겼다.

```text
run_approval_graph(text, thread_id, requester_id)
   ├─ 그래프 실행 → gate 에서 멈춤
   └─ open_request : 요청 1행 + 로그 「Slack 전송 요청 → 승인 대기」  (한 트랜잭션)

approve(req_id, approver_id)
   ├─ _decide : 대기 중인가? 권한 있나? → 상태 「승인」 + 로그 「승인」
   ├─ _resume : Command(resume={"approved": True}) → send → Slack 전송 시도
   └─ _close  : 결과로 「승인·실행」 또는 「실패 · 사유」 + 로그
```

`_send` 는 `registry.get("send_slack").fn(...)` 을 부른다. `Tool.run()` 이 아니라 `fn` 이다. [[86_도구_등록소]]의
`run()` 은 external 을 막는 입구였고, `fn` 은 막지 않는다. **승인을 거친 길만 `fn` 을 직접 쥔다.**

## 실제로 돌려 봤다

```text
요청          : REQ-0148 대기중                         (요청자 1번 김민준, 일반)
승인 by 1     : PermissionDenied 승인 권한이 없습니다
승인 by 2     : 실패 · 전송 꺼짐                        (정현우 팀장, ALLOW_EXTERNAL_SEND=false)
승인 by 3     : PermissionDenied 이미 처리된 요청: 실패 · 전송 꺼짐
로그          : Slack 전송 요청 → 승인 대기 · 승인 · 전송 안 됨 · 전송 꺼짐
```

[[87_외부_전송과_승인_경계]]의 세 문이 순서대로 보인다. ①은 사람이 열었고(승인), ②(`ALLOW_EXTERNAL_SEND`)에서
막혔다. 그 사실이 「승인·실행」이 아니라 「실패 · 전송 꺼짐」으로 남는다. 승인했다는 것과 실행됐다는 것이 다른 칸이다.

## 본인 요청을 본인이 승인할 수 있었다

```text
1 김민준  일반    can_approve=False
2 정현우  팀장    True
3 한서영  관리자  True
5 박성호  팀장    True ...
```

`_decide` 는 「대기 중인가」와 「`can_approve` 인가」만 봤다. 팀장이 요청자이면 자기 요청을 자기가 승인할 수
있었다. 승인의 뜻이 「다른 사람이 한 번 더 본다」인데 그게 빠진다. 이 저장소는 한 줄을 넣었다.

```python
if row.requester_id == approver_id:
    raise PermissionDenied("본인 요청은 승인·반려할 수 없습니다")
```

```text
팀장 2번의 요청을 2번이 승인 : PermissionDenied 본인 요청은 승인·반려할 수 없습니다
같은 요청을 5번이 반려       : 반려됨
```

## 반려 뒤 다시 쓰기는 아직 길이 없다

`ApprovalState.rewrites` 칸이 있고 `reject()` 에는 「다시 멈추면 재작성」 분기가 있다. 그런데 그래프는 반려하면
END 로 간다. 다시 쓰는 노드도 gate 로 돌아가는 선도 없다. 분기는 있는데 그 분기를 탈 길이 없다 —
[[77_점수를_재면서_쓰지_않는다]]의 `judge_gate` 와 같은 모양이다. 다음 수업에서 rewrite 노드가 붙을 자리다.

## 남은 것

- 승인 문구는 사람이 요청할 때 준 그대로다(`_draft` 가 받은 것을 그대로 돌려준다). 모델이 쓴 문구가 오면
  [[87_외부_전송과_승인_경계]]의 「신청자 이름·지어낸 연도가 실린 문구」를 사람이 승인 화면에서 봐야 한다.
- `REQ_START = 148` 과 「기존 번호 중 가장 큰 것 + 1」. 두 요청이 동시에 열리면 같은 번호를 잡을 수 있다.
  PK 라 둘째가 실패할 뿐 잘못 저장되지는 않는다.

참고: backend/app/agent/graph.py, backend/app/agent/state.py, backend/app/models/approval.py,
backend/app/services/approval_service.py, backend/app/services/chat_service.py
