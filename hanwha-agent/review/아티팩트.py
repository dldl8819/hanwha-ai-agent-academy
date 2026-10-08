# -*- coding: utf-8 -*-
"""개념 노트와 회상 카드를 Claude 아티팩트용 HTML 한 장으로 묶는다.

`만들기.py` 와 재료는 같고 담는 그릇이 다르다.

| | 만들기.py | 아티팩트.py |
| --- | --- | --- |
| 결과 | `복습.html` — 파일로 옮겨 연다 | 아티팩트로 올려 주소로 연다 |
| 진도 | 브라우저 localStorage — 기기마다 따로 | `db` 기능 — 기기 사이에 이어진다 |
| 기록 | 다음에 볼 날짜뿐 | 날짜별 학습량 · 카드별 오답 · 노트별 약점 |

    python review/아티팩트.py

쓰고 나면 그 파일을 아티팩트로 올린다. 카드가 늘면 다시 만들어 같은 주소에 올린다.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = ROOT / "concepts"
CARDS_MD = ROOT / "review" / "카드.md"
OUT = ROOT / "review" / "복습_아티팩트.html"

# 상자별로 며칠 뒤에 다시 보나. 틀리면 0번 상자로 돌아간다.
STEPS = [1, 3, 7, 21, 60]
NEW_PER_DAY = 10


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
        return f'<a class="wiki" href="#" onclick="openNote(&#39;{name}&#39;);return false;">{label}</a>'

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


템플릿 = r"""<title>에이전트 과정 복습</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600&family=Gowun+Batang:wght@400;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 레이아웃 — 상단 고정 탭 + 한 칼럼(최대 660px). 카드는 앞뒤로 뒤집는 한 장. */
:root {
  --paper:   #f6f5f1;
  --card:    #fffefb;
  --ink:     #1d2321;
  --dim:     #6b7471;
  --line:    #ddddd4;
  --accent:  #0e6b60;
  --ok:      #3f7d53;
  --no:      #a9503f;
  --sans: "IBM Plex Sans KR", system-ui, -apple-system, "Malgun Gothic", sans-serif;
  --serif: "Gowun Batang", "Nanum Myeongjo", Georgia, serif;
  --mono: "IBM Plex Mono", ui-monospace, "D2Coding", Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #141817; --card: #1c2220; --ink: #e8e9e5; --dim: #96a09c;
    --line: #2e3734; --accent: #5cc3b3; --ok: #74b98a; --no: #d88a76;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --paper: #141817; --card: #1c2220; --ink: #e8e9e5; --dim: #96a09c;
  --line: #2e3734; --accent: #5cc3b3; --ok: #74b98a; --no: #d88a76;
  color-scheme: dark;
}

* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: var(--sans); font-size: 15px; line-height: 1.65;
  -webkit-text-size-adjust: 100%;
}
.wrap { max-width: 660px; margin: 0 auto; padding-inline: 16px; padding-block: 0 48px; }

/* ── 탭 ── */
.bar {
  position: sticky; top: env(safe-area-inset-top, 0px); z-index: 10;
  background: var(--paper); border-bottom: 1px solid var(--line);
}
.bar-in { max-width: 660px; margin: 0 auto; padding-inline: 16px;
          display: flex; align-items: center; gap: 2px; min-height: 48px; }
.tab {
  appearance: none; border: 0; background: none; color: var(--dim);
  font: 500 14px/1 var(--sans); padding: 14px 10px; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.tab[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--accent); }
.tab:focus-visible { outline: 2px solid var(--accent); outline-offset: -4px; border-radius: 3px; }
.spacer { flex: 1; }
.ghost {
  appearance: none; border: 1px solid var(--line); background: var(--card); color: var(--dim);
  border-radius: 999px; font: 500 12px/1 var(--sans); padding: 7px 11px; cursor: pointer;
}
.ghost:hover { color: var(--ink); }

/* ── 카드 ── */
.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 26px 22px; margin-top: 18px;
}
.q { font-family: var(--serif); font-size: 21px; line-height: 1.6; font-weight: 700;
     margin: 0; text-wrap: balance; }
