"""Builds the synthetic lab under tests/fixtures/morning_report/root/referee/LAB for tests/test_morning_report.py.

    python tests/fixtures/morning_report/build_fixture.py

Every row is made up (no real seeds, no real run); the numbers are small enough to check by hand and the tests quote them:

  nightly/2026-11-01  g7   4 ended runs, no crash                        (generation 7)
  nightly/2026-11-02  g9   4 ended + 1 crash row                         (generation 9, floors 20 30 17 40)
  nightly/2026-11-03  g9   4 ended + 1 crash row + 1 fight_unfinished    (generation 9, floors 10 17 17 34)
  nightly/2026-11-04  g11  8 ended + 2 crash rows of 10 seeds            (generation 11, floors 10 17 25 34 51 12 17 20)

The emulator arm of each night is `g<N>-emu`. The 2026-11-04 night also carries ranked.json, by_family.json,
divergences.jsonl, machine.jsonl, compare.json, wall.json, a Windows-log export (winlog.json, beside this script) and a copy of the real arm's game logs
(root/logs/w5-night-20261104-stdout).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "root"  # the lab sits where the real one does: <root>/referee/LAB, the copied logs in <root>/logs
LAB = ROOT / "referee" / "LAB"


def epoch(text: str) -> float:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()


def put(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")


def putl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def real_end(seed, floor, acts=(), end="death", asked=100, d=0, ra=0, rf=0, cards=(), streak=None, extra=None, w=0) -> dict:
    row = {"ev": "end", "w": w, "seed": seed, "character": "IRONCLAD", "end": end, "floor": floor, "asked": asked,
           "stats": {"decisions": asked, "diverged": d, "reanchors": ra, "reanchor_failed": rf},
           "boss_damage_acts": [list(a) for a in acts], "cards": [list(c) for c in cards], "nodes": "", "t_end": 0.0,
           "streak": streak or {"n": 1, "screen": "combat", "action": 0}}
    row.update(extra or {})
    return row


def real_crash(seed, error, t_end, w=0, where=None) -> dict:
    row = {"ev": "crash", "w": w, "seed": seed, "error": error, "s": 12.5, "t_end": t_end, "restarts": 0,
           "streak": {"n": 0, "screen": None, "action": None}, "divergences": []}
    if where:
        row["where"] = where
    return row


def emu_row(ix, seed, floor, acts=(), nodes="", end="death", win=False, crash=False, decisions=80) -> dict:
    return {"seed": seed, "ix": ix, "win": win, "floor": floor, "end": end, "decisions": decisions, "crash": crash,
            "boss_damage_acts": [list(a) for a in acts], "nodes": nodes, "cards": []}


def seeds(prefix: str, n: int) -> list[str]:
    return [f"{prefix}{i:02d}" for i in range(n)]


def night_files(date, agent, gen, real_rows, emu_rows, extra_summary=None, decisions=None, noid=0, planned=None):
    """summary.json / result.json for the real arm and summary.json for the emulator arm, consistent with the rows."""
    base = LAB / "nightly" / date
    ended = [r for r in real_rows if r["ev"] == "end"]
    crashes = [r for r in real_rows if r["ev"] == "crash"]
    decs = decisions if decisions is not None else sum(r["asked"] for r in ended)
    reached = sum(1 for r in ended if any(a[0] == 0 for a in r["boss_damage_acts"]))
    won = sum(1 for r in ended if any(a[0] == 0 and a[1] == 1.0 for a in r["boss_damage_acts"]))
    n_c = len(ended) + len(crashes)
    summ = {"character": "IRONCLAD", "engine": "core2", "runs": len(ended), "crashes": len(crashes), "wins": sum(1 for r in ended if r["end"] == "win"),
            "mean_floor": round(sum(r["floor"] for r in ended) / len(ended), 2), "decisions": decs,
            "diverged_decisions": sum(r["stats"]["diverged"] for r in ended), "reanchors": sum(r["stats"]["reanchors"] for r in ended),
            "reanchor_failed": sum(r["stats"]["reanchor_failed"] for r in ended), "wall_s": 7200.0,
            "died_respawns": 0, "deadline_respawns": 0, "unplayed_after_cap": 0, "wrapup_terminated": 0, "network_connections": [],
            "errors": [{"ev": "crash"}] * len(crashes), "gaps": 3,
            "run_fields": {"boss_act1": {"runs": len(ended), "reached": reached, "won": won}},
            "nightly": {"date": date, "agent": agent, "generation": gen, "role": "incumbent", "seed_block": f"N-{date}",
                        "runs_planned": planned or n_c, "runs": n_c,
                        "mean_floor": round(sum(r["floor"] for r in ended) / n_c, 3), "crashes": len(crashes)}}
    summ["divergence_rate"] = round(summ["diverged_decisions"] / decs, 4) if decs else None
    if noid:
        summ["reanchor_fail_reasons"] = {"fight_start:anchor:no emulator id for The given key 'MONSTER_ALPHA_SEG": noid}
    summ.update(extra_summary or {})
    put(base / agent / "summary.json", summ)
    put(base / agent / "result.json", {"runs": n_c, "decisions": decs, "date": date})
    e_end = [r for r in emu_rows if not r["crash"]]
    e_reached = sum(1 for r in e_end if any(a[0] == 0 for a in r["boss_damage_acts"]))
    e_won = sum(1 for r in e_end if any(a[0] == 0 and a[1] == 1.0 for a in r["boss_damage_acts"]))
    put(base / f"{agent}-emu" / "summary.json",
        {"runs": len(emu_rows), "crashes": len(emu_rows) - len(e_end), "wall_s": 3600.0, "decisions": sum(r["decisions"] for r in emu_rows),
         "floor": {"n": len(e_end), "mean": round(sum(r["floor"] for r in e_end) / len(e_end), 4)},
         "run_fields": {"boss_act1": {"runs": len(e_end), "reached": e_reached, "won": e_won}},
         "pool": {"started": 3, "recycled": 0, "died": 0, "timed_out": 0, "raised": 0, "retried": 0, "lost": 0}})
    putl(base / agent / "runs.jsonl", real_rows)
    putl(base / f"{agent}-emu" / "runs.jsonl", emu_rows)


def job(name, date, start, end, secs):
    d = LAB / "runs" / name
    put(d / "job.json", {"version": 1, "job": "nightly-real", "name": name, "main_sha": "0123456789abcdef0123456789abcdef01234567",
                         "created_utc": start, "resumed": 0,
                         "steps": [{"name": "nightly-real", "status": "done", "started_utc": start, "finished_utc": end,
                                    "cmds": {"nightly-real": {"status": "done", "rc": 0, "secs": secs}}}]})
    put(d / "result.json", {"date": date, "wall_s": secs - 60})


def main() -> None:
    # ---- earlier nights
    night_files("2026-11-01", "g7", 7,
                [real_end(f"OLD7{i:02d}", f, asked=50) for i, f in enumerate((10, 12, 14, 16))],
                [emu_row(i, f"OLD7{i:02d}", f) for i, f in enumerate((11, 13, 15, 17))])
    r2 = [real_end("OLD901", 20, [(0, 1.0)], d=1, ra=1), real_end("OLD902", 30, [(0, 1.0), (1, 0.5)]), real_end("OLD903", 17, [(0, 0.5)]),
          real_end("OLD904", 40, [(0, 1.0), (1, 1.0)]),
          real_crash("OLD905", "RuntimeError: the engine refused action 3 in phase 5", epoch("2026-11-02T23:00:00Z"), where="agent")]
    night_files("2026-11-02", "g9", 9, r2, [emu_row(i, f"OLD90{i + 1}", f, [(0, 1.0)] if i else [], "MMB") for i, f in enumerate((18, 22, 17, 33))],
                noid=1)
    r3 = [real_end("NEW901", 10), real_end("NEW902", 17, [(0, 0.3)]), real_end("NEW903", 17, [(0, 0.6)]),
          real_end("NEW904", 34, [(0, 1.0), (1, 0.2)]), real_end("NEW905", 21, end="fight_unfinished", streak={"n": 10, "screen": "shop", "action": 0}),
          real_crash("NEW906", "RuntimeError: the engine refused action 9 in phase 5", epoch("2026-11-03T01:00:00Z"), where="agent")]
    night_files("2026-11-03", "g9", 9, r3, [emu_row(i, f"NEW90{i + 1}", f, [(0, 1.0)] if i == 3 else [], "MMB") for i, f in enumerate((12, 14, 16, 35, 20))],
                noid=2)
    job("20261102T2030-nightly-real", "2026-11-03", "2026-11-02T20:30:00Z", "2026-11-03T00:30:00Z", 14400.0)

    # ---- the night under test: seeds S0000..S0009
    S = [f"SEED{i:04d}" for i in range(10)]
    crash_game_t = epoch("2026-11-03T22:46:08.9Z")
    real = [
        real_end(S[0], 10, asked=100, d=0, ra=1, rf=0, cards=[(2, "BASH"), (5, "skip")], extra={"monsters": ["MONSTER_ALPHA_SEGMENT_A", "MONSTER_ALPHA_SEGMENT_B"]}),
        real_end(S[1], 17, [(0, 0.5)], asked=120, d=1, ra=2, rf=1, cards=[(2, "ANGER"), (4, "ANGER")]),
        real_end(S[2], 25, [(0, 1.0)], asked=140, d=0, ra=0, rf=0, cards=[(3, "skip"), (6, "skip"), (20, "BASH")]),
        real_end(S[3], 34, [(0, 1.0), (1, 0.25)], asked=160, d=2, ra=3, rf=0),
        real_end(S[4], 51, [(0, 1.0), (1, 1.0), (2, 1.0)], end="win", asked=200, d=0, ra=2, rf=1),
        real_end(S[5], 12, asked=80),
        real_end(S[6], 17, [(0, 0.9)], asked=100, d=1, ra=1),
        real_end(S[7], 20, end="fight_unfinished", asked=60, streak={"n": 10, "screen": "shop", "action": 0}),
        real_crash(S[8], "RuntimeError: the engine refused action 24 in phase 5", epoch("2026-11-03T21:10:00Z"), w=2, where="agent"),
        real_crash(S[9], "GameDied: game exited (3221225477)", crash_game_t, w=3),
    ]
    emu = [emu_row(0, S[0], 10, [], "MMM"),
           emu_row(1, S[1], 20, [(0, 1.0)], "MEBM"),
           emu_row(2, S[2], 25, [(0, 1.0)], "MMEBME"),
           emu_row(3, S[3], 17, [(0, 0.4)], "MMB"),
           emu_row(4, S[4], 51, [(0, 1.0), (1, 1.0), (2, 1.0)], "MBMBMB", end="win", win=True),
           emu_row(5, S[5], 12, [], "MM"),
           emu_row(6, S[6], 17, [(0, 0.8)], "MB"),
           emu_row(7, S[7], 25, [(0, 1.0)], "MEBM"),
           emu_row(8, S[8], 19, [(0, 0.2)], "MB"),
           emu_row(9, S[9], 15, [], "M")]
    night_files("2026-11-04", "g11", 11, real, emu, noid=1, planned=10, extra_summary={
        "reanchor_fail_reasons": {"fight_start:anchor:no emulator id for The given key 'MONSTER_ALPHA_SEG": 1, "fight_start:to_map": 1},
        "first_loss_by_reason": {"state_diverged:": 3}})
    base = LAB / "nightly" / "2026-11-04"
    put(base / "g11" / "compare.json", {"paired_seeds": 10, "floor_gap": {"n": 10, "mean": 2.5, "lo": -3.0, "hi": 8.0, "seeds": 10}})
    put(base / "g11" / "wall.json", {"wall_s": 7200.0})
    groups = [
        {"id": "Gother00000", "rank": 1, "tag": "architectural", "class": "damage_block_pipeline", "weight": 600.0, "decisions_affected": 30,
         "divergences": 3, "first_floor": 12, "outcome_changing_confirmed": 2, "display": {"type": "combat", "kinds": [".combat.enemy_hp"], "entities": ["enemy"]}},
        {"id": "Gdb57549c26", "rank": 2, "tag": "architectural", "class": "action_queue", "weight": 300.0, "decisions_affected": 12,
         "divergences": 2, "first_floor": 21, "outcome_changing_confirmed": 1, "display": {"type": "combat", "kinds": [".combat.hand"], "entities": ["card:STRIKE_IRONCLAD"]}},
        {"id": "G2f160e9505", "rank": 3, "tag": "architectural", "class": "action_queue", "weight": 100.0, "decisions_affected": 6,
         "divergences": 1, "first_floor": 17, "outcome_changing_confirmed": 0, "display": {"type": "combat", "kinds": [".combat.hand"], "entities": ["card:DEFEND_IRONCLAD"]}},
    ]
    put(base / "g11" / "ranked.json", {"summary": {"decisions": 960, "state_divergences": 4, "mapping_gaps": 3, "groups": 3, "total_weight": 1000.0,
                                                    "arch_share": 0.5, "outcome_confirmed": 3, "outcome_proxy": 0}, "groups": groups})
    put(base / "g11" / "by_family.json", {"summary": {"verdict": "Tier 1 (synthetic)", "unassigned_share": 0.1},
                                          "families": [{"family": "F06", "name": "card play", "coarse": "card-play hooks", "weight": 500.0, "share": 0.5, "groups": 2},
                                                       {"family": "F08", "name": "damage / HP", "coarse": "damage and block pipeline", "weight": 400.0, "share": 0.4, "groups": 1}]})

    def hand(a, b):
        return {"decision": 1, "floor": 5, "type": "combat", "diff": [[".combat.hand", a, b]]}

    putl(base / "g11" / "divergences.jsonl", [
        hand(["A", "B", "C"], ["A", "B"]),            # game has more
        hand(["A", "B", "C", "D"], ["A", "B", "C"]),  # game has more
        hand(["A"], ["A", "B"]),                      # emulator has more
        hand(["A", "B"], ["A", "C"]),                 # both sides differ: not the D11C shape
        {"decision": 2, "floor": 6, "type": "reward", "diff": [[".hp", 1, 2]]},
    ])
    putl(base / "g11" / "machine.jsonl", [
        {"t": 1.0, "utc": "2026-11-03T20:10:00Z", "cpu_pct": 80.0, "avail_mb": 9000, "mem_load_pct": 60, "disk_latency_ms": 5.0, "games": 12},
        {"t": 2.0, "utc": "2026-11-03T20:10:30Z", "cpu_pct": 60.0, "avail_mb": 7000, "mem_load_pct": 70, "disk_latency_ms": 9.0, "games": 12},
        {"t": 3.0, "utc": "2026-11-03T20:11:00Z", "cpu_pct": 70.0, "avail_mb": 8000, "mem_load_pct": 65, "disk_latency_ms": 7.0, "games": 11}])
    job("20261103T2000-nightly-real", "2026-11-04", "2026-11-03T20:00:00Z", "2026-11-04T00:00:00Z", 14400.0)
    put(LAB / "jobs.json", {"nightly-real": {"enabled": True, "every_h": 20}})
    (LAB / "runner.log").write_text(
        "2026-11-02T20:30:00Z job 20261102T2030-nightly-real: ladder: nightly-real (priority 2)\n"
        "2026-11-03T00:30:00Z nightly-real/nightly-real: rc=0 in 14400.0s\n"
        "2026-11-03T20:00:00Z job 20261103T2000-nightly-real: ladder: nightly-real (priority 2)\n"
        "2026-11-03T22:00:00Z step nightly-real stopped: pause (LAB/PAUSE)\n"
        "2026-11-04T00:00:00Z nightly-real/nightly-real: rc=0 in 14400.0s\n"
        "2026-11-04T01:00:00Z step nightly-real stopped: user (input 0s ago)\n", encoding="utf-8")

    # ---- a Windows-log export (what Get-WinEvent returns, trimmed): the night's window and the previous night's
    def ev(utc, prov, eid, msg):
        return {"utc": utc, "provider": prov, "id": eid, "msg": msg}

    emu_stack = ("Application: pythonw.exe\nCoreCLR Version: 9.0.20\nDescription: The process was terminated due to an unhandled exception.\n"
                 "Exception Info: System.InvalidOperationException: Collection was modified\n"
                 "   at System.Collections.Generic.List`1.Enumerator.MoveNextRare() + 0x27\n"
                 "   at Sts2Emulator.Core.CombatEngine.EndTurn(CombatState, Random) + 0x25aa\n"
                 "   at Sts2Emulator.Core.CombatEngine.StepCore(CombatState, Int32, Random, Int32) + 0x96\n")
    ready_stack = ("Application: pythonw.exe\nCoreCLR Version: 9.0.20\nDescription: The process was terminated due to an unhandled exception.\n"
                   "Exception Info: System.InvalidOperationException: UsePotion#12 Executing at the front of queue 0 is in an invalid state\n"
                   "   at Sts2Emulator.Core2.ActionQueueSet.GetReadyAction() + 0x287\n")
    companion = ("Faulting application name: pythonw.exe, version: 0.0.0.0\nFaulting module name: Sts2Emulator.dll, version: 1.0.0.0\n"
                 "Exception code: 0xc0000409\nFault offset: 0x000000000016ef0b\n")
    game = ("Application: SlayTheSpire2.exe\nCoreCLR Version: 9.0.725.31616\nDescription: The process was terminated due to an unhandled exception.\n"
            "Stack:\n   at Godot.GodotObject.Dispose(Boolean)\n   at Godot.GodotObject.Finalize()\n   at System.GC.RunFinalizers()\n")
    events = [
        ev("2026-11-03T21:30:00.1000000Z", ".NET Runtime", 1026, emu_stack),
        ev("2026-11-03T21:30:01.2000000Z", "Application Error", 1000, companion),                     # companion of the line above
        ev("2026-11-03T22:10:00.0000000Z", ".NET Runtime", 1026, ready_stack),
        ev("2026-11-03T23:00:00.0000000Z", "Application Error", 1000, companion),                     # a native fault alone
        ev("2026-11-03T22:46:08.6720000Z", ".NET Runtime", 1026, game),                                # the game's death, S9's crash row
        ev("2026-11-03T22:50:00.0000000Z", "VSS", 8224, "The VSS service is shutting down."),          # not a process death
        ev("2026-11-03T18:00:00.0000000Z", ".NET Runtime", 1026, emu_stack),                           # before the window
        ev("2026-11-02T22:00:00.0000000Z", ".NET Runtime", 1026, ready_stack),                         # the previous night's window
    ]
    put(HERE / "winlog.json", {"events": events})

    # ---- the copied game logs of the real arm: three runs
    def room(name):
        return f"[INFO] Creating NCombatRoom (synthetic) encounter={name}."

    def dec(i, screen):
        return f"[referee] run decision {i} {screen} x"

    lines = [
        dec(0, "map"), room("JAW_WORM_NORMAL"), dec(1, "combat"), room("CULTISTS_WEAK"), dec(2, "combat"),
        f"[referee] run {S[0]} ended: death after 100 decisions, floor 10",
        dec(0, "map"), room("JAW_WORM_NORMAL"), dec(1, "combat"), room("NOB_ELITE"), dec(2, "combat"), room("GUARDIAN_BOSS"), dec(3, "combat"),
        room("SLIMES_WEAK"), dec(4, "combat"), dec(5, "event"),
        f"[referee] run {S[1]} ended: death after 120 decisions, floor 17",
        dec(0, "map"), room("JAW_WORM_NORMAL"), dec(1, "combat"), room("MYSTERY_EVENT_ENCOUNTER"), dec(2, "combat"), room("OVERGROWTH_CRAWLERS"),
        dec(3, "combat"), room("GUARDIAN_BOSS"), dec(4, "combat"),
        f"[referee] run {S[2]} ended: death after 140 decisions, floor 25",
    ]
    out = ROOT / "logs" / "w5-night-20261104-stdout"
    out.mkdir(parents=True, exist_ok=True)
    (out / "p00r0.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
