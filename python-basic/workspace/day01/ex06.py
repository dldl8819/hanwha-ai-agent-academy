# set은 {}로 선언
nums = {}
nums2 = {1,2,2,3,3,3,4,4,4,4}

print(nums2)

# 값 추가
# nums.add(5)
# print(nums) dict object라서 add 불가 AttributeError 발생
nums2.add(5)
print(nums2)

# 값 삭제
nums2.discard(5)
print(nums2)

# 집합 연산
a = {1,2,3}
b = {3,4,5}
print ("합집합", a | b)
print ("교집합", a & b)
print ("차집합", a - b) # 차집합은 순서가 중요
