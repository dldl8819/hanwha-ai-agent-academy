score = 15
'''
if score >= 60: 
    print("합격")
else:
    print("불합격")
'''
# score가 90점 이상하면 "A", 80점대면 "B", 70점대면 "C", 그 이하는 "재시험"
# 출력되도록 만들어 보세요. 
if score >= 90: 
    print("A")
elif score >= 80:
    print("B")
elif score >= 70:
    print("C")
else:
    print("재시험")


x = 10 

if x % 2 == 0:
    print("짝수입니다.")

if x > 0 and x < 20:
    print("hahahahaha")

name = ""
if not name:
    print("이름이 비어있습니다.")

# 중첩 조건 
age = 20 
is_student = True

if age >= 18:
    if is_student:
        print("성인이며 학생입니다.")
    else:
        print("그냥 성인입니다.")
else:
    print("미성년자 입니다.")





