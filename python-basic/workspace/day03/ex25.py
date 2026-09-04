# 예외 처리 전: 아래처럼 바로 실행하면 잘못된 입력에 ValueError가 발생해 프로그램이 즉시 종료됨
# num = input("정수 : ")
# int(num) # ValueError
# print(num)

try:
    num = input("정수 : ")
    int(num) 
    print(num)
except ValueError:
    print("정수를 입력하십시오.")

lst = [1, 2, 3]
try:
    num = int(input("정수: "))
    print(num)
    print(3 / num) # num에 0 입력 시 ZeroDivisionError 발생 가능
    print(lst[num]) # 5 입력 시 IndexError 발생 가능

# 각각의 예외에 대한 처리를 하나씩 해보기

except ValueError:
    print("정수를 입력하십시오.")
except ZeroDivisionError:
    print("0으로는 나눌 수 없습니다.")
except IndexError:
    print("리스트에 인덱스를 확인해주십시오.")

# 예외 처리 하나로 처리하기
except Exception as e:
    print(f"오류가 발생했습니다. ({e})")

else:
    print("정상 실행되었습니다.")

finally:
    print("finally는 항상 실행되는 코드 블럭")

