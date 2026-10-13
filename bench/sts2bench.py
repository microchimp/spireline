#!/usr/bin/env python3
"""UNTESTED wrapper for the day-4 measurements the emulator's own scripts do not expose.

Written 2026-10-10 against r33hab/sts2 @ b745217 by READING its source only. Nothing here
has been imported or run. It uses only functions the emulator defines, called exactly as
its own scripts call them; every borrowed call names the line it copies.

Subcommands (each writes one JSON with --json and a readable log on stdout):

  search  sims/s on ONE core for the default combat searcher -- combat_mcts.run_search +
          best_action with c=0.1, tempo rollout, CRN over the first 20% -- on combat
          handles, at each budget. Fights are built exactly as play_net.py builds its
          held-out set (play_net.py:163-169, 248-253).
  scale   the SAME fixed work in W processes at once, for each W in --workers-list:
          aggregate sims/s and per-worker speed against W=1. Workers start together
          (barrier) after a warm-up, so imports and first-call caches are not timed.
  csweep  exploration-constant sweep: the same fights at every c, recording end HP,
          death, and visit entropy / log(n legal) at every decision. The script that
          produced FINDINGS.md:114-119 is not in the repo (see README), so the searcher
          settings are flags.
  crn     paired-vs-independent variance of a root-action comparison at one position,
          the measurement of FINDINGS.md:296-304 rebuilt from combat_mcts primitives.

Run it with the emulator's venv and STS2_EMU set to the emulator checkout:

    STS2_EMU=~/git/sts2 ~/git/sts2/.venv/bin/python sts2bench.py search --json s.json
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import os
import platform
import queue as queue_mod
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

UNTESTED = True
EMU_ENV = "STS2_EMU"
CHARACTER = "Ironclad"  # combat_mcts samplers take a character; play_net passes "Ironclad"


# --------------------------------------------------------------------------------------
# The emulator, imported lazily so spawned workers set the path before importing it
# --------------------------------------------------------------------------------------


def _emu():
    """Return (numpy, combat_mcts, sts2_gym.native, sts2_gym.names) from STS2_EMU.

    `combat_mcts` puts `src/` on sys.path itself (combat_mcts.py:63); `rl/` has to be put
    there by the caller, as waste_probe.py:26-28 does.
    """
    root = os.environ.get(EMU_ENV)
    if not root:
        raise SystemExit(f"set {EMU_ENV} to the emulator checkout, or pass --emu")
    base = Path(root).expanduser().resolve()
    for sub in ("src", "rl"):
        path = str(base / sub)
        if path not in sys.path:
            sys.path.insert(0, path)
    import numpy as np  # noqa: PLC0415
    import combat_mcts as cm  # noqa: PLC0415
    from sts2_gym import names, native  # noqa: PLC0415

    return np, cm, native, names


def _loadavg() -> list[float]:
    try:
        return [round(x, 2) for x in os.getloadavg()]
    except (OSError, AttributeError):  # Windows has no getloadavg
        return []


def _machine() -> dict:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": sys.version.split()[0],
        "loadavg": _loadavg(),
        "emu": Path(os.environ.get(EMU_ENV, "")).name,  # no absolute paths in results
    }


def _write(path: str | None, payload: dict) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out}", flush=True)


# --------------------------------------------------------------------------------------
# One fight under search, as play_net.play_gen plays it
# --------------------------------------------------------------------------------------


def _cfg(args: argparse.Namespace) -> dict:
    extra_low, extra_high = (int(x) for x in args.extra_cards.split(","))
    relic_low, relic_high = (int(x) for x in args.relics.split(","))
    return {
        "c": float(getattr(args, "c", 0.1)),
        "rollout": args.rollout,
        "crn_fraction": float(args.crn_fraction),
        "select": args.select,
        "ascension": int(args.ascension),
        "extra_low": extra_low,
        "extra_high": extra_high,
        "relic_low": relic_low,
        "relic_high": relic_high,
    }


def fight_list(cm, count: int, seed_base: int, encounter: int | None = None) -> list:
    """(seed, encounter) pairs exactly as play_net.main builds them (play_net.py:248-253)."""
    if encounter is not None:
        return [(seed_base + i, encounter) for i in range(count)]
    pool = list(cm.OVERGROWTH_WEAK) + list(cm.OVERGROWTH_NORMAL)
    return [(seed_base + i, pool[i % len(pool)]) for i in range(count)]


def open_fight(np, cm, seed: int, encounter: int, cfg: dict):
    """The fight and its search RNG, as play_net.play_gen opens them (play_net.py:163-169)."""
    extra = cm.sample_extra_cards(seed, cfg["extra_low"], cfg["extra_high"], CHARACTER)
    relics = cm.sample_relics(seed, cfg["relic_low"], cfg["relic_high"], CHARACTER)
    rng = np.random.default_rng([encounter, seed])
    combat = cm.Combat.opening(seed, encounter, cfg["ascension"], 0, extra, relics)
    return combat, rng, extra, relics


def _search(cm, combat, legal, sims: int, rng, move: int, cfg: dict):
    """One decision's tree. Signature: combat_mcts.run_search (combat_mcts.py:791-808)."""
    return cm.run_search(
        combat,
        legal,
        sims,
        rng,
        cfg["c"],
        move,
        None,
        greedy_rollout=cfg["rollout"] == "tempo",
        crn=cfg["crn_fraction"] > 0,
        crn_fraction=cfg["crn_fraction"],
    )


