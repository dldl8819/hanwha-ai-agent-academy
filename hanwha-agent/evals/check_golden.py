"""골든셋이 지금 DB 와 맞는지 검사한다.

    python evals/check_golden.py
    python evals/check_golden.py --quiet     # 요약만

문서가 개정되면 골든셋의 기대값이 조용히 어긋난다. 번호가 바뀌고, 판이 올라가고,
조항이 옮겨 간다. 그래도 측정은 돌아가고 숫자만 내려간다 — 검색이 나빠진 것처럼 보인다.

이 검사는 임베딩 모델을 부르지 않는다. 전부 DB 조회와 문자열 비교다. 그래서 30문항을
도는 측정보다 훨씬 싸고, 측정을 돌리기 전에 먼저 돌리는 자리에 있다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.db.session import session_scope  # noqa: E402
from app.models.document import Chunk, Document, DocumentVersion  # noqa: E402

GOLDEN = ROOT / "evals" / "golden_set.yaml"


# 검사 하나의 결과 — (심각도, 문항 ID, 항목 번호, 메시지)
# 심각도를 둘로 나눈다
#  - 오류: 그대로 측정하면 채점할 수 없는 문항이 된다. 고치거나 빼야 한다.
#  - 경고: 채점은 되지만 기대값이 시스템 상태와 어긋나 있다.
오류, 경고 = "오류", "경고"


def check_item(item: dict, session) -> list[tuple[str, int, str]]:
    """문항 하나를 여섯 항목으로 검사한다. 돌려주는 것은 (심각도, 항목번호, 메시지) 목록."""
    문제: list[tuple[str, int, str]] = []

    doc_id = item.get("expect_doc")
    # 근거 부족이 정답인 문항은 가리키는 문서가 없다. 검사할 기대값 자체가 없으므로 건너뛴다.
    if not doc_id:
        return 문제

    # ① 문서가 DB 에 있는가
    document = session.get(Document, doc_id)
    if document is None:
        문제.append((오류, 1, f"문서 없음 — 문서 번호가 틀렸거나 문서가 폐기됐다: {doc_id}"))
        return 문제  # 문서가 없으면 아래 항목은 물어볼 대상이 없다

    # ② 기대한 판이 있는가
    기대판 = item.get("expect_version")
    dv = next((v for v in document.versions if v.version == 기대판), None)
    if dv is None:
        있는판 = ", ".join(sorted(v.version for v in document.versions)) or "없음"
        문제.append((오류, 2, f"버전 없음 — 개정으로 번호가 바뀌었다: {기대판} (DB: {있는판})"))
        return 문제

    # ③ 그 판이 현행인가
    # - 과거 판을 일부러 가리키는 문항(needs_past_version)은 현행이 아닌 것이 정상이다.
    #   오히려 현행이 되어 있으면 문항의 의도가 깨진 것이다.
    과거를_묻는가 = bool(item.get("needs_past_version"))
    if 과거를_묻는가 and dv.status == "현행":
        문제.append((경고, 3, f"과거 판을 묻는 문항인데 {기대판} 이 현행이다"))
    elif not 과거를_묻는가 and dv.status != "현행":
        문제.append((경고, 3, f"현행이 아님({dv.status}) — 이전 버전으로 정답을 적어 뒀다"))

    # ④ 그 판에 청크가 있는가
    청크 = session.execute(
        select(Chunk).where(Chunk.version_id == dv.id)
    ).scalars().all()
    if not 청크:
        문제.append((오류, 4, f"청크 0 — 적재되지 않았다 (색인 상태: {dv.index_status})"))
        return 문제  # 청크가 없으면 ⑤⑥ 은 전부 같은 원인으로 걸린다

    # ⑤ expect_kind 가 표인데 표 청크가 있는가
    기대종류 = item.get("expect_kind")
    if 기대종류 and not any(c.kind == 기대종류 for c in 청크):
        종류들 = ", ".join(sorted({c.kind for c in 청크}))
        문제.append((오류, 5, f"'{기대종류}' 청크 없음 — 표가 조항 단위로 잘렸다 (있는 종류: {종류들})"))

    # ⑥ 키워드가 한 청크에 모두 있는가
    # - 흩어져 있으면 채점기가 그 문항을 맞힐 수 없다. judge() 는 청크 하나를 두고
    #   키워드 전부를 보기 때문이다. 어느 조각에도 없으면 원문이 바뀐 것이다.
    키워드 = item.get("expect_keywords") or []
    if 키워드:
        한_청크에_다 = any(all(k in c.text for k in 키워드) for c in 청크)
        if not 한_청크에_다:
            없는것 = [k for k in 키워드 if all(k not in c.text for c in 청크)]
            if 없는것:
                문제.append((오류, 6, f"키워드 사라짐 — 어느 청크에도 없다: {없는것}"))
            else:
                문제.append((경고, 6, f"키워드 흩어짐 — 각각은 있으나 한 청크에 모이지 않는다: {키워드}"))

    return 문제


def main() -> int:
    parser = argparse.ArgumentParser(description="골든셋 기대값이 DB 와 맞는지 검사")
    parser.add_argument("--quiet", action="store_true", help="문항별 줄을 생략하고 요약만")
    args = parser.parse_args()

    data = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))
    items = data["items"]

    전체: list[tuple[str, str, int, str]] = []
    with session_scope() as session:
        for item in items:
            for 심각도, 번호, 메시지 in check_item(item, session):
                전체.append((심각도, item["id"], 번호, 메시지))

    오류수 = sum(1 for s, *_ in 전체 if s == 오류)
    경고수 = len(전체) - 오류수
    문항수 = len({i for _, i, _, _ in 전체})

    print(f"\n골든셋 {len(items)}문항 검사 — 오류 {오류수} · 경고 {경고수} "
          f"(문항 {문항수}개에서)\n")
    if not args.quiet:
        for 심각도, gid, 번호, 메시지 in 전체:
            print(f"  [{심각도}] {gid} ({번호}) {메시지}")
        if 전체:
            print()

    # 항목별로 몇 건인지
    if 전체:
        print("  항목별")
        이름 = {1: "문서 없음", 2: "버전 없음", 3: "현행 아님", 4: "청크 0",
                5: "기대 종류 청크 없음", 6: "키워드 문제"}
        for 번호 in sorted({n for _, _, n, _ in 전체}):
            수 = sum(1 for _, _, n, _ in 전체 if n == 번호)
            print(f"    {번호} {이름[번호]:16} {수:>3}건")
        print()

    # 오류가 있으면 0 이 아닌 값으로 끝낸다 — 측정 전에 멈추게 하려는 것
    return 1 if 오류수 else 0


if __name__ == "__main__":
    raise SystemExit(main())
