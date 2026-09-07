# 06. 딕셔너리와 자료구조
import random

# 문제 1. 영한 사전
dictionary = {
    "apple": "사과", "banana": "바나나", "cat": "고양이", "dog": "개",
    "house": "집", "book": "책", "water": "물", "school": "학교",
    "friend": "친구", "computer": "컴퓨터",
}
while True:
    word = input("영어 단어: ")
    if word == "exit":
        print("프로그램 종료!")
        break
    if word in dictionary:
        print(f"뜻: {dictionary[word]}")
    else:
        print("사전에 없는 단어입니다.")

print("-" * 40)

# 문제 2. 성적 관리 프로그램
scores = {}
while True:
    print("** Python 성적 관리 프로그램 **")
    print("1. 전체 조회")
    print("2. 등록")
    print("3. 수정")
    print("4. 삭제")
    print("5. 전체 평균")
    print("6. 프로그램 종료")
    choice = int(input("선택: "))

    if choice == 1:
        if not scores:
            print("등록된 학생이 없습니다.")
        for name, score in scores.items():
            print(f"{name}: {score}")

    elif choice == 2:
        name = input("학생 이름: ")
        if name in scores:
            print("이미 등록된 학생입니다.")
            continue
        score = int(input("Python 점수: "))
        if not 0 <= score <= 100:
            print("점수는 0~100 사이여야 합니다.")
            continue
        scores[name] = score
        print("등록했습니다.")

    elif choice == 3:
        name = input("학생 이름: ")
        if name not in scores:
            print("등록되지 않은 학생입니다.")
            continue
        score = int(input("새 Python 점수: "))
        if not 0 <= score <= 100:
            print("점수는 0~100 사이여야 합니다.")
            continue
        scores[name] = score
        print("수정했습니다.")

    elif choice == 4:
        name = input("학생 이름: ")
        if name not in scores:
            print("등록되지 않은 학생입니다.")
            continue
        del scores[name]
        print("삭제했습니다.")

    elif choice == 5:
        if not scores:
            print("등록된 학생이 없습니다.")
        else:
            print(f"전체 평균: {sum(scores.values()) / len(scores)}")

    elif choice == 6:
        print("프로그램 종료!")
        break

    else:
        print("잘못된 선택입니다.")

print("-" * 40)

# 문제 3. 학생 연락처 검색
class StudentContact:
    def __init__(self, student_id, tel):
        self.student_id = student_id
        self.tel = tel

contacts = {
    "아림": StudentContact("202601", "010-1234-5678"),
    "민식": StudentContact("202602", "010-2222-3333"),
    "소울": StudentContact("202603", "010-4444-5555"),
}
while True:
    name = input("검색할 이름: ")
    if name == "exit":
        print("프로그램 종료!")
        break
    if name in contacts:
        student = contacts[name]
        print(f"학번: {student.student_id}, 전화번호: {student.tel}")
    else:
        print("등록되지 않은 학생입니다.")

print("-" * 40)

# 문제 4. 나라별 인구 저장과 검색
populations = {}
print("나라 이름과 인구를 입력하세요.")
while True:
    line = input("나라 이름, 인구: ")
    if line == "그만":
        break
    country, pop = line.split()
    pop = int(pop)
    if pop < 0:
        print("인구는 음수일 수 없습니다.")
        continue
    populations[country] = pop

while True:
    country = input("인구 검색: ")
    if country == "그만":
        print("프로그램 종료!")
        break
    if country in populations:
        print(f"{country}의 인구는 {populations[country]}")
    else:
        print(f"{country} 나라는 없습니다.")

print("-" * 40)

# 문제 5. 학생 정보 관리
class Student:
    def __init__(self, name, dept, student_id, gpa):
        self.name = name
        self.dept = dept
        self.student_id = student_id
        self.gpa = gpa

    def __str__(self):
        return f"{self.name}, {self.dept}, {self.student_id}, {self.gpa}"

student_list = [
    Student("아이언맨", "빅데이터", 4, 4.25),
    Student("캡틴", "컴퓨터공학", 3, 4.0),
    Student("토르", "전자공학", 2, 3.5),
    Student("헐크", "물리학", 4, 3.8),
]

# list[Student] 검색
def find_in_list(students, name):
    for s in students:
        if s.name == name:
            return s
    return None

# dict[str, Student] 검색 (이름을 키로 사용)
student_dict = {s.name: s for s in student_list}

