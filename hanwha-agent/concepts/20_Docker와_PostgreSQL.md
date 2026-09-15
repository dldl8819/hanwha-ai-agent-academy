# Docker와 PostgreSQL

지금까지는 [[11_SQLAlchemy]]에서 만든 SQLite 파일(`app.db`) 하나로 DB를 써 왔다. SQLite는 설치 없이 파일 하나로 끝나서 실습에는 편하지만, 서버 여러 대가 같은 DB를 보거나 벡터 검색 같은 확장 기능을 붙이기는 어렵다. 그래서 실제 DB 서버인 PostgreSQL로 옮길 준비를 하는데, PostgreSQL을 PC에 직접 설치하지 않고 **Docker 컨테이너로 띄운다.**

## Docker 개념

| 용어 | 비유 | 뜻 |
| --- | --- | --- |
| 이미지(Image) | 붕어빵 틀 | 컨테이너를 만들기 위한 틀. Docker Hub에서 받거나 직접 만든다 |
| 컨테이너(Container) | 붕어빵 | 이미지로 만든 실체. 프로그램과 그 프로그램이 돌아가는 데 필요한 것을 묶어 격리해서 돌린다 |

같은 이미지로 컨테이너를 여러 개 만들 수 있다. PC에 PostgreSQL을 설치하면 버전 충돌이나 삭제 후 찌꺼기 문제가 생기지만, 컨테이너는 지우고 다시 만들면 깨끗한 상태로 돌아간다.

### `pgvector/pgvector:pg16`

PostgreSQL 16에 `pgvector` 확장이 미리 들어 있는 이미지다. `pgvector`는 임베딩 벡터를 저장하고 유사도로 검색하는 확장이라, 이후 문서 검색(RAG)에서 쓰게 된다.

이미지 이름의 `:` 뒤는 태그(버전)다. `docker compose up`을 하면 compose 파일에 적힌 `pgvector/pgvector:pg16`을 알아서 받아오므로 `docker pull`을 따로 할 필요는 없다. `pgvector/pgvector:0.8.6-pg18-trixie`처럼 다른 태그를 받으면 PostgreSQL 18 이미지라서, 접속 확인 노트북의 "16 이어야 한다" 검사와 맞지 않는다.

## Docker Desktop 설치 (Windows)

1. Docker Desktop을 내려받아 설치한다. 설치 옵션에서 **Use WSL 2 instead of Hyper-V**를 체크한다.
2. WSL이 없다는 창이 뜨면 cmd에서 설치한다.

   ```bash
   wsl --install
   ```

3. 설치 확인

   ```bash
   docker --version
   # Docker version 29.8.0, build 88096ef

   docker compose version
   # Docker Compose version v5.5.1
   ```

## `docker-compose.yml` — 컨테이너 설정을 파일로

컨테이너를 만들 때마다 긴 `docker run` 명령을 치는 대신, 설정을 파일로 적어두고 `docker compose` 명령으로 한 번에 만들고 관리한다.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: agent-postgres
    environment:
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: agent
      POSTGRES_DB: agent
      TZ: Asia/Seoul
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent -d agent"]
      interval: 5s
      timeout: 3s
      retries: 20

volumes:
  pgdata:
