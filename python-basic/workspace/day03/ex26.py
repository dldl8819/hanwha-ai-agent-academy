class Person:
    def __init__(self):
        self.age = 0

    def set_age(self, v):
        # 예외 발생 강제
        if not isinstance(v, int):
            raise TypeError("입력하신 데이터 타입을 확인해주십시오.")
        if v < 0:
            raise ValueError("나이는 음수가 될 수 없습니다.")
        self.age = v

p = Person()
print(p.age)
p.set_age(10)
print(p.age)
# 예외 처리 전: 아래처럼 바로 호출하면 TypeError/ValueError가 발생해 프로그램이 즉시 종료됨
# p.set_age("소울")
# print(p.age)
# p.set_age(-10)
# print(p.age)

try:
    p.set_age(-10) # 예외 발생 가능한 위치
except TypeError as e:
    print(f"예외 발생!! 정수가 아닌 숫자는 나이가 될 수 없습니다. {e}")
    # 원래 예외를 그대로 다시 발생시키기
    raise
except ValueError as e:
    print(f"예외 발생!! 나이는 음수가 될 수 없습니다. {e}")
else:
    print(p.age)

print(p.age)