.a { border-top: 1px solid var(--line); margin-top: 20px; padding-top: 18px; }
.a > :first-child { margin-top: 0; }
.a > :last-child { margin-bottom: 0; }
.a p, .a li { font-size: 14.5px; }
.from { font: 500 11px/1 var(--sans); letter-spacing: .07em; text-transform: uppercase;
        color: var(--dim); margin-bottom: 14px; display: block; }

/* 간격 반복 상자 — 1·3·7·21·60일 */
.rail { display: flex; gap: 4px; margin-top: 16px; align-items: center; }
.pip { height: 4px; flex: 1; border-radius: 2px; background: var(--line); }
.pip.on { background: var(--accent); }
.rail-n { font: 500 11px/1 var(--mono); color: var(--dim); margin-left: 6px;
          font-variant-numeric: tabular-nums; }

.acts { display: flex; gap: 10px; margin-top: 18px; }
.btn {
  appearance: none; flex: 1; border-radius: 8px; cursor: pointer;
  font: 500 15px/1 var(--sans); padding: 15px 12px; border: 1px solid var(--line);
  background: var(--card); color: var(--ink);
}
.btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.btn.primary { background: var(--accent); border-color: var(--accent); color: var(--paper); }
.btn.ok  { border-color: var(--ok); color: var(--ok); }
.btn.no  { border-color: var(--no); color: var(--no); }

/* ── 수치 ── */
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(118px, 1fr)); gap: 10px; margin-top: 18px; }
.tile { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px 15px; }
.tile b { display: block; font: 500 26px/1.1 var(--mono); font-variant-numeric: tabular-nums; }
.tile span { display: block; font-size: 12px; color: var(--dim); margin-top: 5px; }

h2 { font-size: 15px; font-weight: 600; margin: 32px 0 0; letter-spacing: -.01em; }
h2 + .note-lead { color: var(--dim); font-size: 13px; margin: 6px 0 0; }

/* 날짜별 막대 */
.days { display: flex; align-items: flex-end; gap: 3px; height: 92px; margin-top: 16px;
        padding: 12px 12px 0; background: var(--card); border: 1px solid var(--line);
        border-radius: 10px; overflow-x: auto; }
.day { flex: 0 0 11px; background: var(--accent); border-radius: 2px 2px 0 0; min-height: 2px; opacity: .85; }
.day.zero { background: var(--line); }

/* 목록 */
.rows { margin-top: 14px; border: 1px solid var(--line); border-radius: 10px;
        background: var(--card); overflow: hidden; }
.row { display: flex; gap: 12px; align-items: baseline; padding: 12px 15px;
       border-top: 1px solid var(--line); }
.row:first-child { border-top: 0; }
.row-q { flex: 1; min-width: 0; font-size: 14px; }
.row-n { font: 500 12px/1 var(--mono); color: var(--no); font-variant-numeric: tabular-nums;
         white-space: nowrap; }
.row-note { font-size: 11.5px; color: var(--dim); display: block; margin-top: 3px; }
.meter { height: 3px; background: var(--line); border-radius: 2px; margin-top: 6px; }
.meter i { display: block; height: 100%; background: var(--no); border-radius: 2px; }

/* 노트 */
.notes-list a { display: block; padding: 11px 15px; border-top: 1px solid var(--line);
                color: inherit; text-decoration: none; font-size: 14px; }
.notes-list a:first-child { border-top: 0; }
.notes-list a:hover { color: var(--accent); }
.notes-list .g { font: 500 11px/1 var(--mono); color: var(--dim); margin-right: 9px; }
.body { margin-top: 18px; }
.body h1 { font-size: 22px; margin: 0 0 4px; }
.body h2 { font-size: 16px; margin-top: 28px; }
.body h3 { font-size: 14px; margin-top: 22px; }
.body pre { background: var(--paper); border: 1px solid var(--line); border-radius: 8px;
            padding: 12px 14px; overflow-x: auto; font: 400 12.5px/1.6 var(--mono); }
.body code { font: 400 .92em/1.5 var(--mono); }
.body :not(pre) > code { background: var(--paper); border: 1px solid var(--line);
                         border-radius: 4px; padding: 1px 4px; }
