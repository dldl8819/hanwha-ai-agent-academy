# 01. 변수와 연산

# 문제 1. 두 변수의 값 교환
a = 10
b = 20
print(f"교환 전: {a} {b}")

# 다중 대입을 사용한 방법
a, b = b, a
print(f"교환 후: {a} {b}")

# 임시 변수를 사용한 방법
a, b = 10, 20
tmp = a
a = b
b = tmp
print(f"교환 후(임시 변수): {a} {b}")

print("-" * 40)

# 문제 2. 나눗셈과 형 변환
print(10 / 4, type(10 / 4))
print(10 // 4, type(10 // 4))
print(10.0 / 4, type(10.0 / 4))
print(int(2.9) + 1.8, type(int(2.9) + 1.8))
print(int(2.9 + 1.8), type(int(2.9 + 1.8)))
print(int(2.9) + int(1.8), type(int(2.9) + int(1.8)))
# / 는 결과가 항상 실수(float)이고, // 는 몫만 취해서 정수부(int/float 중 피연산자에 따름)를 반환한다.

print("-" * 40)

# 문제 3. 사칙연산 계산기
num1 = float(input("첫 번째 수: "))
num2 = float(input("두 번째 수: "))
print(f"덧셈: {num1 + num2}")
print(f"뺄셈: {num1 - num2}")
print(f"곱셈: {num1 * num2}")
if num2 == 0:
    print("나눗셈을 할 수 없습니다.")
else:
    print(f"나눗셈: {num1 / num2}")

print("-" * 40)

# 문제 4. 초를 시·분·초로 변환
sec_input = int(input("초 입력: "))
hours = sec_input // 3600
minutes = (sec_input % 3600) // 60
seconds = sec_input % 60
print(f"{hours}시간 {minutes}분 {seconds}초")

print("-" * 40)

# 문제 5. 최소 화폐 수 구하기
money = int(input("금액 입력: "))
units = [50000, 10000, 5000, 1000, 500, 100]
remain = money
for unit in units:
    count = remain // unit
    remain %= unit
    unit_name = "장" if unit >= 1000 else "개"
    print(f"{unit}원: {count}{unit_name}")

print("-" * 40)

# 문제 6. 몫과 나머지
n1 = int(input("첫 번째 정수: "))
n2 = int(input("두 번째 정수: "))
if n2 == 0:
    print("0으로 나눌 수 없습니다.")
else:
    print(f"몫: {n1 // n2}")
    print(f"나머지: {n1 % n2}")

print("-" * 40)

# 문제 7. 날짜 단위 변환
days = int(input("일 수: "))
months = days // 30
remain_days = days % 30
print(f"{months}개월 {remain_days}일")

print("-" * 40)

# 문제 8. 총점과 평균
scores = input("세 과목 점수: ").split()
scores = [int(s) for s in scores]
total = sum(scores)
avg = total / len(scores)
print(f"총점: {total}")
print(f"평균: {avg:.1f}")
