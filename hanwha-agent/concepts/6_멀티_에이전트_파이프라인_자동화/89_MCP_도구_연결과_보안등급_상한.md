# MCP 도구 연결과 보안등급 상한

[[88_MCP_stdio_서버]]는 `initialize` 와 `ping` 만 받았다. 이번에 `tools/list`·`tools/call` 을 붙여
[[86_도구_등록소]]의 도구를 밖으로 내놓았다.

## 무엇을 내놓나

| 도구 | 등급 | 밖에 내놓기 | 이유 |
| --- | --- | --- | --- |
| search_documents | none | 예 | 읽기만 한다 |
| get_document_versions | none | 예 | 읽기만 한다 (새 도구) |
| create_draft | internal | 아니오 | 우리 DB 에 행을 쓴다 |
| send_slack | external | 아니오 | 되돌릴 수 없다 |

```python
def _exposed() -> dict:
    registry.load_all()
    return {t.name: t for t in registry.all_tools() if t.side_effect is registry.SideEffect.NONE}
```

[[86_도구_등록소]]에서 등급을 열거형으로 둔 것이 여기서 쓰인다. 내놓을지를 도구 이름이 아니라 **등급으로**
정한다. 도구가 늘어도 이 줄은 그대로다. 확인해 보니 목록에 둘만 나오고, 목록에 없는 `create_draft` 를
직접 부르면 `-32601 알 수 없는 도구` 로 막혔다.

## 새 도구 — 버전 이력

```python
def _run(*, doc_id: str) -> dict:
    with session_scope() as s:
        doc = document_repo.get_document(s, doc_id)
        if doc is None:
            return {"error": f"문서를 찾을 수 없습니다: {doc_id}"}
        versions = sorted(doc.versions, key=lambda v: v.version, reverse=True)
        return {"doc_id": ..., "title": ..., "dept": ..., "security_level": ...,
                "versions": [{"version", "status", "period", "chunk_count", "searchable"} ...]}
```

```text
국내출장 여비 규정 · 인사총무 · 일반
v2.0 · 현행 · 2025-07-01 ~             · 청크 53 · 검색 True
v1.1 · 만료 · 2024-09-01 ~ 2025-06-30  · 청크 24 · 검색 False
```

[[62_현행_판과_보안등급]]에서 만료본을 지우지 않고 거른다고 한 것이 이 도구의 재료다. 만료본이 남아
있어야 「언제까지였나」에 답할 수 있다.

정렬이 버전 **문자열** 정렬이다. `"v10.0" < "v2.0"` 이라 열 번째 판이 나오면 순서가 틀린다.
지금 문서는 한 자리 판뿐이라 드러나지 않는다.

## 등록소 → MCP 모양

```python
def on_tools_list(msg_id, params):
    for t in _exposed().values():
        props = dict(t.schema["input_schema"]["properties"])
        if t.name in USER_TOOLS:
            props["clearance"] = CLEARANCE
        tools.append({"name": t.name, "description": t.description,
                      "inputSchema": {**t.schema["input_schema"], "properties": props}})
```

Anthropic 도구 정의는 `input_schema`, MCP 는 `inputSchema` 다. 칸 이름만 다르고 안은 같은 JSON Schema 다
([[79_도구_정의와_tool_result]]). 등록소 하나로 두 규약에 다 내보낸다.

## 실패를 돌려주는 두 길

```python
if tool is None:
    respond(msg_id, error={"code": -32601, ...})                       # 프로토콜 오류
...
except Exception as e:
    respond(msg_id, {"content": [{"type": "text", "text": f"도구 실행 중 오류: {e}"}], "isError": True})
...
respond(msg_id, {"content": [{"type": "text", "text": text}], "isError": "error" in out})
```

| 실패 | 어디로 | 누가 읽나 |
| --- | --- | --- |
| 없는 도구 이름 | JSON-RPC `error` | 클라이언트 (프로토콜 문제) |
| 도구 안의 실패 | `result` 의 `isError: true` | **모델** |

