# 질의 재작성과 Multi-Query

[[65_측정값_뜯어보기]]에서 틀린 6문항을 다섯 고장으로 갈라 놓았다. 오늘은 그 고장마다
붙는 처방이 따로 있다는 쪽으로 시작했다.

| 오답 원인 | 처방 |
| --- | --- |
| 낱말이 달라서 못 찾는다 | 질의 재작성 — 한 질문을 여러 질의로 |
| 고유명사·숫자를 못 잡는다 | 하이브리드 — 키워드 검색을 더한다 |
| 답이 후보에 있는데 순위가 낮다 | 리랭킹 — 다른 기준으로 다시 줄 세운다 |
| 없는 것을 있다고 한다 | 크로스 인코더 + 합격선 |

[[65_측정값_뜯어보기]]의 G26(해외를 물었는데 국내 금액)이 네 번째 줄이고, G16(표가
5위로 밀림)이 세 번째 줄이다. 처방을 네 갈래로 나눈 것이 좋았다 — 「검색을 개선한다」
하나로 두면 무엇을 고칠지가 안 정해진다.

## 질문을 고칠 수 없으면 질문을 늘린다

사용자가 쓰는 낱말과 규정이 쓰는 낱말이 다르다. 먼저 글자로 세어 봤다.

```text
LIKE '%출장비%'   →  0건
LIKE '%여비%'     → 32건
LIKE '%숙박%'     → 26건
LIKE '%1박당%'    →  2건
LIKE '%1박 당%'   →  0건
```

**「출장비」가 0건이다.** 사용자는 출장비라고 묻는데 규정은 여비라고 쓴다. 질문을
고칠 수는 없으니 질문을 늘린다.

아래 두 줄도 같은 모양이다. 「1박당」은 2건이고 띄어 쓴 「1박 당」은 0건이다.
글자 하나 차이로 갈리는 자리가 이렇게 많다.

## 설정 두 줄을 더한다

```python
multi_query_n: int = Field(default=3, ge=1, le=10)   # 질문을 몇 갈래까지 늘리는가
rerank_top_n: int = Field(default=3, ge=1, le=20)    # 다시 줄 세운 뒤 몇 건을 남길 것인가
```

`rerank_top_n` 이 [[64_골든셋과_채점기]]의 `DEFAULT_TOP_N = 3` 과 같은 값이다.
채점기가 상위 3건만 보는 것과 검색기가 3건만 돌려주는 것이 맞물린다.

## 결과 모양을 먼저 정한다

```python
@dataclass
class RetrievalResult:
    sources: list[dict] = field(default_factory=list)  # 근거 후보 목록
    steps: list[dict] = field(default_factory=list)    # 화면에 검색 과정을 보여줄 때 사용
    best_score: float = 0.0                            # 후보 중 가장 높은 유사도
    passed: bool = False                               # 최고 점수가 임계값을 넘었는가
    version_note: str | None = None
    threshold: float = 0.55
```

`steps` 가 눈에 띈다. [[56_배경_작업과_작업_번호]]의 업로드 단계 목록과 같은 모양이다.
검색도 여러 단계를 거치므로 어느 단계에서 몇 건이 나왔는지를 화면에 보일 수 있게
들고 다닌다.

`passed` 를 결과에 넣은 것도 짚어 둘 만하다. 임계값 판정을 부르는 쪽마다 다시 하지
않고 검색기가 한 번 해서 들고 온다.

## 세 갈래로 늘리는 규칙

`backend/app/rag/retriever.py` 를 새로 만들었다.

```python
SYNONYMS = {
    "출장비": "여비 일비 숙박비 식비",
    "여비": "출장비 일비 숙박비",
    "숙박": "숙박비 호텔 1박",
    "교통": "교통비 KTX 항공",
    "기준": "규정 상한 지급 기준표",
    "신청서": "신청 양식 서식",
    "법인카드": "카드 결제 사용",
    "재택": "재택근무 원격",
}

def expand_queries(question: str, n: int = 3) -> list[str]:
    q = (question or "").strip()
    out = [q]                                   # 1. 원문
    extra = " ".join(v for k, v in SYNONYMS.items() if k in q)
    if extra:
        out.append(f"{q} {extra}")              # 2. 동의어를 덧붙인 질문
    core = " ".join(t for t in q.split() if len(t) > 1)[:120]
    if core and core != q:
        out.append(core)                        # 3. 한 글자 토씨를 걷어낸 핵심어
    return out[:n]
```

세 갈래가 각각 다른 것을 노린다 — 원문 그대로, 규정 용어를 더한 것, 군더더기를 뺀 것이다.

### 실제로는 1.73갈래다

골든셋 30문항에 돌려 봤다.

```text
갈래 수 분포 : {1: 14, 2: 10, 3: 6}   총 30문항 · 평균 1.73개
```

**절반 가까운 14문항이 한 갈래로 끝난다.** 동의어 사전에 걸리는 낱말이 없고 한 글자
토큰도 없으면 원문 하나만 남는다.

