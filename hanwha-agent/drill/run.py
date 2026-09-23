"""drill 러너 — 문제를 고르고, 풀고, 채점한다.

사용법
    python drill/run.py 목록
    python drill/run.py 풀기 28_가드
    python drill/run.py 채점 28_가드
    python drill/run.py 검증              # 문제 자체가 멀쩡한지 확인 (원본 코드로 채점해 본다)

설계 메모
    화면(Streamlit)이 얇아지려면 판정이 전부 여기 있어야 한다.
    그래서 CLI 는 아래 함수들이 돌려주는 dict 를 출력만 한다.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 윈도우 콘솔 기본 코드페이지(cp949)로는 — 같은 글자에서 터진다
# - 한글 문제 이름과 표를 그대로 찍기 위해 출력 스트림을 UTF-8 로 맞춘다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

DRILL = Path(__file__).resolve().parent
PROBLEMS = DRILL / "problems"
WORK = DRILL / "작업"
ROOT = DRILL.parent                      # hanwha-agent/

# 시작.py 에서 "머리말"과 "직접 채우는 부분"을 가르는 줄
# - 채점에는 쓰지 않는다. 검증(원본 코드 붙여넣기)과 사람 눈에만 쓰인다
MARKER = "# ══════ 여기부터 직접 채운다 ══════"


# ── 문제 읽기 ────────────────────────────────────────────────

def _메타(문제id: str) -> dict:
    path = PROBLEMS / 문제id / "문제.json"
    if not path.exists():
        raise SystemExit(f"그런 문제가 없습니다 : {문제id}\n  python drill/run.py 목록")
    return json.loads(path.read_text(encoding="utf-8"))


def 목록() -> list[dict]:
    """문제 전부를 번호순으로. 푼 흔적이 있으면 표시한다."""
    out = []
    for d in sorted(PROBLEMS.iterdir()) if PROBLEMS.exists() else []:
        if not (d / "문제.json").exists():
            continue
        meta = json.loads((d / "문제.json").read_text(encoding="utf-8"))
        out.append({
            "id": d.name,
            "제목": meta.get("제목", d.name),
            "개념": meta.get("개념", ""),
            "작업중": (WORK / d.name / "시작.py").exists(),
        })
    return out


# ── 원본에서 정답 조각 꺼내기 ─────────────────────────────────
# 정답 파일을 따로 저장하지 않는다. 필요할 때 원본에서 이름으로 잘라 온다.
# 줄 번호가 아니라 이름으로 찾으므로 위쪽 코드가 밀려도 안 깨진다.

def _조각(path: Path, 이름들: list[str]) -> dict[str, str]:
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    tree = ast.parse(src)
    found: dict[str, str] = {}

    def 담기(name: str, first: int, last: int) -> None:
        start = first - 1
        # 바로 위에 붙은 주석도 같이 가져온다 — "왜 그렇게 짰는지"가 거기 있다
        while start > 0 and lines[start - 1].lstrip().startswith("#"):
            start -= 1
        found[name] = "\n".join(lines[start:last]).rstrip()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in 이름들:
                first = min([node.lineno] + [d.lineno for d in node.decorator_list])
                담기(node.name, first, node.end_lineno)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in 이름들:
                    담기(t.id, node.lineno, node.end_lineno)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id in 이름들:
                담기(node.target.id, node.lineno, node.end_lineno)

    빠진 = [n for n in 이름들 if n not in found]
    if 빠진:
        raise SystemExit(f"원본 {path} 에서 찾지 못했습니다 : {', '.join(빠진)}")
    return {n: found[n] for n in 이름들}


def _원본조각(meta: dict) -> dict[str, str]:
    정답 = meta["정답"]
    return _조각(ROOT / 정답["파일"], 정답["함수"])


# ── 풀기 ─────────────────────────────────────────────────────

def 풀기(문제id: str, *, 다시: bool = False) -> dict:
    """작업 폴더에 시작.py 를 깔아준다. 이미 있으면 건드리지 않는다."""
    meta = _메타(문제id)
    src = PROBLEMS / 문제id / "시작.py"
    work = WORK / 문제id
    work.mkdir(parents=True, exist_ok=True)
    dst = work / "시작.py"

    있었나 = dst.exists()          # 복사하고 나면 항상 있으므로 먼저 본다
    if 있었나 and not 다시:
        상태 = "이미 있어 그대로 둡니다 (다시 받으려면 --다시)"
    else:
        shutil.copy2(src, dst)
        상태 = "처음부터 다시 받았습니다" if 있었나 else "새로 받았습니다"

    return {
        "문제": 문제id,
        "제목": meta.get("제목", 문제id),
        "파일": str(dst),
        "요구사항": str(PROBLEMS / 문제id / "요구사항.md"),
        "상태": 상태,
    }


# ── 채점 ─────────────────────────────────────────────────────

def _pytest(폴더: Path) -> tuple[bool, str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=폴더, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return p.returncode == 0, (p.stdout or "") + (p.stderr or "")


def _diff(내것: str, 원본: str, 이름: str) -> str:
    d = difflib.unified_diff(
        내것.splitlines(), 원본.splitlines(),
        fromfile=f"{이름} (내 답안)", tofile=f"{이름} (원본)", lineterm="", n=2,
    )
    body = "\n".join(d)
    return body if body else f"{이름} : 원본과 같습니다"


def 채점(문제id: str) -> dict:
    """pytest 로 채점하고, 통과하면 원본과의 diff 까지 만들어 돌려준다."""
    meta = _메타(문제id)
    work = WORK / 문제id
    답안 = work / "시작.py"
    if not 답안.exists():
        raise SystemExit(f"아직 안 받았습니다. 먼저 :\n  python drill/run.py 풀기 {문제id}")

    # 채점기는 매번 새로 덮어쓴다 — 고쳐서 통과시키는 일이 없도록
    shutil.copy2(PROBLEMS / 문제id / "test_문제.py", work / "test_문제.py")

    통과, 출력 = _pytest(work)

    diffs = None
    if 통과:
        원본 = _원본조각(meta)
        내것 = _조각(답안, meta["정답"]["함수"])
        diffs = {n: _diff(내것[n], 원본[n], n) for n in 원본}

    return {
        "문제": 문제id,
        "제목": meta.get("제목", 문제id),
        "통과": 통과,
        "출력": 출력.strip(),
        "diff": diffs,
        "개념": meta.get("개념", ""),
    }


# ── 검증 : 문제 자체가 멀쩡한가 ───────────────────────────────
# 원본 코드를 그대로 넣었을 때 통과하지 않으면, 틀린 것은 푸는 사람이 아니라 문제다.

def 검증(문제id: str) -> dict:
    meta = _메타(문제id)
    시작 = (PROBLEMS / 문제id / "시작.py").read_text(encoding="utf-8")
    if MARKER not in 시작:
        raise SystemExit(f"{문제id}/시작.py 에 구분선이 없습니다 : {MARKER}")

    머리말 = 시작.split(MARKER)[0]
    본문 = "\n\n\n".join(_원본조각(meta).values())

    # 작업 폴더가 아니라 시스템 임시 폴더에 푼다
    # - 답안을 쓰는 drill/작업/ 안에 검증 찌꺼기가 섞이면 어디를 고쳐야 할지 헷갈린다
    tmp = Path(tempfile.gettempdir()) / "drill_검증" / 문제id
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "시작.py").write_text(머리말 + MARKER + "\n\n" + 본문 + "\n", encoding="utf-8")
    shutil.copy2(PROBLEMS / 문제id / "test_문제.py", tmp / "test_문제.py")

    통과, 출력 = _pytest(tmp)
    return {"문제": 문제id, "통과": 통과, "출력": 출력.strip()}


# ── 출력 ─────────────────────────────────────────────────────

def _print_목록(rows: list[dict]) -> None:
    if not rows:
        print("문제가 없습니다.")
        return
    print(f"{'문제':<16} {'상태':<6} 제목")
    print("-" * 68)
    for r in rows:
        print(f"{r['id']:<16} {'작업중' if r['작업중'] else '':<6} {r['제목']}")
    print(f"\n{len(rows)}문제.  python drill/run.py 풀기 <문제>")


def _print_채점(r: dict) -> None:
    print(f"\n{r['문제']} — {r['제목']}")
    print("=" * 68)
    print(r["출력"])
    if not r["통과"]:
        print("\n아직입니다. 위 실패 사유를 보고 고쳐서 다시 채점하세요.")
        return
    print("\n통과했습니다. 이제 원본과 대봅니다 — 통과가 곧 잘 쓴 코드는 아닙니다.\n")
    for 이름, d in (r["diff"] or {}).items():
        print("-" * 68)
        print(d)
    if r["개념"]:
        print("-" * 68)
        print(f"개념 노트 : {r['개념']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="drill — 스스로 코드를 쓰게 하는 연습 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("목록")
    p_s = sub.add_parser("풀기"); p_s.add_argument("문제"); p_s.add_argument("--다시", action="store_true")
    p_g = sub.add_parser("채점"); p_g.add_argument("문제")
    p_v = sub.add_parser("검증"); p_v.add_argument("문제", nargs="?")
    a = ap.parse_args()

    if a.cmd == "목록":
        _print_목록(목록())

    elif a.cmd == "풀기":
        r = 풀기(a.문제, 다시=a.다시)
        print(f"{r['문제']} — {r['제목']}")
        print(f"  요구사항 : {r['요구사항']}")
        print(f"  답안 파일 : {r['파일']}  ({r['상태']})")
        print(f"\n다 쓰면 :  python drill/run.py 채점 {r['문제']}")

    elif a.cmd == "채점":
        r = 채점(a.문제)
        _print_채점(r)
        sys.exit(0 if r["통과"] else 1)

    elif a.cmd == "검증":
        대상 = [a.문제] if a.문제 else [r["id"] for r in 목록()]
        실패 = []
        for 문제id in 대상:
            r = 검증(문제id)
            print(f"  {'OK  ' if r['통과'] else '실패'} {문제id}")
            if not r["통과"]:
                실패.append(r)
        print(f"\n{len(대상) - len(실패)}/{len(대상)} 통과")
        for r in 실패:
            print("\n" + "=" * 68)
            print(r["문제"])
            print(r["출력"])
        sys.exit(1 if 실패 else 0)


if __name__ == "__main__":
    main()
