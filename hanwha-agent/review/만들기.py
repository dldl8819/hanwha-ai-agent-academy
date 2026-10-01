"""개념 노트와 복습 카드를 오프라인 HTML 한 장으로 묶는다.

    python review/만들기.py

결과는 review/복습.html 하나다. 인터넷 없이 열리도록 글꼴도 스크립트도
바깥에서 불러오지 않는다. 폰에 옮겨서 "홈 화면에 추가" 해 두고 쓴다.

진도(어느 카드를 언제 다시 볼지)는 파일이 아니라 폰 브라우저의 localStorage 에
쌓인다. 그래서 파일을 새로 만들어 덮어써도 진도는 남는다.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS = ROOT / "concepts"
CARDS_MD = ROOT / "review" / "카드.md"
OUT = ROOT / "review" / "복습.html"


def 렌더러():
    from markdown_it import MarkdownIt
    return MarkdownIt("commonmark").enable(["table", "strikethrough"])


def 본문_html(md: str, stems: set[str]) -> str:
    """노트 한 편을 HTML 로. [[위키링크]] 는 같은 페이지 안 이동으로 바꾼다."""
    def 링크(m: re.Match) -> str:
        name = m.group(1)
        if name not in stems:                      # 깨진 링크는 글자 그대로 둔다
            return f"[[{name}]]"
        label = name.split("_", 1)[-1].replace("_", " ")
        return f'<a class="wiki" href="#note-{name}">{label}</a>'

    # 코드블록 안의 [[...]] 까지 링크로 바뀌면 곤란하므로 펜스 밖에서만 친다.
    조각, 안쪽 = [], False
    for line in md.split("\n"):
        if line.lstrip().startswith("```"):
            안쪽 = not 안쪽
        조각.append(line if 안쪽 else re.sub(r"\[\[([^\]]+)\]\]", 링크, line))
    return 렌더러().render("\n".join(조각))


def 카드_읽기(path: Path, stems: set[str]) -> list[dict]:
    """카드.md 를 읽는다.  '## 노트이름' 아래 '### 질문' + 본문(답)."""
    if not path.is_file():
        return []
    카드: list[dict] = []
    노트: str | None = None
    질문: str | None = None
    답: list[str] = []

    def 닫기() -> None:
        if 노트 and 질문:
            카드.append({
                # 질문 글자로 id 를 만든다. 카드를 사이에 끼워 넣어도
                # 기존 카드의 진도가 밀리지 않는다.
                "id": hashlib.sha1(질문.encode("utf-8")).hexdigest()[:10],
                "note": 노트,
                "q": 질문,
                "a": 렌더러().render("\n".join(답).strip()),
                "raw": "\n".join(답).strip(),      # 옵시디언 내보내기가 쓴다
            })

    펜스 = False
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.lstrip().startswith("```"):
            펜스 = not 펜스
        # 코드블록 안의 '##' 은 형식 설명용 예시다. 카드로 잡으면 안 된다.
        if not 펜스 and line.startswith("## "):
            닫기()
            질문, 답 = None, []
            노트 = line[3:].strip()
            if 노트 not in stems:
                print(f"  [경고] 없는 노트를 가리킨다: {노트}")
        elif not 펜스 and line.startswith("### "):
            닫기()
            질문, 답 = line[4:].strip(), []
        elif 질문 is not None:
            답.append(line)
    닫기()
    return 카드


def 스크립트안전(s: str) -> str:
    """<script> 안에 넣을 JSON. 노트 본문에 </script> 나 <!-- 가 있으면
    브라우저가 거기서 스크립트를 끊어 페이지가 통째로 깨진다."""
    return (s.replace("</", "<\\/")
             .replace(" ", "\\u2028")      # 줄 구분자 — JS 에서 줄바꿈으로 읽힌다
             .replace(" ", "\\u2029"))


def 옵시디언_쓰기(카드: list[dict], 순서: list[str]) -> Path:
    """Obsidian 의 Spaced Repetition 플러그인이 읽는 형식으로 따로 내보낸다.

    플러그인은 '질문 / ? / 답' 세 덩이를 카드 하나로 본다. 답에 코드블록과 표가
    들어가므로 한 줄짜리 `질문::답` 형식은 쓸 수 없다.
    """
    out = [
        "---", "tags:", "  - flashcards", "---", "",
        "# 복습 카드", "",
        "`python review/만들기.py --obsidian` 이 `review/카드.md` 에서 만든 파일이다. 직접 고치지 않는다.",
        "",
        "Obsidian → 설정 → 커뮤니티 플러그인에서 **Spaced Repetition** 을 켜고 이 파일을 열면,",
        "왼쪽 리본의 아이콘으로 오늘 볼 카드가 나온다.",
        "",
    ]
    for stem in 순서:
        몫 = [c for c in 카드 if c["note"] == stem]
        if not 몫:
            continue
        번호, _, 이름 = stem.partition("_")
        out += [f"## {번호} {이름.replace('_', ' ')}", ""]
        for c in 몫:
            # 질문 / ? / 답 사이에 빈 줄을 넣지 않는다. 플러그인이 카드 경계로 읽는다.
            out += [c["q"], "?", c["raw"], ""]
    p = ROOT / "review" / "복습카드_옵시디언.md"
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return p


def 페이지_묶음(페이지: str) -> Path:
    """GitHub Pages 에 올릴 폴더를 만든다.

    단일 파일과 내용은 같고, 서비스 워커·manifest·아이콘이 옆에 붙는다.
    아이폰은 로컬 파일을 홈 화면에 추가할 수 없어서, 아이폰에서 앱처럼 쓰려면
    주소가 있어야 한다.
    """
    site = ROOT / "review" / "_site"
    site.mkdir(parents=True, exist_ok=True)
    (site / "index.html").write_text(페이지, encoding="utf-8-sig")

    # 버전이 바뀌면 캐시를 통째로 갈아엎는다. 내용으로 이름을 지어
    # 노트가 하나라도 바뀌면 자동으로 새 캐시가 된다.
    ver = hashlib.sha1(페이지.encode("utf-8")).hexdigest()[:12]
    (site / "sw.js").write_text(
        f'''// 자동 생성 — review/만들기.py --pages
const CACHE = "review-{ver}";
const FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];

self.addEventListener("install", (e) => {{
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).catch(() => {{}}));
}});

// 이름이 다른 옛 캐시는 지운다. 안 그러면 갱신해도 옛 화면이 계속 나온다.
self.addEventListener("activate", (e) => {{
  e.waitUntil(caches.keys().then((ks) =>
    Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
}});

// 캐시를 먼저 주고, 없으면 받아 온다. 오프라인에서도 바로 열리는 게 목적이다.
self.addEventListener("fetch", (e) => {{
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {{
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {{}});
      return res;
    }}).catch(() => caches.match("./index.html")))
  );
}});
''', encoding="utf-8")

    (site / "manifest.webmanifest").write_text(json.dumps({
        "name": "복습 — 한화 아카데미",
        "short_name": "복습",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#111418",
        "theme_color": "#111418",
        "icons": [
            {"src": "icon-180.png", "sizes": "180x180", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    아이콘_쓰기(site)
    (site / ".nojekyll").write_text("", encoding="utf-8")
    return site


def 아이콘_쓰기(site: Path) -> None:
    """홈 화면 아이콘. 없으면 아이폰이 화면을 찍어서 쓴다."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  [건너뜀] Pillow 가 없어 아이콘을 만들지 않았다")
        return
    for size in (180, 512):
        img = Image.new("RGB", (size, size), "#2f6feb")
        d = ImageDraw.Draw(img)
        r = size // 2
        # 가운데 흰 원 하나. 글꼴에 기대지 않아 어디서 만들어도 같게 나온다.
        d.ellipse([r - size // 5, r - size // 5, r + size // 5, r + size // 5],
                  outline="white", width=max(2, size // 22))
        img.save(site / f"icon-{size}.png")


def main() -> int:
    notes = sorted(CONCEPTS.rglob("*.md"), key=lambda p: p.stem)
    if not notes:
        print("개념 노트를 찾지 못했다.")
        return 1
    stems = {p.stem for p in notes}

    묶음 = []
    for p in notes:
        md = p.read_text(encoding="utf-8")
        묶음.append({
            "stem": p.stem,
            "no": p.stem.split("_", 1)[0],
            "title": md.split("\n", 1)[0].lstrip("# ").strip(),
            "group": p.parent.name.split("_", 1)[-1].replace("_", " "),
            "html": 본문_html(md, stems),
        })

    카드 = 카드_읽기(CARDS_MD, stems)
    덮인노트 = {c["note"] for c in 카드}
    빈노트 = [n["no"] for n in 묶음 if n["stem"] not in 덮인노트]

    # raw 는 옵시디언 내보내기 전용이다. 페이지에 넣으면 같은 답이 두 벌 실린다.
    페이지용 = [{k: v for k, v in c.items() if k != "raw"} for c in 카드]
    페이지 = (템플릿
              .replace("/*__NOTES__*/null", 스크립트안전(json.dumps(묶음, ensure_ascii=False)))
              .replace("/*__CARDS__*/null", 스크립트안전(json.dumps(페이지용, ensure_ascii=False)))
              .replace("__BUILT__", date.today().isoformat()))
    # utf-8-sig: BOM 을 붙인다. meta charset 을 무시하는 폰 브라우저가 있어
    # 로컬 파일에서 한글이 깨지는 것을 막는다.
    OUT.write_text(페이지, encoding="utf-8-sig")

    print(f"{OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1024:.0f} KB)")
    print(f"  노트 {len(묶음)}편 · 카드 {len(카드)}장")
    if 빈노트:
        print(f"  카드 없는 노트 {len(빈노트)}편: {', '.join(빈노트)}")

    if "--obsidian" in sys.argv:
        q = 옵시디언_쓰기(카드, [n["stem"] for n in 묶음])
        print(f"{q.relative_to(ROOT)}  ({q.stat().st_size / 1024:.0f} KB)")

    if "--pages" in sys.argv:
        site = 페이지_묶음(페이지)
        총 = sum(f.stat().st_size for f in site.iterdir() if f.is_file())
        print(f"{site.relative_to(ROOT)}/  ({총 / 1024:.0f} KB · "
              f"{', '.join(sorted(f.name for f in site.iterdir() if f.is_file()))})")
    return 0


템플릿 = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#111418">
<!-- 아이폰에서 "홈 화면에 추가" 했을 때 주소창 없이 앱처럼 열리게 한다.
     사파리는 manifest 보다 이 메타 태그를 본다. -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="복습">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="manifest" href="manifest.webmanifest">
<title>복습</title>
<style>
:root{
  --bg:#ffffff; --fg:#16191d; --dim:#5b6470; --line:#e3e6ea;
  --card:#f6f7f9; --accent:#2f6feb; --ok:#1a7f52; --no:#b4483c; --codebg:#f2f3f5;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#111418; --fg:#e8eaed; --dim:#9aa4b0; --line:#272c33;
    --card:#191d23; --accent:#6a9bff; --ok:#54c08a; --no:#ef7a6d; --codebg:#1b1f25;
  }
}
:root[data-theme="dark"]{
  --bg:#111418; --fg:#e8eaed; --dim:#9aa4b0; --line:#272c33;
  --card:#191d23; --accent:#6a9bff; --ok:#54c08a; --no:#ef7a6d; --codebg:#1b1f25;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg); color:var(--fg);
  font:16px/1.75 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",
       "Noto Sans KR",system-ui,sans-serif;
  -webkit-text-size-adjust:100%;
}
.wrap{max-width:720px;margin:0 auto;padding:0 16px 96px}
header{
  position:sticky;top:0;z-index:5;background:var(--bg);
  border-bottom:1px solid var(--line);
  padding:calc(env(safe-area-inset-top) + 10px) 16px 10px;margin:0 0 20px;
}
.bar{display:flex;align-items:center;gap:10px;max-width:720px;margin:0 auto}
.tabs{display:flex;gap:4px;flex:1}
.tab{appearance:none;border:0;background:none;color:var(--dim);
  font:600 15px/1 inherit;padding:9px 12px;border-radius:8px;cursor:pointer}
.tab[aria-selected="true"]{background:var(--card);color:var(--fg)}
.icon{appearance:none;border:1px solid var(--line);background:none;color:var(--dim);
  width:36px;height:36px;border-radius:9px;cursor:pointer;font-size:15px;line-height:1}
.prog{height:3px;background:var(--line);border-radius:2px;margin-top:9px;
  overflow:hidden;max-width:720px;margin-left:auto;margin-right:auto}
.prog i{display:block;height:100%;background:var(--accent);width:0;transition:width .25s}
.meta{color:var(--dim);font-size:13px;margin:0 0 14px}
.q{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:26px 20px;margin:0 0 18px}
.q h2{margin:0;font-size:20px;line-height:1.5;font-weight:650}
.src{margin:14px 0 18px;font-size:13px;color:var(--dim)}
.src a{color:var(--accent);text-decoration:none}
.ans{border-left:3px solid var(--accent);padding:2px 0 2px 16px;margin:0 0 4px}
.ans>*:last-child{margin-bottom:0}
.btn{appearance:none;width:100%;border:1px solid var(--line);background:var(--card);
  color:var(--fg);font:600 16px/1 inherit;padding:16px;border-radius:12px;cursor:pointer}
.btn:active{opacity:.7}
.row{display:flex;gap:10px}
.row .btn{flex:1}
.btn.no{border-color:var(--no);color:var(--no)}
.btn.ok{border-color:var(--ok);color:var(--ok)}
.done{text-align:center;padding:64px 0;color:var(--dim)}
.done b{display:block;color:var(--fg);font-size:19px;margin-bottom:8px}
.grp{margin:26px 0 8px;font-size:13px;font-weight:700;color:var(--dim)}
.item{display:flex;gap:12px;align-items:baseline;padding:13px 2px;
  border-bottom:1px solid var(--line);color:inherit;text-decoration:none}
.item b{color:var(--dim);font:600 13px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;
  min-width:24px}
.note{display:none}
.note.on{display:block}
.back{appearance:none;border:0;background:none;color:var(--accent);
  font:600 15px/1 inherit;padding:10px 0;cursor:pointer;margin-bottom:4px}
.body h1{font-size:23px;margin:8px 0 18px;line-height:1.4}
.body h2{font-size:18px;margin:32px 0 10px;padding-top:14px;border-top:1px solid var(--line)}
.body h3{font-size:16px;margin:24px 0 8px;color:var(--dim)}
.body p{margin:0 0 14px}
.body ul,.body ol{margin:0 0 14px;padding-left:22px}
.body li{margin:0 0 6px}
.body a{color:var(--accent)}
.body strong{font-weight:680}
.body code{background:var(--codebg);border-radius:4px;padding:.12em .35em;
  font:500 .87em/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:break-word}
.body pre{background:var(--codebg);border-radius:10px;padding:14px;margin:0 0 16px;
  overflow-x:auto;-webkit-overflow-scrolling:touch}
.body pre code{background:none;padding:0;font-size:13px;line-height:1.65;white-space:pre}
.body blockquote{margin:0 0 14px;padding-left:14px;border-left:3px solid var(--line);color:var(--dim)}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 16px}
.body table{border-collapse:collapse;font-size:14px;min-width:100%}
.body th,.body td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
.body th{background:var(--card);font-weight:650;white-space:nowrap}
</style>
</head>
<body>
<header>
  <div class="bar">
    <div class="tabs">
      <button class="tab" id="t-card" aria-selected="true">오늘 카드</button>
      <button class="tab" id="t-note" aria-selected="false">노트</button>
    </div>
    <button class="icon" id="theme" title="밝기">&#9689;</button>
  </div>
  <div class="prog"><i id="bar"></i></div>
</header>

<div class="wrap">
  <section id="view-card"></section>
  <section id="view-note" hidden>
    <div id="list"></div>
    <div id="reader"></div>
  </section>
</div>

<script>
/* 식별자는 전부 ASCII 로 둔다.
   폰에서 로컬 파일을 열면 브라우저가 인코딩을 잘못 잡는 경우가 있는데,
   그때 한글 함수·변수 이름이 깨지면 SyntaxError 가 나서 화면이 통째로 빈다.
   문자열 안의 한글은 깨져도 글자만 이상하게 보일 뿐 멈추지 않는다. */
var NOTES = /*__NOTES__*/null;
var CARDS = /*__CARDS__*/null;
var BUILT = "__BUILT__";

/* 무엇이든 던지면 빈 화면 대신 이유를 보여 준다. */
function fail(e) {
  var v = document.getElementById("view-card");
  if (!v) return;
  v.innerHTML = '<div class="done"><b>화면을 그리지 못했습니다</b>'
    + '<code style="font-size:12px">' + String(e && e.message ? e.message : e) + '</code></div>';
}
window.onerror = function (msg) { fail(msg); };

/* 진도 저장. localStorage 는 비공개 모드 등에서 던질 수 있어 전부 감싼다.
   못 쓰면 진도만 사라지고 화면은 그대로 돈다. */
var KEY = "review.v1";
var S = { box: {}, due: {}, seen: [], day: "" };
try {
  var saved = JSON.parse(localStorage.getItem(KEY) || "{}");
  for (var k in saved) if (saved.hasOwnProperty(k)) S[k] = saved[k];
} catch (e) {}
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }

