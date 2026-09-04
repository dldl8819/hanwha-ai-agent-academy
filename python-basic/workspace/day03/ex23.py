# 전체 읽기
with open('Heifam.txt', 'r', encoding='utf-8') as f:
    data = f.read()
    print(data)

print("-" * 40)

# 한 줄씩 읽기
with open('Heifam.txt', 'r', encoding='utf-8') as f:
    line1 = f.readline()
    line2 = f.readline()
    print(line1)
    print(line2)

print("-" * 40)

# 모든 줄 리스트로 읽기
with open('heifam.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(lines)

print("-" * 40)

# 한 줄씩 for문으로 읽기
# strip() 사용해보기
with open('Heifam.txt', 'r', encoding='utf-8') as f:
    for line in f:
        print(line.strip())