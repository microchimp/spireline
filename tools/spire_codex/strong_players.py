"""The strong-player set of the Spire Codex export (D55 addendum 7): who wins at Ironclad Ascension 10, from aggregates only.

Usage: python3 -I strong_players.py <a10_vanilla.jsonl.gz> <exam_ids.txt> <out_dir> [--min-runs 20] [--strength 20] [--top 0.25]
                                     [--write-corpus]

The input is the vanilla A10 working file written by `filter_a10.py --keep-player-token` and `vanilla_filter.py` (it holds the
pseudonymous `player_token`). The steps:

1. The pool: every Ironclad Ascension 10 standard single-player finished unmodified run with a token, outside the exam fifth. The
   exam fifth (D38: the ids file united with the fixed hash bucket 0, as `tools/boss_entry.is_exam`) is never counted into the
   selection or the pool; it is counted once, as the exam, in the report.
2. A player is eligible with at least `--min-runs` such runs. Players are ranked by a shrunk win rate, the posterior mean of a beta
   prior with the pool's win rate as its mean and `--strength` runs of weight: (wins + strength * pool_rate) / (runs + strength).
3. The strong set is the top `--top` of the eligible players by that rank (ties: more runs, then a fixed hash of the id).
4. `aggregates.json`: counts and rates for the strong set, the other eligible players, the players under the run threshold and the
   pool (runs, wins, Act 1 and Act 2 boss kills per 100 runs), per fifth, and an honest check that selects on fifths 1 to 3 only and
   reads the same players on fifth 4. A cell under `MIN_CELL` runs is suppressed (null). No player id is written to it.
5. With `--write-corpus`, `strong_corpus.jsonl.gz` holds the strong players' non-exam runs with `player_token` removed, for the human
   prior's pipeline (a working file under data/, never committed).

Nothing here prints or stores a player id outside the process; the corpus file carries none.
"""

import argparse
import collections
import gzip
import hashlib
import json
import math
import os
import sys

EXAM_SALT = "spireline-d38-exam-fifth|"  # tools/boss_entry.py's rule: the fifth of a run by a fixed hash of its id
EXAM_BUCKET = 0
MIN_CELL = 20  # D13: a cell over fewer runs is not shown
CHARACTER = "CHARACTER.IRONCLAD"


def exam_bucket(run_id: str) -> int:
    return int(hashlib.sha256((EXAM_SALT + str(run_id)).encode()).hexdigest()[:8], 16) % 5


def run_id(r: dict) -> str:
    return str(r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}")


def is_exam(rid: str, ids) -> bool:
    return rid in ids or exam_bucket(rid) == EXAM_BUCKET


def human_ok(r: dict) -> bool:
    """Ironclad, Ascension 10, standard, one player, finished (not abandoned), no modifiers (tools/boss_entry.human_ok)."""
    pl = r.get("players") or []
    return (r.get("ascension") == 10 and r.get("game_mode") == "standard" and not r.get("was_abandoned") and not r.get("modifiers")
            and len(pl) == 1 and pl[0].get("character") == CHARACTER)


def reached(r: dict) -> tuple[int, int]:
    """(Act 1 boss beaten, Act 2 boss beaten) as 0/1: the run entered Act 2 (Act 3), or won."""
    acts = r.get("map_point_history") or []
    win = bool(r.get("win"))
    a1 = int(win or (len(acts) >= 2 and bool(acts[1])))
    a2 = int(win or (len(acts) >= 3 and bool(acts[2])))
    return a1, a2


def shrunk(wins: int, runs: int, pool_rate: float, strength: float) -> float:
    """Posterior mean of the win rate: a beta prior with mean `pool_rate` worth `strength` runs."""
    return (wins + strength * pool_rate) / (runs + strength)