.body table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
.body th, .body td { border: 1px solid var(--line); padding: 6px 9px; text-align: left; }
.body blockquote { border-left: 2px solid var(--line); margin: 16px 0; padding-left: 14px; color: var(--dim); }
.scroll { overflow-x: auto; }

.lead { color: var(--dim); font-size: 13.5px; margin-top: 10px; }
.empty { text-align: center; padding: 56px 20px; color: var(--dim); }
.empty b { display: block; color: var(--ink); font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>

<div class="bar">
  <div class="bar-in">
    <button class="tab" id="t-today" aria-selected="true" onclick="go('today')">오늘</button>
    <button class="tab" id="t-log"   aria-selected="false" onclick="go('log')">기록</button>
    <button class="tab" id="t-weak"  aria-selected="false" onclick="go('weak')">약한 곳</button>
    <button class="tab" id="t-notes" aria-selected="false" onclick="go('notes')">노트</button>
    <span class="spacer"></span>
    <button class="ghost" id="themeBtn" onclick="flipTheme()">테마</button>
  </div>
</div>

<div class="wrap">
  <div id="today"></div>
  <div id="log" hidden></div>
  <div id="weak" hidden></div>
  <div id="notes" hidden></div>
</div>

<script>
var NOTES = /*__NOTES__*/null;
var CARDS = /*__CARDS__*/null;
var STEPS = /*__STEPS__*/null;
var NEW_PER_DAY = /*__NEWPER__*/10;
var BUILT = "__BUILT__";

var store = null;      // db 네임스페이스. 없으면 null 로 남는다.
var state = {};        // cardId -> {box, due, right, wrong, last, note}
var days = {};         // "YYYY-MM-DD" -> {seen, right, wrong}
var queue = [], shown = null, flipped = false;

function ymd(d) {
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") +
         "-" + String(d.getDate()).padStart(2, "0");
}
function today() { return ymd(new Date()); }
function addDays(n) { var d = new Date(); d.setDate(d.getDate() + n); return ymd(d); }
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function byId(id) { for (var i = 0; i < CARDS.length; i++) if (CARDS[i].id === id) return CARDS[i]; return null; }
function noteOf(stem) { for (var i = 0; i < NOTES.length; i++) if (NOTES[i].stem === stem) return NOTES[i]; return null; }

/* ── 탭 ── */
function go(name) {
  var tabs = ["today", "log", "weak", "notes"];
  for (var i = 0; i < tabs.length; i++) {
    var on = tabs[i] === name;
    document.getElementById(tabs[i]).hidden = !on;
    document.getElementById("t-" + tabs[i]).setAttribute("aria-selected", on ? "true" : "false");
  }
  if (name === "log") drawLog();
  if (name === "weak") drawWeak();
  if (name === "notes") drawNotes();
  window.scrollTo(0, 0);
}

function flipTheme() {
  var now = document.documentElement.getAttribute("data-theme");
  var next = now === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem("rv-theme", next); } catch (e) {}
}
try {
  var saved = localStorage.getItem("rv-theme");
  if (saved) document.documentElement.setAttribute("data-theme", saved);
} catch (e) {}

/* ── 오늘 볼 카드 고르기 ── */
function buildQueue() {
  var t = today(), due = [], fresh = [];
  for (var i = 0; i < CARDS.length; i++) {
    var c = CARDS[i], s = state[c.id];
    if (!s) { fresh.push(c); }
    else if (s.due <= t) { due.push(c); }
  }
  var seenToday = days[t] ? days[t].seen : 0;
  var room = Math.max(0, NEW_PER_DAY - seenToday);
  queue = due.concat(fresh.slice(0, room));
}

