#!/usr/bin/env python3
"""Turn a run_all.sh results directory into one JSON of key figures, and print a table.

Pure standard library (Python 3.8+), so it runs with the system python3 on either machine
and imports nothing from the emulator:

    python3 collect.py results/<host>-<date>            # writes <dir>/summary.json
    python3 collect.py results/<host>-<date> --json other.json

Measured figures are compared against two kinds of reference, kept apart on purpose:
  design  the Spireline design's M1 Pro ESTIMATES (spireline-design-v1.1.md), which were
          extrapolated from the M4 Max and never measured;
  M4 Max  r33hab's MEASURED figures on an Apple M4 Max (rl/run_train/DESIGN.md at b745217).
FINDINGS.md figures come from evangambit's machine, which the repo never names (its
reproduce block builds win-x64, FINDINGS.md:720); they appear in the notes column only.

Written 2026-10-10 against outputs the emulator's scripts are DOCUMENTED to print; the
parsers have never seen real output. Anything that fails to parse is reported as missing
rather than guessed.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

DESIGN = "spireline-design-v1.1.md"
M4 = "rl/run_train/DESIGN.md"
FIND = "rl/FINDINGS.md"

# Every reference number, with where it was read. (lo, hi) tuples are ranges.
REF = {
    # Spireline design: M1 Pro estimates and the acceptance rules of day 4 / P0.
    "design_sims_s_6w": ((5000.0, 8000.0), DESIGN + ":81, :465 (6 workers, estimate)"),
    "design_ms_per_sim": ((0.4, 0.7), DESIGN + ":15 (M4 Max, as quoted by the design)"),
    "design_sims_s_core_target": (1000.0, DESIGN + ":972 (target >= 1,000; plan adjusted below 600)"),
    "design_sims_s_core_floor": (600.0, DESIGN + ":972"),
    "design_rollout_ms": ((0.7, 0.9), DESIGN + ":467 (tempo rollout to end of fight, estimate)"),
    "design_step_us": ((58.0, 72.0), DESIGN + ":15"),
    "design_clone_us": ((17.0, 70.0), DESIGN + ":411 (conflicts with M4 8.8/1.4 us)"),
    "design_scaling": (0.9, DESIGN + ":465"),
    # r33hab, Apple M4 Max, measured (rl/run_train/DESIGN.md).
    "m4_clone_run_resample_us": (8.8, M4 + ":356 (8.7-10.7 at real run positions)"),
    "m4_clone_combat_resample_us": (1.4, M4 + ":356"),
    "m4_clone_run_faithful_us": ((7.1, 8.8), M4 + ":357"),
    "m4_sim_run_us": (648.0, M4 + ":358 (turn-0, 25.3 steps)"),
    "m4_sim_combat_us": (448.0, M4 + ":358 (turn-0, 25.0 steps)"),
    "m4_step_run_us": (25.6, M4 + ":359"),
    "m4_step_combat_us": (17.9, M4 + ":359"),
    "m4_inrun_ms_per_sim": ((0.40, 0.41), M4 + ":361-363 (run handles, inside whole runs)"),
    "m4_inrun_ms_per_decision_60": (24.4, M4 + ":362"),
    "m4_combat_ms_per_decision_300_est": (85.0, M4 + ":1881-1883 (DERIVED: 0.4 ms / 1.45)"),
    "m4_s_per_run_60": (2.89, M4 + ":373"),
    "m4_s_per_run_300_interp": (15.6, M4 + ":376, :378 (interpolated between 250 and 500)"),
    "m4_per_worker_8w": (0.93, M4 + ":586 (A9, 120/500, runner); 'about 0.9' :599"),
    "m4_runs_h_8w_60_linear": (9980.0, M4 + ":439 (linear extrapolation, not measured)"),
    # evangambit's machine (unnamed), FINDINGS.md.
    "ev_step_us": (58.0, FIND + ":614"),
    "ev_s_per_fight_60": ((0.65, 0.86), FIND + ":619"),
    "ev_rollout_us": (750.0, FIND + ":621"),
    "mcts_probe_step_us": (72.0, "rl/mcts_probe.py:249"),
    "crn_variance_reduction": (4.6, FIND + ":301-304"),
}
PUBLISHED_C = {  # FINDINGS.md:116-119 (240 fights per setting, settings undocumented)
    0.0: {"mean_hp": 36.2, "p_death": 0.179, "entropy_ratio": 0.39},
    0.1: {"mean_hp": 41.0, "p_death": 0.092, "entropy_ratio": 0.77},
    0.6: {"mean_hp": 40.7, "p_death": 0.133, "entropy_ratio": 0.98},
    1.4: {"mean_hp": 37.5, "p_death": 0.183, "entropy_ratio": 1.00},
}


# --------------------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------------------


def load_json(d: Path, name: str):
    p = d / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"warning: {name} unreadable: {exc}", file=sys.stderr)
        return None


def load_text(d: Path, name: str):
    p = d / name
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def read_env(d: Path) -> dict:
    out = {}
    text = load_text(d, "00_env.txt") or ""
    for line in text.splitlines():
        if line.startswith("---"):
            break
        key, sep, value = line.partition(": ")
        if sep:
            out[key.strip()] = value.strip()
    return out


def read_steps(d: Path) -> list:
    rows = []
    text = load_text(d, "steps.tsv") or ""
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        rows.append({"step": parts[0], "rc": _int(parts[1]), "seconds": _int(parts[4]),
                     "load1_before": _float(parts[5]) if len(parts) > 5 else None,
                     "load1_after": _float(parts[6]) if len(parts) > 6 else None})
    return rows


def _int(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def _float(s):
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


def grab(pattern: str, text, group: int = 1):
    if not text:
        return None
    m = re.search(pattern, text, re.MULTILINE)
    return _float(m.group(group)) if m else None


def peak_rss_mb(text):
    kb = grab(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
    return kb / 1024.0 if kb is not None else None


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------


def mean_ci(values: list):
    if not values:
        return None, None
    m = statistics.fmean(values) if hasattr(statistics, "fmean") else statistics.mean(values)
    if len(values) < 2:
        return m, None
    return m, 1.96 * statistics.stdev(values) / math.sqrt(len(values))


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p from the discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


def within(x, ref) -> bool:
    if x is None:
        return False
    lo, hi = ref if isinstance(ref, tuple) else (ref, ref)
    return lo <= x <= hi


# --------------------------------------------------------------------------------------
# Per-step extraction
# --------------------------------------------------------------------------------------


def verify(d: Path) -> dict:
    out = {}
    for name in ("01_verify_combat.log", "01_verify_run.log"):
        text = load_text(d, name)
        if text is None:
            out[name] = None
            continue
        fails = [ln.strip() for ln in text.splitlines() if "FAIL" in ln]
        oks = sum(1 for ln in text.splitlines() if re.search(r"\bok\b", ln))
        out[name] = {"ok_lines": oks, "fail_lines": fails, "passed": oks > 0 and not fails,
                     "distinct_futures": grab(r"(\d+) distinct futures", text)}
    return out


def agent_probe(d: Path) -> dict:
    text = load_text(d, "02_agent_probe.log")
    us = grab(r"overall:\s*([\d.]+)\s*us/step", text)
    clones = grab(r"clone \+ destroy:\s*([\d,]+)\s*/s", text)
    return {"env_step_us": us, "env_steps_per_s": 1e6 / us if us else None,
            "clone_destroy_per_s_run_start": clones,
            "clone_destroy_us_run_start": 1e6 / clones if clones else None,
            "peak_rss_mb": peak_rss_mb(text)}


def mcts_probe(d: Path) -> dict:
    s = load_text(d, "04_mcts_search.log")
    p = load_text(d, "04_mcts_pressure.log")
    return {"run_search_sims_per_s": grab(r"^\s*([\d,]+)\s+simulations/s", s),
            "run_search_us_per_sim": grab(r"^\s*([\d,.]+)\s+us per simulation", s),
            "run_search_steps_per_s": grab(r"^\s*([\d,]+)\s+steps/s inside search", s),
            "run_search_steps_per_sim": grab(r"^\s*([\d.]+)\s+steps per simulation", s),
            "handle_pool_clones": grab(r"clones held at once before the pool refused:\s*(\d+)", p)}


def micro(d: Path) -> dict:
    js = load_json(d, "03_micro.json")
    if not js or "micro" not in js:
        return {}
    m = js["micro"]
    ab = m.get("ab", {})
    in_run = m.get("in_run", {})
    out = {"ab": ab, "in_run": in_run}
    resample = [v.get("run_clone_resample_us") for v in in_run.values() if v.get("run_clone_resample_us")]
    faithful = [v.get("run_clone_faithful_us") for v in in_run.values() if v.get("run_clone_faithful_us")]
    out["run_clone_resample_us_in_run"] = resample
    out["run_clone_faithful_us_in_run"] = faithful
    out["combat_us_per_step"] = ab.get("combat_us_per_step")
    out["run_us_per_step"] = ab.get("run_us_per_step")
    out["combat_native_steps_per_s"] = 1e6 / ab["combat_us_per_step"] if ab.get("combat_us_per_step") else None
    out["run_native_steps_per_s"] = 1e6 / ab["run_us_per_step"] if ab.get("run_us_per_step") else None
    return out


def runs_by_budget(runs: list) -> dict:
    groups = {}
    for r in runs or []:
        groups.setdefault(str(r.get("budget") or r.get("sims")), []).append(r)
    out = {}
    for b, rs in groups.items():
        sims = sum(f["decisions"] * f["sims"] for r in rs for f in r.get("fights", []))
        search = sum(r.get("seconds_search", 0.0) for r in rs)
        decisions = sum(f["decisions"] for r in rs for f in r.get("fights", []))
        s_mean, s_ci = mean_ci([r["seconds_total"] for r in rs])
        out[b] = {"runs": len(rs), "s_per_run": s_mean, "s_per_run_ci95": s_ci,
                  "ms_per_sim": 1000.0 * search / sims if sims else None,
                  "sims_per_s": sims / search if search else None,
                  "ms_per_decision": 1000.0 * search / decisions if decisions else None,
                  "mean_floor": statistics.mean(r["floor"] for r in rs),
                  "deaths": sum(1 for r in rs if r.get("died")),
                  "boss_kills": sum(1 for r in rs if r.get("boss_killed")),
                  "search_share": search / sum(r["seconds_total"] for r in rs) if rs else None}
    return out


def search(d: Path) -> dict:
    js = load_json(d, "06_search.json")
    if not js:
        return {}
    out = {}
    for b, block in js.get("budgets", {}).items():
        rows = block.get("fights", [])
        sims = sum(r["sims_total"] for r in rows)
        secs = sum(r["search_s"] for r in rows)
        dec = sum(r["decisions"] for r in rows)
        per_fight = [1000.0 * r["search_s"] / r["sims_total"] for r in rows if r["sims_total"]]
        m, ci = mean_ci(per_fight)
        out[b] = {"fights": len(rows), "sims_per_s": sims / secs if secs else None,
                  "ms_per_sim": 1000.0 * secs / sims if sims else None,
                  "ms_per_sim_ci95": ci, "ms_per_decision": 1000.0 * secs / dec if dec else None,
                  "decisions_per_fight": dec / len(rows) if rows else None,
                  "s_per_fight": statistics.mean(r["wall_s"] for r in rows) if rows else None,
                  "deaths": sum(1 for r in rows if not r["won"])}
    return out


def scale(d: Path) -> dict:
    js = load_json(d, "07_scale.json")
    if not js:
        return {}
    levels = js.get("levels", [])
    base = next((lv for lv in levels if lv.get("workers") == 1 and lv.get("ok") == 1), None)
    rows = []
    for lv in levels:
        w = lv.get("workers")
        per = lv.get("mean_per_worker_sims_per_s")
        eff = per / base["mean_per_worker_sims_per_s"] if base and per else None
        rows.append({"workers": w, "ok": lv.get("ok"), "agg_sims_per_s": lv.get("agg_sims_per_s"),
                     "mean_per_worker_sims_per_s": per, "efficiency_vs_1": eff,
                     "max_rss_mb": (lv.get("max_rss_kb") or 0) / 1024.0 or None,
                     "errors": len(lv.get("errors", [])),
                     "failed_workers": (w or 0) - (lv.get("ok") or 0),
                     "load_before": (lv.get("loadavg_before") or [None])[0]})
    best = max((r for r in rows if r["agg_sims_per_s"]), key=lambda r: r["agg_sims_per_s"], default=None)
    return {"levels": rows, "best": best, "settings": js.get("settings", {})}


def parallel(d: Path) -> dict:
    out = {}
    for name in ("08_parallel_8.json", "08_parallel_N.json"):
        js = load_json(d, name)
        if not js or "parallel" not in js:
            continue
        par = js["parallel"]
        single = runs_by_budget(js.get("runs", []))
        s1 = next(iter(single.values()), {}).get("s_per_run") if single else None
        inw = par.get("mean_seconds_per_run_in_worker")
        out[name] = {"workers": par.get("workers"), "runs": par.get("runs"),
                     "runs_per_hour": par.get("runs_per_hour"), "wall_s": par.get("wall_seconds"),
                     "in_worker_s_per_run": inw, "single_s_per_run_other_seeds": s1,
                     "per_worker_speed_rough": s1 / inw if s1 and inw else None}
    return out


def csweep(d: Path, name: str) -> dict:
    js = load_json(d, name)
    if not js:
        return {}
    rows = js.get("fights", [])
    by_c = {}
    for r in rows:
        by_c.setdefault(float(r["c"]), {})[(r["seed"], r["encounter"])] = r
    arms = {}
    for c, fights in sorted(by_c.items()):
        rs = list(fights.values())
        n = len(rs)
        deaths = sum(1 for r in rs if not r["won"])
        hp_m, hp_ci = mean_ci([r["end_hp"] for r in rs])
        ent_n = sum(r["ent_n"] for r in rs)
        logn = sum(r["ent_logn_sum"] for r in rs)
        lo, hi = wilson(deaths, n)
        pub = PUBLISHED_C.get(c)
        arms[str(c)] = {"fights": n, "deaths": deaths, "p_death": deaths / n if n else None,
                        "p_death_wilson95": [lo, hi], "mean_end_hp": hp_m, "mean_end_hp_ci95": hp_ci,
                        "entropy_ratio": sum(r["ent_ratio_sum"] for r in rs) / ent_n if ent_n else None,
                        "entropy_ratio_of_means": sum(r["ent_h_sum"] for r in rs) / logn if logn else None,
                        "decisions_per_fight": statistics.mean(r["decisions"] for r in rs) if rs else None,
                        "published": pub,
                        "published_p_death_in_ci": within(pub["p_death"], (lo, hi)) if pub and lo is not None else None}
    out = {"settings": js.get("settings", {}), "crashed": len(js.get("crashed", [])), "arms": arms}
    if 0.1 in by_c and 1.4 in by_c:
        keys = sorted(set(by_c[0.1]) & set(by_c[1.4]))
        a = [by_c[0.1][k] for k in keys]
        b = [by_c[1.4][k] for k in keys]
        only_lo = sum(1 for x, y in zip(a, b) if not x["won"] and y["won"])
        only_hi = sum(1 for x, y in zip(a, b) if x["won"] and not y["won"])
        diffs = [x["end_hp"] - y["end_hp"] for x, y in zip(a, b)]
        dm, dci = mean_ci(diffs)
        p = mcnemar_exact(only_lo, only_hi)
        arm_lo, arm_hi = arms.get("0.1", {}), arms.get("1.4", {})
        reproduced = bool(
            arm_lo.get("published_p_death_in_ci") and arm_hi.get("published_p_death_in_ci")
            and (arm_lo.get("p_death") or 0) < (arm_hi.get("p_death") or 0) and p < 0.05
        )
        out["paired_0.1_vs_1.4"] = {"pairs": len(keys), "died_only_at_0.1": only_lo,
                                    "died_only_at_1.4": only_hi, "mcnemar_p_two_sided": p,
                                    "hp_diff_0.1_minus_1.4": dm, "hp_diff_ci95": dci,
                                    "reproduced": reproduced}
    return out


def crn(d: Path, name: str) -> dict:
    js = load_json(d, name)
    if not js:
        return {}
    return {"variance_reduction": js.get("variance_reduction"),
            "independent": js.get("independent"), "crn": js.get("crn"),
            "position": js.get("position"), "rollout": js.get("settings", {}).get("rollout")}


# --------------------------------------------------------------------------------------
# Table
# --------------------------------------------------------------------------------------


def fmt(x, digits: int = 0) -> str:
    if x is None:
        return "missing"
    if isinstance(x, tuple):
        return "-".join(fmt(v, digits) for v in x)
    if isinstance(x, float) and (math.isinf(x) or math.isnan(x)):
        return str(x)
    if digits == 0:
        return f"{x:,.0f}"
    return f"{x:,.{digits}f}"


def ref(key: str, digits: int = 0) -> str:
    return fmt(REF[key][0], digits) if key in REF else ""


def build_rows(s: dict) -> list:
    rows = []
    mic, ap, se, ru, sc = s["micro"], s["agent_probe"], s["search"], s["runs"], s["scale"]

    def add(label, measured, design="", m4="", note=""):
        rows.append((label, measured, design, m4, note))

    add("gym run-env step, random play (us)", fmt(ap.get("env_step_us")), ref("design_step_us"), "",
        "agent_probe; FINDINGS:614 58 us, mcts_probe:249 ~72 us")
    add("native step in rollout, combat (us)", fmt(mic.get("combat_us_per_step"), 1), "", ref("m4_step_combat_us", 1),
        "probe_throughput micro A/B")
    add("native step in rollout, run (us)", fmt(mic.get("run_us_per_step"), 1), "", ref("m4_step_run_us", 1), "")
    add("single-core native steps/s, combat", fmt(mic.get("combat_native_steps_per_s")), "",
        fmt(1e6 / REF["m4_step_combat_us"][0]), "1e6 / us per step")
    ab = mic.get("ab", {})
    rr = mic.get("run_clone_resample_us_in_run") or []
    add("clone+resample, run handle (us)", ", ".join(fmt(v, 1) for v in rr) or "missing",
        ref("design_clone_us"), ref("m4_clone_run_resample_us", 1), "in run: fight 1, fight 6")
    add("clone+resample, run, turn 0 (us)", fmt(ab.get("run_clone_resample_us"), 1), "", ref("m4_clone_run_resample_us", 1), "A/B fights")
    add("clone faithful, run handle (us)", ", ".join(fmt(v, 1) for v in (mic.get("run_clone_faithful_us_in_run") or [])) or "missing",
        "", ref("m4_clone_run_faithful_us", 1), "")
    add("clone+resample, combat handle (us)", fmt(ab.get("combat_clone_resample_us"), 1), "", ref("m4_clone_combat_resample_us", 1), "")
    add("clone+destroy at run start (us)", fmt(ap.get("clone_destroy_us_run_start"), 1), "", "", "agent_probe")
    add("turn-0 rollout sim, combat (us)", fmt(ab.get("combat_simulation_us")), fmt(tuple(x * 1000 for x in REF["design_rollout_ms"][0])),
        ref("m4_sim_combat_us"), "FINDINGS:621 ~750 us")
    add("turn-0 rollout sim, run (us)", fmt(ab.get("run_simulation_us")), "", ref("m4_sim_run_us"), "")
    for b in ("60", "300"):
        blk = se.get(b, {})
        add(f"combat search @{b}: ms/sim, 1 core", fmt(blk.get("ms_per_sim"), 3), ref("design_ms_per_sim", 2),
            "~0.28 (derived)" if b == "300" else "", "combat handles, c=0.1 tempo CRN0.2")
        add(f"combat search @{b}: sims/s, 1 core", fmt(blk.get("sims_per_s")), ">= " + ref("design_sims_s_core_target"), "", "design:972 target")
        add(f"combat search @{b}: ms/decision", fmt(blk.get("ms_per_decision"), 1), "",
            ref("m4_combat_ms_per_decision_300_est") + " (derived)" if b == "300" else "", "")
    blk60 = se.get("60", {})
    add("combat fight @60: s/fight, 1 core", fmt(blk60.get("s_per_fight"), 2), "", "", "FINDINGS:619 0.65-0.86 (machine unknown)")
    for b, key in (("60", "m4_s_per_run_60"), ("300", "m4_s_per_run_300_interp")):
        blk = ru.get(b, {})
        add(f"in-run search @{b}: ms/sim (run handles)", fmt(blk.get("ms_per_sim"), 3), "", ref("m4_inrun_ms_per_sim", 2), "probe_throughput runs")
        add(f"Act 1 rules run @{b}: s/run, 1 core", fmt(blk.get("s_per_run"), 2), "", ref(key, 2), "A8 Ironclad")
    lv = {r["workers"]: r for r in sc.get("levels", [])}
    for w in sorted(lv):
        r = lv[w]
        design = fmt(REF["design_sims_s_6w"][0]) if w == 6 else ""
        m4 = ref("m4_per_worker_8w", 2) + " eff" if w == 8 else ""
        add(f"aggregate sims/s, {w} workers (@60)", fmt(r["agg_sims_per_s"]), design, m4,
            f"eff {fmt(r['efficiency_vs_1'], 2)}"
            + (f", {r['failed_workers']} workers FAILED" if r["failed_workers"] else ""))
    best = sc.get("best")
    if best:
        add("best aggregate sims/s", fmt(best["agg_sims_per_s"]), "", "", f"at {best['workers']} workers")
    for name, par in s["parallel"].items():
        add(f"probe_throughput --parallel {par['workers']}: runs/h @60", fmt(par["runs_per_hour"]), "",
            ref("m4_runs_h_8w_60_linear") + " (linear)" if par["workers"] == 8 else "",
            f"rough per-worker {fmt(par['per_worker_speed_rough'], 2)} (different seeds)")
    for label, cs in (("historical", s["csweep_historical"]), ("current", s["csweep_current"])):
        for c, arm in cs.get("arms", {}).items():
            pub = arm.get("published") or {}
            lo, hi = arm["p_death_wilson95"]
            add(f"c-sweep {label} c={c}: P(death)", f"{fmt(arm['p_death'], 3)} [{fmt(lo, 3)}, {fmt(hi, 3)}]",
                fmt(pub.get("p_death"), 3) if pub else "", "", f"FINDINGS:116-119, n={arm['fights']}")
            add(f"c-sweep {label} c={c}: mean HP / entropy", f"{fmt(arm['mean_end_hp'], 1)} / {fmt(arm['entropy_ratio'], 2)}",
                f"{fmt(pub.get('mean_hp'), 1)} / {fmt(pub.get('entropy_ratio'), 2)}" if pub else "", "", "")
        pr = cs.get("paired_0.1_vs_1.4")
        if pr:
            add(f"c-sweep {label}: paired 0.1 vs 1.4", f"McNemar p {pr['mcnemar_p_two_sided']:.3g}",
                "reproduced" if pr["reproduced"] else "NOT reproduced", "",
                f"{pr['died_only_at_0.1']} vs {pr['died_only_at_1.4']} discordant; dHP {fmt(pr['hp_diff_0.1_minus_1.4'], 1)}")
    for label, cr in (("tempo", s["crn_tempo"]), ("uniform", s["crn_uniform"])):
        if cr:
            fb = (cr.get("position") or {}).get("fallback_actions")
            add(f"CRN variance reduction ({label})", fmt(cr.get("variance_reduction"), 2) + "x", "", "",
                f"FINDINGS:301-304 4.6x" + ("; FALLBACK position" if fb else ""))
    return rows


def print_table(rows: list) -> None:
    head = ("quantity", "measured", "design est.", "M4 Max", "note")
    widths = [max(len(str(r[i])) for r in rows + [head]) for i in range(4)]
    widths = [min(w, 44) for w in widths]
    line = f"{head[0]:<{widths[0]}}  {head[1]:>{widths[1]}}  {head[2]:>{widths[2]}}  {head[3]:>{widths[3]}}  {head[4]}"
    print(line)
    print("-" * len(line))
    for r in rows:
        print(f"{r[0]:<{widths[0]}}  {r[1]:>{widths[1]}}  {r[2]:>{widths[2]}}  {r[3]:>{widths[3]}}  {r[4]}")


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------


def checks(s: dict) -> dict:
    out = {}
    steps = s["steps"]
    out["failed_steps"] = [r["step"] for r in steps if r["rc"] not in (0, None)]
    out["timed_out_steps"] = [r["step"] for r in steps if r["rc"] == 124]
    out["csweep_crashed_jobs"] = sum(s[k].get("crashed", 0) for k in ("csweep_historical", "csweep_current"))
    out["scale_failed_workers"] = sum(r["failed_workers"] for r in s["scale"].get("levels", []))
    out["zero_unretried_crashes"] = (not out["failed_steps"] and out["csweep_crashed_jobs"] == 0
                                     and out["scale_failed_workers"] == 0)
    v = s["verify"]
    out["invariants_passed"] = all(x and x.get("passed") for x in v.values()) if v else False
    noisy = [r["step"] for r in steps if (r.get("load1_before") or 0) > 1.0]
    out["steps_started_with_load_above_1"] = noisy
    se60 = s["search"].get("60", {}).get("sims_per_s")
    out["sims_per_s_core_at_60"] = se60
    out["meets_core_target_1000"] = se60 is not None and se60 >= REF["design_sims_s_core_target"][0]
    out["below_replan_floor_600"] = se60 is not None and se60 < REF["design_sims_s_core_floor"][0]
    lv6 = next((r for r in s["scale"].get("levels", []) if r["workers"] == 6), None)
    agg6 = lv6["agg_sims_per_s"] if lv6 else None
    lo, hi = REF["design_sims_s_6w"][0]
    out["sims_per_s_6_workers"] = agg6
    out["vs_design_6_workers"] = None if agg6 is None else ("below" if agg6 < lo else "above" if agg6 > hi else "within")
    out["c_sweep_reproduced"] = {k: (s[k].get("paired_0.1_vs_1.4") or {}).get("reproduced")
                                 for k in ("csweep_historical", "csweep_current")}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("results", type=Path)
    ap.add_argument("--json", type=Path, default=None, help="default <results>/summary.json")
    args = ap.parse_args()
    d = args.results
    if not d.is_dir():
        print(f"no such directory: {d}", file=sys.stderr)
        return 2
    s = {
        "results_dir": str(d.resolve()),
        "env": read_env(d),
        "steps": read_steps(d),
        "verify": verify(d),
        "agent_probe": agent_probe(d),
        "micro": micro(d),
        "mcts_probe": mcts_probe(d),
        "runs": runs_by_budget((load_json(d, "05_runs.json") or {}).get("runs", [])),
        "search": search(d),
        "scale": scale(d),
        "parallel": parallel(d),
        "csweep_historical": csweep(d, "09_csweep_historical.json"),
        "csweep_current": csweep(d, "09_csweep_current.json"),
        "crn_tempo": crn(d, "10_crn_tempo.json"),
        "crn_uniform": crn(d, "10_crn_uniform.json"),
        "references": {k: {"value": v[0], "source": v[1]} for k, v in REF.items()},
        "published_c_sweep": {str(k): v for k, v in PUBLISHED_C.items()},
    }
    s["checks"] = checks(s)
    rows = build_rows(s)
    s["table"] = [dict(zip(("quantity", "measured", "design", "m4_max", "note"), r)) for r in rows]
    env = s["env"]
    print(f"{env.get('host', '?')}  {env.get('cpu_model', '?')}  nproc {env.get('nproc', '?')} "
          f"(physical {env.get('physical_cores', '?')})  wsl {env.get('wsl', '?')}  emu {env.get('emu_head', '?')[:9]}")
    print()
    print_table(rows)
    print()
    for k, v in s["checks"].items():
        print(f"  {k}: {v}")
    out = args.json or (d / "summary.json")
    out.write_text(json.dumps(s, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
