# pytest

## pytest란

파이썬 테스트용 프레임워크다. 내가 만든 함수/코드가 예상대로 동작하는지 사람이 매번 눈으로 확인하지 않고, 자동으로 검사해주는 도구다.

```bash
python -m pip install pytest
```

## 이름 규칙이 곧 등록이다

pytest에는 "이 테스트를 실행하라"고 별도로 등록하는 곳이 없다. 대신 이름 규칙을 따르기만 하면 pytest가 알아서 찾아서 실행해준다.

- 파일명: `test_*.py`
- 함수명: `test`로 시작

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

참고: sandbox/w2/day02/04.pytest기초.ipynb, sandbox/w2/day02/test_calculator.py, sandbox/w2/day02/calculator.py
