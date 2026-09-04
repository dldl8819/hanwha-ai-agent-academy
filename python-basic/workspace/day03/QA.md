# Day 03 Q&A

## Q1. `@property`의 getter에서 `self.age`라고 작성하면 왜 무한 반복(재귀)이 발생하나요?

**답변**

우체국 창구에 비유하면 이해하기 쉽다.

- `age`라는 이름의 창구 직원(getter 메서드)이 있다. 이 직원의 일은 "손님이 `age`를 물어보면 답해주는 것".
- 그런데 직원이 답을 구하려고 "`self.age`가 뭐였지?" 하고 확인하는 순간, 이건 **본인이 일하는 그 창구에 다시 문의하는 것**과 같다.
- `self.age`는 "Person 객체의 `age`라는 속성을 조회해줘"라는 뜻인데, `@property`가 붙어 있는 이상 `age`라는 이름은 이미 "그 창구 직원(메서드)"으로 예약되어 있다. 그래서 `self.age`를 실행하면 파이썬은 다시 그 창구 직원, 즉 `age` getter 메서드를 호출한다.
- 그 안에서 또 `return self.age`를 실행하니, 창구 직원이 자기 자신에게 되묻고, 그 대답을 듣기 위해 또 자기 자신에게 되묻고... 이게 끝없이 반복된다. (실제로는 `RecursionError: maximum recursion depth exceeded`로 종료됨)

**해결책**: 실제 값은 창구 뒤에 있는 별도의 사서함, 즉 `_age`(언더바 붙은 진짜 저장 공간)에 보관한다.
- `p1.age` 조회 → `age` getter 호출 → 직원은 자기 이름(`age`)이 아니라 **뒷방 사서함(`self._age`)**을 열어서 값을 꺼내 알려줌
- 값 저장(`@age.setter`)도 `self.age = val`이 아니라 **`self._age = val`**로 뒷방 사서함에 직접 저장

즉, `age`는 손님을 응대하는 "창구(인터페이스)"이고 `_age`는 실제 값이 보관되는 "창고". 창구 직원이 자기 이름을 다시 호출하면 무한히 자기 자신을 부르게 되므로, 반드시 창구 이름과 다른 이름의 창고에 실제 값을 넣어야 한다.

```python
class Person:
    def __init__(self, age):
        self.age = age

    @property
    def age(self):
        return self._age   # self.age라고 쓰면 무한 재귀

    @age.setter
    def age(self, val):
        self._age = val
```

## Q2. 특수 메서드를 왜 "던더(dunder)", "매직 메서드(magic method)"라고 부르나요?

**답변**

두 이름 다 별명이고, 유래는 다르다.

- **던더(dunder)**: **D**ouble **UNDER**score의 줄임말. `__init__`처럼 앞뒤로 언더바(`_`)가 2개(double underscore)씩 붙어 있는 "생긴 모양"에서 그대로 따온 이름.
- **매직 메서드(magic method)**: "동작 방식"에서 나온 이름. 보통 메서드는 `객체.메서드()`처럼 직접 호출해야 하는데, 던더 메서드는 `+`, `==`, `print()`, `len()` 같은 일반 연산자·내장 함수를 사용했을 뿐인데 파이썬이 알아서 뒤에서 호출해준다.
  - `item1 + item2` → 내부적으로 `item1.__add__(item2)` 자동 호출
  - `print(item1)` → 내부적으로 `item1.__str__()` 자동 호출
  - `len(my_list)` → 내부적으로 `my_list.__len__()` 자동 호출
- 개발자 입장에서는 "호출한 적도 없는데 알아서 실행되네?"처럼 보여서, 마치 마법처럼 느껴진다고 해서 **magic method**라는 별명이 붙었다.

정리: **던더**는 이름의 생김새(밑줄 2개)에서, **매직**은 특정 문법을 만나면 파이썬이 자동으로 호출해준다는 동작 특성에서 나온 별명이다.

## Q3. class A가 B의 부모, B가 C의 부모, C가 D의 부모이면, D는 A/B/C의 자식이라고 할 수 있나요?

**답변**

네, 맞다. 다만 정확히는 "다중 상속"이 아니라 **다단계 상속(multi-level inheritance)**이라는 별개의 개념이다.

```python
class A:
    def a(self): pass

class B(A):   # B는 A의 자식
    def b(self): pass

class C(B):   # C는 B의 자식 (= A의 손자)
    def c(self): pass

class D(C):   # D는 C의 자식 (= B의 손자, A의 증손자)
    def d(self): pass

d = D()
d.a()  # A에게서 물려받음
d.b()  # B에게서 물려받음
d.c()  # C에게서 물려받음
d.d()  # 자기 것

print(isinstance(d, A))  # True
print(isinstance(d, B))  # True
print(isinstance(d, C))  # True
print(D.__mro__)         # (D, C, B, A, object) — 조회 순서
```

**가족 관계로 비유하면**: D는 C의 친자식, C는 B의 친자식, B는 A의 친자식이니까 D 입장에서 C는 부모, B는 조부모, A는 증조부모가 된다. 족보상 D는 A, B, C 모두의 "후손"이 맞고, 조상들이 가진 재산(속성)과 기술(메서드)을 대를 이어 전부 물려받는다.

**다중 상속(`class D(A, B, C)`)과 헷갈리지 않게 구분하면:**

