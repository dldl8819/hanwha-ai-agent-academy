# 도구 정의와 tool_result

[[78_에이전트_루프와_멈추는_조건]]의 한 바퀴를 메시지 단위로 뜯는다.

## 도구 하나를 말로 쓴다

```python
SCHEMA = {
    "name": "search_documents",
    "description": "사내 규정 문서를 검색해 근거 문단을 돌려준다. 현행 버전, 보안 등급 필터가 적용된다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "찾을 내용. 질문을 그대로 넣어도 된다."},
        },
        "required": ["query"],
    },
}
```

| 칸 | 뜻 |
| --- | --- |
| `name` | 모델이 부를 이름. `tool_use.name` 으로 돌아온다 |
| `description` | **모델이 언제 부를지 판단하는 유일한 근거** |
| `input_schema` | 인자 모양. JSON Schema 그대로 |

`description` 은 사람용 주석이 아니다. 모델은 코드를 못 보고 이 문장만 본다.
「법인카드처럼 규정에 적힌 값을 물어보면 이 도구를 쓴다」를 노트북 초안에 넣은 이유다.

`input_schema` 에 **`user` 가 없다.** 이 한 줄이 권한 설계다(아래).

## 도구 = 네 가지

`backend/app/tools/search_documents.py` 한 파일에 넷이 있다.

| 이름 | 누가 쓰나 |
| --- | --- |
| `NAME` | 서비스가 `TOOL_RUNNERS` 를 만들 때 |
| `SIDE_EFFECT` | 승인 갈래가 생기면 그때 ([[78_에이전트_루프와_멈추는_조건]]) |
| `SCHEMA` | 모델에게 보낸다 |
| `run()` | 우리 코드가 실행한다 |

`run()` 은 새로 만든 검색이 아니다. `LiveRetriever().search()` 를 감싼 껍데기다.
[[76_정책_필터를_되돌리고_다시_재다]]의 파이프라인(재작성 → 하이브리드 → 정책 → 리랭킹 → 판정)이
도구 안에 통째로 들어간다.

## 한 바퀴의 메시지

```text
[user]       부산 출장 숙박비 얼마까지 되나요?
[assistant]  text: 사내 규정을 찾아보겠습니다.
             tool_use: id=toolu_01ABC name=search_documents input={query: 부산 출장 숙박비}
[user]       tool_result: tool_use_id=toolu_01ABC content="{sources: [...], passed: true, ...}"
[assistant]  text: 부산 출장 숙박비는 1박당 70,000원을 상한으로 합니다.   ← end_turn
```

규칙 셋.

1. **assistant 블록을 그대로 되돌려 보낸다.** 모델은 이전 호출을 기억하지 못한다.
   `messages` 가 기억의 전부다. `blocks` 를 `extras` 에 실어 오는 이유다.
2. **tool_result 는 `user` 역할에 담는다.** 도구 결과는 모델 바깥에서 들어온 관찰이다.
3. **`tool_use_id` 는 모델이 준 id 를 그대로.** 한 턴에 도구를 둘 부르면 결과 둘을
   어느 요청에 맞출지 이 id 로 안다. 실제로 둘을 부르는 경우가 나왔다([[80_도구_루프를_돌려_보다]]).

`content` 는 문자열이나 블록 목록이다. 지금은 `json.dumps(out, ensure_ascii=False)` 다.

```text
json.dumps(...)                      길이 182
json.dumps(..., ensure_ascii=False)  길이 117
```

`ensure_ascii=True`(기본)면 한글이 `\uXXXX` 여섯 글자로 바뀐다. 모델이 읽는 데는
지장이 없지만 같은 내용이 1.6배 길어지고 그만큼 입력 토큰이 늘어난다.

## 어댑터는 한 번만 부른다

```python
def answer_with_tools(self, *, messages, tools, user) -> LLMResult:
    system = _load_prompt("agent_system.md")
    ...
    calls = [ToolCall(id=b.id, name=b.name, args=dict(b.input))
             for b in resp.content if getattr(b, "type", "") == "tool_use"]
    return LLMResult(..., extras={"tool_calls": calls, "stop_reason": ..., "blocks": ...})
```

루프는 서비스에 있고 어댑터에는 없다. [[23_포트와_어댑터]]의 경계가 그대로다 —
어댑터는 SDK 응답을 우리 규격(`ToolCall`, `LLMResult`)으로 바꾸는 데까지만 한다.
그래서 노트북의 `_CannedLLM` 처럼 `answer_with_tools` 하나만 흉내 내면 키 없이 루프 전체를
돌릴 수 있다.

시스템 프롬프트도 새로 만들었다(`agent_system.md`). `answer_system.md` 는 「JSON 으로 답하라」
였고 도구 루프는 문장으로 답한다. 출처는 시스템이 붙인다고 적었다 — 모델이 출처를 지어낼
자리를 없앤 것이다.

## 권한: user 는 모델이 넣지 않는다

```python
out = runner(**c.args, user=user)
```

`c.args` 는 모델이 정한 값, `user` 는 서비스가 정한 값이다. 보안등급(`clearance`)이 `user`
안에 있다. 스키마에 `user` 칸이 없으니 모델은 보안등급을 고를 수 없다.

모델이 스키마를 어기고 `user` 를 넣으면 어떻게 되는지 직접 넣어 봤다.

```text
{'query': 'x', 'user': {'clearance': '대외비'}}
    -> TypeError: run() got multiple values for keyword argument 'user'
{}  -> TypeError: run() missing 1 required keyword-only argument: 'query'
{'query': 'x', 'top_k': 5}
    -> TypeError: run() got an unexpected keyword argument 'top_k'
```

권한은 안전하다 — 등급을 올리려는 인자가 실행 전에 막힌다. 대신 **막히는 방식이 예외다.**
`ask_with_tools` 는 이 예외를 잡지 않으니 루프가 그대로 터지고 Run 은 「진행중」으로 남는다.

수업 노트에 나온 `is_error` 가 이 자리의 답이다.

```python
{"type": "tool_result", "tool_use_id": c.id, "content": "인자 오류: query 가 필요합니다", "is_error": True}
```

도구가 실패했다는 사실을 루프를 끊지 않고 모델에게 알린다. 모델은 인자를 고쳐 다시 부를 수
있다. [[28_가드와_재시도_폴백]]의 재시도 힌트와 같은 생각이다 — 그때는 스키마 위반을
`_hint_from` 으로 모델에게 돌려줬다. 지금 코드에는 `is_error` 를 쓰는 곳이 없다.

참고: backend/app/tools/search_documents.py, backend/app/integrations/ports.py,
backend/app/integrations/llm_claude.py, sandbox/w8/day01/00.에이전트툴.ipynb
