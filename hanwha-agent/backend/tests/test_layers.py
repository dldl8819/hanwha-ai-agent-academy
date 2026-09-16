# 계층 의존 방향 검사 테스트 코드
# api/v1 -> services -> repositories -> models
# -> 규칙을 테스트로 만들어서 체크
#
# 동작하는지가 아니라 "구조가 무너졌는지"를 보는 테스트다.
# 라우터가 급할 때 리포지토리를 직접 부르는 식의 우회는 기능상 잘 돌아가기 때문에,
# 사람이 코드 리뷰로만 막으면 시간이 지나며 새어 나간다.


from __future__ import annotations

import ast
from pathlib import Path

# 이 파일 기준 backend/tests/test_layers.py -> parents[1] = backend -> backend/app
APP = Path(__file__).resolve().parents[1] / "app"

# 우리 앱 패키지 이름. 외부 라이브러리(import fastapi 등)와 구분하는 기준이 된다
OURS = "app"

# 파일 최상단에서 import 하는 모듈 이름을 모으는 함수
# - 코드를 실행하지 않고 ast 로 구문만 읽는다 (import 부작용 없이 안전하게 검사)
# - tree.body 만 보므로 함수 안에서 하는 지연 import 는 걸러지지 않는다
def _top_level_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):           # import app.models
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):     # from app.models import User
            if node.module:
                names.append(node.module)
    return names

# 계층 폴더 하나 안에 있는 .py 파일을 전부 찾는 함수
def _py_files(layer: str) -> list[Path]:

    folder = APP / layer
    if not folder.is_dir():
        return []
    return sorted(folder.rglob("*.py"))

# 모듈이 그 패키지에 속하는지 여부를 판단
# - 뒤에 "." 를 붙여 비교하므로 app.models 규칙이 app.models_backup 같은 이름까지 잡지 않는다
def _is(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")

# 한 계층 안에서 금지된 import를 하는 자리 모으는 함수
# - forbidden : 이 계층이 import 하면 안 되는 패키지
# - allowed   : forbidden 안에서 예외로 허용할 패키지 (먼저 검사해서 빠져나간다)
def _violations(
    layer: str,
    forbidden: tuple[str, ...],
    allowed: tuple[str, ...] = (),
) -> list[str]:
    found: list[str] = []
    for path in _py_files(layer):
        for name in _top_level_imports(path):
            if not _is(name, OURS):
                continue                                  # 외부 패키지는 관심 밖
            if any(_is(name, ok) for ok in allowed):
                continue
            if any(_is(name, bad) for bad in forbidden):
                # 어느 파일이 무엇을 불렀는지 남긴다 (실패 메시지에 그대로 보여주려고)
                found.append(f"{path.relative_to(APP)} → {name}")
    return found

# 모델은 최하위 계층이라, 우리 앱의 다른 계층을 모른다.
# - 우리의 다른 계층을 역으로 부르는지 검사하는 함수
# - forbidden 을 app 전체로 두고 app.models 만 예외로 허용한다 (모델끼리는 서로 참조 가능)
def test_models_import_nothing_but_models() -> None:
    offenders = _violations("models", forbidden=(OURS,), allowed=("app.models",))
    assert not offenders, (
        "models 가 다른 계층을 import 합니다. 모델은 맨 아래층이라 아무도 올려다보지 "
        "않습니다. 필요한 값은 인자로 받고, 규칙은 services 로 올리세요:\n  "
        + "\n  ".join(offenders)
    )


# 라우터는 services 만 부른다
# - 한 단계 건너뛰어 repositories/models 를 직접 부르면 트랜잭션 경계와 규칙이 라우터로 샌다
def test_api_does_not_import_repositories_or_models() -> None:
    offenders = _violations("api/v1", forbidden=("app.repositories", "app.models"))
    assert not offenders, (
        "라우터가 repositories/models 를 직접 import 합니다. 그 호출을 services 의 "
        "함수로 옮기고 라우터는 그 함수만 부르세요:\n  " + "\n  ".join(offenders)
    )

# 서비스에서 API 라우터 import 하지 않게 검사
# - 아래층이 위층을 부르면 순환 import 가 생기고 계층이 의미를 잃는다
def test_services_do_not_import_api() -> None:
    offenders = _violations("services", forbidden=("app.api",))
    assert not offenders, (
        "services 가 api 를 import 합니다. 의존이 거꾸로 섰습니다. 필요한 값은 "
        "라우터가 인자로 내려 주게 바꾸세요:\n  " + "\n  ".join(offenders)
    )

# 리포지토리는 DB만 다룬다.
# - 서비스 또는 API 라우터를 import 하지 않게 검사
def test_repositories_do_not_import_services_or_api() -> None:
    offenders = _violations("repositories", forbidden=("app.services", "app.api"))
    assert not offenders, (
        "repositories 가 services/api 를 import 합니다. 판단은 services 에 두고 "
        "리포지토리는 값만 돌려주세요:\n  " + "\n  ".join(offenders)
    )

# 외부 연동은 factory 한 곳으로만 들어가도록 검사
# - 어댑터를 직접 import 하면 공급자 SDK 가 서비스 코드에 박힌다 (모델/외부 서비스 교체가 어려워진다)
# - factory 만 예외로 허용해서, 서비스는 Protocol 타입으로만 받게 강제한다
def test_services_reach_integrations_only_through_factory() -> None:
    offenders = _violations(
        "services",
        forbidden=("app.integrations",),
        allowed=("app.integrations.factory",),
    )
    assert not offenders, (
        "services 가 어댑터를 직접 import 합니다. integrations/factory.py 를 거쳐 "
        "Protocol 타입으로만 받으세요:\n  " + "\n  ".join(offenders)
    )