`multi_query_n = 3` 으로 설정해 뒀지만 실제 평균은 1.73이다. 설정값이 상한일 뿐이라
그 숫자만 보고 「세 배로 검색한다」고 읽으면 틀린다. 동의어 사전이 여덟 줄이라
그만큼만 걸린다.

늘어나려면 사전이 커져야 한다. 그런데 사전을 손으로 키우는 것은 끝이 없다 —
이것이 LLM 재작성을 보게 되는 이유다.

## 사전 대신 모델에게 맡기면

`sandbox/w7/day02/rewrite_try.py` 로 규칙 기반과 LLM 재작성을 나란히 놓고 비교했다.
API 키 없이도 돌아가도록 미리 뽑아 둔 결과를 쓰는 `StubRewriter` 가 붙어 있다.

```text
모드: mock

[1] "출장비 얼마까지 나오나요?"
 규칙 기반 2갈래 : 출장비 얼마까지 나오나요? / 출장비 얼마까지 나오나요? 여비 일비 숙박비 식비
 재작성 2갈래 : 국내출장 여비 지급 상한 / 일비 숙박비 식비 기준액

[3] "재택은 주 며칠까지 되나요?"
 규칙 기반 3갈래 : 재택은 주 며칠까지 되나요? / 재택은 주 며칠까지 되나요? 재택근무 원격 / 재택은 며칠까지 되나요?
 재작성 2갈래 : 재택근무 주당 허용 일수 / 재택근무 운영 지침 신청 기준

규칙 기반 평균 2.3갈래. 재작성 평균 2.0갈래
```

갈래 수는 비슷한데 모양이 다르다. 규칙 기반은 **원문에 낱말을 덧붙이고**, 재작성은
**원문을 버리고 규정 말투의 명사구로 바꾼다.**

프롬프트가 그렇게 지시한다.

```text
사용자의 질문에 답하지 않습니다. 근거 문서는 필요없습니다.
규정 내용을 말하는 것이 아니라 검색창에 넣을 문장을 만드는 일입니다.
- 각 질의는 20자 안팎의 명사구로 작성한다.
- 금액,일수 같은 숫자는 지어내지 않는다.
```

「답하지 않는다」를 두 번 적어 둔 것이 중요하다고 본다. 질문을 주면 모델은 답하려
든다. 검색 질의를 만드는 일과 답하는 일은 다른 일인데 프롬프트로 갈라 줘야 한다.

마지막 줄도 그렇다. 금액을 지어내면 그 숫자로 검색하게 되고, 없는 금액이 걸릴 리
없으니 검색이 조용히 망가진다.

### 돌려 보니 터졌다

`rewrite_try.py` 가 처음에 `NameError` 로 죽었다.

```python
made = [... llm.answer(question=PROMPT + q, ...) ...]
```

`REWRITE_SYSTEM` 으로 정의해 두고 쓰는 쪽에서 `PROMPT` 를 불렀다. 이름이 어긋났다.
`REWRITE_SYSTEM + "\n" + q` 로 고쳤다 — `StubRewriter` 가 마지막 줄을 질문으로 읽도록
`question.rsplit("\n", 1)[-1]` 로 받기 때문에 줄바꿈으로 이어야 맞는다.

## 검색 파이프라인 일곱 단계

| 단계 | 하는 일 |
| --- | --- |
| 1 | 질의 재작성 `expand_queries` |
| 2 | 갈래마다 임베딩 `embed_query` — 갈래 수만큼 호출 |
| 3 | 갈래마다 벡터 검색 → `chunk_id` 로 중복 제거 |
| 4 | 키워드 검색 + RRF `keyword_search` / `fuse` ([[73_키워드_검색과_RRF]]) |
| 5 | 정책 필터 `policy.filter_candidates` |
| 6 | 리랭킹 `rerank` |
| 7 | 임계값 `best >= retrieval_threshold` |

오늘 구현한 것은 1·2·3·4·7 이다. **5번 정책 필터와 6번 리랭킹은 코드에 들어가지
않았다.** 5번이 빠진 것이 [[74_기법을_더했는데_떨어졌다]]에서 점수를 끌어내린다.

### 중복 제거를 세 갈래에 걸쳐 한다

```python
seen: dict[int, dict] = {}
for one in queries:
    vec = embedder.embed_query(one)
    question_vec = question_vec or vec
    for row in store.vector_search(session, vec, limit=settings.retrieval_top_k):
        seen.setdefault(row["chunk_id"], row)
```

`setdefault` 라서 **먼저 들어온 쪽의 점수가 남는다.** 같은 청크가 세 갈래에서 다 걸리면
첫 갈래(원문)의 점수를 쓴다.

`question_vec = question_vec or vec` 한 줄이 중요하다. 늘린 질의가 아니라 **원래 질문의
벡터**를 따로 보관한다. 임계값은 원래 질문과의 거리로 그은 선이므로([[63_검색_정책]]),
동의어를 덧붙인 질의로 재면 낱말이 늘어난 만큼 점수가 올라가 선이 흔들린다.

참고: backend/app/rag/retriever.py, backend/app/core/config.py,
backend/app/integrations/ports.py, sandbox/w7/day02/rewrite_try.py,
sandbox/w7/day02/00.하이브리드_리랭킹_재측정.ipynb
