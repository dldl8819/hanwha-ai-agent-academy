class Person:
    def __init__(self, name):
        self.name = name

    def work(self):
        print(f"{self.name}이/가 일을 한다.")

class Postman(Person):  # self.name, work()
    # 오버라이딩 : 부모로부터 물려받은 기능이 마음에 안들어, 내용물을 수정하는 것
    def __init__(self, name, postman_id):
        super().__init__(name) # 부모 생성자 호출하여 name 속성 초기화
        self.postman_id = postman_id

    def work(self):
        print(f"{self.name}이/가 우편물을 배달한다.")



p = Postman("우체부", 100)
print(p.name)
# print(p.postman_id)
p.work()

per = Person("부모")
print(per.name)
per.work()



#---------------------------------------------------
class A:
    def hello(self):
        print("hello AAA")

class B(A):
    # override
    def hello(self):
        print("hello BBB")

class C(A):
    # override
    def hello(self):
        print("hello CCC")

class F:
    def hello(self):
        print("FFFF")

class D(B, C):
    # override
    def hello(self):
        print("hello DDD")
        super(D, self).hello() # BBB
        super(C, self).hello() # AAA
        super(B, self).hello() # CCC
        # super(F, self).hello() # error 부모자식 관계 X
        # super(A, self).hello() # error object는 hello() 메서드 없음

x = D()
x.hello()
print(D.mro())
