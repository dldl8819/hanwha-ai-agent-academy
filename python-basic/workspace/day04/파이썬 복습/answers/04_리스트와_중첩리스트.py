# 04. 리스트와 중첩 리스트

# 문제 1. 리스트 기본 조작
numbers = [10, 20, 30, 40, 50]
print(f"초기 리스트: {numbers}")

# 1. 모든 요소 출력
for n in numbers:
    print(n)

# 2. 인덱스 1과 3의 값의 합 출력
print(f"인덱스 1과 3의 합: {numbers[1] + numbers[3]}")

# 3. 인덱스를 입력받아 해당 값 출력(잘못된 인덱스 처리 포함)
idx = int(input("인덱스 입력: "))
if 0 <= idx < len(numbers):
    print(f"해당 값: {numbers[idx]}")
else:
    print("잘못된 인덱스입니다.")

# 4. 모든 요소의 합 출력
print(f"합계: {sum(numbers)}")

# 5. 값을 입력받아 그 값의 인덱스 출력(없으면 안내 메시지 출력)
target = int(input("찾을 값: "))
if target in numbers:
    print(f"인덱스: {numbers.index(target)}")
else:
    print("리스트에 없는 값입니다.")

# 6. 인덱스 2와 4의 값 교환 후 리스트 출력
numbers[2], numbers[4] = numbers[4], numbers[2]
print(f"교환 결과: {numbers}")

print("-" * 40)

# 문제 2. 입력, 정렬, 추가
nums = []
while len(nums) < 5:
    n = int(input(f"정수 입력({len(nums) + 1}/5): "))
    if n in nums:
        print("이미 입력한 값입니다. 다시 입력해주세요.")
        continue
    nums.append(n)
nums.sort()
print(f"정렬 결과: {nums}")
extra = int(input("추가할 정수: "))
nums.append(extra)
print(f"추가 결과: {nums}")

print("-" * 40)

# 문제 3. 게임 랭킹 보드
# 동점자는 먼저 입력된 사람을 상위로 처리한다.
players = []
for i in range(5):
    name = input(f"플레이어 {i + 1} 이름: ")
    score = int(input(f"플레이어 {i + 1} 점수: "))
    players.append([name, score])

# 1. 입력 순서대로 이름과 점수 출력
for name, score in players:
    print(f"{name} {score}")

# 2. 두 번째와 세 번째 플레이어의 점수를 교환
players[1][1], players[2][1] = players[2][1], players[1][1]

def print_ranking(player_list):
    ranked = sorted(player_list, key=lambda p: p[1], reverse=True)
    print(f"{'rank':<5}{'user_name':<10}{'score':>5}")
    print("-" * 22)
    for rank, (name, score) in enumerate(ranked, start=1):
        print(f"{rank:<5}{name:<10}{score:>5}")

# 3. 점수가 높은 순서로 1~5위 출력
print_ranking(players)

# 4. 새 플레이어 한 명을 추가한 뒤 상위 5명만 다시 출력
new_name = input("새 플레이어 이름: ")
new_score = int(input("새 플레이어 점수: "))
players.append([new_name, new_score])
ranked_all = sorted(players, key=lambda p: p[1], reverse=True)[:5]
print_ranking(ranked_all)

print("-" * 40)

# 문제 4. 로또 번호 생성
import random

lotto_a = sorted(random.sample(range(1, 46), 6))
print(f"로또 번호(random.sample): {lotto_a}")

lotto_b = []
while len(lotto_b) < 6:
    n = random.randint(1, 45)
    if n not in lotto_b:
        lotto_b.append(n)
lotto_b.sort()
print(f"로또 번호(직접 구현): {lotto_b}")

print("-" * 40)

# 문제 5. 비정방 중첩 리스트
matrix = [[10, 11, 12], [20, 21], [30, 31, 32], [40, 41]]
for row in matrix:
    line = ""
    for value in row:
        line += f"{value} "
    print(line.strip())

print("-" * 40)

# 문제 6. 아파트 관리비
fees = [[0] * 5 for _ in range(3)]
for floor in range(3):
    for unit in range(5):
        room = (floor + 1) * 100 + (unit + 1)
        fees[floor][unit] = int(input(f"{room}호 관리비: "))

# 1. 15세대의 관리비 입력 및 전체 출력
for floor in range(3):
    for unit in range(5):
        room = (floor + 1) * 100 + (unit + 1)
        print(f"{room}호 관리비: {fees[floor][unit]}")