```

| 항목 | 뜻 |
| --- | --- |
| `image` | 어떤 이미지로 만들지 |
| `container_name` | 컨테이너 이름. 안 주면 `폴더명-서비스명-1` 식으로 자동으로 붙는다 |
| `environment` | 처음 만들 때 생성할 계정·비밀번호·DB 이름, 시간대 |
| `ports` | `"PC 포트:컨테이너 포트"`. PC의 5432로 들어온 요청을 컨테이너의 5432로 넘긴다 |
| `volumes` | 컨테이너 안 데이터 폴더를 `pgdata`라는 이름의 볼륨에 연결한다. 컨테이너를 지워도 데이터가 남는다 |
| `healthcheck` | 5초마다 컨테이너 **안에서** `pg_isready`로 DB가 응답하는지 확인한다. 통과하면 상태에 `(healthy)`가 붙는다 |

`environment`의 계정 정보는 볼륨이 **처음 만들어질 때만** 적용된다. 이미 `pgdata` 볼륨이 있는 상태에서 비밀번호를 바꾸고 다시 띄워도 기존 DB의 비밀번호는 그대로다.

이 파일에는 DB 비밀번호가 들어 있어서 `.gitignore`에 추가했다. 팀원과 같은 DB 구성을 공유해야 하는 시점이 오면, 파일은 커밋하고 비밀번호만 `${POSTGRES_PASSWORD}`로 바꿔 이미 무시되고 있는 `.env`로 옮기는 방식이 일반적이다.

## docker compose 명령

`hanwha-agent` 폴더(compose 파일이 있는 곳)에서 실행한다.

```bash
docker compose up -d      # 이미지 받기 + 컨테이너 생성 + 실행 (-d: 백그라운드)
docker compose ps         # 상태 확인
```

```text
NAME             IMAGE                    STATUS                        PORTS
agent-postgres   pgvector/pgvector:pg16   Up About a minute (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
```

| 명령 | 컨테이너 | 볼륨(데이터) |
| --- | --- | --- |
| `docker compose stop` | 멈춤(남아 있음) | 유지 |
| `docker compose start` | 멈춘 컨테이너 다시 실행 | 유지 |
| `docker compose down` | 삭제 | **유지** |
| `docker compose down -v` | 삭제 | **삭제** |
| `docker compose up -d --force-recreate` | 지우고 새로 생성 | 유지 |

`down`은 컨테이너만 지우고 데이터는 남긴다. `-v`를 붙여야 볼륨까지 지워져 DB가 완전히 비워진다.

## 드라이버 설치

```bash
python -m pip install "psycopg[binary]==3.3.4" "alembic==1.19.2"
```

- **psycopg**: 파이썬에서 PostgreSQL에 접속하는 드라이버. SQLAlchemy가 이걸 통해 실제 DB와 통신한다. `[binary]`는 C 라이브러리를 따로 설치하지 않아도 되는 미리 빌드된 버전이다.
- **alembic**: 마이그레이션 도구. [[17_비밀번호_해싱_bcrypt]]에서 컬럼 하나 추가하려고 DB 파일을 지우고 다시 만들었는데, 실제 서버 DB에서는 그렇게 할 수 없어서 스키마 변경을 이력으로 관리하는 도구를 쓴다. 이번에는 설치만 했다.

## DB URL

```text
sqlite:///./app.db

postgresql+psycopg://agent:agent@localhost:5432/agent
└─방언──┘ └드라이버┘ └계정┘ └비번┘ └─호스트─┘ └포트┘ └DB이름┘
```

SQLAlchemy는 URL만 바꾸면 같은 코드로 다른 DB에 붙는다. 방언(`postgresql`)으로 SQL 문법 차이를 맞추고, 드라이버(`psycopg`)로 실제 통신을 한다. 지금 `.env`의 `DATABASE_URL`은 아직 SQLite 그대로다.

## 접속 확인 — `sandbox/w3/day02/00.postgresql.ipynb`

```python
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

PG_URL = "postgresql+psycopg://agent:agent@localhost:5432/agent"

try:
    pg_engine = create_engine(PG_URL, connect_args={"connect_timeout": 5})
    with pg_engine.connect() as conn:
        server_version = conn.execute(text("SELECT version()")).scalar()
        print("서버가 알려 준 판 :", server_version)

        major_version = server_version.split()[1].split(".")[0]
        print(f"PostgreSQL 메이저 판 : {major_version}   (16 이어야 한다)")

        db_name, db_user = conn.execute(text("SELECT current_database(), current_user")).one()
        print(f"데이터베이스 : {db_name} · 접속 계정 : {db_user}")

        table_count = conn.execute(text(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
        )).scalar()
        print("public 스키마의 표 개수 :", table_count)
except OperationalError as exc:
    print("접속하지 못했습니다 :", str(exc.orig).strip().splitlines()[0])
    print("터미널에서 docker compose ps 로 STATUS 가 (healthy) 인지 먼저 확인하세요.")
```

- `connect_args={"connect_timeout": 5}`는 SQLAlchemy가 아니라 **드라이버(psycopg)에 그대로 넘기는 옵션**이다. 서버가 안 받으면 5초 뒤 포기한다.
- `create_engine`은 접속하지 않는다. 실제 접속은 `connect()`에서 일어나서 예외도 거기서 난다.
- `exc.orig`는 SQLAlchemy가 감싸기 전의 드라이버 원본 예외다. 첫 줄만 잘라서 보여준다.
- `information_schema.tables`에서 `public` 스키마 표 개수를 세면, 방금 만든 컨테이너인지(0) 예전에 표를 만든 적 있는 볼륨인지 알 수 있다.

```text
서버가 알려 준 판 : PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on x86_64-pc-linux-gnu, ...
PostgreSQL 메이저 판 : 16   (16 이어야 한다)
데이터베이스 : agent · 접속 계정 : agent
public 스키마의 표 개수 : 0
```

## 실습 중 만난 문제 — `(healthy)`인데 접속이 안 된다

노트북이 `접속하지 못했습니다 : connection timeout expired`를 출력했는데, `docker compose ps`를 보면 `Up 20 minutes (healthy)`였다.

```text
NAME             STATUS                    PORTS
agent-postgres   Up 20 minutes (healthy)   5432/tcp                      ← 문제 상태
agent-postgres   Up 7 seconds (healthy)    0.0.0.0:5432->5432/tcp, ...   ← 정상 상태
```

차이는 **PORTS 칸**이었다. `5432/tcp`만 있으면 컨테이너 안에서만 5432가 열려 있고 PC와는 연결되지 않은 상태다. `->`가 있어야 PC의 `localhost:5432`가 컨테이너로 이어진다.

확인해보니 compose 설정(`HostConfig.PortBindings`)에는 `5432:5432`가 제대로 들어 있었는데, 실제로 열린 포트(`NetworkSettings.Ports`)는 비어 있었다. PC 쪽 5432에서 기다리는 프로그램이 없어서 노트북은 5초 동안 응답을 기다리다 타임아웃이 난 것이다.

```bash
docker inspect agent-postgres --format '{{json .NetworkSettings.Ports}}'
# {"5432/tcp":[]}                                        ← 포트가 안 붙음
# {"5432/tcp":[{"HostIp":"0.0.0.0","HostPort":"5432"}]}  ← 정상
```

`(healthy)`가 떠도 안 됐던 이유는 **healthcheck가 컨테이너 안에서 실행되기 때문**이다. `pg_isready`는 DB가 떠 있는지만 보고, PC에서 들어올 수 있는지는 보지 않는다. 그래서 상태 확인은 STATUS의 `(healthy)`와 PORTS의 `->`를 둘 다 봐야 한다.

컨테이너를 다시 만들어 해결했다. 데이터는 볼륨에 있어서 유지된다.

```bash
docker compose up -d --force-recreate postgres
```

포트 충돌(다른 프로그램이 5432 사용)이나 윈도우 예약 포트 범위 문제는 아니었고, 컨테이너가 다시 켜질 때 포트 연결만 빠진 경우였다.

참고: hanwha-agent/docker-compose.yml(커밋 제외), sandbox/w3/day02/00.postgresql.ipynb
