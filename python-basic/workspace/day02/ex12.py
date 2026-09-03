nums = [1, 2, 3, 4, 5]
squares = [n*n for n in nums]

print("리스트 컴프리헨션: ", squares)

sq = []
for n in nums:
    sq.append(n*n)

print("for문으로 작성해보기", sq)

# 조건 포함
# nums 중 짝수만 가져오기
even_nums = [n for n in nums if n % 2 == 0]
print(even_nums)

# 문자열 처리
words = ['oops', 'soul', 'minsik']
a = "heifam"
# a. 했을 때 나오는 메서드들 확인
caped = [word.upper() for word in words]
print(caped)

# 중첩 for 반복문
# 다중 리스트 풀어보기
matrix = [[10, 20], [30, 40]] 
flattened = [num for row in matrix for num in row ]
print(flattened)

# 보조 제어문 활용
# break
for i in range(1, 10):
    if i == 5:
        break
    print(i)
# continue
for i in range(1, 10):
    if i == 5:
        continue
    print(i)