# 2. 층별 평균 출력
floor_avgs = [sum(row) / len(row) for row in fees]
print(f"층별 평균: 1층 {floor_avgs[0]:.1f}원, 2층 {floor_avgs[1]:.1f}원, 3층 {floor_avgs[2]:.1f}원")

# 3. 전체 평균 출력
all_fees = [fee for row in fees for fee in row]
overall_avg = sum(all_fees) / len(all_fees)
print(f"전체 평균: {overall_avg:.1f}원")

# 4. 103호와 203호의 관리비 교환
fees[0][2], fees[1][2] = fees[1][2], fees[0][2]
print(f"교환 후 103호: {fees[0][2]}, 203호: {fees[1][2]}")

# 5. 전체 평균보다 관리비가 적은 호수 출력
print("전체 평균보다 적은 호수:")
for floor in range(3):
    for unit in range(5):
        room = (floor + 1) * 100 + (unit + 1)
        if fees[floor][unit] < overall_avg:
            print(room)

# 6. 최솟값과 최댓값을 낸 호수 출력
min_fee = min(all_fees)
max_fee = max(all_fees)
for floor in range(3):
    for unit in range(5):
        room = (floor + 1) * 100 + (unit + 1)
        if fees[floor][unit] == min_fee:
            print(f"최소 관리비: {room}호 {min_fee}원")
        if fees[floor][unit] == max_fee:
            print(f"최대 관리비: {room}호 {max_fee}원")

# 7. 관리비가 적은 순서대로 (호수, 관리비) 출력
room_fee_pairs = []
for floor in range(3):
    for unit in range(5):
        room = (floor + 1) * 100 + (unit + 1)
        room_fee_pairs.append((room, fees[floor][unit]))
room_fee_pairs.sort(key=lambda pair: pair[1])
print(room_fee_pairs)

print("-" * 40)

# 문제 7. 다양한 길이의 행 출력
arr = [[1], [1, 2, 3], [1], [1, 2, 3, 4], [1, 2]]
for row in arr:
    line = ""
    for value in row:
        line += f"{value} "
    print(line.strip())

print("-" * 40)

# 문제 8. 알파벳 계단
while True:
    letter = input("소문자 알파벳: ")
    if len(letter) == 1 and letter.isalpha() and letter.islower():
        break
    print("소문자 알파벳 하나를 입력해주세요.")

for end in range(ord(letter), ord('a') - 1, -1):
    print("".join(chr(c) for c in range(ord('a'), end + 1)))

print("-" * 40)

# 문제 9. 3의 배수 찾기
values = list(map(int, input("양의 정수 10개: ").split()))
multiples = [v for v in values if v % 3 == 0]
print("3의 배수:", *multiples)

print("-" * 40)

# 문제 10. 4×4 무작위 배치
grid = [[0] * 4 for _ in range(4)]
positions = random.sample([(r, c) for r in range(4) for c in range(4)], 10)
for r, c in positions:
    grid[r][c] = random.randint(1, 10)

for row in grid:
    print(" ".join(str(v) for v in row))

print("-" * 40)

# 문제 11. 최댓값 찾기
raw_values = input("정수 입력: ").split()
collected = []
for v in raw_values:
    if v == "-1":
        break
    collected.append(int(v))

# max() 사용
print(f"가장 큰 수는 {max(collected)}")

# max()를 사용하지 않는 풀이
biggest = collected[0]
for v in collected[1:]:
    if v > biggest:
        biggest = v
print(f"가장 큰 수는(직접 구현) {biggest}")

print("-" * 40)

# 문제 12. 학점 평균
grade_points = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
while True:
    grades = input("6개의 학점을 입력하세요(A/B/C/D/F): ").split()
    if len(grades) == 6 and all(g in grade_points for g in grades):
        break
    print("잘못된 학점입니다. 다시 입력해주세요.")

avg_point = sum(grade_points[g] for g in grades) / len(grades)
print(f"평균: {avg_point:.2f}")

print("-" * 40)

# 문제 13. 강수량 평균 관리
rainfalls = []
while True:
    value = int(input("강수량 입력(0이면 종료): "))
    if value == 0:
        print("프로그램 종료!")
        break
    rainfalls.append(value)
    print("강수량:", *rainfalls)
    avg_rain = sum(rainfalls) / len(rainfalls)
    print(f"현재 평균: {avg_rain:.1f}")