def _choose(cm, root, legal, rng, select: str) -> int:
    """`value`: combat_mcts.best_action (argmax mean without a prior, combat_mcts.py:822-846).
    `visits`: argmax visits, exactly as waste_probe.py:127 selects."""
    if select == "value":
        return cm.best_action(root, legal, rng)
    if not root.children:
        return int(rng.choice(legal))
    return max(root.children, key=lambda a: root.children[a].visits)


def _visit_entropy(root, legal: list, rec: dict) -> None:
    """H(root visits over the legal actions) / log(n legal), for decisions with >= 2 legal.

    FINDINGS.md:114 reports "visit entropy / uniform" without defining it; this is the
    reading that gives 1.00 for round-robin visits. Assumption, see README.
    """
    if len(legal) < 2:
        return
    counts = [root.children[a].visits if a in root.children else 0 for a in legal]
    total = sum(counts)
    if total <= 0:
        return
    h = -sum((n / total) * math.log(n / total) for n in counts if n > 0)
    logn = math.log(len(legal))
    rec["ent_ratio_sum"] += h / logn
    rec["ent_h_sum"] += h
    rec["ent_logn_sum"] += logn
    rec["ent_n"] += 1


def play_fight(np, cm, seed: int, encounter: int, sims: int, cfg: dict) -> dict:
    """Play one fight to its end under search; time only the search (run_search + choose).

    Same loop as play_net.play_gen (play_net.py:170-196): STEP_CAP moves, a fight that
    ends un-won scores 0 HP. probe_throughput.play_fight (probe_throughput.py:496-517)
    times the same span.
    """
    combat, rng, extra, relics = open_fight(np, cm, seed, encounter, cfg)
    rec = {
        "seed": seed,
        "encounter": encounter,
        "sims": sims,
        "c": cfg["c"],
        "extra_cards": len(extra),
        "relics": len(relics),
        "decisions": 0,
        "search_s": 0.0,
        "ent_ratio_sum": 0.0,
        "ent_h_sum": 0.0,
        "ent_logn_sum": 0.0,
        "ent_n": 0,
    }
    start = time.perf_counter()
    try:
        for move in range(cm.STEP_CAP):
            if combat.done:
                break
            legal = combat.legal()
            if not legal:
                break
            t0 = time.perf_counter()
            root = _search(cm, combat, legal, sims, rng, move, cfg)
            action = _choose(cm, root, legal, rng, cfg["select"])
            rec["search_s"] += time.perf_counter() - t0
            rec["decisions"] += 1
            _visit_entropy(root, legal, rec)
            combat.step(action)
        won = bool(combat.won())
        rec["won"] = won
        rec["end_hp"] = combat.hp() if won else 0
        rec["max_hp"] = combat.max_hp()
        rec["capped"] = not combat.done
    finally:
        combat.close()
    rec["wall_s"] = time.perf_counter() - start
    rec["sims_total"] = rec["decisions"] * sims
    return rec