var STEPS = [1, 3, 7, 21, 60];   // 상자별로 며칠 뒤에 다시 보나
var NEW_PER_DAY = 10;            // 하루에 새로 꺼내는 장수

/* Intl 을 쓰지 않는다. 구형 웹뷰는 로케일 데이터가 빠져 있어
   toLocaleDateString 이 엉뚱한 형식을 돌려줄 수 있다. */
function ymd(d) {
  var m = d.getMonth() + 1, day = d.getDate();
  return d.getFullYear() + "-" + (m < 10 ? "0" + m : m) + "-" + (day < 10 ? "0" + day : day);
}
function today() { return ymd(new Date()); }
function addDays(n) { var d = new Date(); d.setDate(d.getDate() + n); return ymd(d); }

function dueToday() {
  var t = today();
  if (S.day !== t) { S.day = t; S.seen = []; save(); }   // 날이 바뀌면 새 카드 배정을 리셋
  var review = [], fresh = [];
  for (var i = 0; i < CARDS.length; i++) {
    var c = CARDS[i];
    if (!S.due[c.id]) fresh.push(c);
    else if (S.due[c.id] <= t) review.push(c);
  }
  var room = NEW_PER_DAY - S.seen.length;
  if (room < 0) room = 0;
  return review.concat(fresh.slice(0, room));
}

