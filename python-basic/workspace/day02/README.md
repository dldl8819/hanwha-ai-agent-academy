# Day 02 진행 상황

## 어제 복습 문제 풀이
어제(day01) 숙제로 받은 while문 복습 문제 5개를 오늘 [day01/ex09.py](../day01/ex09.py)에 풀이로 정리했다.

```python
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
    if i % 2 == 1:
        print(i)
    i += 1

# 문제4. 1 ~ 50까지의 총 합을 출력.
i = 1
total = 0
while i <= 50:
    total += i
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
```

## 오늘 배운 내용

### for문과 반복 ([ex11.py](ex11.py))
- list, 문자열 반복: `for x in 컬렉션`
- `range(start, stop, step)`으로 범위 지정 반복
- dict 반복: `for k in dic`(키만), `for v in dic.values()`(값만), `for k, v in dic.items()`(키-값 쌍, 가장 많이 사용)
- `enumerate(iterable, start=0)`으로 인덱스 + 값을 함께 순회
- 패킹/언패킹: `a, b, c = [1,2,3]`, `nums = 10, 20`처럼 괄호 없이도 튜플 패킹 가능
- 데이터 스왑: `int1, int2 = int2, int1` (임시변수 없이 교환)

### 리스트 컴프리헨션 ([ex12.py](ex12.py))
- 기본형: `[식 for 변수 in 리스트]` → for문보다 짧게 새 리스트 생성
- 조건 포함: `[식 for 변수 in 리스트 if 조건]`
- 문자열 처리: `[word.upper() for word in words]`
- 중첩 for문으로 다중 리스트(matrix) 풀어서 1차원으로 만들기
- 보조 제어문 복습: `break`(반복 종료), `continue`(현재 회차만 건너뛰기)
