# Alembic — 스키마 변경 이력 관리

## 왜 필요한가

[[17_비밀번호_해싱_bcrypt]]에서 `User`에 `password_hash` 컬럼을 추가했을 때, DB 파일을 지우고 다시 만들었다. `init_db()`가 부르는 `Base.metadata.create_all()`은 **표가 없으면 만들고 이미 있으면 아무것도 하지 않기** 때문에, 모델만 고쳐서는 기존 표에 컬럼이 생기지 않는다.

실습용 SQLite 파일은 지우면 그만이지만 실제 서버 DB는 지울 수 없다. 이미 들어 있는 데이터를 유지한 채 표 구조만 바꿔야 하고, 그 변경을 팀원과 서버 여러 대에 같은 순서로 적용해야 한다. Alembic은 그 일을 한다.

- 변경 내용을 **파일**로 남긴다 (코드처럼 커밋할 수 있다)
- 변경의 **순서**를 기억한다 (각 파일이 앞 파일을 가리킨다)
- **어디까지 적용했는지**를 DB에 적어둔다 (`alembic_version` 표)

## 명령

```bash
alembic init <폴더경로>                        # 설정 파일과 폴더 생성
alembic revision --autogenerate -m "메시지"    # 모델과 DB를 비교해 변경 파일 생성
alembic upgrade head                          # 최신까지 적용
alembic stamp head                            # 적용하지 않고 "여기까지 적용된 것으로" 표시만
alembic downgrade -1                          # 한 단계 되돌리기
```

`--autogenerate`는 **모델의 metadata와 지금 DB의 실제 구조를 비교해서** 차이를 파일로 적어준다. 사람이 `ALTER TABLE`을 직접 쓰지 않아도 되지만, 비교 결과가 항상 완벽하지는 않아서 생성된 파일을 읽어보고 고치는 단계가 필요하다.

## 프로젝트에 붙이기

### 1. 초기화

```bash
cd backend
alembic init app/db/migrations
```

`backend/alembic.ini`와 `backend/app/db/migrations/`(안에 `env.py`, `script.py.mako`, `versions/`)가 생긴다.

### 2. `backend/alembic.ini`

```ini
script_location = %(here)s/app/db/migrations
prepend_sys_path = %(here)s     # 기본값 "." 에서 수정
sqlalchemy.url =                # = 뒤 값을 지운다
```

- `prepend_sys_path`는 Alembic이 `env.py`를 실행할 때 모듈 검색 경로에 넣을 폴더다. `%(here)s`는 `alembic.ini`가 있는 폴더, 즉 `backend/`를 가리킨다. 이게 있어야 `env.py`에서 `from app.core.config import ...`가 된다.
- `sqlalchemy.url`을 비우는 이유는 접속 정보를 `.env` 한 곳에서만 관리하기 위해서다. 여기에 URL을 적으면 **비밀번호가 ini 파일에 남아 커밋된다.**

### 3. `backend/app/db/migrations/env.py`

```python
from alembic import context          # 원래 있는 줄

from app.core.config import get_settings
import app.models                    # 모델을 전부 불러와 Base에 등록시킨다
from app.models.base import Base

config = context.config              # 원래 있는 줄
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# target_metadata = None             # 주석 처리
target_metadata = Base.metadata
```

- `config.set_main_option(...)`으로 `.env`에서 읽은 URL을 넣는다. ini를 비워둔 자리를 여기서 채우는 셈이다.
- `import app.models`가 꼭 필요하다. `--autogenerate`는 `Base.metadata`에 등록된 표를 기준으로 비교하는데, 모델 모듈을 한 번도 import하지 않으면 등록이 안 돼서 **Alembic이 "표가 하나도 없다"고 판단하고 전부 삭제하는 마이그레이션을 만든다.**
- `target_metadata = Base.metadata`가 비교 기준이다.

### 4. 첫 마이그레이션 만들기

```bash
cd ..    # hanwha-agent 루트로
alembic -c backend/alembic.ini revision --autogenerate -m "initial schema"
alembic -c backend/alembic.ini stamp head
```

`-c`로 설정 파일 위치를 지정하면 루트에서 실행할 수 있다. `.env`가 루트에 있어서 작업 폴더를 루트로 두는 편이 맞다.

### `upgrade head`가 아니라 `stamp head`인 이유

지금 DB에는 이미 `init_db()`(`create_all`)로 만든 표가 들어 있다. 여기에 "표를 만들라"는 첫 마이그레이션을 `upgrade`로 실행하면 이미 있는 표를 또 만들려다 실패한다.

`stamp`는 **마이그레이션을 실행하지 않고 `alembic_version` 표에 "여기까지 적용됨"만 기록한다.** 이미 만들어진 DB와 이력의 시작점을 맞추는 용도다. 이후 컬럼을 추가할 때부터는 `revision --autogenerate` → `upgrade head` 순서로 쓴다.

## 지금 상태

`backend/app/db/migrations/versions/` 폴더가 비어 있어서, 첫 마이그레이션 파일은 아직 만들어지지 않았다. `--autogenerate`는 DB에 실제로 접속해서 비교하기 때문에 **PostgreSQL 컨테이너가 떠 있어야** 동작한다([[20_Docker와_PostgreSQL]]).

참고: backend/alembic.ini, backend/app/db/migrations/env.py