var queue = [], cur = null, shown = false, batch = 0;

function drawCard() {
  var v = document.getElementById("view-card");
  if (!CARDS || !CARDS.length) {
    v.innerHTML = '<div class="done"><b>카드가 아직 없습니다</b>'
      + 'review/카드.md 에 추가한 뒤 다시 만드세요.</div>';
    setBar(0, 1); return;
  }
  if (!cur) {
    queue = dueToday();
    batch = queue.length;
    if (!queue.length) {
      var rest = [];
      for (var id in S.due) if (S.due[id]) rest.push(S.due[id]);
      rest.sort();
      v.innerHTML = '<div class="done"><b>오늘 몫은 끝났습니다</b>'
        + (rest.length ? "다음 복습 : " + rest[0] : "") + "</div>";
      setBar(1, 1); return;
    }
    cur = queue[0]; shown = false;
  }
  var c = cur, n = null;
  for (var i = 0; i < NOTES.length; i++) if (NOTES[i].stem === c.note) n = NOTES[i];
  setBar(batch - queue.length, batch);

  var h = '<p class="meta">남은 카드 ' + queue.length + "장</p>"
        + '<div class="q"><h2>' + esc(c.q) + "</h2></div>";
  if (shown) {
    h += '<div class="ans body">' + c.a + "</div>"
       + '<p class="src"><a href="#note-' + encodeURIComponent(c.note) + '">'
       + (n ? esc(n.no + " " + n.title) : esc(c.note)) + " 원문 보기 &rarr;</a></p>"
       + '<div class="row"><button class="btn no" id="b-no">몰랐다</button>'
       + '<button class="btn ok" id="b-ok">알았다</button></div>';
  } else {
    h += '<button class="btn" id="b-show">답 보기</button>';
  }
  v.innerHTML = h;
  wrapTables(v);

  var s = document.getElementById("b-show");
  if (s) s.onclick = function () { shown = true; drawCard(); };
  var no = document.getElementById("b-no");
  if (no) no.onclick = function () { grade(false); };
  var ok = document.getElementById("b-ok");
  if (ok) ok.onclick = function () { grade(true); };
  window.scrollTo(0, 0);
}

