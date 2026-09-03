# 연산자 
a = 10
b = 20 
c = 30 
print(a < b and b > c)
print(a < b or b > c)
print(not(a < b))
print("="*30)

# in 연산자 
nums = [1,2,3,4,5]
print(3 in nums)
print(3 not in nums)
print(13 in nums)

string = "hello python"
print("lo py" in string)

colors = ("red", "green", "blue")
print('red' in colors) 

dic = {'name':'pika', 'age': 100}
print('name' in dic) # 키만 존재 여부 확인 
print('pika' in dic) 
print('pika' in dic.values())
print(('name','pika') in dic.items())
print(dic.items())
print(True in [1,2,3]) # True = 1 , False = 0 
print("="*30)

# 삼항 연산자 
score = 50 
result = "합격" if score >= 60 else "불합격"
print(result)


