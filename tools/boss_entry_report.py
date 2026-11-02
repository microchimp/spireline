"""The boss-entry report's tables, from the summaries `tools/boss_entry.py` writes.

    python tools/boss_entry_report.py --human human.jsonl.gz --selfplay selfplay.jsonl.gz --nights nights.jsonl.gz \
        --starts starts.lite.json --out tables.md --json numbers.json

Human cells under `MIN_CELL` runs are suppressed (D13); the human line is the held-out fifth (D38) unless a row says "all".
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boss_entry as be  # noqa: E402
from boss_entry import HP_BINS, MIN_CELL, Cards, cell  # noqa: E402

f1, pct = be.f1, be.pct


def table(head: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out) + "\n"


HEADLINE_HEAD = ["Group", "Runs", "Mean floor", "Reach Act 1 boss", "Kill it (of reached)", "Cleared Act 1 (of runs)", "Reach Act 2 boss",
                 "Kill it (of reached)", "Cleared Act 2 (of runs)", "Won", "Cards taken a run", "Skip rate", "Rests upgraded"]


def headline_row(label: str, runs: list[dict]) -> list[str]:
    h = be.headline(runs)
    if h["n"] < MIN_CELL:
        return [label, str(h["n"]), "suppressed"] + ["."] * 10
    return [label, f"{h['n']:,}", f1(h["floor"]), pct(h["a1_reached"]), pct(h["a1_kill_rate"]), pct(h["a1_killed_share"]),
            pct(h["a2_reached"]), pct(h["a2_kill_rate"]), pct(h["a2_killed_share"]), pct(h["won"]), f1(h["taken_per_run"]),
            pct(h["skip_rate"], 0), pct(h["smith_share"], 0)]


ENTRY_HEAD = ["Group", "Runs", "HP / max", "HP share", "Cards", "Upgraded", "Attack / skill / power / other", "Strikes + Defends",
              "Relics", "Potions", "Gold"]


def entry_rows(label: str, runs: list[dict], act: int, cards: Cards, cohorts=("boss", "killed", "lost", "before")) -> list[list[str]]:
    rows = []
    for co in cohorts:
        c = cell(runs, act, co, cards)
        name = f"{label}, {be.COHORT_TEXT[co]}"
        if c.get("n_snap", 0) < MIN_CELL:
            rows.append([name, str(c.get("n", 0)), "suppressed" if c.get("n", 0) else "."] + ["."] * 8)
            continue
        rows.append([name, f"{c['n']:,}", f"{f1(c['hp'])} / {f1(c['mhp'])}", pct(c["hp_frac"], 0), f1(c["deck"]), f1(c["upgraded"]),
                     f"{f1(c['attack'])} / {f1(c['skill'])} / {f1(c['power'])} / {f1(c['other'])}", f1(c["basic"]), f1(c["relics"]),
                     f1(c["potions"]), f1(c["gold"], 0)])
    return rows


PATH_HEAD = ["Group", "Runs", "Fights", "Elites", "Rests", "Shops", "Chests", "? rooms", "Upgrades / heals", "Cards taken (skip rate)",
             "Shop visits / cards / relics / removals"]


def path_rows(label: str, runs: list[dict], act: int, cards: Cards, cohorts=("boss",)) -> list[list[str]]:
    rows = []
    for co in cohorts:
        c = cell(runs, act, co, cards)
        name = f"{label}, {be.COHORT_TEXT[co]}"
        if c.get("n", 0) < MIN_CELL:
            rows.append([name, str(c.get("n", 0)), "suppressed"] + ["."] * 8)
            continue
        p = c["path"]
        shop = (f"{f1(c.get('shop_visits'), 2)} / {f1(c.get('shop_cards'), 2)} / {f1(c.get('shop_relics'), 2)} / "
                f"{f1(c.get('shop_removals'), 2)}") if "shop_visits" in c else "."
        rows.append([name, f"{c['n']:,}", f1(p["M"]), f1(p["E"], 2), f1(p["R"], 2), f1(p["S"], 2), f1(p["T"], 2), f1(p["?"], 2),
                     f"{f1(c['rest_smith'], 2)} / {f1(c['rest_heal'], 2)}", f"{f1(c['taken'], 2)} ({pct(c['skip_rate'], 0)})", shop])
    return rows


def pick_gap_rows(ai: list[dict], hum: list[dict], act: int, min_offers: int = 150, top: int = 8) -> list[list[str]]:
    """Cards whose pick rate when offered differs most between the AI and the humans (both ends)."""
    a, h = be.pick_rates(ai, act), be.pick_rates(hum, act)
    rows = []
    for c in set(a) & set(h):
        if a[c][0] >= min_offers and h[c][0] >= min_offers:
            ra, rh = a[c][1] / a[c][0], h[c][1] / h[c][0]
            rows.append((ra - rh, c, a[c][0], ra, h[c][0], rh))
    rows.sort()
    pick = rows[:top] + rows[-top:]
    return [[c.replace("_", " ").title(), f"{na:,}", pct(ra, 0), f"{nh:,}", pct(rh, 0), f"{100 * d:+.0f}"] for d, c, na, ra, nh, rh in pick]


def top_card_rows(ai: list[dict], hum: list[dict], act: int, cards: Cards) -> list[list[str]]:
    a, h = cell(ai, act, "boss", cards), cell(hum, act, "boss", cards)
    na, nh = max(a.get("n_snap", 0), 1), max(h.get("n_snap", 0), 1)
    names = [c for c, _ in (a.get("top_cards") or [])[:8]]
    names += [c for c, _ in (h.get("top_cards") or [])[:8] if c not in names]
    rows = []
    for c in names:
        pa = sum(1 for r in ai if (r["a"][act] or {}).get("r") and any(x.rstrip("+") == c for x in (r["a"][act].get("deck") or [])))
        ph = sum(1 for r in hum if (r["a"][act] or {}).get("r") and any(x.rstrip("+") == c for x in (r["a"][act].get("deck") or [])))
        rows.append([c.replace("_", " ").title(), pct(pa / na, 0), pct(ph / nh, 0) if nh >= MIN_CELL else "."])
    return rows


def rest_hp_rows(ai: list[dict], hum: list[dict], act: int) -> list[list[str]]:
    a, h = be.rest_by_hp(ai, act), be.rest_by_hp(hum, act)
    rows = []
    for b in HP_BINS:
        ok = h[b][0] >= MIN_CELL
        rows.append([b, f"{a[b][0]:,}", pct(a[b][1], 0), f"{h[b][0]:,}" if ok else "suppressed", pct(h[b][1], 0) if ok else "."])
    return rows


def boss_rows(ai: list[dict], hum: list[dict], act: int) -> list[list[str]]:
    a, h = be.boss_table(ai, act), be.boss_table(hum, act)
    rows = []
    for b in sorted(a, key=lambda x: -a[x]["n"]):
        hb = h.get(b)
        ok = hb is not None and hb["n"] >= MIN_CELL
        rows.append([b.removesuffix("_BOSS").replace("_", " ").title(), f"{a[b]['n']:,}", pct(a[b]["kill_rate"], 0), pct(a[b]["hp_frac"], 0),
                     f"{hb['n']:,}" if ok else "suppressed", pct(hb["kill_rate"], 0) if ok else ".", pct(hb["hp_frac"], 0) if ok else "."])
    return rows


SHIFT_NAMES = {"hp_frac": "HP share at entry", "mhp": "Max HP", "upgraded": "Upgraded cards", "relics": "Relics", "potions": "Potions",
               "attacks": "Attack cards", "skills": "Skill cards", "powers": "Power cards", "gold": "Gold"}


def model_rows(ai: list[dict], hum_train: list[dict], hum_exam: list[dict], act: int, cards: Cards) -> tuple[list[list[str]], list[list[str]], dict]:
    """The boss kill on the entry state: one model fitted on the AI's visits, one on the humans' other four fifths, each applied to both
    groups' states (who would win from whose hand); and the one-feature shifts of the AI model toward the human exam fifth's means."""
    va, vh_tr, vh_ex = be.visits(ai, act), be.visits(hum_train, act), be.visits(hum_exam, act)
    ma, mh = be.kill_model(va, cards), be.kill_model(vh_tr, cards)
    info: dict = {"n_ai": len(va), "n_hum_train": len(vh_tr), "n_hum_exam": len(vh_ex)}
    if ma is None or mh is None or len(vh_ex) < MIN_CELL:
        return [], [], info
    act_ai = sum(a["k"] for a in va) / len(va)
    act_hum = sum(a["k"] for a in vh_ex) / len(vh_ex)
    rows = [["Actual kill share", pct(act_ai), pct(act_hum)],
            ["Human-trained model on that group's entry states", pct(be.mean_kill(mh, va, cards)), pct(be.mean_kill(mh, vh_ex, cards))],
            ["AI-trained model on that group's entry states", pct(be.mean_kill(ma, va, cards)), pct(be.mean_kill(ma, vh_ex, cards))]]
    tgt, cur = be.mean_vector(vh_ex, cards), be.mean_vector(va, cards)
    sh_ai = be.shift_effects(ma, va, tgt, cards)
    sh_h = be.shift_effects(mh, vh_ex, cur, cards)
    info.update(actual_ai=act_ai, actual_hum=act_hum, hum_on_ai=be.mean_kill(mh, va, cards), hum_on_hum=be.mean_kill(mh, vh_ex, cards),
                ai_on_ai=be.mean_kill(ma, va, cards), ai_on_hum=be.mean_kill(ma, vh_ex, cards), shift_ai_model=sh_ai, shift_hum_model=sh_h,
                coef_ai=dict(zip(("intercept",) + be.FEATURES, ma)), coef_hum=dict(zip(("intercept",) + be.FEATURES, mh)),
                mean_ai=dict(zip(be.FEATURES, cur)), mean_hum=dict(zip(be.FEATURES, tgt)))
    shifts = []
    for i, k in enumerate(be.FEATURES):
        fmt = (lambda v: pct(v, 0)) if k == "hp_frac" else (lambda v: f1(v, 1 if k != "gold" else 0))
        shifts.append([SHIFT_NAMES[k], fmt(cur[i]), fmt(tgt[i]), f"{100 * sh_ai[k]:+.1f}", f"{100 * sh_h[k]:+.1f}"])
    shifts.append(["All of these together", "", "", f"{100 * sh_ai['all']:+.1f}", f"{100 * sh_h['all']:+.1f}"])
    return rows, shifts, info


def starts_rows(path: Path) -> list[list[str]]:
    """The loop's saved fight starts (every night's emulator arm, 50 runs a night): the boss starts' HP, deck size and relics, by night."""
    rows = []
    if not Path(path).is_file():
        return rows
    docs = json.loads(Path(path).read_text(encoding="utf-8"))
    for night in sorted({d["night"] for d in docs}):
        for cat in ("act1-boss", "act2-boss"):
            sel = [d for d in docs if d["night"] == night and d["cat"] == cat]
            if len(sel) < MIN_CELL:
                continue
            n = len(sel)
            rows.append([night, cat.removesuffix("-boss").replace("act", "Act "), str(n),
                         f"{f1(sum(d['hp'] for d in sel) / n)} / {f1(sum(d['max_hp'] for d in sel) / n)}",
                         pct(sum(d["hp"] / d["max_hp"] for d in sel) / n, 0), f1(sum(d["deck_size"] for d in sel) / n),
                         f1(sum(d["relics"] for d in sel) / n), f1(sum(d["potions"] for d in sel) / n)])
    return rows



