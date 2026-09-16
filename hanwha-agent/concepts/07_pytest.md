# pytest

## pytest란

파이썬 테스트용 프레임워크다. 내가 만든 함수/코드가 예상대로 동작하는지 사람이 매번 눈으로 확인하지 않고, 자동으로 검사해주는 도구다.

```bash
python -m pip install pytest
```

## TDD (Test-Driven Development)

**테스트 코드가 실패하는 코드는 만들지 않겠다**는 개발 방식이다. 기능을 먼저 만들고 나중에 테스트를 붙이는 대신, 무엇이 맞는 동작인지를 테스트로 먼저 적어두고 그 테스트를 통과시키는 방향으로 구현한다. 그러면 "이 코드가 무엇을 보장하는지"가 테스트 파일에 남는다.

## 이름 규칙이 곧 등록이다

pytest에는 "이 테스트를 실행하라"고 별도로 등록하는 곳이 없다. 대신 이름 규칙을 따르기만 하면 pytest가 알아서 찾아서 실행해준다.

- 파일명: `test_`로 시작하거나 `_test`로 끝난다 (`test_config.py`)
- 함수명: `test_`로 시작한다 (`def test_xxxx():`)
- 클래스명: `Test`로 시작한다

규칙을 벗어난 이름은 **에러 없이 그냥 실행되지 않는다.**

```python
def clean_title(raw):
    return raw.strip()

def test_앞뒤_공백을_지운다():
    assert clean_title("     앞뒤 공백이 있는 문자열    ") == "앞뒤 공백이 있는 문자열"

# test_ 가 안 붙어 있어서 실행되지 않는다
def 빈_제목이면_빈_문자열():
    assert clean_title("   ") == ""
```

함수 이름은 한글로 써도 된다. 실행 결과에 이름이 그대로 찍혀서 무엇을 검사하는 테스트인지 읽기 쉬워진다.

```python
def add(a, b):
    return a + b

# 30이 나오는지 테스트
def test_add():
    assert add(10, 20) == 30
```

## assert로 검사하기

기대하는 값과 실제 값이 같은지는 `assert`로 확인한다. `assert 조건`이 참이면 통과, 거짓이면 그 테스트는 실패로 표시된다.

```python
from calculator import add, substract

def test_add():
    result = add(10, 20)
    assert result == 30

def test_substract():
    result = substract(10, 3)
    assert result == 5  # substract(10, 3)은 7이라 일부러 실패하는 케이스로 남겨둔 것
```

실행은 `pytest 파일경로 -v`로 한다. `-v`를 붙이면 각 테스트 함수 이름과 통과(`PASSED`)/실패(`FAILED`) 여부가 한 줄씩 보인다.

```bash
pytest sandbox/w2/day02/test_calculator.py -v
```

## 실습 중 만난 이슈: `__init__.py`가 있으면 import 경로가 바뀐다

`sandbox/` 아래 `day02/` 폴더에 빈 `__init__.py`를 하나 넣어뒀더니, 바로 옆에 있는 `calculator.py`를 `from calculator import add, substract`로 못 찾고 `ModuleNotFoundError: No module named 'calculator'`가 났다.

이유는 pytest의 기본 import 방식 때문이다. 테스트 파일이 있는 폴더에 `__init__.py`가 있으면 pytest는 그 폴더를 "패키지"로 보고, `__init__.py`가 없는 첫 상위 폴더(`w2`)를 `sys.path`에 넣는다. 그러면 `day02` 폴더 자체는 `sys.path`에 안 잡혀서, 같은 폴더의 `calculator.py`를 바로 `import`할 수 없다(`day02.calculator`로는 가능하지만 그렇게 쓰고 있지 않았다).

```text
day02/__init__.py 있음  → sys.path에 w2가 들어감 → from calculator import ... 실패
day02/__init__.py 없음  → sys.path에 day02가 들어감 → from calculator import ... 성공
```

`sandbox/day0N/`처럼 스크립트와 테스트를 나란히 두고 pytest로 그 파일만 바로 돌리는 구조에서는 `__init__.py`를 넣지 않는 게 맞다. 반대로 `backend/app/...`처럼 실제로 다른 모듈에서 import해서 쓰는 패키지에는 `__init__.py`가 필요하다.

## 테스트 파일은 한곳에 모은다

날짜 폴더마다 흩어 두면 나중에 전체를 한 번에 돌리기 어려워서, 테스트 실습용 파일은 `sandbox/pytest/`로 모았다.

```bash
pytest sandbox/pytest -v
```

## 실습 중 만난 이슈: 테스트에서 `app` 모듈을 못 찾는다

프로젝트 설정을 검사하는 테스트를 만들었더니 수집 단계에서 바로 멈췄다.

```python
# sandbox/pytest/test_import_fail.py
from app.core.config import get_settings

def test_설정_불러오기():
    assert get_settings().app_mode == "mock"
```

```text
ERROR collecting sandbox/pytest/test_import_fail.py
E   ModuleNotFoundError: No module named 'app'
!!!!!!! Interrupted: 1 error during collection !!!!!!!
```

`app` 패키지는 `backend/` 아래에 있는데, `pytest sandbox/pytest`로 실행하면 `sandbox/pytest`만 `sys.path`에 들어가서 `backend`는 검색 경로에 없다. 위 "`__init__.py`가 있으면 import 경로가 바뀐다"와 같은 뿌리의 문제로, **pytest가 어떤 폴더를 `sys.path`에 넣는지**가 핵심이다.

또 하나 눈여겨볼 것은 실패 방식이다. 테스트 하나가 실패한 게 아니라 **수집 단계에서 중단(Interrupted)돼서 나머지 테스트도 실행되지 않았다.** import 오류는 개별 테스트 실패와 다르게 파일 전체를 못 읽게 만든다.

해결은 `backend`를 검색 경로에 알려주는 것이고, 보통 프로젝트 루트의 `pyproject.toml`에 pytest 설정을 넣어 처리한다.

```toml
[tool.pytest.ini_options]
pythonpath = ["backend"]
testpaths = ["sandbox/pytest"]
```

참고: sandbox/pytest/, sandbox/w2/day02/04.pytest기초.ipynb, sandbox/w2/day02/test_calculator.py
