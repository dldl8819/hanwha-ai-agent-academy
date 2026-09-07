# 07. 클래스와 상속
import random
from abc import ABC, abstractmethod

# 문제 1. TV 리모컨
# 채널 범위: 0~99, 중복 없이 10개. 채널 올림/내림은 채널 리스트를 순환(wrap-around)한다.
class RemoteTV:
    def __init__(self):
        self.channels = sorted(random.sample(range(0, 100), 10))
        self.channel_index = 0
        self.volume = 5
        self.is_on = False
        self.is_muted = False
        self._volume_before_mute = 0

    def power_on(self):
        self.is_on = True

    def power_off(self):
        self.is_on = False

    def channel_up(self):
        if not self.is_on:
            return
        self.channel_index = (self.channel_index + 1) % len(self.channels)

    def channel_down(self):
        if not self.is_on:
            return
        self.channel_index = (self.channel_index - 1) % len(self.channels)

    def set_channel(self, channel):
        if not self.is_on:
            return
        if channel in self.channels:
            self.channel_index = self.channels.index(channel)

    def volume_up(self):
        if not self.is_on:
            return
        self.volume = min(10, self.volume + 1)

    def volume_down(self):
        if not self.is_on:
            return
        self.volume = max(0, self.volume - 1)

    def toggle_mute(self):
        if not self.is_on:
            return
        if self.is_muted:
            self.volume = self._volume_before_mute
            self.is_muted = False
        else:
            self._volume_before_mute = self.volume
            self.volume = 0
            self.is_muted = True

    def current_channel(self):
        return self.channels[self.channel_index]

    def show_status(self):
        print(f"전원: {'켜짐' if self.is_on else '꺼짐'}")
        if self.is_on:
            print(f"채널: {self.current_channel()}")
            print(f"볼륨: {self.volume}")

remote = RemoteTV()
remote.power_on()
remote.set_channel(remote.channels[3])
remote.show_status()
remote.channel_up()
print(f"현재 채널: {remote.current_channel()}")
remote.toggle_mute()
print(f"현재 볼륨: {remote.volume}")

print("-" * 40)

# 문제 2. 도서 정보
class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author

books = []
for i in range(2):
    title = input(f"책 {i + 1} 제목: ")
    author = input(f"책 {i + 1} 저자: ")
    books.append(Book(title, author))

for book in books:
    print(f"{book.title} - {book.author}")

print("-" * 40)

# 문제 3. 끝말잇기 게임
class Player:
    def __init__(self, name):
        self.name = name

class WordGame:
    def __init__(self, players):
        self.players = players
        self.used_words = ["자동차"]

    def play(self):
        print(f"시작 단어: {self.used_words[0]}")
        turn = 0
        while True:
            player = self.players[turn % len(self.players)]
            while True:
                word = input(f"{player.name}: ")
                if word == "":
                    print("빈 문자열은 입력할 수 없습니다. 다시 입력해주세요.")
                    continue
                break

            last_word = self.used_words[-1]
            if word[0] != last_word[-1] or word in self.used_words:
                print(f"{player.name}가 졌습니다.")
                break

            self.used_words.append(word)
            turn += 1

count = int(input("참가자 수: "))
players = [Player(input(f"참가자 {i + 1} 이름: ")) for i in range(count)]
WordGame(players).play()

print("-" * 40)

# 문제 4. TV 정보
class TVInfo:
    def __init__(self, manufacturer, year, size):
        self.manufacturer = manufacturer
        self.year = year
        self.size = size

    def show(self):
        print(f"{self.manufacturer}에서 만든 {self.year}년형 {self.size}인치 TV")

my_tv = TVInfo('LG', 2018, 32)
my_tv.show()

print("-" * 40)

# 문제 5. 과목 평균
class Grade:
    def __init__(self, math, science, english):
        for score in (math, science, english):
            if not 0 <= score <= 100:
                raise ValueError("점수는 0~100 사이여야 합니다.")
        self.math = math
        self.science = science
        self.english = english

    def get_average(self):
        return (self.math + self.science + self.english) / 3

grade = Grade(90, 85, 95)
print(f"평균: {grade.get_average():.2f}")

print("-" * 40)

