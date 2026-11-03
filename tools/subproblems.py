"""The sub-problem board's numbers (docs/SUBPROBLEMS.md): six pieces of the AI's game, each against the humans, from files that exist.

    python tools/subproblems.py refresh --out docs/subproblems.json [--render docs/SUBPROBLEMS.md] [--night LAB/nightly/<date>]
        [--gen N] [--humans humans.json] [--agreement agreement.json]
    python tools/subproblems.py render --json docs/subproblems.json --doc docs/SUBPROBLEMS.md
    python tools/subproblems.py humans --out humans.json          # one pass over the human corpus, about 1.5 minutes

`refresh` reads, in seconds, and runs no game and no emulator:
  - the newest finished night with at least 1,000 real-arm rows (`--min-rows`; the newest finished night when none has): `tools/morning_report.py`
    is run on it and its JSON gives the per-fight survival by act and kind
    (real arm and emulator arm); the emulator arm's rows give the route (every map step is logged there), the real arm's rows the
    card picks and skips;
  - the lab's self-play shards of the night's generation (the runs played without exploration): HP, relics, potions, gold, deck and
    shop buys at the Act 1 and Act 2 boss doors, and where the AI drinks a potion (the potions held entering a fight against the
    potions in the first state after it, which only a won fight has);
  - the fight board and the gym's per-kind start sets (`referee/gym-loop/board`, `starts/weights.json`): the AI against the 200
    Act 1 boss starts, ten replays each, the win rate per kind, the potions used in each replay;
  - the per-decision exam on the held-out fifth (`referee/backlog/boss-entry/exam-rows.json`, and an `agreement` output when given);
  - the human side from the boss-entry cache (`human.jsonl.gz`, the exam fifth only) and, when `humans` has been run, from its
    aggregates: Act 1 and 2 fight survival by kind and the potions used in the fights survived.

Every piece of the output is `{value, n, source, date}` or `{"status": "not measured", "reason", "measure_with"}`; a piece whose input is
missing is "not measured", never a guess. Human numbers are aggregates over cells of at least MIN_CELL (D13); the held-out fifth is read
only to score the AI. Paths in the output are relative to the project root (`D:/spireline/`).
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boss_entry as be  # noqa: E402

MIN_CELL = be.MIN_CELL  # D13
ROOT = Path("D:/spireline")
NIGHTLY = ROOT / "referee/LAB/nightly"
RUNS_ROOT = ROOT / "referee/LAB/runs"
LOOP = ROOT / "referee/gym-loop"
BOSS_DIR = ROOT / "referee/backlog/boss-entry"
HUMAN_CACHE = BOSS_DIR / "human.jsonl.gz"
EXAM_ROWS = BOSS_DIR / "exam-rows.json"
HUMANS_JSON = BOSS_DIR / "humans.json"  # the output of `humans`, kept beside the other caches (never committed)
AGREEMENT_JSON = BOSS_DIR / "agreement.json"  # the output of `boss_entry_exam.py agreement`, likewise
MORNING = Path(__file__).resolve().parent / "morning_report.py"
FIGHT_KIND = {1: "hallway", 2: "elite", 6: "boss"}  # the emulator's node types of a fight (run_train.vocab.NODE_*)
MARK_START, MARK_END = "<!-- subproblems:table:start -->", "<!-- subproblems:table:end -->"

# What the 2026-11-02 boss-entry fits say closing a gap could buy, in points of the boss kill share (an association inside two logistic
# fits, not a test: docs/diagnostics/2026-11-02-boss-entry.md, the ranked table and tables 9 and 14).
COULD_BUY = {
    "boss1": ["17 to 23 (the play, not the hand)", "27 to 44 (the play); 22 to 39 is the hand"],
    "route": ["0 to +6 net of the HP the fights cost", "potions +5 to +9, relics +4 to +9, HP share +3 to +5"],
    "cards": ["0 to +2", "+2 to +10"],
    "potions": ["+9 to +10", "+5 to +9"],
    "shops": ["+3 to +8 (relics); gold 0", "+4 to +9 (relics); gold 0"],
}
FAST_TESTS = {  # what runs, what it reads, how long (each time has its source in docs/SUBPROBLEMS.md)
    "boss1": "fight board, 200 Act 1 boss starts x 10 replays: 400 games in about 8 minutes (the gate's stage 1), 2,000 in about 35",
    "act2": "the gym's Act 2 start sets (hallway, elite, boss) in the loop's weights step: 100 games a kind, about 14 minutes for the three",
    "route": "`subproblems.py refresh`: the emulator arm's rows and the shards, about 11 seconds; a fresh 200-run batch about 8 minutes",
    "cards": "`boss_entry_exam.py agreement` on a seeded 1,000 runs of the held-out fifth (14,013 decisions): 8 minutes for a candidate and the incumbent (the full exam: 11 minutes)",
    "potions": "`subproblems.py refresh`: the shards' potions at the doors and in fights, and the board's replays, about 11 seconds",
    "shops": "`subproblems.py refresh`: the shards' relics, gold and shop buys at the doors, about 11 seconds",
}


# ------------------------------------------------------------------------------------------------ small helpers


def rel(path: Path | str, root: Path = ROOT) -> str:
    """A path relative to the project root, forward slashes (results never hold absolute paths); the file name alone when outside it.
    Junctions are not followed, so a folder moved to another drive keeps its place in the project tree."""
    p, r = Path(os.path.abspath(path)), Path(os.path.abspath(root))
    try:
        return p.relative_to(r).as_posix()
    except ValueError:
        return p.name


def rate(k: int, n: int, source: str = "", date: str = "") -> dict:
    """A rate with its sample: k of n, the share and its standard error (cells under MIN_CELL are not published)."""
    if n < MIN_CELL:
        return {"status": "suppressed", "n": n, "source": source}
    p = k / n
    out = {"k": k, "n": n, "value": p, "se": math.sqrt(p * (1 - p) / n), "source": source}
    if date:
        out["date"] = date
    return out


def mean_of(xs: list[float], source: str = "", date: str = "") -> dict:
    n = len(xs)
    if n < MIN_CELL:
        return {"status": "suppressed", "n": n, "source": source}
    out = {"value": sum(xs) / n, "n": n, "source": source}
    if date:
        out["date"] = date
    return out


def not_measured(reason: str, measure_with: str) -> dict:
    return {"status": "not measured", "reason": reason, "measure_with": measure_with}


def val(d: Any, *path: str) -> float | None:
    """A number inside nested dicts; None when a step is missing or the cell is not a measurement."""
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d.get("value") if isinstance(d, dict) else d


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ the newest finished night


def newest_finished_night(root: Path = NIGHTLY, min_rows: int = 0) -> tuple[Path, str] | None:
    """The newest night folder whose real arm has its result and summary files, whose emulator arm has rows and whose real arm has at least
    `min_rows` rows (a 500-seed night checks a fix; a 2,000-seed night measures): (folder, agent label)."""
    for d in sorted((p for p in Path(root).iterdir() if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)), reverse=True):
        for arm in sorted((p for p in d.iterdir() if p.is_dir() and re.fullmatch(r"g\d+", p.name)), key=lambda p: -int(p.name[1:])):
            if (arm / "result.json").is_file() and (arm / "summary.json").is_file() and (d / f"{arm.name}-emu" / "runs.jsonl").is_file():
                if min_rows and sum(1 for _ in (arm / "runs.jsonl").open("rb")) < min_rows:
                    continue
                return d, arm.name
    return None


def run_morning(night: Path, agent: str, runner=subprocess.run, script: Path = MORNING) -> dict | None:
    """`tools/morning_report.py` on the night (Windows log skipped), its JSON read back; None when it fails."""
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, "-I", str(script), str(night), "--agent", agent, "--winlog", "none", "--out", tmp]
        done = runner(cmd, capture_output=True, text=True, timeout=600)
        out = Path(tmp) / "morning_report.json"
        if getattr(done, "returncode", 1) != 0 or not out.is_file():
            return None
        return read_json(out)


def survival(morning: dict) -> dict:
    """The per-fight survival by act and kind, both arms, from morning_report.json (`fights`): {arm: {"a2.elite": rate cell}}."""
    date = (morning.get("night") or {}).get("date", "")
    out: dict = {}
    for arm in ("real", "emu"):
        cells = {}
        for row in (morning.get("fights") or {}).get(arm) or []:
            key = f"a{row['act']}.{row['kind']}"
            n = int(row.get("fights") or 0)
            cells[key] = rate(int(row["survived"]), n, f"morning_report.json, {arm} arm", date) if row.get("survived") is not None else \
                {"status": "suppressed", "n": n, "source": f"morning_report.json, {arm} arm"}
        out[arm] = cells
    return out


def night_header(morning: dict) -> dict:
    night, real = morning.get("night") or {}, morning.get("real") or {}
    return {"date": night.get("date"), "agent": night.get("agent"), "generation": night.get("generation"),
            "folder": night.get("folder"), "real_ended": real.get("ended"), "real_mean_floor": real.get("mean_floor"),
            "act1_boss_kill_of_reached": rate(int(real.get("act1_killed") or 0), int(real.get("act1_reached") or 0),
                                              "morning_report.json, real arm", night.get("date") or ""),
            "act2_boss_kill_of_reached": rate(int(real.get("act2_killed") or 0), int(real.get("act2_reached") or 0),
                                              "morning_report.json, real arm", night.get("date") or "")}


# ------------------------------------------------------------------------------------------------ the nightly rows: route and picks


def night_rows(path: Path) -> list[dict]:
    return [s for s in (be.night_summary(r) for r in be.read_jsonl(path)) if s]


def route_figures(emu_rows: list[dict], cards: be.Cards, source: str, date: str) -> dict:
    """Elites, fights and rests before the Act 1 boss, per run that reached it, from the emulator arm (it logs every map step)."""
    out = {}
    for act, tag in ((0, "a1"), (1, "a2")):
        c = be.cell(emu_rows, act, "boss", cards)
        n = c.get("n", 0)
        if n < MIN_CELL:
            out[tag] = {"status": "suppressed", "n": n, "source": source}
            continue
        p = c["path"]
        out[tag] = {"n": n, "source": source, "date": date, "elites": p["E"], "fights": p["M"] + p["E"], "rests": p["R"], "shops": p["S"]}
    return out


def pick_figures(real_rows: list[dict], cards: be.Cards, source: str, date: str) -> dict:
    """Card rewards before each boss, per boss-reaching run, from the real arm's rows: cards taken and the skip share."""
    out = {}
    for act, tag in ((0, "a1"), (1, "a2")):
        c = be.cell(real_rows, act, "boss", cards)
        n = c.get("n", 0)
        out[tag] = {"status": "suppressed", "n": n, "source": source} if n < MIN_CELL else \
            {"n": n, "source": source, "date": date, "taken": c["taken"], "skipped": c["skipped"], "skip_rate": c["skip_rate"]}
    return out