class Tally:
    """Runs, wins and boss kills of a group; `row()` suppresses a group under MIN_CELL runs."""

    __slots__ = ("runs", "wins", "a1", "a2")

    def __init__(self) -> None:
        self.runs = self.wins = self.a1 = self.a2 = 0

    def add(self, win: int, a1: int, a2: int) -> None:
        self.runs += 1
        self.wins += win
        self.a1 += a1
        self.a2 += a2

    def merge(self, o: "Tally") -> None:
        self.runs += o.runs
        self.wins += o.wins
        self.a1 += o.a1
        self.a2 += o.a2

    def row(self) -> dict:
        if self.runs < MIN_CELL:
            return {"runs": None, "wins_per_100": None, "act1_boss_per_100": None, "act2_boss_per_100": None, "suppressed": True}
        per = lambda n: round(100.0 * n / self.runs, 2)  # noqa: E731
        return {"runs": self.runs, "wins": self.wins, "wins_per_100": per(self.wins), "act1_boss_per_100": per(self.a1),
                "act2_boss_per_100": per(self.a2)}


def read_pool(path: str, exam_ids: frozenset, stats: collections.Counter):
    """Per token: {fifth: Tally} over the pool's runs (exam fifth excluded); and the exam runs of each token, counted for the report."""
    per: dict[str, dict[int, Tally]] = {}
    exam_by_token: dict[str, Tally] = {}
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            stats["lines"] += 1
            if '"CHARACTER.IRONCLAD"' not in line:
                continue
            r = json.loads(line)
            if not human_ok(r):
                continue
            stats["ironclad_a10"] += 1
            tok = r.get("player_token")
            rid = run_id(r)
            win = int(bool(r.get("win")))
            a1, a2 = reached(r)
            if is_exam(rid, exam_ids):
                stats["exam_ironclad_a10"] += 1
                if tok:
                    exam_by_token.setdefault(tok, Tally()).add(win, a1, a2)
                continue
            if not tok:
                stats["no_token"] += 1
                per.setdefault("", {}).setdefault(exam_bucket(rid), Tally()).add(win, a1, a2)
                continue
            per.setdefault(tok, {}).setdefault(exam_bucket(rid), Tally()).add(win, a1, a2)
    return per, exam_by_token


def total(ts: dict[int, Tally], fifths=(1, 2, 3, 4)) -> Tally:
    t = Tally()
    for f in fifths:
        if f in ts:
            t.merge(ts[f])
    return t


def select(per: dict, fifths, min_runs: int, strength: float, top: float):
    """The strong tokens chosen on `fifths`: (strong set, eligible set, pool Tally, pool rate)."""
    pool = Tally()
    counts: dict[str, Tally] = {}
    for tok, ts in per.items():
        t = total(ts, fifths)
        pool.merge(t)
        if tok:
            counts[tok] = t
    rate = pool.wins / pool.runs if pool.runs else 0.0
    eligible = [(tok, t) for tok, t in counts.items() if t.runs >= min_runs]
    eligible.sort(key=lambda x: (-shrunk(x[1].wins, x[1].runs, rate, strength), -x[1].runs,
                                 hashlib.sha256(x[0].encode()).hexdigest()))
    n_strong = math.ceil(top * len(eligible)) if eligible else 0
    strong = {tok for tok, _ in eligible[:n_strong]}
    return strong, {tok for tok, _ in eligible}, pool, rate


def group_rows(per: dict, members: set, fifths) -> Tally:
    t = Tally()
    for tok in members:
        t.merge(total(per[tok], fifths))
    return t


