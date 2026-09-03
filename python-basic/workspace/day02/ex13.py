'''
자료형 복습
int, float, str, bool, None, ...
'''
name: str = "heifam"
age: int = 5
height: float = 123.12
is_student: bool = True
nothing: None = None 

print(name, age, height, is_student, nothing)

# 타입힌트에 값과 다른 타입의 자료형을 선언해도 실행에는 문제가 없다.
name: str = 123
print(name, age, height, is_student, nothing)