# ------------------------------------------------------------------------------------------------ self-play shards: the doors and potion use


def shard_jobs(runs_root: Path, gen: int, exploring: bool = False) -> list[Path]:
    """The shard folders of a generation's self-play jobs; jobs that explore (a non-zero `eps` in the agent block of their shards.json) are left out by default."""
    out = []
    for job in sorted(Path(runs_root).glob("*selfplay*")):
        meta = job / "shards" / "shards.json"
        if not meta.is_file():
            continue
        try:
            m = read_json(meta)
        except (ValueError, OSError):
            continue
        if int(m.get("generation", -1)) != gen:
            continue
        if not exploring and float((m.get("agent") or {}).get("eps") or 0) > 0:
            continue
        out.append(job / "shards")
    return out


def potion_fights(rec: dict) -> list[tuple[int, str, int, int | None]]:
    """(act index, kind, potions held entering the fight, potions used in it or None when no state after it exists) for each hallway,
    elite and boss fight of a run record. The first decision on the fight's floor is taken after the fight, so its potions are the
    ones left; a lost fight ends the run and leaves no such decision."""
    decs = rec.get("decisions") or []
    out = []
    for f in rec.get("fights") or []:
        kind = FIGHT_KIND.get(f.get("node_type"))
        if kind is None:
            continue
        st = f["state"]
        held = len(st.get("potions") or [])
        nxt = next((d for d in decs if d["state"].get("floor") == st.get("floor") and d["state"].get("act_index") == st.get("act_index")), None)
        used = max(0, held - len(nxt["state"].get("potions") or [])) if nxt is not None and f.get("won") else None
        out.append((int(st.get("act_index", 0)), kind, held, used))
    return out