function drawToday() {
  var el = document.getElementById("today");
  if (store === null) {
    el.innerHTML = '<div class="empty"><b>진도를 저장할 수 없습니다</b>' +
      'claude.ai 에 로그인한 상태로 열면 어제까지의 진도가 이어집니다.<br>' +
      '아래 노트 탭은 로그인 없이도 읽을 수 있습니다.</div>';
    return;
  }
  buildQueue();
  var t = today(), d = days[t] || {seen: 0, right: 0, wrong: 0};
  if (!queue.length) {
    el.innerHTML = '<div class="empty"><b>오늘 볼 카드가 없습니다</b>' +
      (d.seen ? '오늘 ' + d.seen + '장을 봤습니다. 다음 카드는 내일 돌아옵니다.'
              : '카드 ' + CARDS.length + '장이 모두 다음 날짜를 기다리고 있습니다.') +
      '</div>';
    shown = null;
    return;
  }
  shown = queue[0];
  flipped = false;
  render();
}

function render() {
  var c = shown, s = state[c.id] || {box: -1, right: 0, wrong: 0};
  var box = s.box === undefined ? -1 : s.box;
  var pips = "";
  for (var i = 0; i < STEPS.length; i++) {
    pips += '<span class="pip' + (i <= box ? " on" : "") + '"></span>';
  }
  var tally = (s.right || s.wrong)
      ? '<span class="rail-n">' + (s.right || 0) + "/" + ((s.right || 0) + (s.wrong || 0)) + "</span>"
      : '<span class="rail-n">새 카드</span>';

  var html =
    '<div class="card">' +
      '<span class="from">' + esc(c.note) + "</span>" +
      '<p class="q">' + esc(c.q) + "</p>" +
      (flipped ? '<div class="a">' + c.a + "</div>" : "") +
      '<div class="rail">' + pips + tally + "</div>" +
    "</div>";

  html += flipped
    ? '<div class="acts">' +
        '<button class="btn no" onclick="grade(false)">다시</button>' +
        '<button class="btn ok" onclick="grade(true)">기억남</button>' +
      "</div>"
    : '<div class="acts"><button class="btn primary" onclick="flip()">답 보기</button></div>';

  var left = queue.length;
  html += '<p class="lead">남은 ' + left + "장 · 오늘 " +
          ((days[today()] || {}).seen || 0) + "장 봄" +
          (failed ? " · 저장이 막혔습니다. 이 기기에서만 세고 있습니다" : "") + "</p>";
  document.getElementById("today").innerHTML = html;
}

function flip() { flipped = true; render(); }

/* 쓰기는 문서마다 한 번에 하나씩 보낸다. 겹쳐 보내면 뒤엣것이 이기는데
   어느 쪽이 뒤인지 보장이 없다. 경로별로 약속을 이어 붙여 줄을 세운다. */
var chains = {}, failed = false;
function put(path, body) {
  var prev = chains[path] || Promise.resolve();
  var next = prev.then(function () { return store.doc(path).set(body); })
                 .catch(function () { failed = true; render(); });
  chains[path] = next;
  return next;
}

/* 하루 집계는 카드를 넘길 때마다 같은 문서를 건드린다.
   손이 멈춘 뒤 한 번만 쓴다. */
var dayTimer = null;
function putDay(t) {
  clearTimeout(dayTimer);
  dayTimer = setTimeout(function () { put("days/" + t, days[t]); }, 700);
}

function grade(right) {
  if (!shown || !store) return;
  var c = shown, t = today();
  var s = state[c.id] || {box: -1, right: 0, wrong: 0, note: c.note};
  var box = right ? Math.min((s.box === undefined ? -1 : s.box) + 1, STEPS.length - 1) : 0;
  var row = {
    box: box,
    due: addDays(STEPS[box]),
    right: (s.right || 0) + (right ? 1 : 0),
    wrong: (s.wrong || 0) + (right ? 0 : 1),
    last: t,
    note: c.note
  };
  state[c.id] = row;

  var d = days[t] || {seen: 0, right: 0, wrong: 0};
  d = {seen: d.seen + 1, right: d.right + (right ? 1 : 0), wrong: d.wrong + (right ? 0 : 1)};
  days[t] = d;

  put("cards/" + c.id, row);
  putDay(t);

  queue.shift();
  if (!right) queue.push(c);     // 틀린 카드는 오늘 안에 한 번 더
  if (!queue.length) { drawToday(); return; }
  shown = queue[0]; flipped = false; render();
}

