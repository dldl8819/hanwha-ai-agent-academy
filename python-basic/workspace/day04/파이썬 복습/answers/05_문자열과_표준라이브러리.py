# 05. 문자열과 표준 라이브러리

# 문제 1. 글자 배열의 공백 바꾸기
def print_char_list(chars):
    text = ""
    for c in chars:
        text += c
    print(text)

def replace_space(chars):
    result = []
    for c in chars:
        if c == ' ':
            result.append(',')
        else:
            result.append(c)
    return result

chars = ['I', ' ', 'a', 'm', ' ', 'a', ' ', 'b', 'o', 'y']
print("변경 전: ", end="")
print_char_list(chars)
new_chars = replace_space(chars)
print("변경 후: ", end="")
print_char_list(new_chars)

print("-" * 40)

# 문제 2. 문장 속 단어 수
while True:
    sentence = input(">> ")
    if sentence == "그만":
        print("프로그램 종료!")
        break
    word_count = len(sentence.split())
    print(f"단어 수는 {word_count}")

print("-" * 40)

# 문제 3. 문자열 수정 명령

def replace_first_with_replace(text, old, new):
    return text.replace(old, new, 1)

def replace_first_with_slice(text, old, new):
    idx = text.find(old)
    if idx == -1:
        return text
    return text[:idx] + new + text[idx + len(old):]

sentence = input(">> ")
while True:
    command = input("명령: ")
    if command == "그만":
        print("종료합니다.")
        break

    parts = command.split("!")
    if len(parts) != 2 or parts[0] == "" or parts[1] == "":
        print("잘못된 명령입니다!")
        continue

    old, new = parts
    if old not in sentence:
        print("찾을 수 없습니다!")
        continue

    sentence = replace_first_with_replace(sentence, old, new)
    print(sentence)

print("-" * 40)

# 문제 4. 같은 좌표의 점
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p = Point(3, 50)
q = Point(4, 50)
print(p)
print('같은 점' if p == q else '다른 점')

print("-" * 40)

# 문제 5. 중심이 같은 원
class Circle:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

    def __str__(self):
        return f"Circle({self.x}, {self.y}), 반지름 {self.radius}"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

circle_a = Circle(2, 3, 5)
circle_b = Circle(2, 3, 30)
print(f"원 a: {circle_a}")
print(f"원 b: {circle_b}")
print('같은 원' if circle_a == circle_b else '다른 원')
