# MCP stdio 서버

[[86_도구_등록소]]로 도구를 한 곳에 모았다. 다음은 그 도구를 우리 앱 밖의 AI 앱에서도 쓰게 하는 것이고,
그 규약이 MCP(Model Context Protocol)다.

## 라이브러리가 아니라 프로토콜이다

MCP 는 설치하는 제품이 아니라 통신 규약 문서다. HTTP 처럼 「이 모양으로 주고받자」는 약속이다.

| 구성 | 하는 일 | 예 |
| --- | --- | --- |
| 호스트 | 사용자가 쓰는 AI 앱 | Claude 데스크톱, IDE |
| 클라이언트 | 호스트 안에서 서버 **하나**와 연결을 맡는다 | 호스트가 서버마다 하나씩 만든다 |
| 서버 | 도구·데이터를 MCP 규약으로 제공 | 이번에 만든 것 |

서버가 제공하는 기능은 셋이고, **누가 쓰느냐**로 나뉜다.

| 기능 | 쓰는 쪽 | 뜻 |
| --- | --- | --- |
| Tools | 모델 | 실행할 함수. 이름·설명·입력 JSON Schema |
| Resources | 애플리케이션 | 읽기 전용 컨텍스트 (문서 본문, 설정) |
| Prompts | 사용자 | 미리 만든 프롬프트 템플릿 |

Tools 의 모양은 [[79_도구_정의와_tool_result]]의 `SCHEMA` 와 같다. 이름·설명·입력 스키마. 우리 도구를
MCP 로 내보내는 일이 어렵지 않은 이유다.

## 메시지와 전송

- 메시지 형식: **JSON-RPC 2.0** — `{"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}`
- 전송 방식 둘: **stdio**(표준 입출력, 로컬) / **Streamable HTTP**(원격, 배포용)

stdio 는 호스트가 서버를 자식 프로세스로 띄우고 stdin 으로 요청을 쓰고 stdout 으로 답을 읽는다.
한 줄이 한 메시지다.

## 동작 순서

1. 클라이언트가 서버에 연결하고 제공 기능(도구 목록)을 조회한다
2. 클라이언트가 도구 목록을 모델에 넘긴다
3. 사용자가 질문하면 모델이 도구와 인자를 정한다
4. 클라이언트가 서버에 도구 실행을 요청하고 결과를 받는다
5. 결과를 모델에 다시 넘기고 모델이 답을 쓴다

[[78_에이전트_루프와_멈추는_조건]]의 루프와 같다. 다른 점은 3·5번의 모델 호출을 호스트가 하고,
4번의 실행이 **다른 프로세스**에서 일어난다는 것이다. `ask_with_tools` 에서는 모두 한 프로세스였다.

## 만든 서버

```python
METHODS = {"initialize": on_initialize, "ping": on_ping}

def handle(message: dict) -> None:
    msg_id = message.get("id")
    if msg_id is None:          # 알림(notification). 답하지 않는다
        return
    fn = METHODS.get(message.get("method"))
    if fn is None:
        respond(msg_id, error={"code": -32601, "message": f"지원하지 않는 메서드: ..."})
        return
    fn(msg_id, message.get("params") or {})
```

| 짚을 것 | 이유 |
| --- | --- |
| `id` 가 없으면 무시 | JSON-RPC 에서 `id` 없는 메시지는 알림이다. 답을 보내면 안 된다. `notifications/initialized` 가 그렇다 |
| `-32601` | JSON-RPC 의 「Method not found」 표준 코드 |
| `CAPABILITIES = {}` | 아직 tools 를 선언하지 않았다. 클라이언트는 `tools/list` 를 부르지 않는다 |
| `PROTOCOL_VERSION = "2024-11-05"` | 규약 버전. 공식 문서에 날짜로 된 버전이 여럿 있다 |

## stdout 은 프로토콜 전용이다

```python
setup_logging(stream=sys.stderr)
_PROTOCOL_OUT = sys.stdout
sys.stdout = sys.stderr
```

이 서버에서 가장 중요한 세 줄이다. stdio 서버는 stdout 이 곧 통신선이다. 로그 한 줄, `print` 한 번이
stdout 에 섞이면 클라이언트는 그걸 JSON 메시지로 읽으려다 실패한다.

- `setup_logging(stream=sys.stderr)` — 우리 로그를 stderr 로. [[06_로깅]]의 기본은 stdout 이었다.
- `_PROTOCOL_OUT` — 진짜 출구는 따로 쥔다. `respond()` 만 여기에 쓴다.
- `sys.stdout = sys.stderr` — 누가 실수로 `print` 해도 stderr 로 간다.

순서도 중요하다. `get_logger()` 는 처음 불릴 때 `setup_logging()` 을 기본값(stdout)으로 부르고, 한 번 설정되면
다시 안 바뀐다(`_CONFIGURED`). 다른 모듈이 먼저 로거를 꺼내면 stdout 으로 굳는다. 그래서
`app.core.logging` 만 import 한 직후, 다른 앱 모듈을 import 하기 전에 부른다.

## 윈도우에서 한글이 깨졌다

수업 코드 그대로 돌리니 이렇게 나왔다.

```text
{"jsonrpc": "2.0", "id": 3, "error": {"code": -32601, "message": "�������� �ʴ� �޼���: tools/list"}}
```

윈도우의 파이썬은 콘솔이 아닌 파이프에 쓸 때 시스템 인코딩(cp949)을 쓴다. `ensure_ascii=False` 로
한글을 그대로 쓰니 cp949 바이트가 나갔다. MCP 클라이언트는 UTF-8 을 기대한다. 영어 메시지만 오가면
안 보이다가, 도구 결과에 규정 본문이 실리는 순간 깨진다.

```python
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(newline="\n")
```

입력도 같이 고정한다. 모델이 한글 인자(`{"query": "부산 출장 숙박비"}`)를 보내면 stdin 도 cp949 로 읽어
깨진다. `newline="\n"` 은 텍스트 모드가 `\n` 을 `\r\n` 으로 바꾸지 않게 한다. 고친 뒤 바이트로 확인하니
UTF-8 이고 줄 끝이 `\n` 하나였다.

[[52_파서_진입점과_형식_확장]]에서 cp949 메모 파일을 읽으며 인코딩을 다뤘는데 같은 문제가 반대 방향(쓰기)으로 나왔다.

## 확인

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
              '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
              '{"jsonrpc":"2.0","id":2,"method":"ping"}' | python mcp_server/server.py
```

```text
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {...}}}
{"jsonrpc": "2.0", "id": 2, "result": {}}
```

알림에는 답이 없다. 세 줄을 보내고 두 줄을 받았다.

다음 단계는 `capabilities` 에 tools 를 선언하고 `tools/list`·`tools/call` 을 [[86_도구_등록소]]에 잇는 것이다.
그때 [[87_외부_전송과_승인_경계]]의 ①번 문이 MCP 쪽에서도 그대로 서야 한다. 등록소의 `Tool.run()` 을
거치면 그대로 선다.

참고: mcp_server/server.py, backend/app/core/logging.py