def dose_rows(ai: list[dict], hum: list[dict], act: int, cards: Cards) -> list[list[str]]:
    """The boss kill share by what the run brought, for the AI and the humans (cells under MIN_CELL visits are suppressed)."""
    va, vh = be.visits(ai, act), be.visits(hum, act)
    rows = []
    dose = (
        ("HP share on entry", lambda a: a["hp"] / a["mhp"], (0.5, 0.7, 0.85), ("under 50%", "50-70%", "70-85%", "85% or more")),
        ("Potions held", lambda a: a.get("pot", 0), (1, 2), ("0", "1", "2 or more")),
        ("Relics held", lambda a: a["rel"], (4, 6, 8), ("under 4", "4-5", "6-7", "8 or more")),
        ("Upgraded cards", lambda a: sum(c.endswith("+") for c in a["deck"]), (2, 4, 6), ("0-1", "2-3", "4-5", "6 or more")),
        ("Skill cards", lambda a: sum(1 for c in a["deck"] if cards.kind(c) == "skill"), (5, 8, 11), ("under 5", "5-7", "8-10", "11 or more")),
    )
    for name, fx, edges, labels in dose:
        def bucket(rows_: list[dict]) -> list[list[int]]:
            cnt = [[0, 0] for _ in labels]
            for a in rows_:
                k = sum(1 for e in edges if fx(a) >= e)
                cnt[k][0] += 1
                cnt[k][1] += a["k"]
            return cnt

        ca, ch = bucket(va), bucket(vh)
        for i, lab in enumerate(labels):
            rows.append([name if i == 0 else "", lab, f"{ca[i][0]:,}", pct(ca[i][1] / ca[i][0], 0) if ca[i][0] >= MIN_CELL else ".",
                         f"{ch[i][0]:,}" if ch[i][0] >= MIN_CELL else "suppressed", pct(ch[i][1] / ch[i][0], 0) if ch[i][0] >= MIN_CELL else "."])
    return rows


