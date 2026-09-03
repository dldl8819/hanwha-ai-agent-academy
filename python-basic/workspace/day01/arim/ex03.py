# list 
fruits = ["apple", "banana", "cherry"]
print(fruits)
print(fruits[0])
print(fruits[-1])
# print(fruits[3]) # IndexError : 인덱스번호 에러  

# 값 추가 : .append(값)
fruits.append("orange")
print(fruits)

# 값 삭제 : .remove(값) 
fruits.remove("cherry")
print(fruits)

# 리스트의 길이(데이터의 개수) : len(리스트)
length = len(fruits)
print(length)

e = [1, 2, ['Life', 'is', [10, 20]]]
print(e[2][0])
print(e[2][2][0])

num = [1,2,3,4,5]
print(num[0:3]) # [시작인덱스:끝인덱스] : 시작부터 끝인덱스 전까지 
print(num[:3]) # [:끝인덱스] = 처음부터 끝인덱스 전까지 
print(num[2:]) # [시작인덱스:] = 시작인덱스부터 마지막까지 
print(num[:]) 

# 리스트 값 수정 
num[2] = 30
print(num)

# 인덱스 번호로 데이터 삭제 
del num[2]
print(num)


# 정렬 
num2 = [3,5,1,7,6]
num2.sort()  # 오름차순 정렬 
print(num2)
num2.reverse() # 역순으로 변경  
print(num2)
# 내림차순 정렬 한번에 : num2.sort().reverse() 