def _warm(np, cm, fight, cfg: dict) -> None:
    """One small search, so the card-type cache (combat_mcts.py:393-397), the pools and the
    library's first calls are paid before anything is timed."""
    combat, rng, _e, _r = open_fight(np, cm, fight[0], fight[1], cfg)
    try:
        legal = combat.legal()
        if legal:
            _search(cm, combat, legal, 8, rng, 0, cfg)
    finally:
        combat.close()


def _mean_ci(values: list) -> tuple:
    if not values:
        return 0.0, 0.0
    mean = statistics.fmean(values)
    if len(values) < 2:
        return mean, float("inf")
    return mean, 1.96 * statistics.stdev(values) / math.sqrt(len(values))


def summarize_search(rows: list) -> dict:
    sims = sum(r["sims_total"] for r in rows)
    search_s = sum(r["search_s"] for r in rows)
    decisions = sum(r["decisions"] for r in rows)
    per_fight = [1000.0 * r["search_s"] / r["sims_total"] for r in rows if r["sims_total"]]
    mean_ms, ci_ms = _mean_ci(per_fight)
    return {
        "fights": len(rows),
        "decisions": decisions,
        "sims_total": sims,
        "search_seconds": search_s,
        "sims_per_s": sims / search_s if search_s else 0.0,
        "ms_per_sim": 1000.0 * search_s / sims if sims else 0.0,
        "ms_per_sim_per_fight_mean": mean_ms,
        "ms_per_sim_per_fight_ci95": ci_ms,
        "ms_per_decision": 1000.0 * search_s / decisions if decisions else 0.0,
        "decisions_per_fight": decisions / len(rows) if rows else 0.0,
        "s_per_fight_wall": statistics.fmean(r["wall_s"] for r in rows) if rows else 0.0,
        "deaths": sum(1 for r in rows if not r["won"]),
        "mean_end_hp": statistics.fmean(r["end_hp"] for r in rows) if rows else 0.0,
    }


# --------------------------------------------------------------------------------------
# search: one core
# --------------------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> None:
    np, cm, _native, _names = _emu()
    cfg = _cfg(args)
    budgets = [int(s) for s in args.sims.split(",")]
    fights = fight_list(cm, args.fights, args.seed_base)
    print(f"search: {len(fights)} fights x budgets {budgets}, cfg {cfg}", flush=True)
    _warm(np, cm, fights[0], cfg)
    rows: dict = {str(b): [] for b in budgets}
    load_start = _loadavg()
    # Budgets interleaved per fight, so load drift lands on every budget alike
    # (the same reason probe_throughput.py:45-46 gives).
    for seed, enc in fights:
        for b in budgets:
            rec = play_fight(np, cm, seed, enc, b, cfg)
            rows[str(b)].append(rec)
            ms = 1000.0 * rec["search_s"] / max(1, rec["sims_total"])
            print(
                f"  seed {seed} enc {enc:>3} sims {b:>4}: {rec['decisions']:>3} decisions "
                f"{rec['search_s']:7.2f} s search  {ms:6.3f} ms/sim  "
                f"{'won ' + str(rec['end_hp']) + ' HP' if rec['won'] else 'DIED'}",
                flush=True,
            )
    out = {
        "kind": "search",
        "untested_wrapper": UNTESTED,
        "settings": dict(cfg, budgets=budgets, fights=args.fights, seed_base=args.seed_base),
        "machine": dict(_machine(), loadavg_start=load_start, loadavg_end=_loadavg()),
        "budgets": {b: {"summary": summarize_search(r), "fights": r} for b, r in rows.items()},
    }
    for b, block in out["budgets"].items():
        s = block["summary"]
        print(
            f"sims {b:>4}: {s['sims_per_s']:8.0f} sims/s on one core  "
            f"{s['ms_per_sim']:.3f} ms/sim  {s['ms_per_decision']:.1f} ms/decision  "
            f"{s['decisions_per_fight']:.1f} decisions/fight  {s['s_per_fight_wall']:.2f} s/fight",
            flush=True,
        )
    _write(args.json, out)