def potion_budget(rec: dict) -> dict | None:
    """Where a run's potions went before the Act 1 boss: the potions used in the hallway and elite fights it won, the potions held as the
    boss fight opened, and (as a check on the method) all the potions gained and all the drops in the potion count between its decisions
    before the boss. None when the run never reached the Act 1 boss."""
    boss = next((f for f in rec.get("fights") or [] if f.get("node_type") == 6 and f["state"].get("act_index") == 0), None)
    if boss is None:
        return None
    out = {"hallway": 0, "elite": 0, "door": len(boss["state"].get("potions") or []), "gained": 0, "dropped": 0}
    for act, kind, _held, used in potion_fights(rec):
        if act == 0 and kind in ("hallway", "elite") and used:
            out[kind] += used
    decs = [d for d in rec.get("decisions") or [] if d["state"].get("act_index") == 0 and d["state"].get("floor", 99) < be.BOSS_FLOOR[0]]
    for a, b in zip(decs, decs[1:]):
        x, y = len(a["state"].get("potions") or []), len(b["state"].get("potions") or [])
        out["gained"] += max(0, y - x)
        out["dropped"] += max(0, x - y)
    return out


def budget_figures(budgets: list[dict], source: str, date: str = "") -> dict:
    """The mean potions per run (that reached the Act 1 boss) used in hallway fights and in elite fights, and held at the boss door; for the
    shards also the potions gained and the share of all drops that fall inside the fights the method sees."""
    n = len(budgets)
    if n < MIN_CELL:
        return {"status": "suppressed", "n": n, "source": source}
    m = {k: sum(b[k] for b in budgets) / n for k in ("hallway", "elite", "door")}
    used = m["hallway"] + m["elite"]
    out = {"n": n, "source": source, "date": date, "used_hallway": m["hallway"], "used_elite": m["elite"], "held_at_door": m["door"],
           "hallway_share_of_used": m["hallway"] / used if used else None}
    if all("gained" in b for b in budgets):
        gained, dropped = sum(b["gained"] for b in budgets) / n, sum(b["dropped"] for b in budgets) / n
        out.update(gained=gained, dropped=dropped, drops_explained_by_fights=used / dropped if dropped else None)
    return out


def read_shards(shards: list[Path], cards: be.Cards) -> tuple[list[dict], list[tuple[int, str, int, int | None]], list[dict]]:
    summaries, pots, budgets = [], [], []
    for sd in shards:
        for p in sorted(sd.glob("r*.jsonl.gz")):
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    summaries.append(be.ai_summary(rec, cards))
                    pots.extend(potion_fights(rec))
                    b = potion_budget(rec)
                    if b is not None:
                        budgets.append(b)
    return summaries, pots, budgets


