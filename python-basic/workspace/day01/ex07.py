# 연산자
a = 10
b = 3

print(a+b)
print(a-b)
print(a*b)
print(a/b)
print(a%b)
print(a//b)

a = 10
b = 20
c = 30
print(a<b and b<c)
print(a<b or b>c)
print(not(a<b))

# in 연산자
nums = [1,2,3,4,5]
print(3 in nums)
print(3 not in nums)
print(13 in nums)

#string

string = "hello python"
print("hello py" in string)
print("lo py" in string)

# Tuple

colors = ("red", "green", "blue")
print('red' in colors)
print('redd' in colors)

# dict
dict1 = {'name':'pika', 'age': 100}
print('name' in dict1) # 키만 존재 여부 확인 가능
print('pika' in dict1) # false 값 존재 여부 확인 불가능
print('pika' in dict1.values())
print(('name', 'pika') in dict1.items())
print(dict1.items())
# 굳이 True = 1, False = 0 을 활용하지는 않지만 아래 내용은 참고
print(True in [1,2,3]) # True는 1과 동일하기 때문에 True로 출력됨
print(False in [0,2,3]) # False는 0과 동일하기 때문에 True로 출력됨
print("="*30)

# 삼항 연산자
score = 50
result = "합격" if score >= 60 else "불합격"
print(result)