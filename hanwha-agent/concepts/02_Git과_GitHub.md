# Git & GitHub

## Git과 GitHub의 차이

| 구분 | Git | GitHub |
| --- | --- | --- |
| 정체 | 버전 관리 시스템(프로그램) | Git 저장소를 호스팅하는 온라인 서비스 |
| 위치 | 내 컴퓨터(로컬)에 설치해서 사용 | 클라우드(원격 서버) |
| 역할 | 파일 변경 이력을 기록·관리 | 로컬 저장소를 백업·공유, 협업(PR/이슈 등) 지원 |
| 없어도 되는가 | 없으면 버전 관리 자체가 불가능 | 없어도 로컬에서 git은 그대로 동작함 (원격 백업/공유만 안 됨) |

즉 Git은 버전 관리를 해주는 도구이고, GitHub는 그 Git 저장소를 인터넷에 올려서 남들과 공유하거나 백업해두는 서비스다. `git init`으로 만든 로컬 저장소를 `git remote add`로 GitHub 저장소와 연결해야 둘이 이어진다.

## Git 설치 & 사용자 설정

설치는 기본값으로 계속 next만 눌러서 완료한다. 설치가 끝나면 버전을 확인하고, 커밋에 남길 사용자 이름/이메일을 전역으로 설정해둔다.

```bash
# git 정상 설치 확인
git --version
# >> git version 2.55.0.windows.5

# 사용자 이름 설정
git config --global user.name "{user.name}"
# 사용자 이메일 설정
git config --global user.email "{user.email}"

# 설정 확인
git config --global --list
# >> user.name={user.name}
# >> user.email={user.email}
```

`--global` 옵션을 붙이면 PC 전체에 적용되는 설정이라, 프로젝트마다 다시 설정할 필요가 없다.

## Git 기본 흐름 (로컬)

```bash
# 로컬 저장소 생성 (프로젝트당 1개)
git init

# 현재 상태 확인: git이 추적 중인 파일/변경사항 목록
git status

# staging(커밋 대기 상태)에 올리기
git add 파일명   # 특정 파일만
git add .        # 현재 변경사항 전체

# staging에 올라간 내용을 로컬 저장소에 기록
git commit -m "커밋 메시지"

# 커밋 이력 확인
git log
```

작업 흐름은 `작업(수정) → add(스테이징) → commit(로컬 저장)` 3단계로 이어진다. `add` 전까지는 아직 git이 추적만 할 뿐 기록하지 않은 상태이고, `commit`을 해야 그 시점의 변경사항이 로컬 저장소 이력에 남는다.

## GitHub 연결 & 업로드

로컬 저장소를 원격(GitHub) 저장소와 연결하고 처음으로 업로드하는 절차다.

```bash
# git과 github 연결 (origin이라는 이름으로 원격 저장소 등록)
git remote add origin <http로 시작하는 github 리포지토리 경로>
git remote -v   # 연결 확인

# 기본 브랜치 이름을 main으로 지정
git branch -M main

# github로 업로드 (-u는 이후 git push만 쳐도 되게 origin/main과 연결)
git push -u origin main
```

`origin`은 원격 저장소를 가리키는 이름(관례적으로 origin을 사용), `-u`(`--set-upstream`)로 한 번 연결해두면 다음 push부터는 `git push`만 입력해도 된다.

## .gitignore

git이 추적(버전 관리)하지 않을 파일/폴더를 지정하는 설정 파일이다. 프로젝트 루트에 `.gitignore`라는 이름으로 만들고, `git add .`을 하기 전에 먼저 작성해두는 게 안전하다 — 한 번 커밋된 파일은 `.gitignore`에 나중에 추가해도 자동으로 추적이 끊기지 않기 때문이다.

```bash
# github에 올리지 않을 목록 작성
sandbox/
.venv/

__pycache__/
*.py[cod]
.pytest_cache/

.env

.vscode/
.idea/
.DS_Store
Thumbs.db
```

- 폴더 전체를 제외할 때는 끝에 `/`를 붙인다 (`sandbox/`, `.venv/`)
- 확장자 단위로 제외할 때는 `*.확장자` 패턴을 쓴다 (`*.py[cod]`는 `.pyc`/`.pyo`/`.pyd`를 한 번에 지정)
- `.env`처럼 민감한 값(API 키 등)이 들어가는 파일은 반드시 제외 대상에 넣는다.

### hanwha-agent 프로젝트 git 설정

hanwha-agent 프로젝트는 아래 순서로 자체 git 저장소를 준비했다.

1. GitHub에서 `hanwha-agent`라는 이름의 빈 리포지토리 생성 (README.md 등 초기 파일은 만들지 않음 — 로컬에서 만든 내용과 충돌하지 않게 하기 위함)
2. VSCode 터미널에서 로컬 저장소 생성

   ```bash
   git init
   ```

3. `.gitignore` 파일을 만들어 위 목록을 작성 (`sandbox/`, `.venv/` 등 제외)

`sandbox/`를 통째로 제외하는 이유는, 그 폴더가 연습용 코드 공간이라 실제 프로젝트(backend/frontend) 버전 관리 대상이 아니기 때문이다.

> 참고: 위 실습은 별도의 private 저장소(hanwha-agent)를 만들어서 그대로 따라 진행했다. 지금 이 파일이 들어있는 `hanwha-ai-agent-academy` 저장소는 그것과는 별개로, 한화 내일 아카데미에서 배우는 내용 전체를 한 눈에 볼 수 있도록 정리해두는 기록용 저장소라서 `sandbox/` 제외 규칙을 적용하지 않았다.

참고: git-test/