def door_figures(runs: list[dict], cards: be.Cards, source: str, date: str = "") -> dict:
    """What a group brings to each boss door (the cohort that reached the boss): holdings, route and shop figures, and the boss kill."""
    out = {}
    for act, tag in ((0, "a1"), (1, "a2")):
        c = be.cell(runs, act, "boss", cards)
        n = c.get("n", 0)
        if n < MIN_CELL:
            out[tag] = {"status": "suppressed", "n": n, "source": source}
            continue
        sel = [r["a"][act] for r in runs if be.in_cohort(r["a"][act], "boss")]
        known = [a for a in sel if a.get("k") is not None]
        d = {"n": n, "source": source, "date": date, "kill": rate(sum(a["k"] == 1 for a in known), len(known), source, date)}
        for k in ("hp_frac", "relics", "potions", "gold", "deck", "upgraded", "attack", "skill", "elite_take_rate", "pot_taken", "pot_left",
                  "shop_visits", "shop_cards", "shop_relics", "shop_removals", "skip_rate"):
            if k in c:
                d[k] = c[k]
        d["elites"], d["fights"] = c["path"]["E"], c["path"]["M"] + c["path"]["E"]
        out[tag] = d
    return out


def potion_use_figures(pots: list[tuple[int, str, int, int | None]], source: str, date: str = "") -> dict:
    """The AI's potion use from fights with a state after them: of the fights entered holding a potion, the share that used one."""
    cells: dict = defaultdict(lambda: {"fights": 0, "held": 0, "seen": 0, "seen_held": 0, "used_any": 0, "used": 0})
    for act, kind, held, used in pots:
        c = cells[f"a{act + 1}.{kind}"]
        c["fights"] += 1
        c["held"] += held > 0
        if used is not None:
            c["seen"] += 1
            if held > 0:
                c["seen_held"] += 1
                c["used_any"] += used > 0
                c["used"] += used
    out = {}
    for key, c in sorted(cells.items()):
        if c["fights"] < MIN_CELL:
            out[key] = {"status": "suppressed", "n": c["fights"], "source": source}
            continue
        cell = {"fights": c["fights"], "with_potion": c["held"] / c["fights"], "observed_after": c["seen"] / c["fights"], "source": source,
                "date": date, "note": "use is seen only in fights that were won (the run goes on); a lost fight has no state after it"}
        if c["seen_held"] >= MIN_CELL:
            cell["used_when_held"] = rate(c["used_any"], c["seen_held"], source, date)
            cell["potions_per_use_fight"] = c["used"] / c["seen_held"]
        out[key] = cell
    return out


# ------------------------------------------------------------------------------------------------ the fight board and the gym


def board_figures(board_dir: Path) -> dict:
    """Each fight player's rows on the board's Act 1 boss starts (200 starts, ten replays each): games, wins, the win rate with its
    standard error, the starts never or always won, and the potions used in the replays that began holding one."""
    versions = []
    for f in sorted(Path(board_dir).glob("fp-v*.jsonl"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0)):
        rows = [r for r in be.read_jsonl(f) if r.get("cat") == "act1-boss"]
        if not rows:
            continue
        per_start: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in rows:
            per_start[r["start"]][0] += 1
            per_start[r["start"]][1] += bool(r["won"])
        held = [r for r in rows if (r.get("start_potions") or 0) > 0]
        n = len(rows)
        v = {"version": f.stem.replace("fp-", ""), "players": sorted({str(r.get("player")) for r in rows}), "games": n, "starts": len(per_start),
             "replays_per_start": n / len(per_start), "overall": rate(sum(bool(r["won"]) for r in rows), n, rel(f)),
             "starts_never_won": sum(1 for g, w in per_start.values() if w == 0),
             "starts_always_won": sum(1 for g, w in per_start.values() if w == g)}
        if len(held) >= MIN_CELL:
            v["potions"] = {"games_with_potion": len(held), "used_any": rate(sum((r.get("potions_used") or 0) > 0 for r in held), len(held), rel(f)),
                            "won_with_potion": rate(sum(bool(r["won"]) for r in held), len(held), rel(f))}
        versions.append(v)
    return {"versions": versions, "latest": versions[-1] if versions else None}


def gym_kinds(weights: Path) -> dict:
    """The loop's own win rate per start kind (a fixed number of games each) from `starts/weights.json`."""
    if not Path(weights).is_file():
        return not_measured("no weights.json", "the loop's weights step (starts/weights.json)")
    w = read_json(weights)
    return {"player": w.get("player"), "config": w.get("config"), "written": w.get("written"), "source": rel(weights),
            "note": "the incumbent's games on training starts of each kind (the loop's start mix), not the board's fixed set",
            "kinds": {k: rate(round(v * w["games"][k]), int(w["games"][k]), rel(weights), (w.get("written") or "")[:10])
                      if int(w["games"][k]) >= MIN_CELL else {"status": "suppressed"} for k, v in (w.get("win") or {}).items()}}


# ------------------------------------------------------------------------------------------------ the per-decision exam


