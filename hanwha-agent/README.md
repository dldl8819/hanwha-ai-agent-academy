# hanwha-agent — 사내 업무 에이전트

[한화 내일 아카데미 ICT부문 — 지능형(AI) 에이전트 기반 서비스 개발](https://knda-hanwhasystems.com/) 과정(2026.09.01 ~ 11.13)에서 만드는 실습 프로젝트와, 그 과정에서 정리한 학습 기록입니다.

사내 규정 문서를 올려두고 질문하면 근거와 함께 답하는 업무 에이전트를 목표로, 백엔드(FastAPI)와 화면(Streamlit)을 계층 구조로 나눠 만들고 있습니다.

## 폴더 구조

```text
hanwha-agent/
├── backend/            FastAPI 백엔드
│   ├── app/
│   │   ├── api/v1/       라우터 (요청을 받는 자리)
│   │   ├── services/     업무 규칙, 트랜잭션 경계
│   │   ├── repositories/ DB 접근
│   │   ├── models/       SQLAlchemy 테이블 정의
│   │   ├── schemas/      요청·응답 형태 (Pydantic)
│   │   ├── integrations/ 외부 연동 (LLM 어댑터, 관측)
│   │   ├── agent/        프롬프트 파일
│   │   ├── core/         설정, 예외, 로깅, 보안, 가드
│   │   └── db/           세션, 초기화, 시드, 마이그레이션
│   └── tests/          pytest (계층 규칙 검사 포함)
├── frontend/           Streamlit 화면 + UI 킷
├── concepts/           개념 노트 (과목별 폴더, 번호는 학습 순서)
│   ├── 1_AI서비스_백엔드_실무/
│   ├── 2_AI-Native_아키텍처_테스트/
│   ├── 3_LLM_오케스트레이션_파이프라인/
│   └── 4~8/              남은 과목 (아래 "과정 구성" 참고)
├── blog/최종/           발행한 블로그 글 (날짜별)
└── sandbox/            날짜별 실습 코드
```

## 과정 구성

전체 8개 과목으로 진행합니다. 개념 노트는 수업이 진행된 과목부터 차례로 채워집니다.

| # | 과목 | 폴더 | 개념 노트 |
| --- | --- | --- | --- |
| 1 | AI 서비스 백엔드 프로그래밍 실무 | `1_AI서비스_백엔드_실무/` | 01~20 |
| 2 | AI-Native 아키텍처 및 테스트 공학 | `2_AI-Native_아키텍처_테스트/` | 21~32 |
| 3 | LLM 오케스트레이션 및 파이프라인 구축 | `3_LLM_오케스트레이션_파이프라인/` | 33~38 |
| 4 | 실무형 RAG 시스템 구축 및 최적화 | `4_실무형_RAG_시스템_최적화/` | 예정 |
| 5 | AI 에이전트 기획 및 툴 연동 실무 | `5_에이전트_기획_툴_연동/` | 예정 |
| 6 | 멀티 에이전트 제어 및 파이프라인 자동화 | `6_멀티_에이전트_파이프라인_자동화/` | 예정 |
| 7 | 엔터프라이즈 AI 에이전트 배포 및 상용화 프로젝트 | `7_엔터프라이즈_배포_상용화/` | 예정 |
| 8 | 해커톤 프로젝트 | `8_해커톤_프로젝트/` | 예정 |

## 개념 노트

과목별로 폴더를 나눴고, 번호는 과목을 넘어 학습 순서대로 이어집니다.

### 1. AI 서비스 백엔드 프로그래밍 실무 — `concepts/1_AI서비스_백엔드_실무/`

| # | 주제 | # | 주제 |
| --- | --- | --- | --- |
| 01 | [개발환경설정](concepts/1_AI서비스_백엔드_실무/01_개발환경설정.md) | 11 | [SQLAlchemy](concepts/1_AI서비스_백엔드_실무/11_SQLAlchemy.md) |
| 02 | [Git과 GitHub](concepts/1_AI서비스_백엔드_실무/02_Git과_GitHub.md) | 12 | [리포지토리 패턴](concepts/1_AI서비스_백엔드_실무/12_리포지토리_패턴.md) |
| 03 | [Pydantic](concepts/1_AI서비스_백엔드_실무/03_Pydantic.md) | 13 | [서비스 계층](concepts/1_AI서비스_백엔드_실무/13_서비스_계층.md) |
| 04 | [레이어드 아키텍처](concepts/1_AI서비스_백엔드_실무/04_레이어드_아키텍처.md) | 14 | [문서 업로드 API](concepts/1_AI서비스_백엔드_실무/14_문서_업로드_API.md) |
| 05 | [예외 계층 설계](concepts/1_AI서비스_백엔드_실무/05_예외_계층_설계.md) | 15 | [비동기 asyncio](concepts/1_AI서비스_백엔드_실무/15_비동기_asyncio.md) |
| 06 | [로깅](concepts/1_AI서비스_백엔드_실무/06_로깅.md) | 16 | [Streamlit](concepts/1_AI서비스_백엔드_실무/16_Streamlit.md) |
| 07 | [pytest](concepts/1_AI서비스_백엔드_실무/07_pytest.md) | 17 | [비밀번호 해싱 bcrypt](concepts/1_AI서비스_백엔드_실무/17_비밀번호_해싱_bcrypt.md) |
| 08 | [네트워크와 인터넷 기초](concepts/1_AI서비스_백엔드_실무/08_네트워크와_인터넷_기초.md) | 18 | [로그인과 인증](concepts/1_AI서비스_백엔드_실무/18_로그인과_인증.md) |
| 09 | [HTTP와 URI](concepts/1_AI서비스_백엔드_실무/09_HTTP와_URI.md) | 19 | [문서 목록 화면과 API 연동](concepts/1_AI서비스_백엔드_실무/19_문서_목록_화면과_API_연동.md) |
| 10 | [FastAPI](concepts/1_AI서비스_백엔드_실무/10_FastAPI.md) | 20 | [Docker와 PostgreSQL](concepts/1_AI서비스_백엔드_실무/20_Docker와_PostgreSQL.md) |

### 2. AI-Native 아키텍처 및 테스트 공학 — `concepts/2_AI-Native_아키텍처_테스트/`

| # | 주제 | # | 주제 |
| --- | --- | --- | --- |
| 21 | [Alembic 마이그레이션](concepts/2_AI-Native_아키텍처_테스트/21_Alembic_마이그레이션.md) | 27 | [구조화 출력](concepts/2_AI-Native_아키텍처_테스트/27_구조화_출력.md) |
| 22 | [AI Native 애플리케이션](concepts/2_AI-Native_아키텍처_테스트/22_AI_Native_애플리케이션.md) | 28 | [가드와 재시도·폴백](concepts/2_AI-Native_아키텍처_테스트/28_가드와_재시도_폴백.md) |
| 23 | [포트와 어댑터](concepts/2_AI-Native_아키텍처_테스트/23_포트와_어댑터.md) | 29 | [골든셋 회귀 테스트](concepts/2_AI-Native_아키텍처_테스트/29_골든셋_회귀테스트.md) |
| 24 | [API 토큰과 과금](concepts/2_AI-Native_아키텍처_테스트/24_API_토큰과_과금.md) | 30 | [LLM 프레임워크 개요](concepts/2_AI-Native_아키텍처_테스트/30_LLM_프레임워크_개요.md) |
| 25 | [Claude API 호출](concepts/2_AI-Native_아키텍처_테스트/25_Claude_API_호출.md) | 31 | [관측과 실행 기록](concepts/2_AI-Native_아키텍처_테스트/31_관측과_실행_기록.md) |
| 26 | [프롬프트 설계와 컨텍스트](concepts/2_AI-Native_아키텍처_테스트/26_프롬프트_설계와_컨텍스트.md) | 32 | [사용량과 원가 기록](concepts/2_AI-Native_아키텍처_테스트/32_사용량과_원가_기록.md) |

### 3. LLM 오케스트레이션 및 파이프라인 구축 — `concepts/3_LLM_오케스트레이션_파이프라인/`

| # | 주제 | # | 주제 |
| --- | --- | --- | --- |
| 33 | [RAG 개요](concepts/3_LLM_오케스트레이션_파이프라인/33_RAG_개요.md) | 34 | [LangChain 기초](concepts/3_LLM_오케스트레이션_파이프라인/34_LangChain_기초.md) |
| 35 | [체인 합성](concepts/3_LLM_오케스트레이션_파이프라인/35_체인_합성.md) | 36 | [체인을 앱에 붙이기](concepts/3_LLM_오케스트레이션_파이프라인/36_체인을_앱에_붙이기.md) |
| 37 | [비동기와 스트리밍](concepts/3_LLM_오케스트레이션_파이프라인/37_비동기와_스트리밍.md) | 38 | [동시 실행과 재시도·폴백](concepts/3_LLM_오케스트레이션_파이프라인/38_동시_실행과_재시도_폴백.md) |

## 학습 기록

| 일차 | 날짜 | 주제 | 실습 코드 | 후기 |
| --- | --- | --- | --- | --- |
| day04 | 2026-09-07 | 개발환경 설정, Git/GitHub, 타입 힌트와 Pydantic, 환경변수 | [w2/day01](sandbox/w2/day01) | [네이버](https://blog.naver.com/dldl8819/224403884665) |
| day05 | 2026-09-08 | 레이어드 아키텍처, 예외 처리와 로깅, pytest, 네트워크·HTTP | [w2/day02](sandbox/w2/day02) | [네이버](https://blog.naver.com/dldl8819/224405026520) |
| day06 | 2026-09-09 | FastAPI, APIRouter, 의존성 주입, 예외 처리 | [w2/day03](sandbox/w2/day03) | [네이버](https://blog.naver.com/dldl8819/224406227307) |
| day07 | 2026-09-10 | SQLAlchemy, SQLite, ORM 모델, CRUD, JOIN | [w2/day04](sandbox/w2/day04) | [네이버](https://blog.naver.com/dldl8819/224407392783) |
| day08 | 2026-09-11 | 스키마, 파일 업로드, 검색 키워드 확장 | [w2/day05](sandbox/w2/day05) | [네이버](https://blog.naver.com/dldl8819/224410931250) |
| day09 | 2026-09-14 | async/await, Streamlit, UI 킷, 비밀번호 해싱 | [w3/day01](sandbox/w3/day01) | [네이버](https://blog.naver.com/dldl8819/224412170740) |
| day10 | 2026-09-15 | 로그인, 화면-API 연동, Docker, PostgreSQL | [w3/day02](sandbox/w3/day02) | [네이버](https://blog.naver.com/dldl8819/224412738524) |
| day11 | 2026-09-16 | PostgreSQL 전환, Alembic, 포트와 어댑터, 토큰 과금 | [w3/day03](sandbox/w3/day03) | [네이버](https://blog.naver.com/dldl8819/224413930997) |
| day12 | 2026-09-17 | Claude API 호출, 어댑터 구현, 프롬프트 설계, 구조화 출력 | [w3/day04](sandbox/w3/day04) | [네이버](https://blog.naver.com/dldl8819/224415144340) |
| day13 | 2026-09-18 | 가드 함수, 스키마 검증과 재시도, 폴백, 골든셋 테스트 | [w3/day05](sandbox/w3/day05) | [네이버](https://blog.naver.com/dldl8819/224420059153) |
| day14 | 2026-09-21 | LangChain·LangGraph 개요, LangFuse 관측, 실행 기록 테이블 | [w4/day01](sandbox/w4/day01) | [네이버](https://blog.naver.com/dldl8819/224420075761) |
| day15 | 2026-09-22 | 사용량·원가 기록, RAG 개요, LangChain 기초, 체인 합성 | [w4/day02](sandbox/w4/day02) | [네이버](https://blog.naver.com/dldl8819/224420079457) |
| day16 | 2026-09-23 | LangChain 앱 적용, 비동기와 스트리밍, 재시도·폴백 | [w4/day03](sandbox/w4/day03) | [네이버](https://blog.naver.com/dldl8819/224421103051) |

## 실행

```bash
# 1) PostgreSQL 컨테이너 (compose 파일은 비밀번호가 들어 있어 저장소에 포함하지 않았습니다)
docker compose up -d

# 1-1) DB 스키마 반영
alembic -c backend/alembic.ini upgrade head

# 1-2) 관측 도구가 필요한 날만 (http://localhost:3000)
docker compose exec postgres psql -U agent -d agent -c "CREATE DATABASE langfuse OWNER agent;"
docker compose --profile langfuse up -d

# 2) 백엔드 — http://localhost:8000/docs
uvicorn app.main:app --app-dir backend --reload --port 8000

# 3) 화면 — http://localhost:8501
streamlit run frontend/app.py

# 테스트
pytest -q
```

환경변수는 `.env`로 관리하며 저장소에는 올리지 않습니다. 필요한 키는 `backend/app/core/config.py`의 `Settings`에 정의되어 있습니다.

## 링크

- 학습 기록 블로그: [blog.naver.com/dldl8819](https://blog.naver.com/dldl8819)
- 포트폴리오: [dldl8819.github.io](https://dldl8819.github.io/)