def build_report(per: dict, exam_by_token: dict, stats: collections.Counter, min_runs: int, strength: float, top: float) -> dict:
    all_f = (1, 2, 3, 4)
    strong, eligible, pool, rate = select(per, all_f, min_runs, strength, top)
    rest_eligible = eligible - strong
    small = {t for t in per if t and t not in eligible}
    untokened = Tally()
    if "" in per:
        untokened = total(per[""], all_f)
    by_fifth = {str(f): {"strong": group_rows(per, strong, (f,)).row(), "pool": total_pool(per, (f,)).row()} for f in all_f}
    # the honest check: choose on fifths 1 to 3 only, read the same players on fifth 4 (a fresh read of the same selection rule)
    s13, e13, pool13, rate13 = select(per, (1, 2, 3), min_runs, strength, top)
    held_strong, held_pool = group_rows(per, s13, (4,)), total_pool(per, (4,))
    exam_strong = Tally()
    for tok in strong:
        if tok in exam_by_token:
            exam_strong.merge(exam_by_token[tok])
    n_runs_strong = group_rows(per, strong, all_f).runs
    rep = {
        "source": "Spire Codex public run export for v0.107.1",
        "rule": {"pool": "Ironclad Ascension 10 standard single-player finished unmodified vanilla runs with a player token, exam fifth excluded",
                 "eligible": f"at least {min_runs} such runs", "rank": f"beta posterior mean win rate, pool rate as the prior mean, strength {strength:g} runs",
                 "strong": f"top {top:g} of the eligible players", "min_cell_runs": MIN_CELL},
        "read": {"lines": stats["lines"], "ironclad_a10_runs": stats["ironclad_a10"], "exam_fifth_runs": stats["exam_ironclad_a10"],
                 "pool_runs": pool.runs, "runs_without_token": stats["no_token"]},
        "players": {"with_token": len([t for t in per if t]), "eligible": len(eligible), "strong": len(strong),
                    "rest_eligible": len(rest_eligible), "under_threshold": len(small)},
        "pool_win_rate": round(rate, 6),
        "groups": {"strong": group_rows(per, strong, all_f).row(), "rest_eligible": group_rows(per, rest_eligible, all_f).row(),
                   "under_threshold": group_rows(per, small, all_f).row(), "no_token": untokened.row(), "pool": pool.row()},
        "strong_runs_by_fifth": {str(f): (group_rows(per, strong, (f,)).row()) for f in all_f},
        "by_fifth": by_fifth,
        "honest_check": {"selected_on": "fifths 1 to 3", "players": len(s13), "fifth4_strong": held_strong.row(), "fifth4_pool": held_pool.row()},
        "exam_fifth_of_strong_players": exam_strong.row(),
        "strong_runs_total": n_runs_strong,
    }
    return rep


def total_pool(per: dict, fifths) -> Tally:
    t = Tally()
    for tok, ts in per.items():
        t.merge(total(ts, fifths))
    return t


def write_corpus(src: str, dst: str, exam_ids: frozenset, strong: set) -> int:
    """The strong players' non-exam Ironclad runs, token removed."""
    n = 0
    opener = gzip.open if src.endswith(".gz") else open
    with opener(src, "rt", encoding="utf-8") as fh, gzip.open(dst, "wt", encoding="utf-8") as out:
        for line in fh:
            if '"CHARACTER.IRONCLAD"' not in line:
                continue
            r = json.loads(line)
            if not human_ok(r) or r.get("player_token") not in strong or is_exam(run_id(r), exam_ids):
                continue
            r.pop("player_token", None)
            out.write(json.dumps(r, separators=(",", ":")) + "\n")
            n += 1
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("exam_ids")
    ap.add_argument("out_dir")
    ap.add_argument("--min-runs", type=int, default=20)
    ap.add_argument("--strength", type=float, default=20.0)
    ap.add_argument("--top", type=float, default=0.25)
    ap.add_argument("--write-corpus", action="store_true")
    a = ap.parse_args(argv)
    ids = frozenset(x.strip() for x in open(a.exam_ids, encoding="utf-8").read().split() if x.strip())
    if not ids:
        sys.exit("strong_players: the exam ids file lists no run")
    os.makedirs(a.out_dir, exist_ok=True)
    stats: collections.Counter = collections.Counter()
    per, exam_by_token = read_pool(a.src, ids, stats)
    rep = build_report(per, exam_by_token, stats, a.min_runs, a.strength, a.top)
    with open(os.path.join(a.out_dir, "aggregates.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    if a.write_corpus:
        strong, *_ = select(per, (1, 2, 3, 4), a.min_runs, a.strength, a.top)
        n = write_corpus(a.src, os.path.join(a.out_dir, "strong_corpus.jsonl.gz"), ids, strong)
        print(f"strong_players: {n} runs written to strong_corpus.jsonl.gz", file=sys.stderr)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
