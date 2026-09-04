# 클래스 선언
class Heifam:
    tier = 'S' # 클래스 변수
    greeting = "hello"

    def __init__(self, name):
        self.name = name    # 인스턴스 변수

    # 메서드 선언
    def say_name(self):
        self.age = 200
        msg = f"내 이름은 {self.name}!"
        print(msg)


print(Heifam.tier)  # 클래스 변수는 객체 생성 없이 바로 사용 가능
soul = Heifam("소울")
soul.say_name()
print(soul.age)

class Student:
    # 클래스 변수
    school: str = "HeiFam"

    def __init__(self, name: str, score: int):
        self.name: str = name
        self.score: int = score

    # 인스턴스 메서드
    def is_passed(self) -> bool:
        return self.score >= 60

    def show_info(self) -> None:
        result = "합격" if self.is_passed() else "불합격"
        print(f"{self.name}님은 {self.score}점으로 {result}입니다.")

    # 클래스 메서드
    # @classmethod
    # self 대신 cls (클래스)
    @classmethod
    def show_school(cls):
        print(f"우리는 모두 {cls.school} 멤버 입니다.")

    # 정적 메서드
    @staticmethod
    def study_sum(a, b):
        return a + b 

# 객체 생성
s1: Student = Student("셋쇼", 100)
s2: Student = Student("고니", 50)
s3: Student = Student("민식", 60)

# 메서드 호출
s1.show_info()
s2.show_info()
s3.show_info()

s3.show_school()

print(Student.study_sum(10, 20))

class MathTool:
    @staticmethod
    def add(a, b):
        return a + b
    @staticmethod
    def sub(a, b):
        return a - b

print(MathTool.add(1, 2))

class Person:
    def __init__(self, age):
        self.age = age

    @property
    def age(self):          # getter : 외부에서 age 값을 원할 때 반환해주는 메서드
        return self._age    # self.age 라고 작성하면 무한 반복 -> 관례적으로 _(언더바) 1개를 앞에 붙여서 사용

    @age.setter
    def age(self, val):     # setter : 외부에서 전달한 값으로 age 변수에 값 세팅
        if not isinstance(val, int):
            print("저장할 값이 정수가 아닙니다.")
        if val < 0:
            print("나이는 음수가 불가능합니다.")
        self._age = val
p1 = Person(-5)


class Item:
    def __init__(self, num):
        self.num = num

    def __repr__(self):
        return "Item(name='몬스터볼')"

    def __eq__(self, value):
        return self.num == value.num

# print(repr(Item()))

item1 = Item(10)
item2 = Item(10)

print(item1 == item2)