/* ── 기록 ── */
function drawLog() {
  var el = document.getElementById("log");
  var keys = Object.keys(days).sort();
  if (!keys.length) {
    el.innerHTML = '<div class="empty"><b>아직 기록이 없습니다</b>' +
      '오늘 탭에서 카드를 한 장이라도 보면 날짜별 학습량이 여기 쌓입니다.</div>';
    return;
  }
  var total = 0, right = 0;
  for (var k in days) { total += days[k].seen; right += days[k].right; }

  // 최근 60일 막대
  var bars = "", max = 1;
  for (var k2 in days) if (days[k2].seen > max) max = days[k2].seen;
  for (var i = 59; i >= 0; i--) {
    var day = addDays(-i), v = days[day] ? days[day].seen : 0;
    var h = v ? Math.max(3, Math.round(v / max * 72)) : 2;
    bars += '<div class="day' + (v ? "" : " zero") + '" style="height:' + h + 'px" title="' +
            day + " " + v + '장"></div>';
  }

  // 연속 학습일
  var streak = 0;
  for (var i2 = 0; i2 < 400; i2++) {
    var dd = addDays(-i2);
    if (days[dd] && days[dd].seen) streak++;
    else if (i2 > 0) break;
  }
  var pct = total ? Math.round(right / total * 100) : 0;
  var done = 0;
  for (var id in state) done++;

  el.innerHTML =
    '<div class="tiles">' +
      '<div class="tile"><b>' + total + '</b><span>지금까지 본 장수</span></div>' +
      '<div class="tile"><b>' + streak + '</b><span>연속 학습일</span></div>' +
      '<div class="tile"><b>' + pct + '%</b><span>기억남 비율</span></div>' +
      '<div class="tile"><b>' + done + "/" + CARDS.length + '</b><span>한 번 이상 본 카드</span></div>' +
    "</div>" +
    "<h2>최근 60일</h2>" +
    '<p class="note-lead">막대 하나가 하루입니다. 오른쪽 끝이 오늘입니다.</p>' +
    '<div class="days">' + bars + "</div>";
}

/* ── 약한 곳 ── */
function drawWeak() {
  var el = document.getElementById("weak"), rows = [], byNote = {};
  for (var id in state) {
    var s = state[id], seen = (s.right || 0) + (s.wrong || 0);
    if (!seen) continue;
    var n = s.note || "?";
    if (!byNote[n]) byNote[n] = {wrong: 0, seen: 0};
    byNote[n].wrong += s.wrong || 0;
    byNote[n].seen += seen;
    if (s.wrong) rows.push({id: id, wrong: s.wrong, seen: seen, note: n});
  }
  if (!rows.length) {
    el.innerHTML = '<div class="empty"><b>틀린 카드가 아직 없습니다</b>' +
      '「다시」를 누른 카드가 여기 모입니다. 자주 틀리는 순서로 보여 줍니다.</div>';
    return;
  }
  rows.sort(function (a, b) { return b.wrong - a.wrong || b.seen - a.seen; });

  var html = "<h2>자주 틀리는 카드</h2>" +
             '<p class="note-lead">틀린 횟수가 많은 순입니다.</p><div class="rows">';
  for (var i = 0; i < Math.min(rows.length, 20); i++) {
    var r = rows[i], c = byId(r.id);
    if (!c) continue;
    html += '<div class="row"><div class="row-q">' + esc(c.q) +
            '<span class="row-note">' + esc(r.note) + "</span>" +
            '<div class="meter"><i style="width:' + Math.round(r.wrong / r.seen * 100) + '%"></i></div>' +
            '</div><span class="row-n">' + r.wrong + "/" + r.seen + "</span></div>";
  }
  html += "</div>";

  var ns = [];
  for (var n2 in byNote) if (byNote[n2].wrong) ns.push({note: n2, w: byNote[n2].wrong, s: byNote[n2].seen});
  ns.sort(function (a, b) { return b.w / b.s - a.w / a.s || b.w - a.w; });
  if (ns.length) {
    html += "<h2>노트별 약한 곳</h2>" +
            '<p class="note-lead">틀린 비율이 높은 순입니다. 다시 읽을 노트를 고르는 데 씁니다.</p><div class="rows">';
    for (var j = 0; j < Math.min(ns.length, 12); j++) {
      var x = ns[j], r2 = Math.round(x.w / x.s * 100);
      html += '<div class="row"><div class="row-q">' + esc(x.note) +
              '<div class="meter"><i style="width:' + r2 + '%"></i></div></div>' +
              '<span class="row-n">' + r2 + "%</span></div>";
    }
    html += "</div>";
  }
  el.innerHTML = html;
}

