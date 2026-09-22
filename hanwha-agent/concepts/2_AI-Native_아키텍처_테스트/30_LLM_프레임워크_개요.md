# LLM 프레임워크 개요 — LangChain · LangGraph · LangSmith · LangFuse

이름이 비슷해서 헷갈리지만 역할이 둘로 갈린다.

| | 무엇을 하는가 |
| --- | --- |
| **LangChain · LangGraph** | AI 애플리케이션을 **만드는** 프레임워크 |
| **LangSmith · LangFuse** | 만든 것을 **관찰·평가·개선**하는 도구 |

```text
                     AI Agent 개발
                         │
              ┌──────────┴──────────┐
         LangChain              LangGraph
      LLM/RAG/Tool 을         복잡한 Agent 의
        쉽게 조립              흐름과 상태 제어
              └──────────┬──────────┘
                         ▼
                     AI Agent
                         │ 실행하면서
              ┌──────────┴──────────┐
         LangSmith               LangFuse
       추적/평가/관리           추적/평가/관리
      LangChain 계열 플랫폼    오픈소스·중립적
```

## LangChain — 조립을 쉽게

LLM API 하나만 부르면 LangChain 은 필요하지 않다. 우리 프로젝트가 지금 그렇다([[25_Claude_API_호출]]).

```python
client.messages.create(...)     # 이게 전부라면 프레임워크를 얹을 이유가 없다
```

필요해지는 것은 중간 단계가 늘어날 때다.

```text
사용자 질문 → 질문 분석 → 문서 검색 → Embedding → pgvector 검색
          → 관련 Chunk → Prompt 작성 → Claude 호출 → Tool 호출 → 최종 답변
```

이 구성 요소들을 갈아 끼우기 쉽게 이어 주는 것이 LangChain 이다.

| 구성 요소 | 하는 일 |
| --- | --- |
| Model | Claude·OpenAI 를 같은 인터페이스로 (`model.invoke("안녕 AI")`) |
| Prompt | 프롬프트를 템플릿으로 관리 (`ChatPromptTemplate.from_template(...)`) |
| Document Loader | PDF·HTML·텍스트 등 문서 가져오기 |
| Text Splitter | 큰 문서를 Chunk 로 나누기 |
| Tool | Agent 가 쓸 수 있는 기능 |

Model 과 Prompt 는 우리가 이미 손으로 만든 것과 같은 자리다. `LLMPort` 가 Model 에 해당하고([[23_포트와_어댑터]]), `answer_system.md` 가 Prompt 에 해당한다([[26_프롬프트_설계와_컨텍스트]]). **직접 만들어 본 다음에 프레임워크를 보면 무엇을 대신해 주는지가 보인다.**

## LangGraph — 흐름이 갈라질 때

한 줄로 흐르는 정도면 LangChain 으로 충분하다. 갈라지고 되돌아오면 달라진다.

```text
              사용자 질문 → 질문 분석
      ┌────────────┼────────────┐
   문서질문      직원질문      메일요청
     RAG           DB        Email Tool
      └────────────┼────────────┘
                결과 검증
            ┌───────┴───────┐
           성공            실패
           답변            재검색 → 다시 검증
```

분기와 **되돌아오는 화살표**가 생기면 함수 호출을 이어 붙이는 방식으로는 관리가 안 된다. LangGraph 는 이걸 노드와 엣지를 가진 그래프로, 그리고 노드 사이를 오가는 **상태(state)** 로 다룬다.

우리 코드의 재시도 루프([[28_가드와_재시도_폴백]])가 바로 "검증 실패 → 다시 호출"이라 이 그림의 작은 조각이다. `hint` 변수가 노드 사이를 오가는 상태에 해당한다.

## LangSmith vs LangFuse

둘 다 같은 문제를 푼다. **실행 기록(trace)을 모아서 보고, 디버깅하고, 평가한다.**

| | LangSmith | LangFuse |
| --- | --- | --- |
| 성격 | LangChain 계열 플랫폼 | 오픈소스, 프레임워크 중립 |
| 운영 | 클라우드 | 클라우드 또는 **직접 운영(셀프 호스팅)** |

수업에서 LangFuse 를 쓰는 이유는 두 가지다. LangChain 을 쓰지 않는 우리 코드에도 붙고, 내 PC 에 띄워서 데이터를 밖으로 내보내지 않고 실습할 수 있다.

### LangFuse 의 세 기능

| 기능 | 뜻 |
| --- | --- |
| Observability | 실행을 trace 로 기록 |
| Prompt Management | 프롬프트를 코드와 분리해 버전별로 관리 |
| Evaluation | 답이 쓸 만했는지 점수로 평가 |

Prompt Management 는 우리가 `answer_system.md` 를 파일로 뺀 것과 같은 판단이고, Evaluation 은 골든셋([[29_골든셋_회귀테스트]])의 통과 여부를 기록에 붙이는 자리다.

## 왜 관측 도구가 필요한가

일반 웹 API 는 같은 입력에 같은 출력이 나와서, 문제가 생기면 다시 돌려 보면 된다. LLM 은 그게 안 된다. **다시 부르면 다른 답이 온다.** 그래서 그때 무엇을 보내고 무엇을 받았는지가 남아 있지 않으면 원인을 찾을 길이 없다([[22_AI_Native_애플리케이션]]).

기록을 계층으로 본다.

```text
trace  ── 질문 1건 (RUN-8881)
  ├── observation  프롬프트 읽기            (span)
  ├── observation  Claude 1차 호출          (generation)
  ├── observation  검증 실패 → 재시도
  └── observation  Claude 2차 호출          (generation)
score  ── 이 트레이스에 붙이는 점수 (골든셋 통과 여부 등)
```

| 용어 | 뜻 |
| --- | --- |
| **trace** | 사용자 요청 한 건 전체 |
| **observation** | 그 안의 단계 하나. 모델 호출은 `generation`, 나머지는 `span` |
| **score** | 트레이스에 나중에 붙이는 평가값 |

`generation` 이 따로 있는 이유는 모델 호출에만 붙는 값(모델명·입출력 토큰)이 있어서다. 이 값이 있어야 화면에서 비용을 집계할 수 있다([[24_API_토큰과_과금]]).

다음 노트에서 이 계층을 우리 DB 와 코드에 옮긴다 → [[31_관측과_실행_기록]]

참고: 실습은 [[31_관측과_실행_기록]], sandbox/w4/day01/00.랭퓨즈.ipynb