def potion_elite_rows(ai: list[dict], hum: list[dict], cards: Cards) -> list[list[str]]:
    rows = []
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        for label, runs in (("AI gen 9", ai), ("Humans (exam fifth)", hum)):
            c = cell(runs, act, "boss", cards)
            if c.get("n", 0) < MIN_CELL:
                continue
            rows.append([name, label, f"{c['n']:,}", f1(c.get("pot_taken"), 2), f1(c.get("pot_left"), 2),
                         f1(c["path"]["E"], 2), pct(c.get("elite_take_rate"), 0) if "elite_take_rate" in c else ".",
                         f1(c.get("elite_offers"), 1) if "elite_offers" in c else "."])
    return rows


def elite_dose_rows(ai: list[dict], hum: list[dict], act: int) -> list[list[str]]:
    """The boss kill share, HP share and relics by the number of elites fought before the boss (cells under MIN_CELL suppressed)."""
    def group(runs: list[dict]) -> dict[int, list[dict]]:
        g: dict[int, list[dict]] = defaultdict(list)
        for a in be.visits(runs, act):
            g[min(a["path"].count("E"), 3)].append(a)
        return g

    ga, gh = group(ai), group(hum)
    rows = []
    for e in range(4):
        row = ["3 or more" if e == 3 else str(e)]
        for g in (ga, gh):
            v = g.get(e, [])
            if len(v) < MIN_CELL:
                row += [f"{len(v):,}" if v else "0", "suppressed" if v else ".", ".", "."]
            else:
                row += [f"{len(v):,}", pct(sum(a["k"] for a in v) / len(v), 0), pct(sum(a["hp"] / a["mhp"] for a in v) / len(v), 0),
                        f1(sum(a["rel"] for a in v) / len(v))]
        rows.append(row)
    return rows


