# 02. 조건문

# 문제 1. 양수, 음수, 0 판별
num = int(input("정수 입력: "))
if num > 0:
    print("양수")
elif num < 0:
    print("음수")
else:
    print("0")

print("-" * 40)

# 문제 2. 홀수와 짝수
num = int(input("1~99 사이의 정수: "))
if num < 1 or num > 99:
    print("잘못된 입력")
elif num % 2 == 0:
    print("짝수")
else:
    print("홀수")

print("-" * 40)

# 문제 3. 세 수의 중간값
nums = input("세 정수 입력: ").split()
a, b, c = int(nums[0]), int(nums[1]), int(nums[2])

# sorted()를 사용한 풀이
middle_sorted = sorted([a, b, c])[1]
print(f"중간값(sorted): {middle_sorted}")

# 조건문만 사용한 풀이
if (a - b) * (a - c) < 0:
    middle_if = a
elif (b - a) * (b - c) < 0:
    middle_if = b
else:
    middle_if = c
print(f"중간값(조건문): {middle_if}")

print("-" * 40)

# 문제 4. 369 게임
num = int(input("숫자: "))
count_369 = str(num).count('3') + str(num).count('6') + str(num).count('9')
if count_369 == 1:
    print("박수짝")
elif count_369 >= 2:
    print("박수짝짝")
else:
    print(num)

print("-" * 40)

# 문제 5. 점과 직사각형
x, y = map(int, input("x y 입력: ").split())
if 100 <= x <= 200 and 100 <= y <= 200:
    print("직사각형 안에 있습니다.")
else:
    print("직사각형 밖에 있습니다.")

print("-" * 40)

# 문제 6. 계절 판별
month = int(input("월 입력: "))
if month in (3, 4, 5):
    print("봄")
elif month in (6, 7, 8):
    print("여름")
elif month in (9, 10, 11):
    print("가을")
elif month in (12, 1, 2):
    print("겨울")
else:
    print("잘못된 입력")

print("-" * 40)

# 문제 7. 성적 등급
score = int(input("점수 입력: "))
if 90 <= score <= 100:
    grade = "수"
elif 80 <= score <= 89:
    grade = "우"
elif 70 <= score <= 79:
    grade = "미"
elif 60 <= score <= 69:
    grade = "양"
elif 0 <= score <= 59:
    grade = "가"
else:
    grade = None

if grade is None:
    print("잘못된 입력")
else:
    print(f"등급: {grade}")

print("-" * 40)

# 문제 8. 연산자 선택 계산기
parts = input("두 수와 연산자 입력: ").split()
n1, n2, op = float(parts[0]), float(parts[1]), parts[2]
if op == '+':
    print(f"결과: {n1 + n2}")
elif op == '-':
    print(f"결과: {n1 - n2}")
elif op == '*':
    print(f"결과: {n1 * n2}")
elif op == '/':
    if n2 == 0:
        print("0으로 나눌 수 없습니다.")
    else:
        print(f"결과: {n1 / n2}")
else:
    print("지원하지 않는 연산자입니다.")

print("-" * 40)

# 문제 9. 현재 시각에 맞는 인사
import datetime

now = datetime.datetime.now()
hour, minute = now.hour, now.minute
print(f"현재 시간은 {hour}시 {minute}분입니다.")
if 4 <= hour < 12:
    print("Good Morning")
elif 12 <= hour < 18:
    print("Good Afternoon")
elif 18 <= hour < 22:
    print("Good Evening")
else:
    print("Good Night")
