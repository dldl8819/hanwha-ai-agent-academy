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