def card_model_rows(ai: list[dict], tr: list[dict], ex: list[dict], act: int, cards: Cards, ai_pick: dict, hum_pick: dict) -> tuple[list[list[str]], list[list[str]], dict]:
    """The boss kill on the nine entry features plus the copies held of the 60 commonest cards, fitted on the humans' other four fifths and
    on the AI's visits, scored on the exam fifth and on the AI's; and the cards the human model likes and dislikes most."""
    va, vtr, vex = be.visits(ai, act), be.visits(tr, act), be.visits(ex, act)
    info: dict = {}
    if len(va) < 400 or len(vtr) < 400 or len(vex) < MIN_CELL:
        return [], [], info
    vocab = be.card_vocab(vtr + va, 60)
    fx = be.card_featurizer(cards, vocab)
    base_fx = lambda a: be.features(a, cards)  # noqa: E731
    cut = int(len(va) * 0.8)
    mh = be.kill_model(vtr, cards, fx=fx, ridge=3.0)
    mh0 = be.kill_model(vtr, cards, fx=base_fx)
    ma = be.kill_model(va[:cut], cards, fx=fx, ridge=3.0)
    ma0 = be.kill_model(va[:cut], cards, fx=base_fx)
    ys_h = [a["k"] for a in vex]
    ys_a = [a["k"] for a in va[cut:]]
    rows = [
        ["Human model, nine entry features: AUC on exam fifth", f1(be.auc([be.predict(mh0, base_fx(a)) for a in vex], ys_h), 3),
         pct(be.mean_kill(mh0, va, cards)), pct(be.mean_kill(mh0, vex, cards))],
        ["Human model, with cards: AUC on exam fifth", f1(be.auc([be.predict(mh, fx(a)) for a in vex], ys_h), 3),
         pct(be.mean_kill(mh, va, cards, fx=fx)), pct(be.mean_kill(mh, vex, cards, fx=fx))],
        ["AI model, nine entry features: AUC on held-out AI visits", f1(be.auc([be.predict(ma0, base_fx(a)) for a in va[cut:]], ys_a), 3),
         pct(be.mean_kill(ma0, va, cards)), pct(be.mean_kill(ma0, vex, cards))],
        ["AI model, with cards: AUC on held-out AI visits", f1(be.auc([be.predict(ma, fx(a)) for a in va[cut:]], ys_a), 3),
         pct(be.mean_kill(ma, va, cards, fx=fx)), pct(be.mean_kill(ma, vex, cards, fx=fx))],
    ]
    info.update(auc_h0=be.auc([be.predict(mh0, base_fx(a)) for a in vex], ys_h), auc_h=be.auc([be.predict(mh, fx(a)) for a in vex], ys_h),
                auc_a0=be.auc([be.predict(ma0, base_fx(a)) for a in va[cut:]], ys_a), auc_a=be.auc([be.predict(ma, fx(a)) for a in va[cut:]], ys_a),
                hum_cards_on_ai=be.mean_kill(mh, va, cards, fx=fx), hum_cards_on_hum=be.mean_kill(mh, vex, cards, fx=fx),
                ai_cards_on_ai=be.mean_kill(ma, va, cards, fx=fx), ai_cards_on_hum=be.mean_kill(ma, vex, cards, fx=fx))
    n9 = len(be.FEATURES)
    pres = {c: sum(1 for a in vtr if any(x.rstrip("+") == c for x in a["deck"])) / len(vtr) for c in vocab}
    coefs = [(mh[1 + n9 + i], c) for i, c in enumerate(vocab) if pres[c] >= 0.05]
    coefs.sort()
    pick = coefs[:6] + coefs[-6:]
    crow = []
    for w, c in pick:
        ap, hp = ai_pick.get(c), hum_pick.get(c)
        crow.append([c.replace("_", " ").title(), f"{w:+.2f}", pct(pres[c], 0),
                     pct(ap[1] / ap[0], 0) if ap and ap[0] >= 100 else ".", pct(hp[1] / hp[0], 0) if hp and hp[0] >= 100 else "."])
    return rows, crow, info


