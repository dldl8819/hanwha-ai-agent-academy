heifam: list[str] = ["Youtube", "Soop", "Instargram"]
print(heifam[0])

heifam_member: tuple[str, str, str] = 'minsik', 'daha', 'daeha'
print(heifam_member)

nums: tuple[int, ...] = 10, 20, 30
print(nums)

tim:dict[str, object] = {
    'name'  : 'minsik',
    'age'   : 20,
    'is_stu': True
}

print(tim)
print(tim['name'])
print(tim.get('name'))

# Set (집합)
numbers: set[int] = {1, 2, 2, 3, 4}
print(numbers)

# 동적 타입
x: int | str = 10
print(x)
x = "hello"
print(x)