/* ── 노트 ── */
function drawNotes() {
  var el = document.getElementById("notes");
  var html = '<p class="lead">개념 노트 ' + NOTES.length + "편 · 카드 " + CARDS.length +
             "장 · " + BUILT + " 기준</p><div class=\"rows notes-list\">";
  for (var i = 0; i < NOTES.length; i++) {
    var n = NOTES[i];
    html += '<a href="#" onclick="openNote(\'' + n.stem + '\');return false;">' +
            '<span class="g">' + esc(n.no) + "</span>" + esc(n.title) + "</a>";
  }
  el.innerHTML = html + "</div>";
}

function openNote(stem) {
  var n = noteOf(stem);
  if (!n) return;
  document.getElementById("notes").innerHTML =
    '<p class="lead"><button class="ghost" onclick="drawNotes()">← 노트 목록</button></p>' +
    '<div class="body">' + n.html + "</div>";
  window.scrollTo(0, 0);
}

/* ── 시작 ── */
drawToday();   // store 없이도 첫 화면은 그린다

(async function () {
  var db = window.claude && window.claude.use ? await window.claude.use("db") : null;
  if (!db) { drawToday(); return; }
  store = db;
  try {
    // QuerySnapshot.docs 의 각 DocumentSnapshot 은 id 와 data() 를 준다.
    var cs = await db.collection("cards").get();
    cs.docs.forEach(function (d) { state[d.id] = d.data(); });
    var ds = await db.collection("days").get();
    ds.docs.forEach(function (d) { days[d.id] = d.data(); });
  } catch (e) {
    // 읽기 실패는 진도가 없는 것과 같게 두고 화면은 그린다.
  }
  drawToday();
})();
</script>
"""


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
    # raw 는 옵시디언 내보내기 전용이다. 페이지에 넣으면 같은 답이 두 벌 실린다.
    페이지용 = [{k: v for k, v in c.items() if k != "raw"} for c in 카드]

    안전 = 스크립트안전
    페이지 = (템플릿
              .replace("/*__NOTES__*/null", 안전(json.dumps(묶음, ensure_ascii=False)))
              .replace("/*__CARDS__*/null", 안전(json.dumps(페이지용, ensure_ascii=False)))
              .replace("/*__STEPS__*/null", json.dumps(STEPS))
              .replace("/*__NEWPER__*/10", str(NEW_PER_DAY))
              .replace("__BUILT__", date.today().isoformat()))

    # 노트 54 는 cp949 를 utf-8 로 읽으면 어떻게 보이는지를 예시로 담고 있어
    # 깨진 글자(U+FFFD) 자체가 본문이다. 아티팩트는 이 문자를 사고로 보고 거절하므로
    # 엔티티로 바꿔 싣는다. 본문은 innerHTML 로 들어가니 화면에서는 그대로 보인다.
    깨짐 = 페이지.count("�")
    if 깨짐:
        페이지 = 페이지.replace("�", "&#xFFFD;")
        print(f"  U+FFFD {깨짐}개를 엔티티로 바꿨다 (노트 54 의 cp949 예시)")

    OUT.write_text(페이지, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1024:.0f} KB)")
    print(f"  노트 {len(묶음)}편 · 카드 {len(카드)}장")
    덮인 = {c['note'] for c in 카드}
    빈 = [n['no'] for n in 묶음 if n['stem'] not in 덮인]
    if 빈:
        print(f"  카드 없는 노트 {len(빈)}편: {', '.join(빈)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