def exam_section(path: Path, id_map: Path = be.DEFAULT_ID_MAP) -> tuple[str, dict]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = doc["rows"]
    nums: dict = {"runs": doc["runs"], "decisions": len(rows)}
    out = [f"{doc['runs']:,} exam-fifth runs, {len(rows):,} decisions scored in Acts 1 and 2 ({doc['skipped']} without donor maps).\n"]
    cr = [r for r in rows if r["type"] == "card_reward"]
    rest = [r for r in rows if r["type"] == "rest"]
    tbl = []
    for lab, sel in (("Act 1", [r for r in cr if r["act"] == 0]), ("Act 2", [r for r in cr if r["act"] == 1]), ("Both", cr)):
        n = len(sel)
        if n < MIN_CELL:
            continue
        tbl.append([lab, f"{n:,}", pct(sum(r["top"] == r["human"] for r in sel) / n, 0), pct(sum(r["rank"] <= 1 for r in sel) / n, 0),
                    pct(sum(r["human_skip"] for r in sel) / n, 0), pct(sum(r["ai_skip"] for r in sel) / n, 0),
                    pct(sum(r["human_skip"] == r["ai_skip"] for r in sel) / n, 0), f1(sum(r["regret"] for r in sel) / n, 2)])
        nums[f"card_{lab}"] = {"n": n, "same_choice": sum(r["top"] == r["human"] for r in sel) / n,
                               "human_skip": sum(r["human_skip"] for r in sel) / n, "ai_skip": sum(r["ai_skip"] for r in sel) / n,
                               "regret": sum(r["regret"] for r in sel) / n}
    out.append("Card rewards\n")
    out.append(table(["Act", "Decisions", "AI picks what the human picked", "Human's pick is the AI's first or second", "Human skips", "AI would skip",
                      "Same take-or-skip", "Floors the AI thinks the human's pick loses"], tbl))
    # per card: how often taken when offered, human vs the AI chooser
    off: Counter = Counter()
    h_take: Counter = Counter()
    a_take: Counter = Counter()
    for r in cr:
        for c in set(r["offered"]):
            off[c] += 1
            h_take[c] += r["human_card"] == c
            a_take[c] += r["ai_card"] == c
    id_name = {v: be.slug(k) for k, v in json.loads(Path(id_map).read_text(encoding="utf-8"))["cards"].items()}
    gaps = sorted(((a_take[c] - h_take[c]) / off[c], c) for c in off if off[c] >= 150)
    crow = [[id_name.get(c, str(c)).replace("_", " ").title(), f"{off[c]:,}", pct(h_take[c] / off[c], 0), pct(a_take[c] / off[c], 0), f"{100 * g:+.0f}"]
            for g, c in gaps[:8] + gaps[-8:]]
    out.append("Cards the AI's chooser would take far less or far more often than the humans did, from the same states (cards offered 150 times or more)\n")
    out.append(table(["Card", "Offered", "Human took it", "AI would take it", "Gap (points)"], crow))
    # rest sites
    rt = []
    for lab, sel in (("Act 1", [r for r in rest if r["act"] == 0]), ("Act 2", [r for r in rest if r["act"] == 1])):
        for hb in be.HP_BINS:
            part = [r for r in sel if r["hp_frac"] is not None and be.hp_bin(r["hp_frac"]) == hb]
            if len(part) < MIN_CELL:
                continue
            n = len(part)
            rt.append([lab, hb, f"{n:,}", pct(sum(r["human_smith"] for r in part) / n, 0), pct(sum(r["ai_smith"] for r in part) / n, 0),
                       pct(sum(r["human_smith"] == r["ai_smith"] for r in part) / n, 0)])
    out.append("Rest sites: the share spent on an upgrade, by HP on arrival\n")
    out.append(table(["Act", "HP on arrival", "Decisions", "Human upgrades", "AI would upgrade", "Same choice"], rt))
    nums["rest"] = {"n": len(rest), "human_smith": sum(r["human_smith"] for r in rest) / max(len(rest), 1),
                    "ai_smith": sum(r["ai_smith"] for r in rest) / max(len(rest), 1),
                    "same": sum(r["human_smith"] == r["ai_smith"] for r in rest) / max(len(rest), 1)}
    return "\n".join(out), nums


