"""How the run-level chooser's values hold up on the runs it played (reset order step C, 2026-11-02).

    python -I tools/vrun_residuals.py --runs-root <LAB>/runs --gens 9 --out residuals.json

For every self-play decision with two or more valued options (`values`, the chooser's V_W in floors, recorded at the time) it
keeps: the gap between the best and the second-best option, and the residual of the chosen option (the run's final floor
minus V_W of the option taken). A generation's fit was trained on the three generations before it, so its own generation's
runs are out of sample. Grouped by act, screen and what was taken (for the map: the node type; elites split by whether one was
on offer). Only aggregates are written. One process, BelowNormal priority, no game.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boss_entry import below_normal, shard_files  # noqa: E402

NODE = {1: "M", 2: "E", 3: "R", 4: "S", 5: "T", 6: "B", 7: "?", 8: "A"}
GAPS = (0.1, 0.25, 0.5, 1.0)


class Cell:
    __slots__ = ("n", "r", "r2", "gap_n", "gaps")

    def __init__(self) -> None:
        self.n, self.r, self.r2, self.gap_n = 0, 0.0, 0.0, 0
        self.gaps = [0] * len(GAPS)

    def add(self, residual: float, gap: float) -> None:
        self.n += 1
        self.r += residual
        self.r2 += residual * residual
        for i, g in enumerate(GAPS):
            self.gaps[i] += gap < g

    def row(self) -> dict:
        m = self.r / self.n
        sd = math.sqrt(max(0.0, self.r2 / self.n - m * m))
        return {"n": self.n, "residual": round(m, 3), "se": round(sd / math.sqrt(self.n), 3),
                **{f"gap<{g}": round(c / self.n, 3) for g, c in zip(GAPS, self.gaps)}}


def what_taken(d: dict) -> str:
    o = d["options"][d["chosen"]]
    k = o["kind"]
    if k == "map.node":
        t = NODE.get(int(o["node"][2]), "x")
        if t != "E" and any(int(x["node"][2]) == 2 for x in d["options"] if x["kind"] == "map.node"):
            return f"map:{t}(E offered)"
        return f"map:{t}"
    return k


def explore_cost(vals: list[float], tau: float, eps: float) -> tuple[float, float]:
    """(floors lost by the head's own values, chance of a pick other than the best) under softmax(V / tau) plus eps uniform."""
    best = max(vals)
    w = [math.exp((v - best) / tau) for v in vals] if tau > 0 else [float(v == best) for v in vals]
    z = sum(w)
    pi = [(1 - eps) * x / z + eps / len(vals) for x in w]
    ev = sum(p * v for p, v in zip(pi, vals))
    return best - ev, 1.0 - max(pi)


def scan(paths, cells, margins, per_run, explore=None) -> int:
    runs = 0
    for p, _g in paths:
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r["policy"].get("tau", 0) or r["policy"].get("eps", 0):
                    per_run["exploring_runs"] += 1
                runs += 1
                floor = int(r["outcome"]["final_floor"])
                killed = floor > 17 or bool(r["outcome"].get("won"))
                for d in r["decisions"]:  # the playing net's own Act 1 boss-kill reading, rows before the boss room (keep.py's cut)
                    pf = d.get("p_floor")
                    if pf and int(d["floor"]) <= 16:
                        per_run["head_rows"] += 1
                        per_run["head_p"] += sum(pf[17:])
                        per_run["head_y"] += killed
                        per_run["head_sq"] += (sum(pf[17:]) - killed) ** 2
                for d in r["decisions"]:
                    vals = d.get("values") or []
                    vv = sorted((v for v in vals if v is not None), reverse=True)
                    if len(vv) < 2 or vals[d["chosen"]] is None:
                        continue
                    act = int(d["state"]["act_index"]) + 1
                    gap = vv[0] - vv[1]
                    res = floor - vals[d["chosen"]]
                    taken = what_taken(d)
                    for key in (f"act{act}|{d['type']}|{taken}", f"act{act}|{d['type']}|*", f"act{act}|*|*"):
                        cells[key].add(res, gap)
                    per_run["chosen_not_best"] += vals[d["chosen"]] < vv[0] - 1e-9
                    if explore:
                        lost, other = explore_cost(vv, *explore)
                        per_run[f"explore_lost_act{act}"] += lost
                        per_run[f"explore_other_act{act}"] += other
                        per_run[f"explore_decisions_act{act}"] += 1
                    per_run["decisions"] += 1
                    if d["type"] == "map":  # the elite's margin where one was on offer beside another node type
                        ev = [v for o, v in zip(d["options"], vals) if v is not None and int(o["node"][2]) == 2]
                        ov = [v for o, v in zip(d["options"], vals) if v is not None and int(o["node"][2]) != 2]
                        if ev and ov:
                            margins[f"act{act}"].append(max(ev) - max(ov))
    return runs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--gens", default="9")
    ap.add_argument("--max-files", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--explore", help="tau,eps: also the floors self-play would give up by the head's own values under that sampling")
    a = ap.parse_args(argv)
    below_normal()
    gens = {int(x) for x in a.gens.split(",")}
    paths = list(shard_files(Path(a.runs_root), gens))
    if a.max_files:
        paths = paths[: a.max_files]
    cells: dict[str, Cell] = defaultdict(Cell)
    margins: dict[str, list[float]] = defaultdict(list)
    per_run: dict[str, int] = defaultdict(int)
    explore = tuple(float(x) for x in a.explore.split(",")) if a.explore else None
    runs = scan(paths, cells, margins, per_run, explore)
    def q(xs, p):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(p * len(xs)))], 3) if xs else None
    if explore:
        per_run = dict(per_run)
        for act in (1, 2, 3):
            n = per_run.get(f"explore_decisions_act{act}", 0)
            if n:
                per_run[f"explore_act{act}"] = {"decisions": n, "floors_lost_per_run": round(per_run[f"explore_lost_act{act}"] / runs, 3),
                                                "other_than_best_share": round(per_run[f"explore_other_act{act}"] / n, 3)}
            for k in ("lost", "other", "decisions"):
                per_run.pop(f"explore_{k}_act{act}", None)
        per_run["explore"] = {"tau": explore[0], "eps": explore[1]}
    per_run = dict(per_run)
    n = per_run.pop("head_rows", 0)
    if n:
        rate, mean_p, sq = per_run.pop("head_y") / n, per_run.pop("head_p") / n, per_run.pop("head_sq") / n
        per_run["recorded_act1_head"] = {"rows": n, "kill_rate": round(rate, 4), "mean_predicted": round(mean_p, 4),
                                         "brier": round(sq, 5), "brier_skill_vs_rate": round(1 - sq / (rate * (1 - rate)), 4)}
    doc = {"gens": sorted(gens), "files": len(paths), "runs": runs, **per_run,
           "cells": {k: c.row() for k, c in sorted(cells.items()) if c.n >= 20},
           "elite_margin": {k: {"n": len(v), "taken_share": round(sum(x > 0 for x in v) / len(v), 3),
                                "q10": q(v, 0.1), "q25": q(v, 0.25), "median": q(v, 0.5), "q75": q(v, 0.75), "q90": q(v, 0.9)}
                            for k, v in sorted(margins.items())}}
    Path(a.out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("files", "runs", "decisions", "chosen_not_best", "exploring_runs") if k in doc}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
