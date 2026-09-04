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