# 문제 6. 노래 정보
class Song:
    def __init__(self, title="제목 없음", artist="아티스트 없음", year=2000, country="대한민국"):
        self.title = title
        self.artist = artist
        self.year = year
        self.country = country

    def show(self):
        print(f"{self.year}년 {self.country} 국적의 {self.artist}가 부른 {self.title}")

song = Song('Alone', 'Collective Arts', 2017, '한국')
song.show()
Song().show()

print("-" * 40)

# 문제 7. 직사각형 포함 관계
class Rectangle:
    def __init__(self, x, y, width, height):
        if width <= 0 or height <= 0:
            raise ValueError("너비와 높이는 양수여야 합니다.")
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def show(self):
        print(f"({self.x}, {self.y}), 너비 {self.width}, 높이 {self.height}")

    def contains(self, other):
        return (self.x <= other.x and self.y <= other.y and
                other.x + other.width <= self.x + self.width and
                other.y + other.height <= self.y + self.height)

outer = Rectangle(0, 0, 100, 100)
inner = Rectangle(10, 10, 50, 50)
outer.show()
inner.show()
print(f"outer가 inner를 포함하는가: {outer.contains(inner)}")

print("-" * 40)

# 문제 8. 월간 일정 관리
class Day:
    def __init__(self):
        self.todo = None

class MonthSchedule:
    def __init__(self, day_count):
        self.day_count = day_count
        self.days = [Day() for _ in range(day_count)]

    def add_todo(self, date, todo):
        if not 1 <= date <= self.day_count:
            print("유효하지 않은 날짜입니다.")
            return
        self.days[date - 1].todo = todo
        print("등록했습니다.")

    def show_todo(self, date):
        if not 1 <= date <= self.day_count:
            print("유효하지 않은 날짜입니다.")
            return
        todo = self.days[date - 1].todo
        if todo is None:
            print(f"{date}일에 등록된 할 일이 없습니다.")
        else:
            print(f"{date}일의 할 일은 {todo}입니다.")

print("이번 달 일정 관리 프로그램")
schedule = MonthSchedule(30)
while True:
    choice = input("할 일(입력: 1, 보기: 2, 끝내기: 3): ")
    if choice == "1":
        date = int(input("날짜(1~30): "))
        todo = input("할 일: ")
        schedule.add_todo(date, todo)
    elif choice == "2":
        date = int(input("날짜(1~30): "))
        schedule.show_todo(date)
    elif choice == "3":
        print("프로그램 종료.")
        break
    else:
        print("잘못된 메뉴입니다.")

print("-" * 40)

# 문제 9. 콘서트 좌석 예약
class SeatGroup:
    def __init__(self, grade, size=10):
        self.grade = grade
        self.seats = [None] * size

    def reserve(self, name, number):
        if not 1 <= number <= len(self.seats):
            print("잘못된 좌석 번호입니다.")
            return
        if self.seats[number - 1] is not None:
            print("이미 예약된 좌석입니다.")
            return
        self.seats[number - 1] = name
        print("<<예약 완료>>")

    def cancel(self, name):
        if name not in self.seats:
            print("존재하지 않는 예약자입니다.")
            return
        self.seats[self.seats.index(name)] = None
        print("<<취소 완료>>")

    def show(self):
        row = " ".join(s if s else "___" for s in self.seats)
        print(f"{self.grade} >> {row}")

class ReservationSystem:
    def __init__(self):
        self.groups = {"1": SeatGroup("S"), "2": SeatGroup("A"), "3": SeatGroup("B")}

    def run(self):
        print("Python 콘서트홀 예약 시스템입니다.")
        while True:
            choice = input("예약: 1, 조회: 2, 취소: 3, 끝내기: 4 >> ")
            if choice == "1":
                grade_choice = input("좌석 구분 S(1), A(2), B(3) >> ")
                group = self.groups.get(grade_choice)
                if group is None:
                    print("잘못된 좌석 구분입니다.")
                    continue
                group.show()
                name = input("이름 >> ")
                number = int(input("번호 >> "))
                group.reserve(name, number)
            elif choice == "2":
                for group in self.groups.values():
                    group.show()
                print("<<조회 완료>>")
            elif choice == "3":
                grade_choice = input("좌석 구분 S(1), A(2), B(3) >> ")
                group = self.groups.get(grade_choice)
                if group is None:
                    print("잘못된 좌석 구분입니다.")
                    continue
                name = input("이름 >> ")
                group.cancel(name)
            elif choice == "4":
                print("예약 시스템을 종료합니다.")
                break
            else:
                print("잘못된 메뉴입니다.")

