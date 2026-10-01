"""받아 둔 임베딩 모델 둘을 같은 문장쌍에 걸어 점수를 비교한다.

    python sandbox/w5/day03/embed_compare.py
"""
import os

# sentence_transformers 는 import 될 때 이 값을 읽는다.
# 그래서 아래쪽 import 보다 먼저 설정해야 오프라인으로 돈다.
os.environ["HF_HUB_OFFLINE"] = "1"

from pathlib import Path

# 이 파일이 sandbox/w5/day03/ 에 있으므로 parents[3] 이 저장소 루트다.
# cwd 가 아니라 __file__ 을 기준으로 잡아야 어디서 실행해도 같은 곳을 본다.
ROOT = Path(__file__).resolve().parents[3]
MODELS = ROOT.parent / "models"        # 저장소 밖. 4.3GB 라 커밋하지 않는다
KURE = MODELS / "KURE-v1"
BGE = MODELS / "bge-m3"

# 사람이 먼저 답을 적어 둔 문장쌍. 점수만 보면 잘한 것처럼 보이므로
# 무엇이 나와야 하는지를 고정하고 나서 모델을 돌린다.
PAIRS = [
    ("광역시 숙박비 상한", "잠자리 비용 한도", "같은 뜻"),
    ("출장 전에 신청서를 낸다", "출장은 사전 신청이 원칙이다", "같은 뜻"),
    ("법인카드로 결제한다", "법인카드 사용 지침을 따른다", "가까움"),
    ("일비는 하루 단위로 준다", "숙박비는 1박 단위로 준다", "가까움"),
    ("출장 신청서를 낸다", "재택근무를 신청한다", "다름"),
    ("숙박비 상한액", "정보보안 지침 위반", "남남"),
]

def main() -> None:
    if not (KURE.is_dir() and BGE.is_dir()):
        print("모델 폴더를 찾지 못했습니다. 경로를 확인해주세요.")
        print(f" {KURE}")
        print(f" {BGE}")
        return

    # 함수 안에서 import 한다. 파일 맨 위에 두면 위의 환경변수 설정보다
    # 먼저 실행될 수 있어 오프라인 설정이 먹지 않는다.
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim

    sents = [s for a, b, _ in PAIRS for s in (a, b)]
    for name, path in (("KURE-v1", KURE), ("bge-m3", BGE)):
        # 이름이 아니라 폴더 경로를 준다. 이름을 주면 저장소에 접속한다.
        model = SentenceTransformer(str(path))
        # 정규화해서 받으므로 크기가 모두 1이다. 이 경우 cos_sim 이 나누는
        # 두 크기가 1이라 내적과 값이 같다.
        v = model.encode(sents, normalize_embeddings=True)
        print(f"[{name}] 차원 {model.get_embedding_dimension()} - 모양 {v.shape}")
        for i, (a, b, label) in enumerate(PAIRS):
            score = float(cos_sim(v[i*2], v[i*2 + 1]))
            print(f" {score:+.4f}  {label:4s} {a} / {b}")

if __name__ == "__main__":
    main()