print("=== 전체 학생 정보 (list 버전) ===")
for s in student_list:
    print(s)

while True:
    name = input("학생 이름: ")
    if name == "그만":
        print("프로그램 종료!")
        break
    found = student_dict.get(name)  # dict 버전은 반복 없이 바로 조회 가능
    if found:
        print(found)
    else:
        print("등록되지 않은 학생입니다.")

print("-" * 40)

# 문제 6. 도시 위치 검색
class Location:
    def __init__(self, city, lon, lat):
        self.city = city
        self.lon = lon
        self.lat = lat

    def __str__(self):
        return f"{self.city}, {self.lon}, {self.lat}"

locations = {}
for _ in range(4):
    city, lon, lat = input("도시, 경도, 위도: ").split(",")
    locations[city] = Location(city, int(lon), int(lat))

for loc in locations.values():
    print(loc)

while True:
    city = input("도시 이름: ")
    if city == "그만":
        print("프로그램 종료!")
        break
    if city in locations:
        print(locations[city])
    else:
        print("등록되지 않은 도시입니다.")

print("-" * 40)

# 문제 7. 장학생 선발
print("Python 장학금 관리 시스템입니다.")
gpas = {}
while len(gpas) < 5:
    name, gpa = input("이름과 학점: ").split()
    gpa = float(gpa)
    if name in gpas:
        print("이미 입력한 이름입니다. 다시 입력해주세요.")
        continue
    if not 0 <= gpa <= 4.5:
        print("학점은 0~4.5 사이여야 합니다.")
        continue
    gpas[name] = gpa

threshold = float(input("장학생 선발 학점 기준: "))
selected = [name for name, gpa in gpas.items() if gpa >= threshold]
print("장학생 명단:", *selected)

print("-" * 40)

# 문제 8. 고객 포인트 관리
print("** 포인트 관리 프로그램 **")
points = {}
while True:
    line = input("이름과 포인트: ")
    if line == "그만":
        print("프로그램 종료!")
        break
    name, point = line.split()
    point = int(point)
    points[name] = points.get(name, 0) + point
    for n, p in points.items():
        print(f"({n}, {p})")

print("-" * 40)

# 문제 9. 스택 구현
class Stack:
    def __init__(self, capacity):
        self._data = []
        self._capacity = capacity

    def push(self, value):
        if self.length() >= self._capacity:
            return False
        self._data.append(value)
        return True

    def pop(self):
        if self.length() == 0:
            return None
        return self._data.pop()

    def length(self):
        return len(self._data)

    def capacity(self):
        return self._capacity

stack = Stack(10)
for i in range(10):
    stack.push(i)

popped = []
while stack.length() > 0:
    popped.append(stack.pop())
print(*popped)

print("-" * 40)

# 문제 10. 제한 용량 문자열 스택
capacity = int(input("총 스택 저장 공간의 크기: "))
str_stack = Stack(capacity)
while True:
    text = input("문자열 입력: ")
    if text == "그만":
        break
    if not str_stack.push(text):
        print("스택이 꽉 차서 추가할 수 없습니다!")

popped_strs = []
while str_stack.length() > 0:
    popped_strs.append(str_stack.pop())
print("스택에 저장된 모든 문자열 팝:", *popped_strs)

print("-" * 40)

# 문제 11. 나라와 수도 퀴즈
# (나라, 수도) 튜플 리스트로 먼저 구현한 뒤, 나라를 키로 하는 딕셔너리로 재구현
capitals = {}
print("** 수도 맞히기 게임을 시작합니다 **")
while True:
    menu = int(input("입력: 1, 퀴즈: 2, 종료: 3 >> "))
    if menu == 1:
        while True:
            line = input("나라, 수도 (그만 입력 시 종료): ")
            if line == "그만":
                break
            country, capital = line.split()
            if country in capitals:
                print("이미 등록된 나라입니다.")
                continue
            capitals[country] = capital
    elif menu == 2:
        while True:
            if not capitals:
                print("등록된 나라가 없습니다.")
                break
            country = random.choice(list(capitals.keys()))
            answer = input(f"{country}의 수도는? ")
            if answer == "그만":
                break
            if answer == capitals[country]:
                print("정답!!")
            else:
                print("아닙니다!!")
    elif menu == 3:
        print("게임을 종료합니다.")
        break
    else:
        print("잘못된 메뉴입니다.")
