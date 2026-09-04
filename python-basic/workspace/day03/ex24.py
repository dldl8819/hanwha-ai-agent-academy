import os 
# 현재 작업 중인 디렉토리 경로 확인
# os.getcwd()
print(os.getcwd()) 

# 나의 위치 찾기
# Path(__file__).resolve().parent
from pathlib import Path

print(Path(__file__).resolve())   # 파일 경로 
print(Path(__file__).resolve().parent) # 파일의 부모 
print(Path(__file__).resolve().parent.parent) # 파일의 2단계 상위 (우리 폴더 구조에서는 ROOT)

ROOT = Path(__file__).resolve().parent.parent
target = ROOT / "Heifam.txt"

# 파일 존재 여부 확인 후 읽기 (없으면 FileNotFoundError 발생 방지)
if os.path.exists(target):
    with open(target, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("파일이 없습니다")