# --------------------------------------------------------------------------------------
# scale: the same work in W processes
# --------------------------------------------------------------------------------------


def _scale_worker(index, barrier, results, cfg, fights, sims, nice) -> None:
    try:
        if nice:
            os.nice(nice)
        np, cm, _native, _names = _emu()
        _warm(np, cm, fights[0], cfg)
        barrier.wait(timeout=300)
        start = _clock()
        recs = [play_fight(np, cm, s, e, sims, cfg) for s, e in fights]
        end = _clock()
        maxrss = _maxrss_kb()
        results.put(
            {
                "index": index,
                "ok": True,
                "pid": os.getpid(),
                "start": start,
                "end": end,
                "sims": sum(r["sims_total"] for r in recs),
                "search_s": sum(r["search_s"] for r in recs),
                "decisions": sum(r["decisions"] for r in recs),
                "maxrss_kb": maxrss,
            },
        )
    except BaseException as exc:  # noqa: BLE001
        try:
            barrier.abort()
        except Exception:  # noqa: BLE001
            pass
        results.put({"index": index, "ok": False, "error": repr(exc)})


# CLOCK_MONOTONIC on Linux, QueryPerformanceCounter on Windows: both comparable across processes.
_clock = time.perf_counter if sys.platform == "win32" else time.monotonic


def _maxrss_kb() -> int:
    if sys.platform == "win32":
        try:
            import ctypes  # noqa: PLC0415
            from ctypes import wintypes  # noqa: PLC0415

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD),
                            ("peak_ws", ctypes.c_size_t)] + [(f"f{i}", ctypes.c_size_t) for i in range(7)]

            k32 = ctypes.WinDLL("kernel32")
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            k32.K32GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD)
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            if k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return pmc.peak_ws // 1024
        except Exception:  # noqa: BLE001
            pass
        return -1
    try:
        import resource  # noqa: PLC0415

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except Exception:  # noqa: BLE001
        return -1


def _run_level(ctx, workers: int, cfg: dict, fights: list, sims: int, nice: int, timeout: float) -> dict:
    barrier = ctx.Barrier(workers)
    results = ctx.Queue()
    procs = [
        ctx.Process(target=_scale_worker, args=(i, barrier, results, cfg, fights, sims, nice))
        for i in range(workers)
    ]
    load_before = _loadavg()
    for p in procs:
        p.start()
    got: list = []
    deadline = time.monotonic() + timeout
    while len(got) < workers and time.monotonic() < deadline:
        try:
            got.append(results.get(timeout=5))
        except queue_mod.Empty:
            dead = [p for p in procs if p.exitcode not in (None, 0)]
            if dead and len(got) < workers:
                # A worker died without reporting (a native abort): release the others.
                try:
                    barrier.abort()
                except Exception:  # noqa: BLE001
                    pass
            if not any(p.is_alive() for p in procs):
                break
    for p in procs:
        p.join(timeout=10)
        if p.is_alive():
            p.terminate()
            p.join(timeout=5)
    ok = [r for r in got if r.get("ok")]
    level = {
        "workers": workers,
        "ok": len(ok),
        "errors": [r for r in got if not r.get("ok")],
        "exitcodes": [p.exitcode for p in procs],
        "loadavg_before": load_before,
        "loadavg_after": _loadavg(),
    }
    if ok:
        span = max(r["end"] for r in ok) - min(r["start"] for r in ok)
        rates = [r["sims"] / (r["end"] - r["start"]) for r in ok if r["end"] > r["start"]]
        search_rates = [r["sims"] / r["search_s"] for r in ok if r["search_s"] > 0]
        level.update(
            {
                "span_s": span,
                "sims_total": sum(r["sims"] for r in ok),
                "agg_sims_per_s": sum(r["sims"] for r in ok) / span if span > 0 else 0.0,
                "per_worker_sims_per_s": rates,
                "per_worker_search_sims_per_s": search_rates,
                "mean_per_worker_sims_per_s": statistics.fmean(rates) if rates else 0.0,
                "min_per_worker_sims_per_s": min(rates) if rates else 0.0,
                "max_rss_kb": max(r.get("maxrss_kb", -1) for r in ok),
            },
        )
    return level