function grade(right) {
  var id = cur.id;
  var prev = (S.box[id] === undefined) ? -1 : S.box[id];
  var b = right ? Math.min(prev + 1, STEPS.length - 1) : 0;
  S.box[id] = b;
  S.due[id] = addDays(STEPS[b]);
  if (S.seen.indexOf(id) < 0) S.seen.push(id);
  save();
  var left = [];
  for (var i = 0; i < queue.length; i++) if (queue[i].id !== id) left.push(queue[i]);
  queue = left;
  cur = queue.length ? queue[0] : null;
  shown = false;
  drawCard();
}

function setBar(done, total) {
  document.getElementById("bar").style.width =
    total ? Math.round(done / total * 100) + "%" : "0";
}

function drawList() {
  var groups = {}, order = [];
  for (var i = 0; i < NOTES.length; i++) {
    var n = NOTES[i];
    if (!groups[n.group]) { groups[n.group] = []; order.push(n.group); }
    groups[n.group].push(n);
  }
  var out = "";
  for (var g = 0; g < order.length; g++) {
    var arr = groups[order[g]];
    out += '<div class="grp">' + esc(order[g]) + "</div>";
    for (var j = 0; j < arr.length; j++) {
      out += '<a class="item" href="#note-' + encodeURIComponent(arr[j].stem) + '">'
           + "<b>" + esc(arr[j].no) + "</b><span>" + esc(arr[j].title) + "</span></a>";
    }
  }
  document.getElementById("list").innerHTML = out;
}

