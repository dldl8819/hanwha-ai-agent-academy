class Person:
    def __init__(self, name):
        self.name = name

    def study(self):
        print(f"{self.name}님은 공부를 한다.")

class Heifam(Person):   # self.name, study()

    def __init__(self, name, email):
        super().__init__(name) # 부모 생성자를 호출하여 name 속성 초기화
        self.email = email

    # 오버라이딩 
    # 부모로부터 물려받은 기능을 수정하는 것
    # 기존 def study(self): 선언부는 동일해야 한다.
    def study(self):
        print(f"{self.name}님은 Python 공부를 한다.")

member = Heifam("소울", "test@example.com")
print(f"{member.name}님의 이메일 주소는 {member.email}입니다.") 

member.study()
member.name = "민식"    # 물려받은 변수의 값 수정
member.study()

# 다중 상속 가능 

class A:
    def __init__(self):
        print("A 생성자")

    def a(self):
        pass

class B:
    def __init__(self):
        print("B 생성자")

    def b(self):
        pass

class C:
    def __init__(self):
        print("C 생성자")

    def c(self):
        pass

class D(A, B, C):
    def __init__(self):
        print("D 생성자")

    def d(self):
        pass
# 상속을 받아도 본인의 생성자만 실행된다.

a1 = A()
b1 = B()
c1 = C()
d1 = D()

d1.a()
d1.b()
d1.c()
d1.d()