ReservationSystem().run()

print("-" * 40)

# 문제 10. 필기구 상속 구조
class WritingTool:
    def __init__(self, remaining):
        self.remaining = remaining

class MechanicalPencil(WritingTool):
    def __init__(self, remaining, thickness):
        super().__init__(remaining)
        self.thickness = thickness

class BallpointPen(WritingTool):
    def __init__(self, remaining, color):
        super().__init__(remaining)
        self.color = color

class FountainPen(WritingTool):
    def __init__(self, remaining, color):
        super().__init__(remaining)
        self.color = color

    def refill(self, amount):
        self.remaining += amount

pencil = MechanicalPencil(100, "0.5mm")
pen = BallpointPen(80, "검정")
fountain = FountainPen(50, "파랑")
fountain.refill(20)
print(f"샤프펜슬: 남은 양 {pencil.remaining}, 굵기 {pencil.thickness}")
print(f"볼펜: 남은 양 {pen.remaining}, 색상 {pen.color}")
print(f"만년필: 남은 양 {fountain.remaining}, 색상 {fountain.color}")

print("-" * 40)

# 문제 11. 추상 계산기
class Calculator(ABC):
    @abstractmethod
    def add(self, a, b):
        pass

    @abstractmethod
    def subtract(self, a, b):
        pass

    @abstractmethod
    def average(self, numbers):
        pass

class MyCalculator(Calculator):
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def average(self, numbers):
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)

calc = MyCalculator()
print(f"덧셈: {calc.add(3, 4)}")
print(f"뺄셈: {calc.subtract(10, 3)}")
print(f"평균: {calc.average([10, 20, 30])}")
print(f"빈 리스트 평균: {calc.average([])}")

print("-" * 40)

# 문제 12. TV 다단계 상속
class TV:
    def __init__(self, size):
        self.size = size

class ColorTV(TV):
    def __init__(self, size, colors):
        super().__init__(size)
        self.colors = colors

    def show(self):
        print(f"{self.size}인치 {self.colors}컬러")

class IPTV(ColorTV):
    def __init__(self, address, size, colors):
        super().__init__(size, colors)
        self.address = address

    def show(self):
        print(f"나의 IPTV는 {self.address} 주소의 {self.size}인치 {self.colors}컬러")

ColorTV(32, 1024).show()
IPTV('192.1.1.2', 32, 2048).show()

print("-" * 40)

# 문제 13. 단위 변환기
class Converter(ABC):
    @abstractmethod
    def convert(self, value):
        pass

    @abstractmethod
    def unit_name(self):
        pass

    @abstractmethod
    def prompt(self):
        pass

    def run(self):
        value = float(input(self.prompt()))
        result = self.convert(value)
        print(f"변환 결과: {result}{self.unit_name()}입니다.")

class WonToDollar(Converter):
    def prompt(self):
        print("원을 달러로 바꿉니다.")
        return "원을 입력하세요: "

    def convert(self, value):
        return value / 1200

    def unit_name(self):
        return "달러"

class KmToMile(Converter):
    def prompt(self):
        print("km를 mile로 바꿉니다.")
        return "km를 입력하세요: "

    def convert(self, value):
        return value / 1.6

    def unit_name(self):
        return "mile"

WonToDollar().run()
KmToMile().run()

print("-" * 40)

# 문제 14. 색이 있는 점
class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def set_xy(self, x, y):
        self.x = x
        self.y = y

class ColorPoint(Point):
    def __init__(self, x=0, y=0, color="BLACK"):
        super().__init__(x, y)
        self.color = color

    def set_color(self, color):
        self.color = color

    def __str__(self):
        return f"({self.x}, {self.y}), {self.color}"

cp = ColorPoint()
print(cp)
cp.set_xy(3, 4)
cp.set_color("RED")
print(cp)

print("-" * 40)

# 문제 15. 3차원 점
class Point3D(Point):
    def __init__(self, x=0, y=0, z=0):
        super().__init__(x, y)
        self.z = z

    def move_up(self):
        self.z += 1

    def move_down(self):
        self.z -= 1

    def move(self, x, y, z=None):
        self.x += x
        self.y += y
        if z is not None:
            self.z += z

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})의 점"

