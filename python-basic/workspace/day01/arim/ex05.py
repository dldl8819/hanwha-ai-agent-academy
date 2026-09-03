# dict 
person = {"name": "pikachu", "age": 10, "height": 230.5}
print(person)

# 키로 값 조회 : [키값] or .get(키값)
print(person["name"])
# print(person["address"]) # 없는 키 조회시 에러 발생 
print(person.get("name"))
print(person.get("address")) # 없는 키 조회시 None 리턴, 에러 X

# 값 수정 
person["age"] = 100  # 키가 존재하면 값 수정 
print(person)
person["email"] = "pika@test.com" # 키가 없으면 추가 
print(person)

# 값 삭제
del person["email"] 
print(person) 

# 키값 전체 조회 
print(person.keys()) 
# > dict_keys(['name', 'age', 'height'])
# dict_keys([리스트]) -> 뷰 객체 (보는 용도) 
# 리스트로 사용하고 싶으면 list() 감싸주기 (형변환)
# keys = list(person.keys())
# keys[0]

# 값 전체 조회 
print(person.values())
# 키-값 쌍 조회 
print(person.items())

# 키 존재 여부 확인 : 존재하면 True 리턴
print("age" in person)

# 데이터 전체 삭제 
person.clear() 
print(person)