class Person:
    def __init__(self):
        self.name = "사람"

    def study(self):
        print(f"{self.name}님이 공부를 한다.")

class Heifam(Person):   # self.name, study()
    # 오버라이딩 
    # 부모로부터 물려받은 기능을 수정하는 것
    # 기존 def study(self): 선언부는 동일해야 한다.
    def study(self):
        print(f"{self.name}님이 Python 공부를 한다.")

member = Heifam()
print(member.name)      # 물려 받은 상태 그대로 출력
member.study()
member.name = "민식"    # 물려받은 변수의 값 수정
member.study()