# dict
person = {"name": "pikachu", "age":10, "height":230.5}
print(person)

# 키로 값 조회 : [키값], or .get(키값)
print(person["name"])
print(person["age"])
#print(person["address"]) # 없는 키로 값을 조회하면 에러(KeyError) 발생

# get 메서드로 값 조회
print(person.get("name"))
print(person.get("age"))
print(person.get("height")) 

# 없는 키로 조회 시 에러가 발생하지 않고 None 출력됨
print(person.get("address")) # 없는 키 조회 시 None 리턴, 에러가 아님

# 값 수정
person["age"] = 100 # 키가 존재하면 값 수정 가능
print(person)
# print(person[1]) KeyError 발생

# 값 추가
person["email"] = "pika@test.com" # 키가 없으면 값 추가 가능
print(person)
print(person.get("email"))

# 값 삭제
del person["email"]
print(person)

# 키 전체 조회
print(person.keys())
# > dict_keys(['name', 'age', 'height'])
'''
dict_keys([Lists])
- 뷰 객체 
- 보는 용도로만 사용
- 원본을 실제로 보는 것
- 리스트로 사용하고 싶으면 list() 감싸주기 (형 변환)
'''
keys = list(person.keys())
print(keys[0])


# 값 전체 조회
print(person.values())

# 키-값 쌍 조회
print(person.items())

# 키 존재 여부 확인
print("age" in person) # 존재하면 True 리턴
print("address" in person) # 없으면 False 리턴

# 데이터 전체 삭제
person2 = {"name": "민식"}
print(person2)
person2.clear()
print(person2)