def cmd_scale(args: argparse.Namespace) -> None:
    np, cm, _native, _names = _emu()
    del np
    cfg = _cfg(args)
    fights = fight_list(cm, args.fights, args.seed_base)
    counts = sorted({int(w) for w in args.workers_list.split(",") if w.strip() and int(w) > 0})
    ctx = multiprocessing.get_context("spawn")
    print(f"scale: workers {counts}, {len(fights)} fights x {args.sims} sims per worker", flush=True)
    levels = []
    for w in counts:
        level = _run_level(ctx, w, cfg, fights, args.sims, args.nice, args.timeout)
        levels.append(level)
        print(
            f"  W={w:>3}: ok {level['ok']}/{w}  span {level.get('span_s', 0):7.2f} s  "
            f"aggregate {level.get('agg_sims_per_s', 0):9.0f} sims/s  "
            f"per worker {level.get('mean_per_worker_sims_per_s', 0):7.0f} sims/s",
            flush=True,
        )
        time.sleep(args.settle)
    base = next((lv for lv in levels if lv["workers"] == 1 and lv["ok"] == 1), None)
    if base:
        for lv in levels:
            if lv.get("mean_per_worker_sims_per_s"):
                lv["efficiency_vs_1"] = lv["mean_per_worker_sims_per_s"] / base["mean_per_worker_sims_per_s"]
    out = {
        "kind": "scale",
        "untested_wrapper": UNTESTED,
        "settings": dict(cfg, sims=args.sims, fights=args.fights, seed_base=args.seed_base, nice=args.nice),
        "machine": _machine(),
        "levels": levels,
    }
    _write(args.json, out)


# --------------------------------------------------------------------------------------
# csweep: the same fights at every c
# --------------------------------------------------------------------------------------


def _csweep_job(job: tuple) -> dict:
    seed, encounter, c, sims, cfg = job
    np, cm, _native, _names = _emu()
    rec = play_fight(np, cm, seed, encounter, sims, dict(cfg, c=c))
    rec["pid"] = os.getpid()
    return rec