[[79_도구_정의와_tool_result]]의 `is_error` 와 같은 생각이다. 인자를 빠뜨리고 `get_document_versions` 를
부르니 `isError: true` 와 「missing 1 required keyword-only argument: 'doc_id'」가 돌아왔다. 모델이 읽고 고쳐
부를 수 있는 문장이다. 우리 루프(`ask_with_tools`)에는 아직 이게 없는데 MCP 쪽이 먼저 생겼다.

## 보안등급을 호출자가 정한다

```python
USER_TOOLS = ("search_documents",)
CLEARANCE = {"type": "string", "enum": ["일반", "3급", "대외비"], "description": "조회자의 보안등급. 기본값 일반"}
...
clearance = args.pop("clearance", "일반")
ours = {"user": {"id": "mcp", "name": "MCP", "clearance": clearance, "dept_id": ""}}
```

[[79_도구_정의와_tool_result]]에서 「스키마에 `user` 가 없으니 모델은 보안등급을 고를 수 없다」고 적었다.
MCP 쪽은 반대다. `clearance` 를 **스키마에 넣어** 호출하는 쪽이 고르게 했다. 그리고 MCP 에는 인증이 없다.

실제로 넣어 봤다.

```text
search_documents("외부 저장매체 반출 승인 절차")
    → DOC-HR-021 제10조(장비) · 제6조(신청 절차)                    passed False

search_documents("외부 저장매체 반출 승인 절차", clearance="대외비")
    → DOC-SE-011 제4조(반출 신청) · 제7조(반출 시 조치)   (3급)
      DOC-SE-003 제11조(외부 반출)                        (대외비)  passed True
```

인자 한 줄로 대외비 문서가 열렸다. MCP 호스트에 이 서버를 붙인 사람이면 누구나, 또는 모델이 「더 잘 찾으려고」
스스로 적어도 열린다.

`get_document_versions` 는 등급을 아예 보지 않는다.

```text
get_document_versions("DOC-SE-003")
    → {"title": "정보보안 지침", "dept": "보안팀", "security_level": "대외비", "versions": [...]}
```

본문은 없지만 대외비 문서의 존재·제목·소관 부서·개정 이력이 나온다. [[63_검색_정책]]에서 「거른 사유에 제목이
실리면 정보가 샌다」고 적은 그 문제가 도구 하나로 통째로 열려 있다.

## 상한을 서버가 쥔다

수업 구조(clearance 인자)는 두고 상한을 서버 설정으로 걸었다.

```python
mcp_max_clearance: str = Field(default="일반", pattern=r"^(일반|3급|대외비)$")

def _capped(requested: str) -> str:
    cap = get_settings().mcp_max_clearance
    req = requested if requested in CLEARANCE else "일반"
    return req if CLEARANCE[req] <= CLEARANCE[cap] else cap

def _visible(out: dict) -> dict:
    level = out.get("security_level")
    if level and CLEARANCE.get(level, 1) > CLEARANCE[get_settings().mcp_max_clearance]:
        return {"error": f"문서를 찾을 수 없습니다: {out.get('doc_id')}"}
    return out
```

```text
                                        상한 일반(기본)          MCP_MAX_CLEARANCE=대외비
검색 + clearance="대외비"                DOC-HR-021 만            SE-011 · SE-003
get_document_versions("DOC-SE-003")     문서를 찾을 수 없습니다    정보보안 지침 · 대외비
get_document_versions("DOC-HR-014")     정상                      정상
```

두 가지를 골랐다.

- **요청은 상한까지 깎는다.** 거절하지 않는다. 상한 아래 문서로는 여전히 답한다.
- **넘는 문서는 「없다」고 한다.** 「권한이 없다」고 하면 그 문서가 있다는 사실이 샌다.

[[87_외부_전송과_승인_경계]]의 ②번 문(`ALLOW_EXTERNAL_SEND`)과 같은 모양이다. 호출하는 쪽이 아니라 서버를
띄우는 사람이 `.env` 로 정한다. 근본 해결은 아니다. 호출자가 누구인지 확인하는 인증이 생기면 상한 대신
그 사람의 등급을 쓰면 된다 — 그때까지의 안전판이다.

참고: mcp_server/server.py, backend/app/tools/get_document_versions.py, backend/app/tools/registry.py,
backend/app/core/config.py, sandbox/w8/day04/00.mcp도구등록.ipynb
