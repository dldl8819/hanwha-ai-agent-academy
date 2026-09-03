def greeting(name="아무개"):
	print(f"안녕하세요, {name}님")
greeting()
greeting("민식")

# 에러 발생
def greeting2(name="아무개", age):
	print(f"안녕하세요, {age}살이신 {name}님")
greeting2(10)

# default값이 있는 매개변수는 뒤쪽에 배치해주어야 한다.
def greeting2(age, name="아무개"):
	print(f"안녕하세요, {age}살이신 {name}님")
greeting2(10)

# 매개변수와 인자의 순서는 일치해야 한다.
def info(name, age):
	print(f"{name}님의 나이는 {age}입니다.")
info("민식", 20)
info(20, "민식")

# 키워드 인자를 사용하면 인자의 순서를 변경할 수 있다.
info(age=20, name="민식")

# 가변 인자 *args
def total(*nums):
	print(type(nums)) # Tuple로 받아서 여러 인자를 하나의 매개변수에 담아준다.
	return sum(nums)

total(1,2,3)

# 가변 인자도 일반 매개변수 뒤에 배치한다.
def tot(num, *args):
	print(num, args)
	print(type(args))
	return sum(args)
tot(10, 20, 30)

# TypeError: tot() missing 1 required keyword-only argument: 'num'
def tot(*args, num):
	print(num, args)
	print(type(args))
	return sum(args)
tot(10, 20, 30)

# 가변 인자와 default 값의 위치? 
def tot3(num, age=1000, *args):
	print(num, age, args)
	print(type(args))
	return sum(args)
tot3(10, 20, 30)

# default 값이 가장 마지막에 위치해야 한다.
# 가변 인자는 일반 매개변수 바로 옆에 위치해야 한다.
def tot4(num, *args, age=20):
	print(num, age, args)
	return sum(args)
tot4(1,2,3)

# 여러 개의 Key=Value 인자
def show_info(**kwargs):
	print(type(kwargs)) # dict
	for key, value in kwargs.items():
		print(f"{key} : {value}")

show_info(name="Tim", age=20)
print("---------------")
show_info(name="Tim", age=20, email="test@example.com")

# 리턴값 여러개 -> Tuple로 리턴
def get_name_and_age():
	return "Tim", 20

print(type(get_name_and_age()))
name, age = get_name_and_age()
print(name)
print(age)

# 함수 구현부 생략
def test():
	pass
print("함수 구현부 생략된 추상메서드", test())

def test():
	...
print("함수 구현부 생략된 추상메서드", test())