def exam_figures(doc: dict, source: str, date: str = "") -> dict:
    """The exam rows (`boss_entry_exam.py exam`): card rewards and rest sites by act; the AI's chooser against the humans' choices."""
    rows = doc["rows"]
    out: dict = {"runs": doc.get("runs"), "decisions": len(rows), "source": source, "date": date}
    for act, tag in ((0, "a1"), (1, "a2")):
        cr = [r for r in rows if r["type"] == "card_reward" and r["act"] == act]
        rest = [r for r in rows if r["type"] == "rest" and r["act"] == act]
        n = len(cr)
        if n >= MIN_CELL:
            out[f"card_{tag}"] = {"n": n, "same_pick": rate(sum(r["top"] == r["human"] for r in cr), n, source, date),
                                  "first_or_second": rate(sum(r["rank"] <= 1 for r in cr), n, source, date),
                                  "human_skip": rate(sum(bool(r["human_skip"]) for r in cr), n, source, date),
                                  "ai_skip": rate(sum(bool(r["ai_skip"]) for r in cr), n, source, date),
                                  "chance": sum(1 / (len(r["offered"]) + 1) for r in cr) / n,
                                  "regret_floors": sum(r["regret"] for r in cr) / n}
        if len(rest) >= MIN_CELL:
            out[f"rest_{tag}"] = {"n": len(rest), "same_choice": rate(sum(r["human_smith"] == r["ai_smith"] for r in rest), len(rest), source, date),
                                  "human_upgrade": rate(sum(bool(r["human_smith"]) for r in rest), len(rest), source, date),
                                  "ai_upgrade": rate(sum(bool(r["ai_smith"]) for r in rest), len(rest), source, date)}
    return out


def agreement_figures(doc: dict, source: str) -> dict:
    """An `agreement` output (counts and rates only): the incumbent's share of decisions that match the human's, and the candidates'."""
    return {"source": source, "runs": doc.get("runs"), "scored": doc.get("scored"), "incumbent": doc.get("incumbent", {}).get("agreement"),
            "candidates": [{"label": c.get("label"), "measures": c.get("measures")} for c in doc.get("candidates") or []]}


# ------------------------------------------------------------------------------------------------ the human side


def human_door(cache: Path, cards: be.Cards) -> dict | None:
    """The exam fifth at the Act 1 and Act 2 boss doors, from the boss-entry cache (`boss_entry.py human`)."""
    if not Path(cache).is_file():
        return None
    runs = [r for r in be.read_jsonl(cache) if r.get("ex")]
    return door_figures(runs, cards, f"{rel(cache)}, exam fifth", "2026-11-02") if runs else None


def human_fight_events(r: dict) -> list[tuple[int, str, bool, int, int]]:
    """(act index, kind, died in it, potions held entering it, potions used in it) for each hallway, elite and boss fight of Acts 1 and 2
    in a human run record. Event fights (an unknown room that turned out a fight) are not counted, as in the AI's table."""
    acts = list(r.get("map_point_history") or [])
    flat = [pt for a in acts for pt in a]
    killed = (r.get("killed_by_encounter") or "NONE.NONE") != "NONE.NONE" and not r.get("win")
    out, j = [], 0
    for a, pts in enumerate(acts[:2]):
        base = sum(len(x) for x in acts[:a])
        for i, pt in enumerate(pts):
            j = base + i
            kind = {"monster": "hallway", "elite": "elite", "boss": "boss"}.get(pt.get("map_point_type"))
            if kind is None:
                continue
            ps = (pt.get("player_stats") or [{}])[0]
            out.append((a, kind, killed and j == len(flat) - 1, be.human_potions(flat[:j]), len(ps.get("potion_used") or [])))
    return out


def human_potion_budget(r: dict) -> dict | None:
    """The same budget for a human run: potions used in the hallway and elite rooms of Act 1 and potions held entering the boss room;
    None when the run never reached the Act 1 boss."""
    acts = list(r.get("map_point_history") or [])
    if not acts or not acts[0] or acts[0][-1].get("map_point_type") != "boss":
        return None
    flat = [pt for a in acts for pt in a]
    out = {"hallway": 0, "elite": 0, "door": be.human_potions(flat[: len(acts[0]) - 1])}
    for pt in acts[0][:-1]:
        kind = {"monster": "hallway", "elite": "elite"}.get(pt.get("map_point_type"))
        if kind:
            out[kind] += len((pt.get("player_stats") or [{}])[0].get("potion_used") or [])
    return out


def human_fight_figures(runs: Any, source: str) -> dict:
    """Aggregates over human run records of the exam fifth: survival by act and kind, and the potions used in the fights survived."""
    cells: dict = defaultdict(lambda: {"fights": 0, "died": 0, "held": 0, "used_any": 0})
    n_runs, budgets = 0, []
    for r in runs:
        n_runs += 1
        b = human_potion_budget(r)
        if b is not None:
            budgets.append(b)
        for a, kind, died, held, used in human_fight_events(r):
            c = cells[f"a{a + 1}.{kind}"]
            c["fights"] += 1
            c["died"] += died
            if not died and held > 0:
                c["held"] += 1
                c["used_any"] += used > 0
    surv, pots = {}, {}
    for key, c in sorted(cells.items()):
        surv[key] = rate(c["fights"] - c["died"], c["fights"], source)
        pots[key] = {"used_when_held": rate(c["used_any"], c["held"], source)}
    return {"runs": n_runs, "survival": surv, "potion_use": pots, "potion_budget": budget_figures(budgets, source), "source": source,
            "note": "a fight is survived unless it is the last room of a run killed by an encounter; potions held are rebuilt from the record"}