| 구분 | 관계 | 부모 개수 |
| --- | --- | --- |
| 다중 상속 (Multiple) | D가 A, B, C를 **동시에** 직접 상속 | 한 세대에 부모가 여러 명 |
| 다단계 상속 (Multi-level) | A→B→C→D로 **한 줄로 이어서** 상속 | 각 세대마다 부모는 1명, 대신 세대가 여러 층 |

자세한 내용은 [concepts/09_상속.md](../concepts/09_상속.md) 참고.

## Q4. MRO가 무슨 뜻인가요?

**답변**

**MRO = Method Resolution Order**(메서드 결정 순서). 다중 상속에서 같은 이름의 메서드를 여러 부모가 갖고 있을 때, 파이썬이 "어느 클래스의 메서드를 쓸지" 탐색하는 순서를 말한다.

- 사용하는 알고리즘 이름은 **C3 선형화(C3 linearization)**.
- 기본 원칙: 자기 자신 → 왼쪽 부모부터 → 오른쪽 부모 → ... → `object` 순으로 검색.
- `클래스.mro()` 또는 `클래스.__mro__`로 실제 탐색 순서를 직접 확인할 수 있다.

```python
class A:
    def greet(self): print("A")

class B(A):
    def greet(self): print("B")

class C(A):
    def greet(self): print("C")

class D(B, C):   # 다이아몬드 상속: B, C가 둘 다 A를 상속
    pass

d = D()
d.greet()          # "B" — 왼쪽(B)이 오른쪽(C)보다 우선
print(D.mro())      # [D, B, C, A, object] — A는 중복 없이 한 번만 탐색됨
```

## Q5. `D(B, C)`처럼 D가 B, C만 상속받아도, B와 C가 둘 다 A를 상속하고 있으면 D도 A를 물려받나요?

**답변**

네, 맞다. D 선언에는 A가 직접 안 보이지만, B와 C가 각각 A를 상속하고 있으므로 D도 **전이(transitive) 상속**으로 A를 물려받는다.

```python
class A: pass
class B(A): pass   # B는 A를 상속
class C(A): pass   # C도 A를 상속
class D(B, C): pass  # D는 B, C만 직접 나열했지만...

print(isinstance(D(), A))  # True — D도 결국 A의 자손
print(D.mro())              # [D, B, C, A, object]
```

여기서 진짜 흥미로운 지점은 "A를 물려받느냐"가 아니라, A로 가는 경로가 B를 통해서/C를 통해서 두 갈래인데 **왜 MRO에는 A가 딱 한 번만 나타나느냐**다. C3 선형화가 "공통 조상(A)은 그 조상을 상속한 모든 자식(B, C)보다 반드시 뒤에 위치해야 한다"는 규칙을 지켜서, 중복 없이 한 줄로 순서를 정리해주기 때문이다.

## Q6. 각 클래스에 같은 이름의 메서드(`hello`)가 있을 때, 자식(D)에는 그 메서드가 없으면 어떤 부모의 것이 호출되나요?

**답변**

MRO 순서대로 훑다가 **그 메서드가 정의된 첫 번째 클래스를 만나면 거기서 멈춘다.** 더 뒤에 있는 클래스는 확인하지 않는다.

```python
class A:
    def hello(self): print("hello A")

class B(A):
    def hello(self): print("hello B")

class C(A):
    def hello(self): print("hello C")

class D(B, C):
    pass   # hello 없음

d = D()
d.hello()   # "hello B" 출력 — MRO [D, B, C, A, object]에서 B가 첫 매치, C/A는 호출 안 됨
```

오버라이딩과 같은 원리다 — 여러 부모 것을 합치거나 다 실행하는 게 아니라, "가장 먼저 만나는 것 하나만" 실행하고 멈춘다.

## Q7. D에서 `super(D, self)`, `super(B, self)`, `super(C, self)`를 순서대로 호출하면 어떻게 되나요?

**답변**

```python
class D(B, C):
    def hello(self):
        print("hello D")
        super(D, self).hello()
        super(B, self).hello()
        super(C, self).hello()

d = D()
d.hello()
# hello D
# hello B
# hello C
# hello A
```

`super(클래스, self)`는 "`self`의 실제 타입(D)의 MRO `[D, B, C, A, object]`에서, **지정한 클래스 바로 다음부터** 찾아라"라는 뜻이다. 항상 D의 MRO를 기준으로 찾기 때문에, 기준 클래스를 D → B → C로 바꿔가며 호출하면 그 다음 자리(B → C → A)를 하나씩 순서대로 불러올 수 있다.

| 호출 | MRO `[D, B, C, A, object]`에서 시작 위치 | 결과 |
| --- | --- | --- |
| `super(D, self)` | D 다음부터 | B |
| `super(B, self)` | B 다음부터 | C |
| `super(C, self)` | C 다음부터 | A |

참고로 인자 없이 `super().hello()`만 쓰면 `super(D, self)`와 같아서 B만 호출되고 끝난다(Q6과 동일한 "첫 매치에서 멈춘다" 동작). 지금처럼 기준 클래스를 바꿔가며 명시적으로 여러 번 호출하는 건 MRO 동작 원리를 이해하는 데는 좋지만, 실전에서는 각 클래스가 자기 메서드 안에서 `super().메서드()`를 호출해 체인처럼 자동으로 이어지게 하는 협력적 다중 상속 패턴이 더 흔하다.

자세한 내용은 [concepts/09_상속.md](../concepts/09_상속.md) 참고.
