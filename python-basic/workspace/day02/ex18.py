# 클래스 정의
class Person:
    # 생성자
    def __init__(self):
        print("생성자 호출!")
# 객체 생성 : hei1, hei2, hei3은 참조 변수
hei1 = Person()
hei2 = Person()
hei3 = Person()

class Human:
    def __init__(self):
        print("휴먼 생성자 호출!")
        # 인스턴스 변수
        # 값을 초기화
        self.name = ""
        self.age = 0
h1 = Human()
h2 = Human()
h3 = Human()
# heap 메모리에 Human 객체가 생성됨
# Human 객체에 name과 age 라는 인스턴스 변수가 생성됨
# stack 메모리에 h1이라는 객체가 heap 메모리에 저장되어 있는 h1의 Human 객체의 주소가 저장된다.

print("h1.name : ", h1.name)
print("h1.age : ", h1.age)
h1.name = '민식'
h1.age = 20
print("h1.name : ", h1.name)
print("h1.age : ", h1.age)
print("h2.name : ", h2.name)
print("h2.age : ", h2.age)

# 클래스 변수
# 공유해서 쓰는 속성
class Heifam:
    # 클래스 변수 : link1, link2
    link1 = "Youtube"
    link2 = "Soop"

print(Heifam.link1)
print(Heifam.link2)

Heifam.link1 = "Instargarm" # 클래스 변수

print(Heifam.link1)

hf1 = Heifam()
hf2 = Heifam()

print(hf1.link1)
print(hf2.link1)
hf2.link2 = "heifam.co.kr" # 인스턴스 변수
print(hf1.link1)
print(hf2.link1)

# 함수
def hello():
    # 지역변수
    x = 10

# 전역변수
num1 = 10