def run_pool(fn, jobs: list, workers: int) -> tuple:
    """Run every job; survive a worker that dies (a native abort breaks the whole pool).

    Two pool attempts; whatever is left then runs one job per process, so a job that kills
    its process is named rather than taking innocent jobs down with it.
    """
    ctx = multiprocessing.get_context("spawn")
    done: dict = {}
    crashed: list = []
    pending = list(range(len(jobs)))
    for attempt in (1, 2):
        if not pending:
            break
        try:
            with ProcessPoolExecutor(max_workers=max(1, min(workers, len(pending))), mp_context=ctx) as pool:
                futures = {pool.submit(fn, jobs[i]): i for i in pending}
                for n, fut in enumerate(as_completed(futures), start=1):
                    i = futures[fut]
                    try:
                        done[i] = fut.result()
                    except BrokenProcessPool:
                        raise
                    except Exception as exc:  # noqa: BLE001  a Python-level failure
                        crashed.append({"job": list(jobs[i][:3]), "error": repr(exc), "attempt": attempt})
                        done[i] = None
                    if n % 40 == 0:
                        print(f"    {len(done)}/{len(jobs)} fights done", flush=True)
        except BrokenProcessPool as exc:
            print(f"  pool broke on attempt {attempt}: {exc!r}; retrying the unfinished jobs", flush=True)
        pending = [i for i in pending if i not in done]
    for i in pending:
        try:
            with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as pool:
                done[i] = pool.submit(fn, jobs[i]).result()
        except BrokenProcessPool:
            crashed.append({"job": list(jobs[i][:3]), "error": "worker process died", "attempt": "isolated"})
            done[i] = None
        except Exception as exc:  # noqa: BLE001
            crashed.append({"job": list(jobs[i][:3]), "error": repr(exc), "attempt": "isolated"})
            done[i] = None
    return [done.get(i) for i in range(len(jobs))], crashed


def cmd_csweep(args: argparse.Namespace) -> None:
    _np, cm, _native, _names = _emu()
    cfg = _cfg(args)
    c_values = [float(x) for x in args.c_values.split(",")]
    fights = fight_list(cm, args.fights, args.seed_base)
    # Fight-major order: every c sees the same load drift.
    jobs = [(seed, enc, c, args.sims, cfg) for seed, enc in fights for c in c_values]
    print(
        f"csweep: {len(fights)} fights x c {c_values} at {args.sims} sims, rollout {cfg['rollout']}, "
        f"crn_fraction {cfg['crn_fraction']}, select {cfg['select']}, {args.workers} workers",
        flush=True,
    )
    start = time.perf_counter()
    results, crashed = run_pool(_csweep_job, jobs, args.workers)
    elapsed = time.perf_counter() - start
    rows = [r for r in results if r is not None]
    for c in c_values:
        sel = [r for r in rows if r["c"] == c]
        if not sel:
            continue
        ent_n = sum(r["ent_n"] for r in sel)
        print(
            f"  c={c:<5} fights {len(sel):>4}  mean end HP {statistics.fmean(r['end_hp'] for r in sel):6.2f}  "
            f"P(death) {sum(not r['won'] for r in sel) / len(sel):.3f}  "
            f"visit entropy / uniform {sum(r['ent_ratio_sum'] for r in sel) / max(1, ent_n):.3f}",
            flush=True,
        )
    print(f"  crashed jobs: {len(crashed)}   wall {elapsed:.0f} s", flush=True)
    out = {
        "kind": "csweep",
        "untested_wrapper": UNTESTED,
        "settings": dict(cfg, sims=args.sims, fights=args.fights, seed_base=args.seed_base, c_values=c_values),
        "machine": _machine(),
        "elapsed_s": elapsed,
        "workers": args.workers,
        "crashed": crashed,
        "fights": rows,
    }
    _write(args.json, out)


# --------------------------------------------------------------------------------------
# crn: paired vs independent determinizations at one position
# --------------------------------------------------------------------------------------

IND_BASE = 1_000_000  # determinization seeds stay well inside a C int (seeding.py:26)
CRN_BASE = 5_000_000


def _hand(native, obs) -> list:
    """(slot, card id) for every card in hand, as waste_probe.hand_cards reads them
    (waste_probe.py:61-69). A hand card's action index is its slot (waste_probe.py:152-153)."""
    out = []
    for i in range(native.OBS_MAX_HAND):
        cid = int(obs[native.OBS_HAND_OFFSET + i * native.OBS_CARD_SLOT_SIZE])
        if cid == 0:
            break
        out.append((i, cid))
    return out


