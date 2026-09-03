# while
i = 1           # 초기식 
while i <= 5:   # 조건식 
    print(i)
    i = i + 1   # 증감식  i += 1

# 무한반복 : 어느시점에는 반복이 종료되도록 설계 
while True:
    answer = input("아무것이나 입력(종료는 exit입력):")
    if answer == "exit":
        break     # while 문 강제 종료하는 키워드 
    print(answer)


#---------------------------------------------------------
# 문제1. 0 ~ 15까지 출력 
i = 0
while i <= 15:
    print(i)
    i += 1
# 문제2. 0 ~ 100까지 10단위로 출력. ex. 0 10 20 30 ...
i = 0
while i <= 100:
    print(i)
    i += 10
# 문제3. 1 ~ 50까지 중 홀수만 출력. 
i = 1
while i < 50:
    if i % 2 == 1: # 홀수 판단
        print(i)
    i += 1
# 문제4. 1 ~ 50까지의 총 합을 출력. 
i = 1
total = 0
while i <= 50:
    total += i # total에 i값 누적
    i += 1
print("total: ", total)
# 문제5. 1 ~ 100까지 짝수들의 총 합 출력. 
i = 1
tot = 0
while i <= 100:
    if i % 2 == 0:
        tot += i
    i += 1
print("total: ", tot)





