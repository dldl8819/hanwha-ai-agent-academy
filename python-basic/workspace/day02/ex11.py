# list 반복
fruits = ["apple", "banana", "cherry"]

# print(fruits[0])
# print(fruits[1])
# print(fruits[2])

for fr in fruits:
    print(fr)

# 문자열 반복
word = "hello"
for char in word:
    print(char)

# 1부터 5까지 출력
# range() 
# 지정한 범위의 수를 만들어주는 함수
for i in range(1, 6):
    print(i)

# 1 ~ 10까지 홀수만 출력
for i in range(1, 11, 2):
    print(i)

# dict 반복
info = {'name': 'heifam', 'age': 20, 'height': 190.5}

for i in info:
    print(i) #키만 출력됨

# 값 출력
for v in info.values():
    print(v)

# Key-Value 쌍으로 반복 (가장 많이 사용)
for k, v in info.items():
    print(k, "/", v)

# 키, 값, 인덱스 번호도 필요할 때
# enumerate() -> index, (k, v)
print(enumerate(info.items())) # object 객체 출력됨

# Sequence는 default 0부터 시작
for i, (k, v) in enumerate(info.items()):
    print(i, k, v)


for i, (k, v) in enumerate(info.items(), start=1):
    print(i, k, v)

# List
lst = [1,2,3]
a, b, c = lst 
print(a)
print(b)
print(c)

# Tuple
lst = (1,2,3)
a, b, c = lst 
print(a)
print(b)
print(c)

# 2개면 소괄호 없이도 가능
nums = 10, 20
print(type(nums))

aa, bb = nums 
print(aa)
print(bb)

# ValueError(too many values to unpack) 발생
nums = 10, 20, 30 # packing
aaa, bbb = nums # unpacking
print(aaa)

nums = 10, 20, [1,2,3]
a3, b3, c3 = nums
print(a3)
print(b3)
print(c3)


# 데이터 스왑
int1 = 100
int2 = 200

# int1의 값과 int2의 값을 교환
# Python은 아래 방식으로 할 필요가 없다  
tmp = int1
int1 = int2 
int2 = tmp 

# Python에서는 아래와 같은 방식으로 데이터 스왑이 가능하다.
int1, int2 = int2, int1 
