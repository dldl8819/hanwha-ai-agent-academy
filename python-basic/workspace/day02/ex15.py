# 매개변수와 리턴값 없을 때
def hello():
    print("안녕하세요, 여러분.")
    print("만나서 반갑습니다~~")    
print("이름이 뭐예요?") # hello 함수에 선언되어 있지 않은 코드

hello()
hello() # 함수 호출 여러 번 가능

# 매개변수는 있는데 리턴값은 없을 때)
def greeting(name):
    print("안녕하세요,", name + "님")
    print(f"안녕하세요, {name}님") 
    print("안녕하세요, {0}".format(name))

greeting("민식")

# 매개변수 없이 리턴값은 있을 때
def get_ten():
    print("get_ten 함수 실행!")
    return 10

result = get_ten()
print(result)

# 매개변수와 리턴값 모두 있을 때
def mulp(a, b):
    res = a * b
    return res

result = mulp(10, 20)
print(result)

def mulp2(c, d):
    return c * d
res2 = mulp2(10, 20)
print(res2)

# add(더하기), sub(빼기), mul(곱하기), div(나누기) 함수를 2개의 정수를 매개변수로 입력 받아 리턴해주는 형태로 만드시오.
def add(n1, n2):
    return n1 + n2
add(1, 2)

def sub(n3, n4):
    return n3 - n4
sub(10, 5)

def mul(n5, n6):
    return n5 * n6
mul(4, 9)

def div(n7, n8):
    return n7 / n8
div(6, 2)

def divType(a: int, b: int) -> float:
    return a / b
divType(6, 3)