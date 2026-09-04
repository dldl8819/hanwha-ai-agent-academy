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
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def is_passed(self):
        return self.score >= 60

    def show_info(self):
        result = "합격" if self.is_passed() else "불합격"
        print(f"{self.name}님은 {self.score}점으로 {result}입니다.")

# 객체 생성
s1 = Student("셋쇼", 100)
s2 = Student("고니", 50)
s3 = Student("민식", 60)

# 메서드 호출
s1.show_info()
s2.show_info()
s3.show_info()
