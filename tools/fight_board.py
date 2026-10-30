"""Build the fight board: one page that shows, fight by fight, how the AI's fight play is doing.

    python tools/fight_board.py --out docs/paper/fight-board.html \
        --starts D:/spireline/referee/lab/results/fight-gym/2026-10-29-m2/starts.jsonl \
        --games  D:/spireline/referee/lab/results/fight-gym/2026-10-29-m2/games.jsonl \
        --arm a3-v1="Usual thinking" --arm x16="Sixteen times the thinking" [--arm x4="Four times the thinking"]
        [--cat act1-boss]

Each saved start is a real fight the AI reached in a night's real-game runs (its deck, relics, potions and health at the
fight's first decision). Each arm replays every start several times with fresh draws. The page shows a cell per fight per
arm, coloured by how many of those replays the AI won, a scoreboard per boss, and the fights nobody wins yet, the fights more
thinking flips, and the fights already safe. Re-run with more --arm entries (a trained fight player, for example) to add rows.
Plain language only: the page is read by the owner on a phone.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

BOSS = {74: "Ceremonial Beast", 77: "Lagavulin Matriarch", 79: "Soul Fysh", 82: "Kin", 83: "Vantom", 84: "Waterfall Giant"}


def load_jsonl(p: Path) -> list[dict]:
    out = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def build(starts: list[dict], games: list[dict], arms: list[tuple[str, str]], cat: str) -> dict:
    keys = [a for a, _ in arms]
    per = defaultdict(lambda: defaultdict(list))
    for g in games:
        if g.get("cat") == cat and g.get("arm") in keys:
            per[g["start"]][g["arm"]].append(g)
    fights = []
    for s in starts:
        if s.get("cat") != cat:
            continue
        enemies = s.get("doc", {}).get("enemies", [])
        row = {
            "id": s["id"], "boss": BOSS.get(s.get("encounter_id"), f"encounter {s.get('encounter_id')}"),
            "hp": s.get("hp"), "max_hp": s.get("max_hp"), "deck": s.get("deck_size"), "relics": s.get("relics"),
            "potions": s.get("potions"), "enemy_hp": sum(e.get("max_hp", 0) for e in enemies), "arms": {},
        }
        for k in keys:
            gs = per[s["id"]].get(k, [])
            wins = [g for g in gs if g.get("won")]
            row["arms"][k] = {
                "n": len(gs), "wins": len(wins),
                "hp_left": round(sum(g.get("end_hp", 0) for g in wins) / len(wins), 1) if wins else None,
                "turns": round(sum(g.get("turns", 0) for g in gs) / len(gs), 1) if gs else None,
            }
        fights.append(row)
    return {"cat": cat, "arms": [{"key": k, "label": l} for k, l in arms], "fights": fights}


TEMPLATE = r"""<title>Fight Board</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=Source+Sans+3:wght@400;600&display=swap">
<style>
/* Layout: one column, phone first; a scoreboard, then one grid of fights per version, then the lists. */
:root{--bg:#f5f7f3;--fg:#19231f;--muted:#5b6a62;--line:#d6ddd7;--card:#ffffff;--accent:#0f6e5c;--accent-ink:#ffffff;
--w0:#e9ece6;--w1:#d9e7df;--w2:#c4ddd1;--w3:#add2c3;--w4:#95c6b4;--w5:#7bb9a4;--w6:#61aa93;--w7:#489981;--w8:#32866e;--w9:#1f725b;--w10:#0f5d49;--none:#f0f1ee;
--display:"Bricolage Grotesque","Avenir Next","Segoe UI",system-ui,sans-serif;--body:"Source Sans 3","Segoe UI",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121815;--fg:#e6ebe7;--muted:#9aaaa2;--line:#2a3530;--card:#1a211e;--accent:#6cc3a8;--accent-ink:#0f1a16;
--w0:#222a27;--w1:#1f3730;--w2:#20463c;--w3:#225548;--w4:#266454;--w5:#2c7461;--w6:#35846e;--w7:#42947c;--w8:#54a48b;--w9:#6ab49b;--w10:#86c6ad;--none:#171d1a;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121815;--fg:#e6ebe7;--muted:#9aaaa2;--line:#2a3530;--card:#1a211e;--accent:#6cc3a8;--accent-ink:#0f1a16;
--w0:#222a27;--w1:#1f3730;--w2:#20463c;--w3:#225548;--w4:#266454;--w5:#2c7461;--w6:#35846e;--w7:#42947c;--w8:#54a48b;--w9:#6ab49b;--w10:#86c6ad;--none:#171d1a;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font-family:var(--body);font-size:16px;line-height:1.45;margin:0}
.wrap{max-width:760px;margin:0 auto;padding-block:20px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:28px}
h1,h2,h3{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.15}
h1{font-size:2rem;font-weight:800}h2{font-size:1.25rem;font-weight:700}h3{font-size:1rem;font-weight:700}
p{margin:0;max-width:62ch}.muted{color:var(--muted)}.lead{font-size:1.05rem}
section{display:flex;flex-direction:column;gap:12px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:2px;min-width:0}
.tile b{font-family:var(--display);font-size:1.9rem;font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1}
.tile span{font-size:.9rem;color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600}
td.num,th.num{text-align:right}tr:last-child td{border-bottom:0}
.rowlabel{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
.grid{display:grid;grid-template-columns:repeat(20,1fr);gap:2px}
.c{aspect-ratio:1;border:0;border-radius:2px;padding:0;background:var(--none);cursor:pointer;min-width:0}
.c:focus-visible,.c.on{outline:2px solid var(--accent);outline-offset:1px}
.w0{background:var(--w0)}.w1{background:var(--w1)}.w2{background:var(--w2)}.w3{background:var(--w3)}.w4{background:var(--w4)}.w5{background:var(--w5)}.w6{background:var(--w6)}.w7{background:var(--w7)}.w8{background:var(--w8)}.w9{background:var(--w9)}.w10{background:var(--w10)}
.legend{display:flex;align-items:center;gap:6px;font-size:.85rem;color:var(--muted);flex-wrap:wrap}
.legend i{display:inline-block;width:14px;height:14px;border-radius:2px}
.detail{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:6px}
.detail dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0;font-variant-numeric:tabular-nums}
dt{color:var(--muted)}dd{margin:0}
ul{margin:0;padding-left:1.2em}li{margin:2px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:3px 10px;font-size:.9rem;cursor:pointer;color:var(--fg);font-family:var(--body)}
.chip:hover,.chip:focus-visible{border-color:var(--accent)}
footer{font-size:.9rem;color:var(--muted);display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--line);padding-top:12px}
@media (prefers-reduced-motion:no-preference){.c{transition:transform .08s}.c:hover{transform:scale(1.25)}}
</style>
<div class="wrap">
<header style="display:flex;flex-direction:column;gap:8px">
<h1>Fight Board</h1>
<p class="lead">Two hundred real boss fights the AI reached in one night, each replayed ten times with fresh card draws. One square per fight. The darker the square, the more of its ten replays the AI won. A new row appears for each new version of the fight player, so the board shows the fight play getting stronger, fight by fight.</p>
<p class="muted" id="updated"></p>
</header>
<section id="tiles"><h2>At a glance</h2><div class="tiles" id="tilebox"></div></section>
<section><h2>By boss</h2><div class="tablewrap"><table id="bossTable"></table></div><p class="muted">Kills in 100 replays. Fights are grouped by boss, hardest boss first.</p></section>
<section id="grids"><h2>Every fight, every version</h2><p class="muted">Tap a square to see that fight. The same square position is the same fight in every row.</p></section>
<section><h2>The fight you tapped</h2><div class="detail" id="detail"><p class="muted">Tap a square above.</p></div></section>
<section><h2>Fights nobody wins yet</h2><p class="muted">Lost in all ten replays under every version. These are the fights the trainer is for.</p><div class="chips" id="never"></div></section>
<section><h2>Fights more thinking flips</h2><p class="muted">Won three times or fewer with the usual thinking, seven or more with more thinking: the deck can do it, the play was the problem.</p><div class="chips" id="flip"></div></section>
<section><h2>Fights already safe</h2><p class="muted">Won all ten replays with the usual thinking.</p><div class="chips" id="safe"></div></section>
<footer><span>Source: the AI's own Act 1 boss fights from the real-game night of 2026-10-29, replayed on the copy by the fight gym. Health is the AI's health entering the fight. "Health left" is the average over the replays it won.</span><span id="log"></span></footer>
</div>
<script>
const DATA = __DATA__;
const UPDATED = "__UPDATED__";
const LOG = __LOG__;
(function(){
  const arms = DATA.arms, A0 = arms[0].key;
  const f = DATA.fights;
  const rate = x => x.n ? x.wins / x.n : null;
  // boss order: hardest first by the first arm
  const byBoss = {};
  f.forEach(x => { (byBoss[x.boss] = byBoss[x.boss] || []).push(x); });
  const bossRate = b => { const r = byBoss[b].reduce((a, x) => [a[0] + x.arms[A0].wins, a[1] + x.arms[A0].n], [0, 0]); return r[1] ? r[0] / r[1] : 0; };
  const bosses = Object.keys(byBoss).sort((a, b) => bossRate(a) - bossRate(b));
  const order = [];
  bosses.forEach(b => byBoss[b].sort((p, q) => (p.arms[A0].wins - q.arms[A0].wins) || ((arms[1] ? p.arms[arms[1].key].wins - q.arms[arms[1].key].wins : 0))).forEach(x => order.push(x)));
  const best = x => Math.max(...arms.map(a => x.arms[a.key].n ? x.arms[a.key].wins : -1));
  const full = x => arms.every(a => x.arms[a.key].n >= 10);
  const safe = order.filter(x => x.arms[A0].n >= 10 && x.arms[A0].wins === x.arms[A0].n);
  const never = order.filter(x => full(x) && best(x) === 0);
  const flip = order.filter(x => x.arms[A0].n >= 10 && x.arms[A0].wins <= 3 && arms.slice(1).some(a => x.arms[a.key].n >= 10 && x.arms[a.key].wins >= 7));
  document.getElementById('updated').textContent = 'Updated ' + UPDATED + '. ' + f.length + ' fights, ' + arms.length + ' version' + (arms.length > 1 ? 's' : '') + ' of the fight player.';
  const pct = (w, n) => n ? Math.round(100 * w / n) : null;
  const tot = a => f.reduce((s, x) => [s[0] + x.arms[a.key].wins, s[1] + x.arms[a.key].n], [0, 0]);
  const tiles = [];
  arms.forEach(a => { const t = tot(a); tiles.push(['<b>' + pct(t[0], t[1]) + '</b><span>kills in 100, ' + a.label.toLowerCase() + '</span>']); });
  tiles.push(['<b>' + safe.length + '</b><span>fights already safe (10 of 10)</span>']);
  tiles.push(['<b>' + never.length + '</b><span>fights nobody wins yet</span>']);
  if (arms.length > 1) tiles.push(['<b>' + flip.length + '</b><span>fights more thinking flips</span>']);
  document.getElementById('tilebox').innerHTML = tiles.map(t => '<div class="tile">' + t[0] + '</div>').join('');
  let th = '<thead><tr><th>Boss</th><th class="num">Fights</th>' + arms.map(a => '<th class="num">' + a.label + '</th>').join('') + '</tr></thead><tbody>';
  bosses.forEach(b => { const xs = byBoss[b]; th += '<tr><td>' + b + '</td><td class="num">' + xs.length + '</td>' + arms.map(a => { const r = xs.reduce((s, x) => [s[0] + x.arms[a.key].wins, s[1] + x.arms[a.key].n], [0, 0]); return '<td class="num">' + (r[1] ? pct(r[0], r[1]) + ' in 100' : '·') + '</td>'; }).join('') + '</tr>'; });
  th += '<tr><td><strong>All</strong></td><td class="num"><strong>' + f.length + '</strong></td>' + arms.map(a => { const t = tot(a); return '<td class="num"><strong>' + pct(t[0], t[1]) + ' in 100</strong></td>'; }).join('') + '</tr></tbody>';
  document.getElementById('bossTable').innerHTML = th;
  const grids = document.getElementById('grids');
  const cls = x => x.n ? 'w' + Math.round(10 * x.wins / x.n) : '';
  arms.forEach(a => {
    const t = tot(a);
    const box = document.createElement('div'); box.style.cssText = 'display:flex;flex-direction:column;gap:6px';
    box.innerHTML = '<div class="rowlabel"><h3>' + a.label + '</h3><span class="muted">' + (t[1] ? pct(t[0], t[1]) + ' kills in 100' : 'not played yet') + (t[1] && t[1] < 10 * f.length ? ', ' + Math.round(t[1] / 10) + ' of ' + f.length + ' fights played' : '') + '</span></div>';
    const g = document.createElement('div'); g.className = 'grid';
    order.forEach((x, i) => { const c = document.createElement('button'); c.className = 'c ' + cls(x.arms[a.key]); c.dataset.i = i; c.title = x.boss + ', ' + (x.arms[a.key].n ? x.arms[a.key].wins + ' of ' + x.arms[a.key].n : 'not played'); c.setAttribute('aria-label', c.title); g.appendChild(c); });
    box.appendChild(g); grids.appendChild(box);
  });
  const leg = document.createElement('div'); leg.className = 'legend'; leg.innerHTML = '<span>Won 0 of 10</span>' + [0, 2, 4, 6, 8, 10].map(k => '<i class="w' + k + '"></i>').join('') + '<span>10 of 10</span>'; grids.appendChild(leg);
  const detail = document.getElementById('detail');
  function show(i) {
    const x = order[i];
    document.querySelectorAll('.c.on').forEach(c => c.classList.remove('on'));
    document.querySelectorAll('.c[data-i="' + i + '"]').forEach(c => c.classList.add('on'));
    let h = '<h3>' + x.boss + '</h3><dl><dt>Fight</dt><dd>' + x.id + ' (floor 17 of the run with that seed)</dd><dt>Entering</dt><dd>' + x.hp + ' of ' + x.max_hp + ' health, ' + x.deck + ' cards, ' + x.relics + ' relics, ' + x.potions + ' potion' + (x.potions === 1 ? '' : 's') + '</dd><dt>Boss health</dt><dd>' + x.enemy_hp + '</dd>';
    arms.forEach(a => { const r = x.arms[a.key]; h += '<dt>' + a.label + '</dt><dd>' + (r.n ? 'won ' + r.wins + ' of ' + r.n + (r.hp_left != null ? ', health left ' + r.hp_left : '') + (r.turns != null ? ', ' + r.turns + ' turns' : '') : 'not played') + '</dd>'; });
    detail.innerHTML = h + '</dl>';
  }
  grids.addEventListener('click', e => { const c = e.target.closest('.c'); if (c) { show(+c.dataset.i); } });
  const chips = (id, xs) => { document.getElementById(id).innerHTML = xs.length ? xs.map(x => '<button class="chip" data-i="' + order.indexOf(x) + '">' + x.boss + ' · ' + x.hp + '/' + x.max_hp + ' hp · ' + x.deck + ' cards</button>').join('') : '<span class="muted">None.</span>'; };
  chips('never', never); chips('flip', flip); chips('safe', safe);
  document.querySelectorAll('.chips').forEach(el => el.addEventListener('click', e => { const c = e.target.closest('.chip'); if (c) { show(+c.dataset.i); document.getElementById('detail').scrollIntoView({ block: 'nearest' }); } }));
  document.getElementById('log').textContent = LOG.join(' · ');
})();
</script>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--starts", required=True)
    ap.add_argument("--games", required=True, action="append", help="games.jsonl; repeatable")
    ap.add_argument("--arm", required=True, action="append", help='key="Label"; repeatable, first is the baseline')
    ap.add_argument("--cat", default="act1-boss")
    ap.add_argument("--log", action="append", default=[], help="a changelog line; repeatable")
    a = ap.parse_args()
    arms = []
    for s in a.arm:
        k, _, l = s.partition("=")
        arms.append((k, l.strip('"') or k))
    starts = load_jsonl(Path(a.starts))
    games = []
    for g in a.games:
        games += load_jsonl(Path(g))
    data = build(starts, games, arms, a.cat)
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    html = (TEMPLATE.replace("__DATA__", json.dumps(data, separators=(",", ":")))
            .replace("__UPDATED__", updated).replace("__LOG__", json.dumps(a.log)))
    Path(a.out).write_text(html, encoding="utf-8", newline="\n")
    n = len(data["fights"])
    print(f"ok {a.out}: {n} fights, arms {[k for k, _ in arms]}, {len(html)} bytes, {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
