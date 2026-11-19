"""The five honest weekly numbers (Act 3 week, lane 6b; analyst B's option 6 of the 2026-11-18 review).

    python tools/weekly_numbers.py [--root D:/spireline] [--now ISO] [--out-dir DIR] [--no-write] [--json-only]
    python tools/weekly_numbers.py --fill docs/paper/SCOREBOARD-TEMPLATE.md [--out-dir DIR]

It reads only files that already exist, plays nothing and touches no network. A number it cannot read prints "no data" with the
reason; it never invents one. Every rate carries n and a 95% (Wilson) interval. The five numbers:

  1. Wins per 100 in the real game for the champion, from the newest real block (<root>/referee/LAB/nightly/<block>/<agent>/runs.jsonl,
     block folders named YYYY-MM-DD or YYYY-MM-DDTHHMM, agent folder g<generation>, its copy arm the sibling g<generation>-emu), with
     the block's date and age in days. A crashed run counts as a loss. When no block holds the champion, the newest block's top
     generation is shown and marked as not the champion.
  2. The first Act 3 boss, got past strictly (the run won, or its floor is above 48), per 100 runs and per 100 arrivals at the boss
     (floor 48 reached, a win, or a boss-damage entry for Act 3): the real game, and the copy on the seeds both arms hold.
  3. Copy honesty per act, on the paired seeds: the share of runs where both arms end in the same act (conditioned on the real arm's
     act), the mean floor difference (copy minus real), and an alarm when the Act 1 or Act 2 figure moves by more than two points
     from the previous block. The two-point line is the brief's; with a few hundred pairs the sampling noise is larger, so the move's
     own 95% noise is printed beside it.
  4. Distance to winning humans: the newest seed-matched human exam (rl/run_seed_exam.py writes <root>/referee/seed-exam/<date>-gen<N>/
     summary.json; other places searched: referee/agent/*/ and referee/backlog/): floors behind on the seeds the human won, and how
     many of those seeds a draw of ours won. Marked when it is not an exam of the champion.
  5. This week's champion against last week's on paired seeds, read strictly from the two arms' runs.jsonl under referee/agent: Act 3
     passes and wins per 100 for both arms, the paired difference and the pooled pairs. A block the champion was promoted on is the
     selection block (the gain there is the best of several candidates); only a block no promotion row of the champion judged on is
     "fresh". Beside it, the stop rule's distance (docs/DECISIONS.md D68).

Human reference figures (Spire Codex public run export for v0.107.1, finished Ironclad Ascension 10 runs, aggregates only) are
constants below with their source. Output: Markdown (stdout, and weekly-numbers-<date>.md), JSON (weekly-numbers-<date>.json); paths
inside print relative to the root; no seed, host or user name is written.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path("D:/spireline")
Z = 1.959964
BOSS_FLOOR = {1: 17, 2: 33, 3: 48}  # the three act bosses; floor 49 is the second Act 3 boss
ARRIVAL_FLOOR = BOSS_FLOOR[3]
PASS_FLOOR = BOSS_FLOOR[3]  # strictly past the first Act 3 boss: a win, or a floor above this
WIN_ENDS = ("win", "victory", "won")
ALARM_POINTS = 2.0
MIN_PAIRS = 20  # a previous block with fewer paired seeds is skipped for the alarm
STOP_DATE = "2026-12-02"
STOP_RULE = {"start_per_100_arrivals": 16.0, "target_per_100_arrivals": 30.0, "target_wins_per_100": 0.5, "pairs_needed": 4000}
HUMANS = {
    "source": "Spire Codex public run export for v0.107.1; Ironclad, Ascension 10; finished runs (14,811); aggregates",
    "wins_per_100": 11.3,
    "wins_per_100_quits_as_losses": 8.0,
    "first_a3_boss_passed_per_100_runs": 18.2,
    "first_a3_boss_passed_per_100_arrivals": 72.7,
}
BLOCK_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2})(\d{2}))?$")
ARM_SUFFIX_RE = re.compile(r"-[a-z]\d+-v\d+$")  # arms/<block>-a3-v1
NO_DATA = "no data"


# ------------------------------------------------------------------------------------------------------------ statistics
def wilson(k: int, n: int, z: float = Z) -> tuple[float, float] | None:
    """The Wilson interval of k out of n, as fractions (None when n is 0)."""
    if n <= 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (0.0 if k == 0 else max(0.0, c - h)), (1.0 if k == n else min(1.0, c + h))


def rate(k: int, n: int) -> dict[str, Any]:
    """k of n as a per-100 figure with its Wilson interval; per100 is None when n is 0."""
    iv = wilson(k, n)
    return {"k": int(k), "n": int(n), "per100": None if iv is None else round(100.0 * k / n, 3),
            "lo": None if iv is None else round(100.0 * iv[0], 3), "hi": None if iv is None else round(100.0 * iv[1], 3)}


def mean_se(values: list[float]) -> tuple[float, float] | None:
    n = len(values)
    if n == 0:
        return None
    m = sum(values) / n
    if n == 1:
        return m, float("nan")
    var = sum((x - m) ** 2 for x in values) / (n - 1)
    return m, math.sqrt(var / n)


def paired_diff(diffs: list[float]) -> dict[str, Any]:
    """Mean of paired differences (already per 100 or in floors), its standard error, 95% interval and z."""
    ms = mean_se(diffs)
    if ms is None:
        return {"n": 0, "mean": None, "se": None, "lo": None, "hi": None, "z": None}
    m, se = ms
    if math.isnan(se):
        return {"n": len(diffs), "mean": round(m, 3), "se": None, "lo": None, "hi": None, "z": None}
    return {"n": len(diffs), "mean": round(m, 3), "se": round(se, 3), "lo": round(m - Z * se, 3), "hi": round(m + Z * se, 3),
            "z": None if se == 0 else round(m / se, 2)}


# ------------------------------------------------------------------------------------------------------------ run rows
def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield row


def act_of(floor: int, win: bool) -> int:
    """The act a run ended in: a win is Act 3; floors up to 17 are Act 1, up to 33 Act 2, the rest Act 3 (floor 49 included)."""
    if win or floor > BOSS_FLOOR[2]:
        return 3
    return 1 if floor <= BOSS_FLOOR[1] else 2


def _win(row: dict[str, Any]) -> bool:
    return bool(row.get("win")) or str(row.get("end", "")).lower() in WIN_ENDS


def norm_row(row: dict[str, Any], crash: bool = False) -> dict[str, Any]:
    """One run as the numbers need it. A crash is a loss on floor 0 (the lab's own rule, gen0.real_runs)."""
    if crash:
        return {"floor": 0, "win": False, "arrived": False, "passed": False, "crash": True}
    try:
        floor = int(row.get("floor") or 0)
    except (TypeError, ValueError):
        floor = 0
    win = _win(row)
    acts = row.get("boss_damage_acts") or []
    a3_entry = False
    for e in acts:
        try:
            if int(e[0]) == 2:  # boss_damage_acts counts acts from 0
                a3_entry = True
        except (TypeError, ValueError, IndexError, KeyError):
            continue
    return {"floor": floor, "win": win, "arrived": bool(win or floor >= ARRIVAL_FLOOR or a3_entry),
            "passed": bool(win or floor > PASS_FLOOR), "crash": False}


def load_real(path: Path) -> dict[str, dict[str, Any]]:
    """The real arm's runs.jsonl (envproto rows: ev 'end' or 'crash') by seed; a later end row replaces an earlier row of the seed."""
    out: dict[str, dict[str, Any]] = {}
    for r in read_jsonl(path):
        seed = r.get("seed")
        if seed is None:
            continue
        ev = r.get("ev")
        if ev == "end":
            out[seed] = norm_row(r)
        elif ev == "crash" and not (seed in out and not out[seed]["crash"]):
            out[seed] = norm_row(r, crash=True)
    return out


def load_arm(path: Path) -> dict[str, dict[str, Any]]:
    """A copy arm's runs.jsonl (the lab's per-run rows: seed, floor, win, end, crash) by seed."""
    out: dict[str, dict[str, Any]] = {}
    for r in read_jsonl(path):
        seed = r.get("seed")
        if seed is None or r.get("ev") not in (None, "end"):
            continue
        out[seed] = norm_row(r, crash=bool(r.get("crash")))
    return out


# ------------------------------------------------------------------------------------------------------------ the folders
def rel(root: Path, p: Path) -> str:
    """The path below the root, as written (a path outside the root prints as its last name, never as an absolute path)."""
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        try:
            return p.resolve().relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            return p.name


def block_start(name: str) -> datetime | None:
    m = BLOCK_RE.match(name)
    if not m:
        return None
    y, mo, d, hh, mm = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0), tzinfo=timezone.utc)
    except ValueError:
        return None


