# 03. 반복문

# 문제 1. while 반복 연습
print("1) 0부터 10까지 출력하기")
i = 0
while i <= 10:
    print(i)
    i += 1

print("2) 1부터 15까지 출력하기")
i = 1
while i <= 15:
    print(i)
    i += 1

print("3) 0부터 100까지 10씩 증가하며 출력하기")
i = 0
while i <= 100:
    print(i)
    i += 10

print("4) 1부터 20까지 홀수만 출력하기")
i = 1
while i <= 20:
    if i % 2 == 1:
        print(i)
    i += 1

print("5) 1부터 10까지의 합 출력하기")
i = 1
total = 0
while i <= 10:
    total += i
    i += 1
print(f"합: {total}")

print("6) 1부터 50까지 짝수의 합 출력하기")
i = 1
total = 0
while i <= 50:
    if i % 2 == 0:
        total += i
    i += 1
print(f"합: {total}")

print("-" * 40)

# 문제 2. 카페 주문 프로그램 (2단계: 초기 금액 20000원, 잔액 부족 시 거절)
menu = {
    1: ("아메리카노", 2500),
    2: ("카페라떼", 3000),
    3: ("카푸치노", 3500),
    4: ("카라멜마끼아또", 4000),
    5: ("샌드위치", 6000),
}
money = 20000
order_total = 0
while True:
    print("*** 카페 메뉴 ***")
    print("1. 아메리카노  2. 카페라떼  3. 카푸치노")
    print("4. 카라멜마끼아또  5. 샌드위치  6. 종료")
    choice = int(input("메뉴 번호: "))
    if choice == 6:
        break
    if choice not in menu:
        print("잘못된 메뉴 번호입니다.")
        continue
    name, price = menu[choice]
    if price > money - order_total:
        print("잔액이 부족합니다.")
        continue
    order_total += price
    print(f"{name}를 주문했습니다.")
print(f"총 주문 금액: {order_total}원")
print(f"남은 돈: {money - order_total}원")

print("-" * 40)

# 문제 3. 종료값까지 합과 평균
nums = []
while True:
    n = int(input("정수 입력(-1이면 종료): "))
    if n == -1:
        break
    nums.append(n)

if len(nums) == 0:
    print("입력된 정수가 없습니다.")
else:
    total = sum(nums)
    avg = total / len(nums)
    print(f"합계: {total}")
    print(f"평균: {avg}")

print("-" * 40)

# 문제 4. exit까지 문자열 입력
while True:
    text = input("문자열 입력: ")
    if text == "exit":
        print("프로그램 종료!")
        break
    print(text)

print("-" * 40)

# 문제 5. for 반복 연습
print("1) 10부터 30까지 출력하기")
for i in range(10, 31):
    print(i)

print("2) 0부터 100까지 10씩 증가하며 출력하기")
for i in range(0, 101, 10):
    print(i)

print("3) 1부터 20까지 짝수만 출력하기")
for i in range(2, 21, 2):
    print(i)

print("4) 1부터 100까지 홀수의 합 출력하기")
odd_sum = 0
for i in range(1, 101, 2):
    odd_sum += i
print(f"합: {odd_sum}")

print("5) 1부터 n까지의 합 출력하기")
n = int(input("정수 n 입력: "))
n_sum = 0
for i in range(1, n + 1):
    n_sum += i
print(f"합: {n_sum}")

print("-" * 40)

# 문제 6. 구구단
print("1) 구구단 2단 출력")
for i in range(1, 10):
    print(f"2 × {i} = {2 * i}")

print("2) 2~9 사이의 단을 입력받아 해당 단 출력")
dan = int(input("단 입력(2~9): "))
for i in range(1, 10):
    print(f"{dan} × {i} = {dan * i}")

print("3) 2단부터 9단까지 전체 출력")
for dan in range(2, 10):
    for i in range(1, 10):
        print(f"{dan} × {i} = {dan * i}")

print("-" * 40)

# 문제 7. Up & Down 게임
import random

while True:
    answer = random.randint(0, 99)
    low, high = 0, 99
    tries = 0
    print("숫자가 정해졌습니다. 맞혀 보세요!")
    while True:
        print(f"현재 범위: {low}~{high}")
        guess = int(input(f"{tries + 1}번째 시도: "))
        if guess < low or guess > high:
            print("범위를 벗어난 입력입니다.")
            continue
        tries += 1
        if guess == answer:
            print("맞았습니다.")
            break
        elif guess < answer:
            print("Up")
            low = guess + 1
        else:
            print("Down")
            high = guess - 1

    again = input("다시 하시겠습니까? (y/n): ")
    if again != "y":
        print("게임 종료!")
        break