def _pair_stats(xa: list, xb: list) -> dict:
    diffs = [a - b for a, b in zip(xa, xb)]
    n = len(diffs)
    mean = statistics.fmean(diffs)
    sd = statistics.stdev(diffs)
    se = sd / math.sqrt(n)
    return {"n": n, "mean_a": statistics.fmean(xa), "mean_b": statistics.fmean(xb),
            "mean_diff": mean, "se": se, "sigma": mean / se if se else float("inf"),
            "sd_per_pair": sd,
            "n_to_2_sigma": math.ceil((2 * sd / abs(mean)) ** 2) if mean else None}


def _indep_stats(xa: list, xb: list) -> dict:
    n = len(xa)
    va, vb = statistics.variance(xa), statistics.variance(xb)
    mean = statistics.fmean(xa) - statistics.fmean(xb)
    se = math.sqrt(va / n + vb / n)
    sd = math.sqrt(va + vb)
    return {"n": n, "mean_a": statistics.fmean(xa), "mean_b": statistics.fmean(xb),
            "mean_diff": mean, "se": se, "sigma": mean / se if se else float("inf"),
            "sd_per_pair": sd,
            "n_to_2_sigma": math.ceil((2 * sd / abs(mean)) ** 2) if mean else None}


def cmd_crn(args: argparse.Namespace) -> None:
    np, cm, native, names = _emu()
    cfg = _cfg(args)
    combat, _rng, extra, relics = open_fight(np, cm, args.seed, args.encounter, cfg)
    infos = names.cards()
    try:
        legal = combat.legal()
        hand = _hand(native, combat.obs)
        hand_names = [infos[cid].name if cid in infos else str(cid) for _s, cid in hand]

        def slot_named(name: str):
            for slot, cid in hand:
                if slot in legal and cid in infos and infos[cid].name == name:
                    return slot
            return None

        a, b = slot_named(args.action_a), slot_named(args.action_b)
        fallback = a is None or b is None
        if fallback:
            # The position is not the one FINDINGS describes; compare the first two
            # distinct playable cards instead and say so.
            seen, picks = set(), []
            for slot, cid in hand:
                if slot in legal and cid not in seen:
                    seen.add(cid)
                    picks.append(slot)
            if len(picks) < 2:
                raise SystemExit(f"crn: fewer than two distinct playable cards in {hand_names}")
            a, b = picks[0], picks[1]
        greedy = cfg["rollout"] == "tempo"

        def value(action: int, seed: int) -> float:
            # A forced root action then a rollout, as simulate_gen does it under CRN:
            # fork with resampling, step, roll out with an RNG seeded from the SAME
            # determinization seed (combat_mcts.py:560-575, 617-625).
            world = combat.fork(seed)
            try:
                world.step(action)
                v, _steps = cm.rollout(world, np.random.default_rng(seed), greedy=greedy)
            finally:
                world.close()
            return float(v)

        n = args.pairs
        t0 = time.perf_counter()
        ind_a = [value(a, IND_BASE + 2 * k) for k in range(n)]
        ind_b = [value(b, IND_BASE + 2 * k + 1) for k in range(n)]
        crn_a = [value(a, CRN_BASE + k) for k in range(n)]
        crn_b = [value(b, CRN_BASE + k) for k in range(n)]
        elapsed = time.perf_counter() - t0
        independent = _indep_stats(ind_a, ind_b)
        paired = _pair_stats(crn_a, crn_b)
        ratio = (independent["se"] / paired["se"]) ** 2 if paired["se"] else float("inf")
        out = {
            "kind": "crn",
            "untested_wrapper": UNTESTED,
            "settings": dict(cfg, encounter=args.encounter, seed=args.seed, pairs=n,
                             action_a=args.action_a, action_b=args.action_b),
            "position": {
                "hand": hand_names,
                "legal": legal,
                "hp": int(combat.obs[0]),
                "max_hp": int(combat.obs[1]),
                "energy": int(combat.obs[3]),
                "extra_card_ids": list(extra),
                "relic_ids": list(relics),
                "action_a": [a, hand_names[a] if a < len(hand_names) else "?"],
                "action_b": [b, hand_names[b] if b < len(hand_names) else "?"],
                "fallback_actions": fallback,
            },
            "independent": independent,
            "crn": paired,
            "variance_reduction": ratio,
            "rollouts": 4 * n,
            "elapsed_s": elapsed,
            "machine": _machine(),
        }
    finally:
        combat.close()
    print(f"crn at encounter {args.encounter} seed {args.seed}: hand {hand_names}", flush=True)
    print(f"  A = {out['position']['action_a']}, B = {out['position']['action_b']}"
          f"{'  (FALLBACK: named cards not both playable)' if fallback else ''}", flush=True)
    for label in ("independent", "crn"):
        s = out[label]
        print(f"  {label:<12} mean diff {s['mean_diff']:+.4f}  SE {s['se']:.4f}  {s['sigma']:.1f} sigma  "
              f"n to 2 sigma {s['n_to_2_sigma']}", flush=True)
    print(f"  variance reduction {ratio:.2f}x  ({4 * n} rollouts, {elapsed:.1f} s)", flush=True)
    _write(args.json, out)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _common(p: argparse.ArgumentParser, *, rollout="tempo", crn_fraction=0.2, select="value") -> None:
    p.add_argument("--seed-base", type=int, default=400, help="400+ is play_net's held-out set")
    p.add_argument("--ascension", type=int, default=8)
    p.add_argument("--extra-cards", default="2,8", help="as play_net.py:234")
    p.add_argument("--relics", default="0,5", help="as play_net.py:235")
    p.add_argument("--rollout", choices=["tempo", "uniform"], default=rollout)
    p.add_argument("--crn-fraction", type=float, default=crn_fraction, help="0 turns CRN off")
    p.add_argument("--select", choices=["value", "visits"], default=select)
    p.add_argument("--json", default=None)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--emu", default=None, help=f"emulator checkout (else ${EMU_ENV})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("search", help="sims/s on one core at each budget")
    _common(p)
    p.add_argument("--sims", default="60,300")
    p.add_argument("--fights", type=int, default=16)
    p.add_argument("--c", type=float, default=0.1)
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("scale", help="the same work in W processes at once")
    _common(p)
    p.add_argument("--workers-list", default="1,2,4,8")
    p.add_argument("--sims", type=int, default=60)
    p.add_argument("--fights", type=int, default=8, help="fights EACH worker plays")
    p.add_argument("--c", type=float, default=0.1)
    p.add_argument("--nice", type=int, default=0)
    p.add_argument("--settle", type=float, default=3.0, help="seconds idle between levels")
    p.add_argument("--timeout", type=float, default=1800.0, help="per level")
    p.set_defaults(fn=cmd_scale)

    p = sub.add_parser("csweep", help="exploration-constant sweep, same fights for every c")
    _common(p, rollout="uniform", crn_fraction=0.0, select="visits")
    p.add_argument("--c-values", default="0.1,1.4")
    p.add_argument("--fights", type=int, default=240)
    p.add_argument("--sims", type=int, default=60)
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    p.set_defaults(fn=cmd_csweep)

    p = sub.add_parser("crn", help="paired vs independent variance at one position")
    _common(p)
    p.add_argument("--encounter", type=int, default=29, help="29 = fogmog (env.py:43)")
    p.add_argument("--seed", type=int, default=406, help="FINDINGS.md:282")
    p.add_argument("--pairs", type=int, default=1500)
    p.add_argument("--action-a", default="Bash")
    p.add_argument("--action-b", default="StrikeIronclad")
    p.set_defaults(fn=cmd_crn)

    args = parser.parse_args(argv)
    if args.emu:
        os.environ[EMU_ENV] = str(Path(args.emu).expanduser().resolve())
    args.fn(args)


if __name__ == "__main__":
    main()