def build(a: argparse.Namespace) -> tuple[str, dict]:
    cards = Cards.load(Path(a.export), Path(a.id_map))
    hum = list(be.read_jsonl(Path(a.human)))
    ex, tr = [r for r in hum if r.get("ex")], [r for r in hum if not r.get("ex")]
    sp = list(be.read_jsonl(Path(a.selfplay)))
    ai9 = [r for r in sp if r.get("gen") == 9]
    nights = list(be.read_jsonl(Path(a.nights)))
    by_night: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in nights:
        by_night[(r["night"], r["arm"])].append(r)
    nums: dict = {"human_all": be.headline(hum), "human_exam": be.headline(ex), "ai_gen9_selfplay": be.headline(ai9)}
    out: list[str] = []

    out.append("### 1. The run in one line, by source\n")
    rows = [headline_row("Humans, exam fifth", ex), headline_row("Humans, all runs", hum), headline_row("AI gen 9 self-play (emulator)", ai9)]
    for (night, arm), runs in sorted(by_night.items()):
        if arm.startswith("g9"):
            rows.append(headline_row(f"AI gen 9 night {night}, {'emulator' if arm.endswith('-emu') else 'real game'}", runs))
    out.append(table(HEADLINE_HEAD, rows))

    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"### {2 + act}. What each group brings to the {name} boss\n")
        rows = entry_rows("Humans (exam fifth)", ex, act, cards) + entry_rows("AI gen 9 self-play", ai9, act, cards)
        out.append(table(ENTRY_HEAD, rows))
    out.append("### 4. The path and the choices before the boss\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        rows = (path_rows(f"{name}, humans (exam fifth)", ex, act, cards, ("boss", "before")) +
                path_rows(f"{name}, AI gen 9 self-play", ai9, act, cards, ("boss", "before")))
        out.append(table(PATH_HEAD, rows))

    out.append("### 5. Rest sites: the share spent on an upgrade, by HP on arrival\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"{name}\n")
        out.append(table(["HP on arrival", "AI sites", "AI upgrade share", "Human sites", "Human upgrade share"],
                         rest_hp_rows(ai9, ex, act)))

    out.append("### 6. Cards in the deck at the boss: share of runs holding each\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"{name} boss\n")
        out.append(table(["Card", "AI gen 9", "Humans (exam fifth)"], top_card_rows(ai9, ex, act, cards)))

    out.append("### 7. Card rewards: pick rate when offered (cards before the boss; largest gaps)\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"{name}\n")
        out.append(table(["Card", "AI offers", "AI pick rate", "Human offers", "Human pick rate", "Gap (points)"], pick_gap_rows(ai9, ex, act)))

    out.append("### 8. Each boss\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"{name}\n")
        out.append(table(["Boss", "AI visits", "AI kill rate", "AI HP share", "Human visits", "Human kill rate", "Human HP share"],
                         boss_rows(ai9, ex, act)))

    out.append("### 9. Who would win from whose hand\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        rows, shifts, info = model_rows(ai9, tr, ex, act, cards)
        nums[f"model_act{act + 1}"] = info
        out.append(f"{name} boss ({info.get('n_ai', 0):,} AI visits, {info.get('n_hum_train', 0):,} human visits for the model, "
                   f"{info.get('n_hum_exam', 0):,} exam-fifth visits)\n")
        if rows:
            out.append(table(["Kill share", "AI's entry states", "Humans' entry states"], rows))
            out.append(table(["Moving the AI's average to the human exam average", "AI now", "Human", "AI model: change in the AI's kill share (points)",
                              "Human model: change in the humans' kill share if their average moved to the AI's (points)"], shifts))

    out.append("### 10. The same figures by night (path and choices before the Act 1 boss)\n")
    rows = []
    for (night, arm), runs in sorted(by_night.items()):
        c = cell(runs, 0, "boss", cards)
        if c.get("n", 0) < MIN_CELL:
            continue
        p = c["path"]
        rows.append([night, "emulator" if arm.endswith("-emu") else "real game", arm.split("-")[0], f"{c['n']:,}", f1(c["taken"], 2),
                     pct(c["skip_rate"], 0), f1(c["rest_smith"], 2), f1(c["rest_heal"], 2),
                     f"{f1(p['M'])} / {f1(p['E'], 2)} / {f1(p['S'], 2)} / {f1(p['?'])}" if arm.endswith("-emu") else "(logged only where a choice existed)"])
    out.append(table(["Night", "Arm", "Agent", "Visits to the boss", "Cards taken", "Skip rate", "Upgrades", "Heals", "Fights / elites / shops / ? rooms"], rows))

    out.append("### 11. Self-play by generation (reached the Act 1 boss)\n")
    rows = []
    for g in sorted({r.get("gen") for r in sp}):
        runs = [r for r in sp if r.get("gen") == g]
        h = be.headline(runs)
        c = cell(runs, 0, "boss", cards)
        if c.get("n_snap", 0) >= MIN_CELL:
            rows.append([f"gen {g}", f"{h['n']:,}", f1(h["floor"]), pct(h["a1_kill_rate"]), f"{f1(c['hp'])} / {f1(c['mhp'])}", f1(c["deck"]),
                         f1(c["upgraded"]), f1(c["relics"]), f1(c["potions"]), f1(c["path"]["E"], 2), f1(c["taken"], 2)])
    out.append(table(["Agent", "Runs", "Mean floor", "Kill Act 1 boss", "HP / max", "Cards", "Upgraded", "Relics", "Potions", "Elites", "Cards taken"], rows))

    out.append("### 12. Potions and elites before the boss\n")
    out.append(table(["Act", "Group", "Visits", "Potion rewards taken", "Potion rewards left", "Elites fought", "Elite taken when on offer", "Map choices with an elite on offer"],
                     potion_elite_rows(ai9, ex, cards)))
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"{name} boss visits by the elites fought before it\n")
        out.append(table(["Elites fought", "AI visits", "AI kill share", "AI HP share", "AI relics", "Human visits", "Human kill share",
                          "Human HP share", "Human relics"], elite_dose_rows(ai9, ex, act)))
    out.append("### 13. Boss kill share by what the run brought\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        out.append(f"{name} boss\n")
        out.append(table(["Factor", "Level", "AI visits", "AI kill share", "Human visits", "Human kill share"], dose_rows(ai9, ex, act, cards)))
    out.append("### 14. The same, with the cards in the deck\n")
    for act, name in ((0, "Act 1"), (1, "Act 2")):
        rows, crow, info = card_model_rows(ai9, tr, ex, act, cards, be.pick_rates(ai9, act), be.pick_rates(ex, act))
        nums[f"card_model_act{act + 1}"] = info
        if rows:
            out.append(f"{name} boss\n")
            out.append(table(["Model", "AUC", "Kill share on the AI's entry states", "Kill share on the exam fifth's"], rows))
            out.append(table(["Card (human model)", "Effect per copy (log-odds)", "Held at the boss by humans (other fifths)", "AI picks it when offered", "Humans pick it when offered"], crow))
    if getattr(a, "exam", None) and Path(a.exam).is_file():
        out.append("### 15. The per-decision exam: the AI's chooser on the humans' states (held-out fifth)\n")
        txt, en = exam_section(Path(a.exam))
        nums["exam"] = en
        out.append(txt)
    out.append("### 16. The loop's saved fight starts (nightly emulator arms, 50 runs a night)\n")
    out.append(table(["Night", "Boss", "Starts", "HP / max", "HP share", "Cards", "Relics", "Potions"], starts_rows(Path(a.starts))))
    return "\n".join(out), nums


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--human", required=True)
    ap.add_argument("--selfplay", required=True)
    ap.add_argument("--nights", required=True)
    ap.add_argument("--starts", default="D:/spireline/referee/gym-loop/starts/starts.lite.json")
    ap.add_argument("--export", default=str(be.DEFAULT_EXPORT))
    ap.add_argument("--id-map", default=str(be.DEFAULT_ID_MAP))
    ap.add_argument("--out", required=True)
    ap.add_argument("--json")
    ap.add_argument("--exam")
    a = ap.parse_args(argv)
    md, nums = build(a)
    Path(a.out).write_text(md, encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(nums, indent=1), encoding="utf-8")
    print(f"wrote {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
