# Day 03 진행 상황

## 배운 내용

### 클래스 메서드 종류와 property, 던더 메서드 ([ex19.py](ex19.py))
- 클래스 변수 vs 인스턴스 변수
- 메서드 3종류: 인스턴스 메서드 / `@classmethod`(cls) / `@staticmethod`
- `@property` getter/setter — `self.age`라고 쓰면 무한 재귀, 관례상 `_age`에 실제 값 저장
- 던더(매직) 메서드: `__repr__`, `__eq__`

### 상속과 오버라이딩 ([ex20.py](ex20.py))
- `class 자식클래스(부모클래스)`, `super().__init__()`로 부모 생성자 명시적 호출
- 오버라이딩: 자식이 재정의하면 부모 것은 자동으로 실행되지 않음
- 다중 상속(`class D(A, B, C)`), MRO(Method Resolution Order)
- `super(클래스, self)`로 MRO 상의 특정 지점부터 탐색 시작 지정

### 추상 클래스 ([ex21.py](ex21.py))
- `abc.ABC`를 상속하고 `@abstractmethod`를 붙이면, 자식 클래스에서 반드시 구현하도록 강제

### 파일 입출력 ([ex22.py](ex22.py), [ex23.py](ex23.py), [ex24.py](ex24.py))
- `open(경로, 모드)` — `r`/`w`/`a`/`x`/`b`/`t`, `with-open`으로 자동 `close()`
- 쓰기(`write`, `writelines`), 이어쓰기(`'a'` 모드), 읽기(`read`, `readlines`, `for line in f`)
- `os.path.exists()`로 파일 존재 여부 확인 후 열기 → `FileNotFoundError` 방지
- `pathlib.Path`로 OS 독립적인 경로 처리 (`Path(__file__).resolve().parent`)

### 예외 처리
- `try-except` 문법
- 자주 쓰는 예외 클래스: `ValueError`, `TypeError`, `KeyError`, `IndexError`, `AttributeError`, `FileNotFoundError`, `ZeroDivisionError`, `UnicodeDecodeError`

## 참고
- 질문/답변 기록: [QA.md](QA.md)
- 개념별 정리(블로그 포스팅용): [concepts/](../concepts/)
