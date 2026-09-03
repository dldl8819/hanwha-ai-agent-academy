score = 60

if score > 60:
    print("합격")

elif score < 60:
    print("불합격")

else:
    print("딱 60점")

# score2가 90점 이상이면 A, 80점대면 B, 70점대면 C, 그 이하는 재시험이 출력되도록 조건문을 만들어라
score2 = 60
if score2 >= 90:
    print("A")
elif score2 >= 80:
    print("B")
elif score2 >= 70:
    print("C")
else:
    print("재시험")

x = 9

if x % 2 == 0:
    print("짝수")
else:
    print("홀수")

if x > 0 and x <20:
    print("20보다 작은 수입니다")

name = ""
if not name:
    print("이름이 비어있습니다.")
else:
    print("이름이 비어 있진 않네요.")

# 중첩 조건
age = 20
is_student = True

if age >= 18:
    pass # 지금 조건이 참일 때 어떤 코드가 작동할지 안쓰고 넘어가기
else:
    print("누구십니까")

if age >=18:
    if is_student:
        print("성인이시고 학생이시군요")
    else:
        print("학생은 아니시고 성인이신 분이군요")
else:
    print("미성년자이시군요")