function openNote(stem) {
  var n = null;
  for (var i = 0; i < NOTES.length; i++) if (NOTES[i].stem === stem) n = NOTES[i];
  if (!n) { closeNote(); return; }
  setTab(1);
  document.getElementById("list").style.display = "none";
  var r = document.getElementById("reader");
  r.className = "note on";
  r.innerHTML = '<button class="back" id="back">&larr; 목록</button>'
              + '<div class="body">' + n.html + "</div>";
  document.getElementById("back").onclick = function () { location.hash = ""; };
  wrapTables(r);
  window.scrollTo(0, 0);
}

function closeNote() {
  document.getElementById("list").style.display = "";
  var r = document.getElementById("reader");
  r.className = ""; r.innerHTML = "";
}

/* NodeList.forEach 는 구형 안드로이드 웹뷰에 없다. 인덱스로 돈다.
   살아 있는 컬렉션이 아니므로 뒤에서부터 돌 필요는 없다. */
function wrapTables(el) {
  var ts = el.getElementsByTagName("table");
  for (var i = ts.length - 1; i >= 0; i--) {
    var t = ts[i];
    if (t.parentNode && t.parentNode.className === "tablewrap") continue;
    var w = document.createElement("div");
    w.className = "tablewrap";
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  }
}

function setTab(i) {
  document.getElementById("t-card").setAttribute("aria-selected", i === 0);
  document.getElementById("t-note").setAttribute("aria-selected", i === 1);
  document.getElementById("view-card").hidden = i !== 0;
  document.getElementById("view-note").hidden = i !== 1;
}
document.getElementById("t-card").onclick = function () {
  if (location.hash) location.hash = "";
  closeNote(); setTab(0); drawCard();
};
document.getElementById("t-note").onclick = function () {
  if (location.hash) location.hash = "";
  closeNote(); setTab(1);
};

function onHash() {
  var m = /^#note-(.+)$/.exec(location.hash);
  if (m) openNote(decodeURIComponent(m[1]));
  else closeNote();
}
if (window.addEventListener) window.addEventListener("hashchange", onHash);
else window.onhashchange = onHash;

var TK = "review.theme", themed = null;
try { themed = localStorage.getItem(TK); } catch (e) {}
if (themed) document.documentElement.setAttribute("data-theme", themed);
document.getElementById("theme").onclick = function () {
  var now = document.documentElement.getAttribute("data-theme");
  var dark = now ? now === "dark"
                 : (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches);
  var next = dark ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem(TK, next); } catch (e) {}
};

function esc(s) {
  return String(s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

/* 서비스 워커. 한 번 열어 두면 그 뒤로는 인터넷 없이 열린다.
   file:// 로 연 단일 파일에서는 등록이 안 되므로(브라우저가 막는다) 조용히 건너뛴다. */
if (location.protocol !== "file:" && navigator.serviceWorker) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").catch(function () {});
  });
}

try {
  drawList();
  drawCard();
  onHash();
} catch (e) {
  fail(e);
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