p3d = Point3D(1, 1, 1)
p3d.move_up()
p3d.move(1, 2, 3)
print(p3d)

print("-" * 40)

# 문제 16. 양의 좌표만 허용하는 점
class PositivePoint(Point):
    def __init__(self, x=0, y=0):
        if x < 0 or y < 0:
            x, y = 0, 0
        super().__init__(x, y)

    def move(self, dx, dy):
        new_x, new_y = self.x + dx, self.y + dy
        if new_x >= 0 and new_y >= 0:
            self.x, self.y = new_x, new_y

pp = PositivePoint(-5, 3)
print(f"({pp.x}, {pp.y})")
pp.move(5, 5)
print(f"({pp.x}, {pp.y})")
pp.move(-100, -100)
print(f"({pp.x}, {pp.y})")

print("-" * 40)

# 문제 17. 배열 기반 사전 클래스
class PairMap(ABC):
    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def put(self, key, value):
        pass

    @abstractmethod
    def delete(self, key):
        pass

    @abstractmethod
    def length(self):
        pass

class Dictionary(PairMap):
    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = []
        self.values = []

    def get(self, key):
        if key in self.keys:
            return self.values[self.keys.index(key)]
        return None

    def put(self, key, value):
        if key in self.keys:
            self.values[self.keys.index(key)] = value
            return
        if len(self.keys) >= self.capacity:
            print("더 이상 저장할 수 없습니다.")
            return
        self.keys.append(key)
        self.values.append(value)

    def delete(self, key):
        if key not in self.keys:
            return None
        idx = self.keys.index(key)
        old_value = self.values[idx]
        del self.keys[idx]
        del self.values[idx]
        return old_value

    def length(self):
        return len(self.keys)

d = Dictionary(10)
d.put("노현태", "빅데이터")
d.put("김아림", "Python")
print(f"노현태의 값은 {d.get('노현태')}")
print(f"김아림의 값은 {d.get('김아림')}")
d.delete("김아림")
print(f"김아림의 값은 {d.get('김아림')}")

print("-" * 40)

# 문제 18. 다형성을 이용한 계산기
class Calc(ABC):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @abstractmethod
    def calculate(self):
        pass

class Add(Calc):
    def calculate(self):
        return self.a + self.b

class Subtract(Calc):
    def calculate(self):
        return self.a - self.b

class Multiply(Calc):
    def calculate(self):
        return self.a * self.b

class Divide(Calc):
    def calculate(self):
        if self.b == 0:
            return "0으로 나눌 수 없습니다."
        return self.a / self.b

calc_map = {"+": Add, "-": Subtract, "*": Multiply, "/": Divide}
n1, n2, op = input("두 정수와 연산자를 입력하세요: ").split()
n1, n2 = int(n1), int(n2)
if op in calc_map:
    print(calc_map[op](n1, n2).calculate())
else:
    print("지원하지 않는 연산자입니다.")

print("-" * 40)

# 문제 19. 텍스트 그래픽 편집기
class Shape(ABC):
    @abstractmethod
    def draw(self):
        pass

class Line(Shape):
    def draw(self):
        print("Line")

class RectangleShape(Shape):
    def draw(self):
        print("Rectangle")

class CircleShape(Shape):
    def draw(self):
        print("Circle")

class GraphicEditor:
    def __init__(self):
        self.shapes = []
        self.shape_types = {"1": Line, "2": RectangleShape, "3": CircleShape}

    def run(self):
        print("그래픽 에디터를 실행합니다.")
        while True:
            choice = input("1. 삽입  2. 삭제  3. 모두 보기  4. 종료 >> ")
            if choice == "1":
                shape_choice = input("1. Line  2. Rectangle  3. Circle >> ")
                shape_class = self.shape_types.get(shape_choice)
                if shape_class is None:
                    print("잘못된 도형 종류입니다.")
                    continue
                self.shapes.append(shape_class())
            elif choice == "2":
                index = int(input("삭제할 순번 >> "))
                if 1 <= index <= len(self.shapes):
                    del self.shapes[index - 1]
                else:
                    print("잘못된 순번입니다.")
            elif choice == "3":
                for shape in self.shapes:
                    shape.draw()
            elif choice == "4":
                print("에디터를 종료합니다.")
                break
            else:
                print("잘못된 메뉴입니다.")

GraphicEditor().run()
