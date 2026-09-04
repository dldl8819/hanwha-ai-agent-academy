# 문제1. 요소 5개의 리스트를 하나 만들어서, 인덱스 번호 두개를 입력받고,
#       해당 인덱스 번호에 자리한 값을 교환해 보세요.
# 힌트 : 입력받기 -> 변수 = input("콘솔에 출력할 메세지")
#       input으로 입력받은 값은 무조건 str 타입으로 가져온다.
lst1 = [10, 20, 30, 40, 50]
idx1 = int(input("교환할 첫 번째 인덱스: "))
idx2 = int(input("교환할 두 번째 인덱스: "))
lst1[idx1], lst1[idx2] = lst1[idx2], lst1[idx1]
print(lst1)

# 문제2. [1,3,4,5,2] 값을 갖는 리스트를 만들고, [5,4,3,2,1] 로 만들어 보세요.
lst2 = [1, 3, 4, 5, 2]
lst2.sort(reverse=True)
print(lst2)

# 문제3. lst = ["korea", ["IT", [1,3,5,7,9], ["even", [0,2,4,6,8]]]]
#       위 lst 리스트에서 Korea 출력
#       숫자 3 출력
#       숫자 8 출력
lst3 = ["korea", ["IT", [1, 3, 5, 7, 9], ["even", [0, 2, 4, 6, 8]]]]
print(lst3[0])            # korea
print(lst3[1][1][1])      # 3
print(lst3[1][2][1][4])   # 8

# 문제4. 국어,영어,수학 3과목에 대한 점수를 입력받아 총점, 평균을 구하여 출력해보세요.
kor = int(input("국어 점수: "))
eng = int(input("영어 점수: "))
math = int(input("수학 점수: "))
total_score = kor + eng + math
avg_score = total_score / 3
print(f"총점: {total_score}, 평균: {avg_score:.2f}")

''' 문제5. 카페 주문 프로그램
    메뉴를 출력하고, 주문은 메뉴 번호로 계속 받습니다.
    종료를 선택하면 주문이 종료되고, 주문한 메뉴들의 총 합을 출력합니다.
    메뉴
    *** 퍼스트존 카페 ***
    1. 아메리카노: 2000원
    2. 카페라떼: 3000원
    3. 화이트모카라떼: 4000원
    4. 자바칩프라푸치노: 4500원
    5. 종료
'''
menu = {
    1: ("아메리카노", 2000),
    2: ("카페라떼", 3000),
    3: ("화이트모카라떼", 4000),
    4: ("자바칩프라푸치노", 4500),
}

order_total = 0
while True:
    print("*** 퍼스트존 카페 ***")
    for num, (name, price) in menu.items():
        print(f"{num}. {name}: {price}원")
    print("5. 종료")

    choice = int(input("메뉴 번호를 선택하세요: "))
    if choice == 5:
        break
    if choice in menu:
        name, price = menu[choice]
        order_total += price
        print(f"{name} 주문 완료!")
    else:
        print("잘못된 메뉴 번호입니다.")

print(f"주문하신 금액의 총합은 {order_total}원입니다.")

''' 문제6. Up, Down 게임
    1 ~ 100사이 임의의 숫자를 입력받고, 그 숫자를 맞추는 게임
    추측한 숫자가 임의의 숫자보다 크면 "Down", 작으면 "Up" 출력,
    임의의 숫자를 맞추면 "축하합니다! 맞췄습니다." 출력 후 게임 종료되며,
    게임을 다시 할 것인지 y또는n으로 입력받는다.
    y를 입력하면 다시 게임이 시작하며, n을 입력하면 게임이 완전히 종료된다.
    콘솔 예시 :
    게임 시작! 숫자를 맞춰 주세요~
    1~100
    1>>  30 (사용자가 숫자 입력)
    "Up"

    30~100
    2>>  40
    "Up"

    40~100
    3>>  80
    "Down"

    40~80
    4>>  65
    "맞췄습니다. 축하합니다!!"
    게임을 다시 시작하시겠습니까?(y/n)  y

    게임 시작! 숫자를 맞춰 주세요~
    1~100
    1>>
    ....
    게임을 다시 시작하시겠습니까?(y/n)  n
    게임 종료!!
'''
# import는 최상단에 위치
import random

while True:
    answer = random.randint(1, 100)
    low, high = 1, 100
    print("게임 시작! 숫자를 맞춰 주세요~")
    while True:
        print(f"{low}~{high}")
        guess = int(input(">> "))
        if guess == answer:
            print("맞췄습니다. 축하합니다!!")
            break
        elif guess < answer:
            print("Up")
            low = guess
        else:
            print("Down")
            high = guess

    again = input("게임을 다시 시작하시겠습니까?(y/n) ")
    if again != "y":
        print("게임 종료!!")
        break
