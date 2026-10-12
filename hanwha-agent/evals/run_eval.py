# 골든셋 30문항으로 검색 정확도를 측정하는 채점기

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 어느 폴더에서 실행해도 app 패키지를 찾도록 backend 를 import 경로 맨 앞에 넣는다
# - PYTHONPATH=backend 를 터미널에서 따로 주지 않아도 된다
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"backend"))

import yaml

from app.core.config import get_settings
from app.db.session import session_scope
from app.integrations.factory import get_embedder
from app.models import EvalRun
from app.rag import policy, store

settings = get_settings()
GOLDEN = Path(__file__).parent / "golden_set.yaml"
REPORTS = Path(__file__).parent / "reports"
DEFAULT_TOP_N = 3 # 상위 몇 건 안에 들어오면 맞는 것으로 볼 것인가

# 설정 목록
# - 같은 골든셋으로 비교할 검색 설정들. 설정 하나가 eval_runs 의 한 줄(막대 하나)이 된다
CONFIGS = [{"name": "기본 검색"}]

# 관리자 시각으로 테스트
# - 검색 결과는 사용자 등급에 따라 달라지므로 한 사람으로 고정해야 점수를 비교할 수 있다
# - 대외비는 CLEARANCE 에서 가장 높은 등급이라 등급 때문에 가려지는 문서가 없다
EVAL_USER = {"id": "2011-0003", "name": "한서영", "clearance": "대외비", "dept_id": "HR"}

# 질문 하나로 후보를 뽑고 정책으로 거른 뒤, 상위 N건만 남기는 함수
def retrieve(session, question: str, top_n: int) -> list[dict]:
    embedder = get_embedder()
    # 벡터 검색은 넉넉히(retrieval_top_k) 뽑는다. 정책에서 걸러지고 나면 줄어들기 때문이다
    rows = store.vector_search(session, embedder.embed_query(question), limit=settings.retrieval_top_k)
    # 두 번째 반환값(걸러낸 사유)은 채점에 쓰지 않아 _ 로 버린다
    kept, _ = policy.filter_candidates(rows, user=EVAL_USER, question=question)
    return kept[:top_n]

# 문항 1개를 채점하는 함수
# - 반환값: (정답 여부, 사유). 사유는 리포트에 그대로 남아 왜 틀렸는지 보여 준다
def judge(item: dict, hits: list[dict], threshold: float) -> tuple[bool, str]:
    # 상위 N건 중 가장 높은 점수. 결과가 한 건도 없으면 0.0
    best = max((h["score"] for h in hits), default=0.0)
    # 규정에 없는 질문은 거꾸로 채점한다. 점수가 임계값 아래여야(근거 부족) 정답
    if item.get("unanswerable"):
        ok = best < threshold
        return ok, "근거 부족 정상" if ok else f"임계값 초과({best:.2f}) - 지어낼 위험"

    # 답이 있는 질문인데 점수가 낮으면 '근거 부족'으로 답하게 되므로 오답
    if best < threshold:
        return False, f"임계값 미달({best:.2f})"

    # 상위 N건 중 한 건이라도 문서·판·종류·키워드 조건을 모두 채우면 정답
    # - 골든셋에 적지 않은 조건(expect_version 등)은 검사하지 않고 넘어간다
    for h in hits:
        if h.get("doc_id") != item.get("expect_doc"):
            continue
        if item.get("expect_version") and h.get("version") != item["expect_version"]:
            continue
        if item.get("expect_kind") and h.get("kind") != item["expect_kind"]:
            continue
        # 키워드는 한 청크 안에 전부 있어야 한다. 여러 청크에 나뉘어 있으면 인정하지 않는다
        keywords = item.get("expect_keywords") or []
        if keywords and not all(k in h.get("text", "") for k in keywords):
            continue
        return True, f"{h['doc_id']} {h['version']} {h['locator']}"

    return False, "정답 문서가 상위에 없음"

# 설정 하나로 골든셋 문항을 전부 테스트하고, 결과를 하나로 모아주는 함수
def run_config(cfg: dict, items: list[dict], top_n: int) -> dict:
    results = []
    # 세션 하나로 30문항을 모두 검색한다
    with session_scope() as session:
        for item in items:
            hits = retrieve(session, item["question"], top_n)
            ok, why = judge(item, hits, settings.retrieval_threshold)
            results.append({"id": item["id"], "type": item.get("type", ""), 
                            "question": item["question"], "ok": ok, "why": why})

    # 전체 정답률 (0~100, 소수 첫째 자리)
    correct = sum(1 for r in results if r["ok"])
    accuracy = round(correct / len(results) * 100, 1) if results else 0.0

    # 유형별 집계: {"단일 조항": {"n": 문항 수, "ok": 맞힌 수}, ...}
    # - 어느 유형에서 약한지 보려고 따로 센다
    by_type: dict[str, dict] = {}
    for r in results:
        bucket = by_type.setdefault(r["type"], {"n": 0, "ok": 0})
        bucket["n"] += 1
        bucket["ok"] += 1 if r["ok"] else 0

    return {"config": cfg["name"], "accuracy": accuracy, "correct": correct,
            "total": len(results), "by_type": by_type, "results": results}

# 리포트 파일 남기고 총점만 eval_runs DB 테이블에 저장
def save(report: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS / f"eval_{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    with session_scope() as session:
        session.query(EvalRun).delete()
        for i, run in enumerate(report["runs"]):
            session.add(EvalRun(config=run["config"], ord=i, accuracy=run["accuracy"],
                                item_count=run["total"], measured_at=datetime.now()))
    return path

def main() -> int:
    parser = argparse.ArgumentParser(description="골든셋 정확도 측정")
    parser.add_argument("--config", help="한 가지 설정만 측정")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--no-save", action="store_true", help="DB, 파일에 남기지 않음")
    args = parser.parse_args()

    items = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))["items"]
    configs = [c for c in CONFIGS if not args.config or c["name"] == args.config]
    if not configs:
        print(f"알 수 없는 설정 : {args.config}")
        return 1

    print(f"\n 문항 {len(items)}개. 임계값 {settings.retrieval_threshold}. 상위 {args.top_n}건\n")
    runs = []
    for cfg in configs:
        run = run_config(cfg, items, args.top_n)
        runs.append(run)
        print(f" {run['config']:16} {run['accuracy']:5.1f}% ({run['correct']}/{run['total']})")
        for type_name, bucket in sorted(run["by_type"].items()):
            rate = bucket["ok"] / bucket["n"] * 100
            print(f"   {type_name:22} {rate:5.1f}% ({bucket['ok']}/{bucket['n']})")
        print()

    report = {"measured_at": datetime.now().isoformat(timespec="seconds"),
              "threshold": settings.retrieval_threshold, "top_n": args.top_n, "runs": runs}

    if not args.no_save:
        print(f"  리포트: {save(report)}\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())