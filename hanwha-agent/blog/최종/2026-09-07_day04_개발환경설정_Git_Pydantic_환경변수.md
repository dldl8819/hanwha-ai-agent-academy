# [한화 내일 아카데미 ICT부문] 4일차 후기 — 개발환경 설정, Git/GitHub, 타입 힌트와 Pydantic, 환경변수

주말 동안은 1~3일차에서 배운 파이썬 문법을 복습 문제 72개로 정리했었는데, 오늘부터는 파이썬 기초 실습에서 실제 AI 에이전트 프로젝트(hanwha-agent) 실습으로 넘어갔습니다. 한화 내일 아카데미 ICT부문 과정의 2주차 첫날로, 프로젝트 개발환경을 새로 세팅하고 Git/GitHub 기본기, 그리고 FastAPI 백엔드에서 바로 쓸 타입 힌트·Pydantic·환경변수까지 하루 만에 진도가 많이 나갔습니다.

오늘 학습한 내용을 순서대로 정리해봅니다.

1. 개발환경 설정 (가상환경, 프로젝트 폴더 구조, Jupyter Notebook)
2. Git과 GitHub 기본기
3. 타입 힌트와 Pydantic
4. 환경 변수와 Pydantic Settings

## 1. 개발환경 설정

작업 폴더에 `hanwha-agent` 폴더를 만들고 VSCode로 연 뒤, 프로젝트 전용 가상환경부터 만들었습니다.

```bash
# 파이썬 버전 확인
python --version

# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (자동으로 안 되면 직접 실행)
.venv\Scripts\activate.bat

# 패키지 매니저 업그레이드
python -m pip install --upgrade pip
```

프로젝트 폴더는 아래처럼 역할별로 나누어 구성했습니다.

```
hanwha-agent/
    backend/            서버 로직
        app/
            main.py         서버 시작점
            core/           설정·예외·로깅
            models/         DB 관련
            schemas/        요청/응답 구조
            repositories/   DB 관련
            services/       비즈니스 로직
            api/
            rag/
    frontend/           화면
    sandbox/            주차/일차별 연습 코드
        w2/day01/
```

`backend/app` 안을 `core`(설정), `models`/`repositories`(DB), `schemas`(요청·응답 구조), `services`(비즈니스 로직), `api`(라우팅)로 미리 나눠두는 구조라, 실습 코드가 늘어나도 어디에 뭘 넣을지 헷갈리지 않게 되어 있습니다.

이후 실습은 VSCode에 Jupyter 확장을 설치하고 `.ipynb` 파일을 만들어서, 커널을 방금 만든 `.venv`로 지정하는 방식으로 진행했습니다.

## 2. Git과 GitHub 기본기

Git은 로컬에서 파일 변경 이력을 기록·관리하는 프로그램이고, GitHub는 그 Git 저장소를 온라인에 올려 백업하고 공유하는 서비스라는 점을 먼저 정리했습니다. Git이 없으면 버전 관리 자체가 안 되지만, GitHub가 없어도 로컬 Git은 그대로 동작합니다.

```bash
# 설치 확인 + 사용자 설정
git --version
git config --global user.name "이름"
git config --global user.email "이메일"

# 로컬 저장소 기본 흐름: 수정 → add → commit
git init
git status
git add .
git commit -m "커밋 메시지"
git log

# GitHub 연결 + 업로드
git remote add origin <저장소 경로>
git branch -M main
git push -u origin main
```

`.gitignore`는 git이 추적하지 않을 파일·폴더를 지정하는 설정 파일로, `git add`를 하기 전에 먼저 만들어두는 것이 안전합니다. 실습에서는 아래처럼 가상환경, 캐시, `.env` 등을 제외 목록에 넣었습니다.

```
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env
.vscode/
.idea/
```

## 3. 타입 힌트와 Pydantic

Pydantic은 파이썬 데이터의 구조와 타입을 정의하고, 실제로 들어온 데이터가 그 규칙에 맞는지 검사해주는 라이브러리입니다. `BaseModel`을 상속받아 필드에 타입 힌트를 작성하면, 값이 안 맞을 때 어느 필드가 왜 틀렸는지까지 알려줍니다.

```python
from pydantic import BaseModel, Field
from datetime import date

class Document(BaseModel):
    doc_id: str = Field(..., pattern=r"DOC-[A-Z]{2,4}-\d{3}$")
    title: str = Field(..., min_length=1, max_length=200)
    version: str = Field(..., pattern=r"^\d+\.\d+$")
    expiry_date: date | None = None
    tags: list[str] = Field(default_factory=list)

doc = Document(doc_id="DOC-HR-002", title="출장비 규정", version="1.2", tags=["a", "b"])
```

