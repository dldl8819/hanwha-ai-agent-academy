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
│   │   ├── core/         설정, 예외, 로깅, 보안
│   │   └── db/           세션, 초기화, 시드, 마이그레이션
│   └── tests/          pytest (계층 규칙 검사 포함)
├── frontend/           Streamlit 화면 + UI 킷
├── concepts/           개념 노트 (주제별)
├── blog/최종/           발행한 블로그 글 (날짜별)
└── sandbox/            날짜별 실습 코드
```

## 개념 노트

| # | 주제 | # | 주제 |
| --- | --- | --- | --- |
| 01 | [개발환경설정](concepts/01_개발환경설정.md) | 13 | [서비스 계층](concepts/13_서비스_계층.md) |
| 02 | [Git과 GitHub](concepts/02_Git과_GitHub.md) | 14 | [문서 업로드 API](concepts/14_문서_업로드_API.md) |
| 03 | [Pydantic](concepts/03_Pydantic.md) | 15 | [비동기 asyncio](concepts/15_비동기_asyncio.md) |
| 04 | [레이어드 아키텍처](concepts/04_레이어드_아키텍처.md) | 16 | [Streamlit](concepts/16_Streamlit.md) |
| 05 | [예외 계층 설계](concepts/05_예외_계층_설계.md) | 17 | [비밀번호 해싱 bcrypt](concepts/17_비밀번호_해싱_bcrypt.md) |
| 06 | [로깅](concepts/06_로깅.md) | 18 | [로그인과 인증](concepts/18_로그인과_인증.md) |
| 07 | [pytest](concepts/07_pytest.md) | 19 | [문서 목록 화면과 API 연동](concepts/19_문서_목록_화면과_API_연동.md) |
| 08 | [네트워크와 인터넷 기초](concepts/08_네트워크와_인터넷_기초.md) | 20 | [Docker와 PostgreSQL](concepts/20_Docker와_PostgreSQL.md) |
| 09 | [HTTP와 URI](concepts/09_HTTP와_URI.md) | 21 | [Alembic 마이그레이션](concepts/21_Alembic_마이그레이션.md) |
| 10 | [FastAPI](concepts/10_FastAPI.md) | 22 | [AI Native 애플리케이션](concepts/22_AI_Native_애플리케이션.md) |
| 11 | [SQLAlchemy](concepts/11_SQLAlchemy.md) | 23 | [포트와 어댑터](concepts/23_포트와_어댑터.md) |
| 12 | [리포지토리 패턴](concepts/12_리포지토리_패턴.md) | 24 | [API 토큰과 과금](concepts/24_API_토큰과_과금.md) |

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
| day11 | 2026-09-16 | Alembic, AI-Native 아키텍처, 포트와 어댑터, 토큰과 과금 | [w3/day03](sandbox/w3/day03) | 작성 중 |

## 실행

```bash
# 1) PostgreSQL 컨테이너 (compose 파일은 비밀번호가 들어 있어 저장소에 포함하지 않았습니다)
docker compose up -d

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