def cmd_humans(a: argparse.Namespace) -> int:
    be.below_normal()
    cards = be.Cards.load()  # the vanilla filter of the boss-entry cache: every final card and relic is in the emulator's id map

    def runs():
        with be.opener(Path(a.corpus)) as fh:
            for line in fh:
                if '"ascension":10' not in line or "CHARACTER.IRONCLAD" not in line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if be.human_ok(r) and be.is_exam(r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}") and cards.vanilla(r):
                    yield r

    doc = human_fight_figures(runs(), "human corpus, exam fifth, one pass (tools/subproblems.py humans)")
    doc["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    Path(a.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"humans: {doc['runs']} exam-fifth runs", file=sys.stderr)
    return 0


# ------------------------------------------------------------------------------------------------ the document's table


def pc(x: float | None, nd: int = 1) -> str:
    return "not measured" if x is None else f"{100 * x:.{nd}f}%"


def num(x: float | None, nd: int = 2) -> str:
    return "not measured" if x is None else f"{x:.{nd}f}"


def cell_n(d: Any, *path: str) -> str:
    for p in path:
        if not isinstance(d, dict):
            return "?"
        d = d.get(p)
    return f"{d['n']:,}" if isinstance(d, dict) and "n" in d else "?"


def gap_pts(a: float | None, b: float | None) -> str:
    """AI minus human, in points, from two shares."""
    return "not measured" if a is None or b is None else f"{100 * (a - b):+.1f}"


def table_rows(doc: dict) -> list[list[str]]:
    """The summary table's rows: piece, what is counted, the AI's number, the humans', the gap, what closing it could buy, the fast test."""
    nt, sv = doc.get("night") or {}, (doc.get("survival") or {}).get("real") or {}
    hd, ad = doc.get("human_door") or {}, doc.get("ai_door") or {}
    hf = doc.get("human_fights") or {}
    nd = nt.get("date") or "?"
    rows = []
    # 1. the first-boss fight
    a, h = val(nt, "act1_boss_kill_of_reached"), val(hd, "a1", "kill")
    rows.append(["1. First-boss fight", "Act 1 boss killed, of runs that reach it",
                 f"{pc(a)} (night {nd}, {cell_n(nt, 'act1_boss_kill_of_reached')} fights)", f"{pc(h)} ({cell_n(hd, 'a1', 'kill')} visits)",
                 gap_pts(a, h), COULD_BUY["boss1"][0], FAST_TESTS["boss1"]])
    # 2. Act 2 fights by kind
    a2, h2 = val(sv, "a2.boss"), val(hd, "a2", "kill")
    hs = hf.get("survival") or {}
    rows.append(["2. Act 2 fights by kind", "Act 2 fights survived: hallway / elite / boss",
                 f"{pc(val(sv, 'a2.hallway'))} / {pc(val(sv, 'a2.elite'))} / {pc(a2)} (night {nd}, {cell_n(sv, 'a2.boss')} boss fights)",
                 f"{pc(val(hs, 'a2.hallway'))} / {pc(val(hs, 'a2.elite'))} / {pc(h2)} ({cell_n(hd, 'a2', 'kill')} boss visits)",
                 f"{gap_pts(val(sv, 'a2.hallway'), val(hs, 'a2.hallway'))} / {gap_pts(val(sv, 'a2.elite'), val(hs, 'a2.elite'))} / {gap_pts(a2, h2)}",
                 COULD_BUY["boss1"][1], FAST_TESTS["act2"]])
    # 3. the route
    rt = (doc.get("route") or {}).get("a1") or {}
    ae, he = rt.get("elites"), val(hd, "a1", "elites")
    rows.append(["3. Route", "Elites fought before the Act 1 boss, per run that reaches it",
                 "not measured" if ae is None else f"{ae:.2f} (emulator arm, night {nd}, {rt['n']:,} runs)", f"{num(he)} ({cell_n(hd, 'a1')} runs)",
                 "not measured" if ae is None or he is None else f"{ae - he:+.2f} elites", COULD_BUY["route"][0], FAST_TESTS["route"]])
    # 4. card picks and skips
    ex = doc.get("exam") or {}
    chance = (ex.get("card_a1") or {}).get("chance")
    ag = (doc.get("agreement") or {}).get("incumbent") or {}
    base = f"; fast-test baseline {pc(ag.get('card_reward'), 1)} cards / {pc(ag.get('rest'), 1)} rests ({doc['agreement']['scored']:,} decisions)" if ag else ""
    rows.append(["4. Card picks and skips", "Card rewards where the AI's chooser takes the human's pick, Act 1 / Act 2; Act 2 skip share",
                 f"{pc(val(ex, 'card_a1', 'same_pick'), 0)} / {pc(val(ex, 'card_a2', 'same_pick'), 0)} (a coin: {pc(chance, 0)}); would skip {pc(val(ex, 'card_a2', 'ai_skip'), 0)}{base}",
                 f"skip {pc(val(ex, 'card_a2', 'human_skip'), 0)} ({cell_n(ex, 'card_a2')} Act 2 decisions)",
                 gap_pts(val(ex, "card_a2", "ai_skip"), val(ex, "card_a2", "human_skip")) + " (skip share)", COULD_BUY["cards"][0] + " (Act 2: +2 to +10)",
                 FAST_TESTS["cards"]])
    # 5. potions
    ap, hp_ = val(ad, "a1", "potions"), val(hd, "a1", "potions")
    ab = (doc.get("potion_use") or {}).get("ai_budget") or {}
    hb = hf.get("potion_budget") or {}

    def spent(b: dict) -> str:
        return "use not measured" if "used_hallway" not in b else f"{b['used_hallway'] + b['used_elite']:.1f} used a run before it, {b['used_hallway']:.1f} in hallway fights"

    rows.append(["5. Potions", "Potions held at the Act 1 boss door; potions used a run before it, and where",
                 f"{num(ap, 1)} held ({cell_n(ad, 'a1')} visits); {spent(ab)}", f"{num(hp_, 1)} held ({cell_n(hd, 'a1')} visits); {spent(hb)}",
                 "not measured" if ap is None or hp_ is None else f"{ap - hp_:+.1f} potions", COULD_BUY["potions"][0], FAST_TESTS["potions"]])
    # 6. shops and relics
    ar, hr = val(ad, "a1", "relics"), val(hd, "a1", "relics")
    rows.append(["6. Shops and relics", "Relics held at the Act 1 boss door, and bought in shops before it",
                 f"{num(ar, 1)} held, {num(val(ad, 'a1', 'shop_relics'))} bought ({cell_n(ad, 'a1')} visits)",
                 f"{num(hr, 1)} held, {num(val(hd, 'a1', 'shop_relics'))} bought ({cell_n(hd, 'a1')} visits)",
                 "not measured" if ar is None or hr is None else f"{ar - hr:+.1f} relics", COULD_BUY["shops"][0], FAST_TESTS["shops"]])
    return rows


def render_table(doc: dict) -> str:
    head = ["Piece", "Counted", "AI now", "Humans", "Gap (AI minus humans)", "Closing it could buy (points of boss kill, Act 1)", "Fast test and run time"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(c.replace("|", "/") for c in row) + " |" for row in table_rows(doc)]
    when = doc.get("generated_utc", "")
    src = (doc.get("night") or {}).get("date", "?")
    lines.append("")
    lines.append(f"Rendered by `tools/subproblems.py` from `docs/subproblems.json` ({when}; newest finished night {src}). Edit the numbers by rerunning the tool, not by hand.")
    return "\n".join(lines)


def render_into(text: str, table: str) -> str:
    """Replace what lies between the two markers; the markers must exist, once each."""
    if text.count(MARK_START) != 1 or text.count(MARK_END) != 1 or text.index(MARK_START) > text.index(MARK_END):
        raise ValueError("the document needs one start marker and one end marker, in that order")
    head, rest = text.split(MARK_START, 1)
    _old, tail = rest.split(MARK_END, 1)
    return f"{head}{MARK_START}\n{table}\n{MARK_END}{tail}"


# ------------------------------------------------------------------------------------------------ refresh


def build(night: tuple[Path, str] | None, morning: dict | None, gen: int | None, cards: be.Cards, shards: list[Path], board_dir: Path,
          weights: Path, human_cache: Path, exam_rows: Path, humans: dict | None, agreement: tuple[dict, str] | None) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc: dict = {"schema": 1, "generated_utc": now, "min_cell": MIN_CELL, "inputs": {}}
    if night and morning:
        folder, agent = night
        doc["night"] = night_header(morning)
        doc["survival"] = survival(morning)
        date = doc["night"]["date"] or ""
        emu = night_rows(folder / f"{agent}-emu" / "runs.jsonl")
        real = night_rows(folder / agent / "runs.jsonl")
        doc["route"] = route_figures(emu, cards, f"{rel(folder / (agent + '-emu'))}/runs.jsonl, emulator arm", date)
        doc["picks"] = pick_figures(real, cards, f"{rel(folder / agent)}/runs.jsonl, real arm", date)
        doc["inputs"]["night"] = rel(folder)
    else:
        doc["night"] = not_measured("no finished night with a morning report", "tools/morning_report.py on the newest night folder")
    if shards:
        summaries, pots, budgets = read_shards(shards, cards)
        src = f"self-play shards of generation {gen} ({len(shards)} jobs, no exploration), emulator"
        doc["ai_generation"] = gen
        doc["ai_door"] = door_figures(summaries, cards, src, now[:10])
        doc["potion_use"] = {"ai": potion_use_figures(pots, src, now[:10]), "ai_budget": budget_figures(budgets, src, now[:10])}
        doc["inputs"]["shards"] = {"generation": gen, "jobs": len(shards), "runs": len(summaries)}
    else:
        doc["ai_door"] = not_measured(f"no self-play shards for generation {gen}", "`tools/boss_entry.py selfplay`")
    hd = human_door(human_cache, cards)
    doc["human_door"] = hd or not_measured("the boss-entry human cache is missing", "`tools/boss_entry.py human` (about 2 minutes)")
    if humans:
        doc["human_fights"] = humans
    else:
        doc["human_fights"] = not_measured("no human per-fight pass has been run", "`tools/subproblems.py humans` (one pass over the corpus, about 1.5 minutes)")
    doc["board"] = board_figures(board_dir) if Path(board_dir).is_dir() else not_measured("no board folder", "the gym loop's board")
    doc["gym_kinds"] = gym_kinds(weights)
    if Path(exam_rows).is_file():
        doc["exam"] = exam_figures(read_json(exam_rows), rel(exam_rows), "2026-11-02")
    else:
        doc["exam"] = not_measured("no exam rows", "`tools/boss_entry_exam.py exam` (about 11 minutes)")
    if agreement:
        doc["agreement"] = agreement_figures(*agreement)
    return doc


def cmd_refresh(a: argparse.Namespace) -> int:
    be.below_normal()
    if a.night:
        arms = sorted((p.name for p in Path(a.night).iterdir() if re.fullmatch(r"g\d+", p.name)), key=lambda s: -int(s[1:]))
        night = (Path(a.night), a.agent or arms[0]) if (a.agent or arms) else None
    else:
        night = newest_finished_night(Path(a.nightly), a.min_rows) or newest_finished_night(Path(a.nightly))
    morning = run_morning(*night) if night else None
    gen = a.gen if a.gen is not None else ((morning or {}).get("night") or {}).get("generation")
    cards = be.Cards.load()
    shards = shard_jobs(Path(a.runs_root), int(gen)) if gen is not None and not a.no_shards else []
    hp, ap = Path(a.humans) if a.humans else HUMANS_JSON, Path(a.agreement) if a.agreement else AGREEMENT_JSON
    humans = read_json(hp) if hp.is_file() else None
    agreement = (read_json(ap), rel(ap)) if ap.is_file() else None
    doc = build(night, morning, gen, cards, shards, Path(a.board), Path(a.weights),
                Path(a.human_cache), Path(a.exam_rows), humans, agreement)
    Path(a.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"subproblems: wrote {rel(a.out) if Path(a.out).is_absolute() else a.out}", file=sys.stderr)
    if a.render:
        Path(a.render).write_text(render_into(Path(a.render).read_text(encoding="utf-8"), render_table(doc)), encoding="utf-8", newline="\n")
        print(f"subproblems: rendered the table into {a.render}", file=sys.stderr)
    return 0


def cmd_render(a: argparse.Namespace) -> int:
    doc = read_json(Path(a.json))
    Path(a.doc).write_text(render_into(Path(a.doc).read_text(encoding="utf-8"), render_table(doc)), encoding="utf-8", newline="\n")
    print(f"subproblems: rendered the table into {a.doc}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("refresh", help="read the files, write the JSON, optionally render the document's table")
    r.add_argument("--out", required=True)
    r.add_argument("--render", help="the document whose table (between the markers) is rewritten")
    r.add_argument("--night", help="a night folder (default: the newest finished one)")
    r.add_argument("--agent", help="the real arm's folder name, g<N> (default: the highest)")
    r.add_argument("--nightly", default=str(NIGHTLY))
    r.add_argument("--min-rows", type=int, default=1000, help="prefer the newest finished night with at least this many real-arm rows (a 2,000-seed block "
                   "over a 500-seed check); the newest finished night when none has")
    r.add_argument("--gen", type=int, help="the generation whose self-play shards give the doors (default: the night's)")
    r.add_argument("--no-shards", action="store_true")
    r.add_argument("--runs-root", default=str(RUNS_ROOT))
    r.add_argument("--board", default=str(LOOP / "board"))
    r.add_argument("--weights", default=str(LOOP / "starts/weights.json"))
    r.add_argument("--human-cache", default=str(HUMAN_CACHE))
    r.add_argument("--exam-rows", default=str(EXAM_ROWS))
    r.add_argument("--humans", help="the output of `humans` (default: referee/backlog/boss-entry/humans.json when it exists)")
    r.add_argument("--agreement", help="an output of `boss_entry_exam.py agreement` (default: referee/backlog/boss-entry/agreement.json when it exists)")
    r.set_defaults(fn=cmd_refresh)
    t = sub.add_parser("render", help="rewrite the document's table from the JSON")
    t.add_argument("--json", required=True)
    t.add_argument("--doc", required=True)
    t.set_defaults(fn=cmd_render)
    h = sub.add_parser("humans", help="one pass over the human corpus: Act 1 and 2 fight survival by kind, potion use (about 1.5 minutes)")
    h.add_argument("--corpus", default=str(be.DEFAULT_CORPUS))
    h.add_argument("--out", required=True)
    h.set_defaults(fn=cmd_humans)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