`Field`의 `pattern`에 넘기는 정규식이 문법적으로 틀리면(괄호·중괄호가 안 맞거나 이스케이프가 빠지면) 클래스를 정의하는 시점에 `SchemaError`가 발생합니다. 실습 중 `\d{3$}`처럼 닫는 중괄호 위치를 잘못 적어서 "unclosed counted repetition" 에러를 직접 만나봤고, `\d{3}$`로 고치고 나서야 정상적으로 모델이 만들어졌습니다.

값 목록을 고정해야 할 때는 `Enum`을 사용합니다. `str`과 함께 상속받으면 문자열처럼 다룰 수 있어 JSON 변환이 편합니다.

```python
from enum import Enum

class SecurityLevel(str, Enum):
    PUBLIC = "공개"
    INTERNAL = "사내공개"
    CONFIDENTIAL = "대외비"
    SECRET = "기밀"
```

모델은 `model_dump()`(딕셔너리로), `model_dump_json()`(JSON 문자열로), `model_validate()`/`model_validate_json()`(딕셔너리·JSON을 모델로)로 서로 변환할 수 있습니다.

실전에서는 요청 모델과 응답 모델을 분리해서 씁니다. 요청·응답을 모델 하나로 같이 쓰면, 응답 전용 값(서버 내부 id 등)이 요청에 섞여 들어가기 쉽기 때문입니다.

```python
# 요청용
class DocumentCreate(BaseModel):
    doc_id: str
    title: str

# 응답용
class DocumentOut(BaseModel):
    doc_id: str
    title: str
    version: str
```

`field_validator`를 쓰면 값을 검증 전에 가공할 수도 있습니다. 예를 들어 `doc_id`가 소문자로 들어와도 대문자로 바꿔서 저장하는 처리입니다.

```python
from pydantic import field_validator

class DocumentCreate(BaseModel):
    doc_id: str

    @field_validator("doc_id", mode="before")
    @classmethod
    def upper_doc_id(cls, v):
        return v.upper() if isinstance(v, str) else v
```

## 4. 환경 변수와 Pydantic Settings

API 키처럼 코드에 그대로 넣으면 유출될 수 있는 값은 `.env` 파일에 따로 작성하고, 코드에서는 이름으로 불러다 씁니다. `python-dotenv`로 `os.environ`에 값을 채워 넣는 방식이 기본이지만, 값이 전부 문자열로만 온다는 한계가 있습니다.

`pydantic-settings`를 쓰면 환경 변수를 타입이 있는 설정 객체로 바로 읽어올 수 있습니다.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_mode: str = "dev"
    anthropic_api_key: str  # 기본값이 없으면 필수 값
    max_tokens: int = Field(default=400, ge=1, le=8192)

settings = Settings()
```

타입이 `int`인 필드는 `.env`의 `"400"`을 자동으로 `400`으로 변환해줘서, 직접 형변환할 필요가 없습니다.

설정을 다룰 때 지켜야 할 원칙도 함께 정리했습니다. 설정을 읽는 곳은 `app/core/config.py` 한 군데로 모으고 다른 파일에서는 그 함수를 가져다 쓰는 방식으로 통일합니다. 파일마다 `os.environ.get()`을 직접 호출하면 기본값이 파일마다 달라질 수 있기 때문입니다. 기본값은 `debug: bool = False`처럼 안전한 쪽으로 잡고, 필수 값에는 기본값을 주지 않아서 값이 없으면 앱이 바로 뜨지 않게 합니다. `.env`(실제 값)와 `.env.example`(이름·설명만 있는 샘플)은 함께 관리합니다.

## 오늘의 소감

파이썬 문법 자체를 배우던 1주차와 달리, 오늘부터는 실제 서버 프로젝트에서 쓰는 도구들을 하나씩 다뤘습니다. Pydantic 실습 중에 정규식 문법 오류로 `SchemaError`를 만난 게 오늘 가장 기억에 남는 부분인데, 에러 메시지가 어느 필드의 어떤 정규식이 문제인지까지 구체적으로 짚어줘서 원인을 바로 찾을 수 있었습니다. 환경변수를 `os.environ`으로 직접 읽는 방식과 `pydantic-settings`로 타입까지 검증하며 읽는 방식의 차이도 코드로 직접 비교하니 확실히 정리됐습니다.

다음 포스팅에서는 이어서 배울 내용을 정리해보겠습니다.

---

\#한화내일아카데미 #한화시스템 #AI개발자 #AI에이전트 #프로젝트세팅 #Pydantic #환경변수 #K뉴딜아카데미 #국비지원교육 #개발자이직 #부트캠프후기

참고 링크 : https://blog.naver.com/dldl8819/224403884665