def list_blocks(nightly: Path) -> list[tuple[datetime, str, Path]]:
    """Block folders oldest first."""
    out = []
    if nightly.is_dir():
        for p in nightly.iterdir():
            st = block_start(p.name)
            if st is not None and p.is_dir():
                out.append((st, p.name, p))
    out.sort(key=lambda t: (t[0], t[1]))
    return out


def agents_in(block: Path) -> dict[int, dict[str, Path | None]]:
    """g<N> folders holding a runs.jsonl: {generation: {'real': path, 'copy': path or None}}."""
    out: dict[int, dict[str, Path | None]] = {}
    for p in block.iterdir():
        m = re.match(r"^g(\d+)$", p.name)
        if m and p.is_dir() and (p / "runs.jsonl").is_file():
            emu = block / (p.name + "-emu") / "runs.jsonl"
            out[int(m.group(1))] = {"real": p / "runs.jsonl", "copy": emu if emu.is_file() else None, "dir": p}
    return out


def champion_of(root: Path) -> dict[str, Any] | None:
    """agent/current.json: generation, and the candidate folder as '<genN>/<name>'."""
    p = root / "referee" / "agent" / "current.json"
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        gen = int(doc["generation"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    parts = [x for x in re.split(r"[\\/]+", str(doc.get("dir", ""))) if x]
    return {"generation": gen, "dir": "/".join(parts[-2:]) if len(parts) >= 2 else None, "promoted": doc.get("promoted"),
            "seed_block": doc.get("seed_block")}


def select_block(blocks: list[tuple[datetime, str, Path]], champion_gen: int | None, before: datetime | None = None,
                 need_copy: bool = False) -> dict[str, Any] | None:
    """The block to read: the newest block that holds the champion's real rows; else the newest block's top generation (marked)."""
    cands = [b for b in blocks if before is None or b[0] < before]
    seen: list[tuple[datetime, str, Path, dict[int, dict[str, Path | None]]]] = []
    for st, name, path in reversed(cands):
        ag = agents_in(path)
        if need_copy:
            ag = {g: v for g, v in ag.items() if v["copy"] is not None}
        if ag:
            seen.append((st, name, path, ag))
    if not seen:
        return None
    if champion_gen is not None:
        for st, name, path, ag in seen:
            if champion_gen in ag:
                return {"start": st, "name": name, "path": path, "generation": champion_gen, "agent": ag[champion_gen],
                        "is_champion": True}
    st, name, path, ag = seen[0]
    gen = max(ag)
    return {"start": st, "name": name, "path": path, "generation": gen, "agent": ag[gen], "is_champion": champion_gen == gen}


def age_days(start: datetime, now: datetime) -> float:
    return round((now - start).total_seconds() / 86400.0, 1)


# ------------------------------------------------------------------------------------------------------------ number 1
def number1(root: Path, champion: dict[str, Any] | None, blocks: list[tuple[datetime, str, Path]], now: datetime) -> dict[str, Any]:
    out: dict[str, Any] = {"name": "wins per 100, real game", "humans_per_100": HUMANS["wins_per_100"],
                           "humans_quits_as_losses_per_100": HUMANS["wins_per_100_quits_as_losses"]}
    sel = select_block(blocks, champion["generation"] if champion else None)
    if sel is None:
        return {**out, "status": NO_DATA, "reason": "no real block with a runs.jsonl under LAB/nightly"}
    rows = load_real(sel["agent"]["real"])
    ends = sum(1 for r in rows.values() if not r["crash"])
    crashes = len(rows) - ends
    wins = sum(1 for r in rows.values() if r["win"])
    floors = [r["floor"] for r in rows.values() if not r["crash"]]
    summ_path = sel["agent"]["dir"] / "summary.json"
    out.update({
        "status": "ok" if sel["is_champion"] else "not the champion",
        "block": sel["name"], "block_date": sel["start"].strftime("%Y-%m-%d"), "age_days": age_days(sel["start"], now),
        "generation": sel["generation"], "champion_generation": champion["generation"] if champion else None,
        "champion_has_real_block": bool(sel["is_champion"]),
        "folder": rel(root, sel["agent"]["dir"]), "summary_json": summ_path.is_file(),
        "wins": rate(wins, len(rows)), "end_rows": ends, "crash_rows": crashes,
        "mean_floor": None if not floors else round(sum(floors) / len(floors), 2),
        "counted": "a crashed run is a loss (floor 0, no win)",
    })
    if not sel["is_champion"]:
        out["reason"] = ("no real block holds generation %s; this is the newest block's top generation (g%s)"
                         % (champion["generation"] if champion else "of the champion", sel["generation"]))
    if not summ_path.is_file():
        out["note"] = "the block's summary.json is not written yet: the block may still be running"
    return out


# ------------------------------------------------------------------------------------------------------------ numbers 2 and 3
def pass_figures(runs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    runs = list(runs)
    n = len(runs)
    arrived = sum(1 for r in runs if r["arrived"])
    passed = sum(1 for r in runs if r["passed"])
    return {"runs": n, "arrivals": arrived, "passed": passed, "per_100_runs": rate(passed, n),
            "per_100_arrivals": rate(passed, arrived), "arrivals_per_100_runs": rate(arrived, n)}


def number2(root: Path, sel: dict[str, Any] | None, n1: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"name": "first Act 3 boss passed (strict: a win or a floor above 48)",
                           "humans_per_100_runs": HUMANS["first_a3_boss_passed_per_100_runs"],
                           "humans_per_100_arrivals": HUMANS["first_a3_boss_passed_per_100_arrivals"]}
    if sel is None:
        return {**out, "status": NO_DATA, "reason": "no real block"}
    real = load_real(sel["agent"]["real"])
    out["block"] = sel["name"]
    out["generation"] = sel["generation"]
    out["real_all"] = pass_figures(real.values())
    if sel["agent"]["copy"] is None:
        return {**out, "status": "real only", "reason": "the block holds no copy arm (g%d-emu)" % sel["generation"]}
    copy = load_arm(sel["agent"]["copy"])
    seeds = sorted(set(real) & set(copy))
    if not seeds:
        return {**out, "status": "real only", "reason": "the real and copy arms share no seed"}
    out["paired_seeds"] = len(seeds)
    out["real_paired"] = pass_figures(real[s] for s in seeds)
    out["copy_paired"] = pass_figures(copy[s] for s in seeds)
    both = sum(1 for s in seeds if real[s]["passed"] and copy[s]["passed"])
    r_only = sum(1 for s in seeds if real[s]["passed"] and not copy[s]["passed"])
    c_only = sum(1 for s in seeds if copy[s]["passed"] and not real[s]["passed"])
    out["discordant"] = {"both": both, "real_only": r_only, "copy_only": c_only}
    out["status"] = "ok" if sel["is_champion"] else "not the champion"
    if not sel["is_champion"]:
        out["reason"] = n1.get("reason")
    return out


def honesty_by_act(real: dict[str, dict[str, Any]], copy: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Per act of the REAL arm's end: runs, the share where the copy ends in the same act, mean floor difference copy minus real."""
    seeds = sorted(set(real) & set(copy))
    groups: dict[Any, list[str]] = {1: [], 2: [], 3: [], "all": list(seeds)}
    for s in seeds:
        groups[act_of(real[s]["floor"], real[s]["win"])].append(s)
    rows = []
    for key in (1, 2, 3, "all"):
        ss = groups[key]
        same = sum(1 for s in ss if act_of(real[s]["floor"], real[s]["win"]) == act_of(copy[s]["floor"], copy[s]["win"]))
        diffs = [float(copy[s]["floor"] - real[s]["floor"]) for s in ss]
        ms = mean_se(diffs)
        iv = wilson(same, len(ss))
        rows.append({"act": key, "runs": len(ss), "same_act": rate(same, len(ss)),
                     "same_act_se_points": None if iv is None else round(100.0 * math.sqrt(max(same / len(ss) * (1 - same / len(ss)), 0) / len(ss)), 3),
                     "floor_diff": None if ms is None else {"mean": round(ms[0], 3), "se": None if math.isnan(ms[1]) else round(ms[1], 3)}})
    return {"pairs": len(seeds), "rows": rows}


def alarm(now_h: dict[str, Any], prev_h: dict[str, Any], points: float = ALARM_POINTS) -> dict[str, Any]:
    """Act 1 and Act 2: the same-act share and the mean floor difference against the previous block; flagged past `points`."""
    flags = []
    moves = []
    prev_rows = {r["act"]: r for r in prev_h["rows"]}
    for r in now_h["rows"]:
        if r["act"] not in (1, 2):
            continue
        p = prev_rows.get(r["act"])
        if p is None or not r["runs"] or not p["runs"]:
            continue
        share_move = r["same_act"]["per100"] - p["same_act"]["per100"]
        se = math.sqrt((r["same_act_se_points"] or 0) ** 2 + (p["same_act_se_points"] or 0) ** 2)
        mv = {"act": r["act"], "same_act_move_points": round(share_move, 3), "same_act_noise95_points": round(Z * se, 3),
              "same_act_beyond_noise": abs(share_move) > Z * se}
        if r["floor_diff"] and p["floor_diff"]:
            fm = r["floor_diff"]["mean"] - p["floor_diff"]["mean"]
            fse = math.sqrt((r["floor_diff"]["se"] or 0) ** 2 + (p["floor_diff"]["se"] or 0) ** 2)
            mv.update({"floor_diff_move": round(fm, 3), "floor_diff_noise95": round(Z * fse, 3), "floor_diff_beyond_noise": abs(fm) > Z * fse})
            if abs(fm) > points:
                flags.append("Act %d mean floor difference moved %+.2f floors (%s)" % (
                    r["act"], fm, "beyond its 95%% noise of %.2f" % (Z * fse) if mv["floor_diff_beyond_noise"] else "within its 95%% noise of %.2f" % (Z * fse)))
        if abs(share_move) > points:
            flags.append("Act %d same-act share moved %+.1f points (%s)" % (
                r["act"], share_move, "beyond its 95%% noise of %.1f" % (Z * se) if mv["same_act_beyond_noise"] else "within its 95%% noise of %.1f" % (Z * se)))
        moves.append(mv)
    return {"flag": bool(flags), "threshold": points, "reasons": flags, "text": "; ".join(flags) if flags else "none", "moves": moves}


def number3(root: Path, sel: dict[str, Any] | None, blocks: list[tuple[datetime, str, Path]], champion: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {"name": "copy honesty per act (paired seeds, copy minus real)", "alarm_points": ALARM_POINTS}
    if sel is None or sel["agent"]["copy"] is None:
        return {**out, "status": NO_DATA, "reason": "no real block with a copy arm" if sel is None else "the block holds no copy arm"}
    real = load_real(sel["agent"]["real"])
    copy = load_arm(sel["agent"]["copy"])
    here = honesty_by_act(real, copy)
    if not here["pairs"]:
        return {**out, "status": NO_DATA, "reason": "the arms share no seed"}
    out.update({"status": "ok" if sel["is_champion"] else "not the champion", "block": sel["name"], "generation": sel["generation"], **here})
    prev = None
    for st, name, path in reversed([b for b in blocks if b[0] < sel["start"]]):
        ag = {g: v for g, v in agents_in(path).items() if v["copy"] is not None}
        if not ag:
            continue
        g = max(ag)
        r2, c2 = load_real(ag[g]["real"]), load_arm(ag[g]["copy"])
        h2 = honesty_by_act(r2, c2)
        if h2["pairs"] >= MIN_PAIRS:
            prev = {"block": name, "generation": g, **h2}
            break
    if prev is None:
        out["previous"] = None
        out["alarm"] = {"flag": False, "reasons": [], "text": "none (no earlier block with at least %d paired seeds to compare with)" % MIN_PAIRS,
                        "note": "no earlier block with at least %d paired seeds" % MIN_PAIRS}
    else:
        out["previous"] = prev
        out["alarm"] = alarm(here, prev)
    return out


# ------------------------------------------------------------------------------------------------------------ number 4
EXAM_GLOBS = ("referee/seed-exam/*/summary.json", "referee/agent/*/summary.json", "referee/agent/*/*/summary.json",
              "referee/agent/*/*/seed-exam*/summary.json", "referee/backlog/*/summary.json", "referee/backlog/*/*/summary.json",
              "referee/backlog/seed-exam/*/summary.json")


def find_exams(root: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    seen: dict[str, tuple[str, Path, dict[str, Any]]] = {}
    for pat in EXAM_GLOBS:
        for p in root.glob(pat):
            key = str(p.resolve())
            if key in seen:
                continue
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(doc, dict) and isinstance(doc.get("paired"), dict) and isinstance(doc.get("agent"), dict):
                seen[key] = (str(doc.get("written") or ""), p, doc)
    return sorted(seen.values(), key=lambda t: (t[0], str(t[1])))


def number4(root: Path, champion: dict[str, Any] | None, now: datetime) -> dict[str, Any]:
    out: dict[str, Any] = {"name": "distance to winning humans (seed-matched exam)", "humans_wins_on_these_seeds": "all of the seeds the human won"}
    exams = find_exams(root)
    if not exams:
        return {**out, "status": NO_DATA, "reason": "no seed-exam summary.json under referee/seed-exam, referee/agent or referee/backlog"}
    written, path, doc = exams[-1]
    won = (doc.get("paired") or {}).get("won") or {}
    fd = won.get("floor_diff") or {}
    gen = (doc.get("agent") or {}).get("generation")
    age = None
    try:
        age = round((now - datetime.strptime(written, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds() / 86400.0, 1)
    except ValueError:
        pass
    seeds_won = won.get("some_draw_won")
    n_seeds = won.get("seeds")
    ours_won = ((doc.get("ours") or {}).get("won") or {})
    draws_won = None
    if ours_won.get("runs") is not None and ours_won.get("win_rate") is not None:
        draws_won = int(round(float(ours_won["win_rate"]) * int(ours_won["runs"])))
    is_champ = champion is not None and gen == champion["generation"]
    out.update({
        "status": "ok" if is_champ else "not the champion", "exam_generation": gen, "champion_generation": champion["generation"] if champion else None,
        "written": written or None, "age_days": age, "folder": rel(root, path.parent), "seeds_human_won": n_seeds,
        "floors_behind_on_human_won_seeds": None if fd.get("mean") is None else {"mean": round(-float(fd["mean"]), 2),
                                                                                   "lo": round(-float(fd["hi"]), 2), "hi": round(-float(fd["lo"]), 2),
                                                                                   "n": fd.get("n")},
        "seeds_won_by_some_draw": seeds_won, "draws_won": draws_won, "draws_played": ours_won.get("runs"),
        "draws_per_seed": doc.get("draws"),
    })
    if not is_champ:
        out["reason"] = "no exam of generation %s exists; the newest is of generation %s" % (champion["generation"] if champion else "the champion", gen)
    return out


# ------------------------------------------------------------------------------------------------------------ number 5
def read_promotions(root: Path) -> list[dict[str, str]]:
    p = root / "referee" / "agent" / "promotions.tsv"
    try:
        with open(p, encoding="utf-8", errors="replace", newline="") as fh:
            return [dict(r) for r in csv.DictReader(fh, delimiter="\t")]
    except OSError:
        return []


def _int(v: Any) -> int | None:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def judging_blocks(rows: list[dict[str, str]], gen: int, dirname: str) -> set[str]:
    """Every block a promotion row of this candidate judged on (the seed_block column and any 'pooled A + B' blocks in the rule text)."""
    out: set[str] = set()
    for r in rows:
        if _int(r.get("cand_gen")) == gen and r.get("cand_dir") == dirname:
            if r.get("seed_block"):
                out.add(r["seed_block"].strip())
            m = re.search(r"pooled\s+(.+?)\s*=", r.get("rule") or "")
            if m:
                for b in re.findall(r"([A-Za-z0-9][A-Za-z0-9_.-]*)\s*\(\d+\)", m.group(1)):
                    out.add(b)
    return out


def arm_blocks(arms: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if arms.is_dir():
        for d in arms.iterdir():
            if (d / "runs.jsonl").is_file():
                out[ARM_SUFFIX_RE.sub("", d.name)] = d / "runs.jsonl"
    return out


def arm_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    f = pass_figures(runs)
    n = f["runs"]
    wins = sum(1 for r in runs if r["win"])
    return {"runs": n, "arrivals": f["arrivals"], "passed": rate(f["passed"], n), "passed_per_arrival": rate(f["passed"], f["arrivals"]),
            "wins": rate(wins, n)}


def compare_pairs(cand: list[dict[str, Any]], base: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(cand)
    d_pass = [100.0 * (int(c["passed"]) - int(b["passed"])) for c, b in zip(cand, base)]
    d_win = [100.0 * (int(c["win"]) - int(b["win"])) for c, b in zip(cand, base)]
    d_v3 = [100.0 * (int(c["passed"]) + int(c["win"]) - int(b["passed"]) - int(b["win"])) for c, b in zip(cand, base)]
    return {"pairs": n, "champion": arm_summary(cand), "previous": arm_summary(base), "diff_passed_per_100": paired_diff(d_pass),
            "diff_wins_per_100": paired_diff(d_win), "diff_rule_v3_measure_per_100": paired_diff(d_v3)}


def number5(root: Path, champion: dict[str, Any] | None, n1: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"name": "this week's champion against last week's, paired copy seeds (strict)"}
    if champion is None or not champion.get("dir"):
        return {**out, "status": NO_DATA, "reason": "agent/current.json is missing or names no folder"}
    gen = champion["generation"]
    dirname = champion["dir"].split("/")[-1]
    rows = read_promotions(root)
    mine = [r for r in rows if _int(r.get("cand_gen")) == gen and r.get("cand_dir") == dirname]
    if not mine:
        return {**out, "status": NO_DATA, "reason": "no promotions.tsv row for the champion (g%d %s)" % (gen, dirname)}
    promo = sorted([r for r in mine if r.get("decision") == "promoted"] or mine, key=lambda r: r.get("written", ""))[-1]
    base_gen = _int(promo.get("base_gen"))
    if base_gen is None:
        return {**out, "status": NO_DATA, "reason": "the champion's row names no base generation"}
    base_rows = sorted([r for r in rows if _int(r.get("cand_gen")) == base_gen and r.get("decision") == "promoted"], key=lambda r: r.get("written", ""))
    if not base_rows:
        return {**out, "status": NO_DATA, "reason": "no promoted row for the previous champion (g%d)" % base_gen}
    base_dirname = base_rows[-1]["cand_dir"]
    agent_root = root / "referee" / "agent"
    cand_blocks = arm_blocks(agent_root / ("gen%d" % gen) / dirname / "arms")
    base_blocks = arm_blocks(agent_root / ("gen%d" % base_gen) / base_dirname / "arms")
    common = sorted(set(cand_blocks) & set(base_blocks))
    judged = judging_blocks(rows, gen, dirname)
    out.update({"champion": "gen%d/%s" % (gen, dirname), "previous": "gen%d/%s" % (base_gen, base_dirname),
                "promotion_judged_blocks": sorted(judged), "promoted": promo.get("written"), "promotion_block": promo.get("seed_block")})
    if not common:
        return {**out, "status": NO_DATA, "reason": "the two candidates' arms folders share no block"}
    per_block = []
    pools: dict[str, tuple[list, list]] = {"all": ([], []), "fresh": ([], [])}
    for b in common:
        c, p = load_arm(cand_blocks[b]), load_arm(base_blocks[b])
        seeds = sorted(set(c) & set(p))
        if not seeds:
            continue
        cl, bl = [c[s] for s in seeds], [p[s] for s in seeds]
        fresh = b not in judged
        per_block.append({"block": b, "fresh": fresh, **compare_pairs(cl, bl)})
        pools["all"][0].extend(cl)
        pools["all"][1].extend(bl)
        if fresh:
            pools["fresh"][0].extend(cl)
            pools["fresh"][1].extend(bl)
    if not per_block:
        return {**out, "status": NO_DATA, "reason": "no shared seed in the common blocks"}
    out["blocks"] = per_block
    out["pooled_all"] = compare_pairs(*pools["all"])
    out["pooled_fresh"] = compare_pairs(*pools["fresh"]) if pools["fresh"][0] else None
    head = out["pooled_fresh"] or out["pooled_all"]
    out["headline"] = {"basis": "fresh pairs" if out["pooled_fresh"] else "the selection block only (not fresh)", "pairs": head["pairs"],
                       "champion_passed_per100": head["champion"]["passed"]["per100"], "previous_passed_per100": head["previous"]["passed"]["per100"],
                       "diff_passed_per100": head["diff_passed_per_100"]["mean"], "diff_passed_se": head["diff_passed_per_100"]["se"],
                       "champion_per_arrival": head["champion"]["passed_per_arrival"]["per100"],
                       "previous_per_arrival": head["previous"]["passed_per_arrival"]["per100"],
                       "champion_wins_per100": head["champion"]["wins"]["per100"], "previous_wins_per100": head["previous"]["wins"]["per100"],
                       "diff_wins_per100": head["diff_wins_per_100"]["mean"], "diff_rule_v3_per100": head["diff_rule_v3_measure_per_100"]["mean"],
                       "diff_rule_v3_se": head["diff_rule_v3_measure_per_100"]["se"]}
    out["status"] = "ok" if out["pooled_fresh"] else "selection block only (no fresh pairs yet)"
    if not out["pooled_fresh"]:
        out["reason"] = "every block with both arms is one the champion was judged on; the gain there is the best of several candidates"
    return out


def stop_rule(n5: dict[str, Any], n1: dict[str, Any], now: datetime) -> dict[str, Any]:
    out: dict[str, Any] = {**STOP_RULE, "stop_date": STOP_DATE}
    try:
        end = datetime.strptime(STOP_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
        out["days_left"] = round((end - now).total_seconds() / 86400.0, 1)
    except ValueError:
        out["days_left"] = None
    pooled = n5.get("pooled_fresh") or n5.get("pooled_all")
    if pooled:
        arm = pooled["champion"]["passed_per_arrival"]
        out.update({"basis": "fresh pairs" if n5.get("pooled_fresh") else "the selection block (not fresh)", "pairs": pooled["pairs"],
                    "now_per_100_arrivals": arm["per100"], "now_per_100_arrivals_lo": arm["lo"], "now_per_100_arrivals_hi": arm["hi"],
                    "arrivals": pooled["champion"]["arrivals"],
                    "now_wins_per_100": pooled["champion"]["wins"]["per100"], "wins": pooled["champion"]["wins"]["k"],
                    "fresh_pairs": n5["pooled_fresh"]["pairs"] if n5.get("pooled_fresh") else 0})
        if arm["per100"] is not None:
            out["gap_to_target_points"] = round(STOP_RULE["target_per_100_arrivals"] - arm["per100"], 2)
    else:
        out["basis"] = NO_DATA
    out["real_block_of_champion"] = bool(n1.get("champion_has_real_block"))
    return out


# ------------------------------------------------------------------------------------------------------------ the report
def build(root: Path, now: datetime) -> dict[str, Any]:
    nightly = root / "referee" / "LAB" / "nightly"
    blocks = list_blocks(nightly)
    champion = champion_of(root)
    sel = select_block(blocks, champion["generation"] if champion else None)
    n1 = number1(root, champion, blocks, now)
    n2 = number2(root, sel, n1)
    n3 = number3(root, sel, blocks, champion)
    n4 = number4(root, champion, now)
    n5 = number5(root, champion, n1)
    return {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "champion": champion, "humans": HUMANS,
            "n1": n1, "n2": n2, "n3": n3, "n4": n4, "n5": n5, "stop_rule": stop_rule(n5, n1, now)}


def fmt(v: Any, nd: int = 1) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return ("%." + str(nd) + "f") % v
    return str(v)


def fmt_rate(r: dict[str, Any] | None, nd: int = 1, with_n: bool = True) -> str:
    if not r:
        return NO_DATA
    if r.get("per100") is None:
        return "none (%d of %d)" % (r["k"], r["n"])
    s = "%s [%s, %s]" % (fmt(r["per100"], nd), fmt(r["lo"], nd), fmt(r["hi"], nd))
    return s + (" (%d of %d)" % (r["k"], r["n"]) if with_n else "")


def render_markdown(doc: dict[str, Any]) -> str:
    n1, n2, n3, n4, n5, sr = doc["n1"], doc["n2"], doc["n3"], doc["n4"], doc["n5"], doc["stop_rule"]
    ch = doc.get("champion") or {}
    lines = ["# The five weekly numbers (%s)" % doc["generated"], "",
             "Champion: generation %s. Rates are per 100 with a 95%% interval in brackets and the counts; humans: %s." % (ch.get("generation", "unknown"), HUMANS["source"]),
             "", "| # | number | now | n | humans | read from |", "|---|---|---|---|---|---|"]
    # 1
    if n1["status"] == NO_DATA:
        row1 = [NO_DATA, "-", "-", n1.get("reason", "")]
    else:
        lead = "" if n1["champion_has_real_block"] else "no data for generation %s (no real block of it yet); newest block, generation %s: " % (
            n1.get("champion_generation"), n1["generation"])
        row1 = ["%s%s" % (lead, fmt_rate(n1["wins"], 2, with_n=False)), str(n1["wins"]["n"]), "%s (%s counting quits)" % (fmt(n1["humans_per_100"]), fmt(n1["humans_quits_as_losses_per_100"])),
                "%s, %s days old (%s)" % (n1["block"], fmt(n1["age_days"]), n1["folder"])]
    lines.append("| 1 | wins per 100, real game | %s |" % " | ".join(row1))
    # 2
    if n2["status"] == NO_DATA:
        lines.append("| 2 | first Act 3 boss passed | %s | - | - | %s |" % (NO_DATA, n2.get("reason", "")))
    else:
        cells = [] if n2["status"] == "ok" else ["not the champion: generation %s, the newest real block's (no block of generation %s yet)" % (
            n2["generation"], (doc.get("champion") or {}).get("generation", "?"))]
        cells += ["real, all runs: %s; per 100 arrivals: %s" % (fmt_rate(n2["real_all"]["per_100_runs"], 2, False), fmt_rate(n2["real_all"]["per_100_arrivals"], 1, False))]
        if "copy_paired" in n2:
            cells.append("copy, same seeds: %s; per 100 arrivals: %s" % (fmt_rate(n2["copy_paired"]["per_100_runs"], 2, False), fmt_rate(n2["copy_paired"]["per_100_arrivals"], 1, False)))
            cells.append("real, same seeds: %s; per 100 arrivals: %s" % (fmt_rate(n2["real_paired"]["per_100_runs"], 2, False), fmt_rate(n2["real_paired"]["per_100_arrivals"], 1, False)))
        ns = "%d real (%d arrivals)" % (n2["real_all"]["runs"], n2["real_all"]["arrivals"])
        if "paired_seeds" in n2:
            ns += ", %d pairs (copy %d arrivals, real %d)" % (n2["paired_seeds"], n2["copy_paired"]["arrivals"], n2["real_paired"]["arrivals"])
        lines.append("| 2 | first Act 3 boss passed | %s | %s | %s per 100 runs, %s per 100 arrivals | %s g%s |" % (
            "<br>".join(cells), ns, fmt(n2["humans_per_100_runs"]), fmt(n2["humans_per_100_arrivals"]), n2["block"], n2["generation"]))
    # 3
    if n3["status"] == NO_DATA:
        lines.append("| 3 | copy honesty | %s | - | - | %s |" % (NO_DATA, n3.get("reason", "")))
    else:
        allrow = next(r for r in n3["rows"] if r["act"] == "all")
        parts = [] if n3["status"] == "ok" else ["not the champion: generation %s, the newest real block's" % n3["generation"]]
        parts.append("both arms end in the same act: %s in 100" % fmt_rate(allrow["same_act"], 1, False))
        for r in n3["rows"]:
            if r["act"] != "all" and r["runs"]:
                fd = r["floor_diff"]
                parts.append("real ended in Act %s (%d runs): copy in the same act %s in 100, floors %+.2f" % (
                    r["act"], r["runs"], fmt(r["same_act"]["per100"]), fd["mean"] if fd else 0))
        fda = allrow["floor_diff"]
        if fda:
            parts.append("all: floors %+.2f (se %s)" % (fda["mean"], fmt(fda["se"], 2)))
        al = n3["alarm"]
        parts.append("alarm: " + ("YES, " + "; ".join(al["reasons"]) if al["flag"] else "none") + ("" if not al.get("note") else " (%s)" % al["note"]))
        lines.append("| 3 | copy honesty (copy minus real) | %s | %d pairs | - | %s g%s vs %s |" % (
            "<br>".join(parts), n3["pairs"], n3["block"], n3["generation"], (n3["previous"] or {}).get("block", "no previous block")))
    # 4
    if n4["status"] == NO_DATA:
        lines.append("| 4 | distance to winning humans | %s | - | - | %s |" % (NO_DATA, n4.get("reason", "")))
    else:
        fb = n4["floors_behind_on_human_won_seeds"]
        txt = "%s floors behind on seeds a human won [%s, %s]; won %s of %s of those seeds (%s of %s draws)" % (
            fmt(fb["mean"]) if fb else "-", fmt(fb["lo"]) if fb else "-", fmt(fb["hi"]) if fb else "-", n4["seeds_won_by_some_draw"], n4["seeds_human_won"],
            n4["draws_won"], n4["draws_played"])
        if n4["status"] != "ok":
            txt += " (generation %s, not the champion: %s)" % (n4["exam_generation"], n4.get("reason", ""))
        lines.append("| 4 | distance to winning humans | %s | %s seeds | the human won all of them | %s, %s days old |" % (txt, n4["seeds_human_won"], n4["folder"], fmt(n4["age_days"])))
    # 5
    if n5["status"] == NO_DATA:
        lines.append("| 5 | champion against last week's | %s | - | - | %s |" % (NO_DATA, n5.get("reason", "")))
    else:
        pooled = n5.get("pooled_fresh") or n5["pooled_all"]
        basis = "fresh pairs" if n5.get("pooled_fresh") else "the selection block only, not fresh"
        c, p = pooled["champion"], pooled["previous"]
        txt = ("%s: passed %s vs %s; wins %s vs %s; difference in passed %s per 100 (se %s)" % (
            basis, fmt(c["passed"]["per100"], 2), fmt(p["passed"]["per100"], 2), fmt(c["wins"]["per100"], 2), fmt(p["wins"]["per100"], 2),
            fmt(pooled["diff_passed_per_100"]["mean"], 2), fmt(pooled["diff_passed_per_100"]["se"], 2)))
        lines.append("| 5 | %s against %s | %s | %d pairs | - | agent arms, promotions.tsv |" % (n5["champion"], n5["previous"], txt, pooled["pairs"]))
    lines += ["", "## The stop rule (by %s)" % sr["stop_date"], ""]
    if sr.get("basis") == NO_DATA:
        lines.append("No champion pairs to read: %s." % NO_DATA)
    else:
        lines.append("First Act 3 boss passed per 100 arrivals: %s now (%s; %d pairs), started at %s, target %s; wins %s per 100 (target %s). "
                     "Fresh pairs so far %d of %d; a real block of the champion: %s; days left %s." % (
                         fmt(sr["now_per_100_arrivals"]), sr["basis"], sr["pairs"], fmt(sr["start_per_100_arrivals"], 0), fmt(sr["target_per_100_arrivals"], 0),
                         fmt(sr["now_wins_per_100"], 2), fmt(sr["target_wins_per_100"], 1), sr["fresh_pairs"], sr["pairs_needed"],
                         "yes" if sr["real_block_of_champion"] else "not yet", fmt(sr["days_left"])))
    lines += ["", "Strict means a run won or its floor is above 48; an arrival is floor 48 reached, a win, or a boss-damage entry for Act 3. "
              "A crashed real run counts as a loss."]
    return "\n".join(lines) + "\n"


def fill_template(text: str, doc: dict[str, Any]) -> str:
    """Replace {{a.b.c}} (and {{a.b.c:nd}}, nd = decimals) with values from the JSON document; a missing value prints 'no data'.
    The leading <!-- ... --> comment of a template (its how-to) is dropped."""
    text = re.sub(r"\A\s*<!--.*?-->\s*", "", text, count=1, flags=re.S)
    def get(path: str) -> Any:
        cur: Any = doc
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                cur = cur[int(part)]
            else:
                return None
        return cur

    def sub(m: re.Match[str]) -> str:
        key, _, nd = m.group(1).partition(":")
        v = get(key.strip())
        if v is None:
            return NO_DATA
        if isinstance(v, float) and nd.strip().isdigit():
            return ("%." + nd.strip() + "f") % v
        if isinstance(v, bool):
            return "yes" if v else "no"
        return str(v)

    return re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", sub, text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The five honest weekly numbers (reads existing files only)")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="the lab root (default D:/spireline)")
    ap.add_argument("--now", help="UTC time to read ages against (ISO, default now)")
    ap.add_argument("--out-dir", help="where weekly-numbers-<date>.json and .md are written (default <root>/referee/backlog/weekly)")
    ap.add_argument("--no-write", action="store_true", help="print only")
    ap.add_argument("--json-only", action="store_true", help="print the JSON instead of the Markdown")
    ap.add_argument("--fill", help="a template file with {{key.path}} tokens: print it filled from the numbers")
    a = ap.parse_args(argv)
    root = Path(a.root)
    now = datetime.now(timezone.utc) if not a.now else datetime.fromisoformat(a.now.replace("Z", "+00:00"))
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    doc = build(root, now)
    md = render_markdown(doc)
    if a.fill:
        print(fill_template(Path(a.fill).read_text(encoding="utf-8"), doc), end="")
    elif a.json_only:
        print(json.dumps(doc, indent=1))
    else:
        print(md, end="")
    if not a.no_write:
        out = Path(a.out_dir) if a.out_dir else root / "referee" / "backlog" / "weekly"
        out.mkdir(parents=True, exist_ok=True)
        stem = "weekly-numbers-%s" % now.strftime("%Y-%m-%d")
        (out / (stem + ".json")).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        (out / (stem + ".md")).write_text(md, encoding="utf-8")
        print("wrote %s.json and %s.md" % (stem, stem), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
