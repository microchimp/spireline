"""The night's morning report as a script (D46 item 4, D49 item 4).

    python tools/morning_report.py <night folder> [--agent g11] [--out DIR] [--lab DIR] [--logs DIR]
        [--winlog auto|none|FILE] [--usage TEXT] [--now ISO] [--check]

`<night folder>` is a lab night, e.g. `LAB/nightly/2026-11-03`, holding the real arm `g<N>` and the emulator arm `g<N>-emu`.
With --out DIR it writes three files and prints the edition list; without it, everything goes to the screen:

  morning_report.json   every figure, by section; `cross_checks` set the rows against the arms' own summary files and
                        `not_computed` names each figure the files cannot give, with the source the lane used
  handoff_line.md       the HANDOFF morning line in the lane's format, then the lane's tables (indented)
  edition_figures.md    the short list the paper's edition takes (floors, boss rates, agreement, crashes, the comparison)

With --check nothing is written or reported but the headline figures (seeds, ended runs, crash rows by kind, mean floors
ended and counted, the Act 1 boss reached and killed, the arms' agreement) from the report and again from a second code path
over the rows (see "--check: a second path" below), each with MATCH or MISMATCH; the exit code is 1 on any mismatch.

Sources: the arms' `runs.jsonl`, `summary.json`, `result.json`, `compare.json`, `ranked.json`, `by_family.json`,
`divergences.jsonl`, `machine.jsonl`, `wall.json`; the earlier nights' folders (history, the pooled comparison); the lab
runner's log and the job record (start, end, tree, interruptions); `jobs.json` (spacing of the next night); the copy of the
real arm's workers' game logs when one exists (the only record of the real arm's per-fight results; the block deletes the
originals when it closes); and the Windows application log for the night's window (emulator fail-fasts, the game's own
deaths), read with `Get-WinEvent`.

Counting rules (the lane's): a run row is `ev == end` (ended) or `ev == crash` (a crash row). "Ended" figures leave crash
rows out; "counted" figures give a crash row floor 0, no win and no boss kill (the lab's convention, `summary.json`
`nightly`). A boss is reached when `boss_damage_acts` lists its act and killed when the fraction is 1.0. Rates of a pool are
over its runs. Standard errors: the sample standard deviation of the floors over sqrt(n), sqrt(p(1-p)/n) for rates,
differences by the sum of the variances. Cells of the per-fight tables under 20 fights are suppressed (D13). Results hold no
host name, user name or absolute path (the folder is named relative to the lab).
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

MIN_CELL = 20  # D13: a cell under 20 fights is suppressed
ACT1_BOSS_FLOOR = 17  # cards decided on floors <= 16 are in the deck entering the Act 1 boss
STARTER = 11  # Ironclad's 10 starting cards + Ascender's Bane at A10 (an assumption of the deck proxy)
R1 = {"floor": 27.05, "act1": 0.546, "act2": 0.291, "wins": 0.113}  # the human reference line (boss-entry exam, held-out fifth)
D11C = {"Gdb57549c26": "Strike", "G2f160e9505": "Defend"}  # the D11F2 proof's two groups (hand differs by one basic card)
Z95 = 1.96
WIN_PAD_BEFORE = timedelta(minutes=5)
WIN_PAD_AFTER = timedelta(minutes=2)
CRASH_MATCH_S = 5.0  # a crash row and a Windows log entry this close are the same death
EXIT_NAMES = {
    0xC0000005: "access violation",
    0xC000001D: "illegal instruction",
    0xC000041D: "fatal user callback exception",
    0xC0000409: "stack buffer overrun (fail-fast)",
    0xC00000FD: "stack overflow",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ARM_RE = re.compile(r"^g(\d+)$")


# ---------------------------------------------------------------------------------------------------- small helpers
def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass  # a torn line from a killed writer; the row counts then say how many rows there are
    return out


def parse_utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hhmm(dt: datetime) -> str:
    """HH:MM of a UTC time (the lane writes it before a Z)."""
    return dt.astimezone(timezone.utc).strftime("%H:%M")


def pct(a: int, b: int, d: int = 1) -> str:
    return "n/a" if not b else f"{100.0 * a / b:.{d}f}%"


def ratio(a: int, b: int) -> float | None:
    return None if not b else a / b


def n_(x) -> str:
    return "n/a" if x is None else f"{x:,}"


def num(x, d: int = 2) -> str:
    return "n/a" if x is None else f"{x:.{d}f}"


def sgn(x, d: int = 2) -> str:
    return "n/a" if x is None else f"{x:+.{d}f}"


def rnd(x, d: int = 3):
    return None if x is None else round(x, d)


def margin95_pts(n: int) -> float | None:
    """The widest 95% margin of a rate over n runs, in points (p = 0.5)."""
    return None if not n else 100.0 * Z95 * math.sqrt(0.25 / n)


def hex_exit(code: int) -> str:
    return f"0x{code & 0xFFFFFFFF:08X}"


# ---------------------------------------------------------------------------------------------------- aggregates
@dataclass
class Agg:
    """Sums over ended runs (floors are integers, so n, s and ss give exact means and variances) plus the crash rows."""

    n: int = 0
    s: int = 0
    ss: int = 0
    crashes: int = 0
    wins: int = 0
    a1r: int = 0
    a1k: int = 0
    a2r: int = 0
    a2k: int = 0
    a3r: int = 0
    a3k: int = 0

    def __add__(self, o: "Agg") -> "Agg":
        return Agg(*(getattr(self, f) + getattr(o, f) for f in self.__dataclass_fields__))

    @property
    def nc(self) -> int:  # runs counted: ended plus crash rows
        return self.n + self.crashes

    def mean(self, counted: bool = False) -> float | None:
        k = self.nc if counted else self.n
        return self.s / k if k else None

    def sd(self, counted: bool = False) -> float | None:
        k = self.nc if counted else self.n
        if k < 2:
            return None
        return math.sqrt(max(0.0, (self.ss - self.s * self.s / k) / (k - 1)))


def boss_hit(row: dict, act: int) -> tuple[bool, bool]:
    """(reached, killed) for the boss of 0-based act `act`, from boss_damage_acts."""
    for a, frac in row.get("boss_damage_acts") or []:
        if a == act:
            return True, frac == 1.0
    return False, False


def is_win(row: dict) -> bool:
    return row.get("end") == "win" or row.get("win") is True


def make_agg(ended: list[dict], crashes: int = 0) -> Agg:
    g = Agg(n=len(ended), crashes=crashes)
    for r in ended:
        f = int(r["floor"])
        g.s += f
        g.ss += f * f
        g.wins += 1 if is_win(r) else 0
        for act, (kr, kk) in enumerate((("a1r", "a1k"), ("a2r", "a2k"), ("a3r", "a3k"))):
            reached, killed = boss_hit(r, act)
            setattr(g, kr, getattr(g, kr) + (1 if reached else 0))
            setattr(g, kk, getattr(g, kk) + (1 if killed else 0))
    return g


def split_rows(rows: list[dict], real: bool) -> tuple[list[dict], list[dict]]:
    """(ended rows, crash rows). Real rows carry `ev`; the emulator arm's carry a `crash` flag."""
    if real:
        return [r for r in rows if r.get("ev") == "end"], [r for r in rows if r.get("ev") == "crash"]
    return [r for r in rows if not r.get("crash")], [r for r in rows if r.get("crash")]


def arm_figures(ended: list[dict], crashes: list[dict], real: bool) -> dict:
    g = make_agg(ended, len(crashes))
    floors = [r["floor"] for r in ended]
    out = {
        "rows": len(ended) + len(crashes), "ended": g.n, "crashes": g.crashes,
        "mean_floor": rnd(g.mean(), 4), "sd_floor": rnd(g.sd(), 4), "median_floor": statistics.median(floors) if floors else None,
        "mean_floor_counted": rnd(g.mean(True), 4), "wins": g.wins,
        "chest_stop": sum(1 for r in ended if r.get("end") == "treasure_without_relic_picking"),
        "fight_unfinished": sum(1 for r in ended if r.get("end") == "fight_unfinished"),
        "decisions": sum((r.get("asked") if real else r.get("decisions")) or 0 for r in ended),
    }
    for act in (1, 2, 3):
        r_, k_ = getattr(g, f"a{act}r"), getattr(g, f"a{act}k")
        out[f"act{act}_reached"], out[f"act{act}_killed"] = r_, k_
        out[f"act{act}_killed_of_runs"] = rnd(ratio(k_, g.n), 4)
        out[f"act{act}_killed_of_reached"] = rnd(ratio(k_, r_), 4)
    reached = [r for r in ended if boss_hit(r, 0)[0]]
    picks = [sum(1 for f, c in (r.get("cards") or []) if f <= ACT1_BOSS_FLOOR - 1 and c != "skip") for r in reached]
    out["act1_picks_mean"] = rnd(statistics.fmean(picks), 3) if picks else None
    out["act1_picks_median"] = statistics.median(picks) if picks else None
    out["deck_proxy"] = rnd(STARTER + statistics.fmean(picks), 3) if picks else None
    if real:
        out["diverged"] = sum((r.get("stats") or {}).get("diverged", 0) for r in ended)
        out["reanchors"] = sum((r.get("stats") or {}).get("reanchors", 0) for r in ended)
        out["reanchor_failed"] = sum((r.get("stats") or {}).get("reanchor_failed", 0) for r in ended)
    return out


def mean_diff(a: Agg, b: Agg, counted: bool = False) -> dict:
    ma, mb, sa, sb = a.mean(counted), b.mean(counted), a.sd(counted), b.sd(counted)
    if None in (ma, mb, sa, sb):
        return {"diff": None, "se": None, "z": None}
    k_a, k_b = (a.nc, b.nc) if counted else (a.n, b.n)
    se = math.sqrt(sa * sa / k_a + sb * sb / k_b)
    return {"diff": rnd(ma - mb, 4), "se": rnd(se, 4), "z": rnd((ma - mb) / se, 3) if se else None}


def rate_diff(ka: int, na: int, kb: int, nb: int) -> dict:
    if not na or not nb:
        return {"diff_pts": None, "se_pts": None, "z": None}
    p1, p2 = ka / na, kb / nb
    se = math.sqrt(p1 * (1 - p1) / na + p2 * (1 - p2) / nb)
    return {"diff_pts": rnd(100 * (p1 - p2), 3), "se_pts": rnd(100 * se, 3), "z": rnd((p1 - p2) / se, 3) if se else None}


def agg_block(g: Agg) -> dict:
    return {"runs": g.n, "crashes": g.crashes, "mean_floor": rnd(g.mean(), 4), "sd_floor": rnd(g.sd(), 4),
            "mean_floor_counted": rnd(g.mean(True), 4), "a1_reached": g.a1r, "a1_killed": g.a1k, "a2_reached": g.a2r,
            "a2_killed": g.a2k, "a1_of_runs": rnd(ratio(g.a1k, g.n), 4), "a1_of_reached": rnd(ratio(g.a1k, g.a1r), 4),
            "a2_of_runs": rnd(ratio(g.a2k, g.n), 4), "wins": g.wins}


def compare_blocks(cur: Agg, base: Agg) -> dict:
    return {"base": agg_block(base), "floor_ended": mean_diff(cur, base), "floor_counted": mean_diff(cur, base, True),
            "act1_of_runs": rate_diff(cur.a1k, cur.n, base.a1k, base.n),
            "act1_of_reached": rate_diff(cur.a1k, cur.a1r, base.a1k, base.a1r),
            "act2_of_runs": rate_diff(cur.a2k, cur.n, base.a2k, base.n)}


# ---------------------------------------------------------------------------------------------------- nights
def list_nights(parent: Path) -> list[Path]:
    return sorted(p for p in parent.iterdir() if p.is_dir() and DATE_RE.match(p.name))


def real_arms(night: Path) -> list[str]:
    return sorted((p.name for p in night.iterdir() if p.is_dir() and ARM_RE.match(p.name) and (p / "runs.jsonl").is_file()),
                  key=lambda a: int(ARM_RE.match(a).group(1)))


def load_arm_pair(night: Path, agent: str) -> dict:
    real_rows = read_jsonl(night / agent / "runs.jsonl")
    emu_rows = read_jsonl(night / f"{agent}-emu" / "runs.jsonl")
    r_end, r_crash = split_rows(real_rows, True)
    e_end, e_crash = split_rows(emu_rows, False)
    return {"date": night.name, "agent": agent, "generation": int(ARM_RE.match(agent).group(1)), "dir": night,
            "real_rows": real_rows, "real_end": r_end, "real_crash": r_crash, "emu_rows": emu_rows, "emu_end": e_end,
            "emu_crash": e_crash, "has_emu": (night / f"{agent}-emu" / "runs.jsonl").is_file()}


def night_agg(p: dict, arm: str) -> Agg:
    return make_agg(p[f"{arm}_end"], len(p[f"{arm}_crash"]))


# ---------------------------------------------------------------------------------------------------- per-fight tables
def fight_table_from_nodes(rows: list[dict]) -> dict[tuple[int, str], list[int]]:
    """(act, kind) -> [fights, survived] from a complete per-floor node string (the emulator arm's rows)."""
    cells: dict[tuple[int, str], list[int]] = defaultdict(lambda: [0, 0])
    kinds = {"M": "hallway", "E": "elite", "B": "boss"}
    for r in rows:
        nodes = r.get("nodes") or ""
        died_last = r.get("end") == "death" and not r.get("win")
        act = 1
        for i, c in enumerate(nodes):
            if c in kinds:
                last = i == len(nodes) - 1
                cell = cells[(act, kinds[c])]
                cell[0] += 1
                cell[1] += 0 if (last and died_last) else 1
            if c == "B":
                act += 1
    return cells


START = re.compile(r"^\[referee\] run decision 0 ")
DECISION = re.compile(r"^\[referee\] run decision (\d+) (\S+) (.*)$")
ROOM = re.compile(r"^\[INFO\] Creating NCombatRoom .*encounter=([A-Z0-9_]+)\.")
ENDED = re.compile(r"^\[referee\] run ([A-Z0-9]+) ended: (\S+) after (\d+) decisions, floor (\d+)")


def encounter_kind(name: str) -> str:
    """The game's encounter ids end in their pool: _WEAK and _NORMAL hallway, _ELITE, _BOSS; _EVENT_ENCOUNTER is an event's fight."""
    if name.endswith("_BOSS"):
        return "boss"
    if name.endswith("_ELITE"):
        return "elite"
    if name.endswith(("_WEAK", "_NORMAL")):
        return "hallway"
    if name.endswith("_EVENT_ENCOUNTER"):
        return "event"
    return "other"


def parse_logs(logs: Path) -> tuple[list[dict], Counter]:
    """One record per combat room of every run that ended in a copied game log: {seed, i, n, encounter, end, floor,
    last_screen}. A death whose last open run screen was `combat` was a death in that fight; one whose last screen was an
    event or a rest was not (the log has one `run decision N combat` per fight; the fight's own moves are the lockstep's)."""
    fights: list[dict] = []
    seen: Counter = Counter()
    for log in sorted(logs.glob("*.log")):
        cur: list[dict] = []
        last_screen = None
        for ln in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if START.match(ln):
                cur, last_screen = [], "start"
            m = DECISION.match(ln)
            if m:
                last_screen = m.group(2)
                continue
            m = ROOM.match(ln)
            if m:
                cur.append({"encounter": m.group(1)})
                continue
            m = ENDED.match(ln)
            if m:
                seed, end, floor = m.group(1), m.group(2), int(m.group(4))
                seen["runs ended in logs"] += 1
                seen[f"end {end}, last screen {last_screen}"] += 1
                for i, f in enumerate(cur):
                    fights.append({**f, "seed": seed, "i": i, "n": len(cur), "end": end, "floor": floor, "last_screen": last_screen})
                cur, last_screen = [], None
    return fights, seen


def real_fight_table(fights: list[dict]) -> tuple[dict, Counter, dict]:
    """(cells, notes, kinds): act by the bosses passed; kind by the encounter id's suffix; a run's last combat room is lost
    when the run ended by death with the combat screen open; every earlier fight was won. Event and unclassed fights are
    counted apart and left out of the table."""
    notes: Counter = Counter()
    kinds = {f["encounter"]: encounter_kind(f["encounter"]) for f in fights}
    cells: dict[tuple[int, str], list[int]] = defaultdict(lambda: [0, 0])
    by_run: dict[str, list[dict]] = defaultdict(list)
    for f in fights:
        by_run[f["seed"]].append(f)
    for fs in by_run.values():
        fs.sort(key=lambda f: f["i"])
        act = 1
        for f in fs:
            k = kinds[f["encounter"]]
            last = f["i"] == f["n"] - 1
            lost = last and f["end"] == "death" and f["last_screen"] == "combat"
            if k in ("event", "other"):
                notes[f"{k} fights (not in the table)"] += 1
                if lost:
                    notes[f"deaths in {k} fights"] += 1
                continue
            cell = cells[(act, k)]
            cell[0] += 1
            cell[1] += 0 if lost else 1
            if k == "boss":
                act += 1
    return cells, notes, kinds


def cells_json(cells: dict, min_cell: int = MIN_CELL) -> list[dict]:
    out = []
    for act in (1, 2, 3):
        for kind in ("hallway", "elite", "boss"):
            f, s = cells.get((act, kind), (0, 0))
            if f == 0:
                continue
            if f < min_cell:
                out.append({"act": act, "kind": kind, "fights": f, "survived": None, "win_rate": None, "suppressed": True})
            else:
                out.append({"act": act, "kind": kind, "fights": f, "survived": s, "win_rate": rnd(s / f, 4), "suppressed": False})
    return out


def cell_of(table: list[dict] | None, act: int, kind: str) -> dict | None:
    for c in table or []:
        if c["act"] == act and c["kind"] == kind and not c["suppressed"]:
            return c
    return None


# ---------------------------------------------------------------------------------------------------- crashes
def crash_kind(err: str) -> dict:
    """The kind of a crash row, from its error text. `exit` is the game's exit code when the game died."""
    m = re.match(r"RuntimeError: the engine refused action (\d+) in phase (\d+)", err)
    if m:
        return {"kind": "engine refused action", "action": int(m.group(1)), "phase": int(m.group(2))}
    m = re.match(r"GameDied: game exited \((\d+)\)", err)
    if m:
        code = int(m.group(1))
        return {"kind": "game exited", "exit": code, "exit_hex": hex_exit(code), "exit_name": EXIT_NAMES.get(code & 0xFFFFFFFF)}
    m = re.match(r"worker process exited (\d+) \((0x[0-9a-fA-F]+)\)", err)
    if m:
        return {"kind": "worker process exited", "exit": int(m.group(1)), "exit_hex": hex_exit(int(m.group(1)))}
    if err.startswith("worker deadline"):
        return {"kind": "worker deadline"}
    if "TimeoutError" in err:
        return {"kind": "timeout"}
    return {"kind": "other", "text": err[:80]}


def crash_rows_json(crashes: list[dict]) -> list[dict]:
    out = []
    for r in crashes:
        k = crash_kind(r.get("error") or "")
        t = r.get("t_end")
        out.append({"seed": r.get("seed"), "worker": r.get("w"), "where": r.get("where"), **k,
                    "utc": iso(datetime.fromtimestamp(t, timezone.utc)) if t else None,
                    "t_end": t, "restarts": r.get("restarts"), "run_s": r.get("s")})
    return sorted(out, key=lambda c: c["t_end"] or 0)


def hp_recorded(rows: list[dict]) -> bool:
    """Whether the rows carry an HP field at all (`boss_damage` is the share of the boss's HP removed, not the player's HP)."""
    pat = re.compile(r"(^|_)hp($|_)")
    return any(pat.search(k) for r in rows[:200] for k in r)


# ---------------------------------------------------------------------------------------------------- Windows log
def classify_event(ev: dict) -> dict | None:
    """One Application-log event -> {utc, kind, app, top_frame, id}; None when it is not a process death.
    kind: game (SlayTheSpire2), emulator (a python host with Sts2Emulator frames), python-other, other."""
    prov, eid, msg = ev.get("provider") or "", int(ev.get("id") or 0), ev.get("msg") or ""
    app = None
    if prov == ".NET Runtime" and eid in (1023, 1025, 1026):
        m = re.search(r"^Application:\s*(\S+)", msg, re.M)
        app = m.group(1) if m else ""
    elif prov == "Application Error" and eid == 1000:
        m = re.search(r"Faulting application name:\s*([^,\s]+)", msg)
        app = m.group(1) if m else ""
    if app is None:
        return None
    low = app.lower()
    frame = None
    m = re.search(r"at (Sts2Emulator[\w.`<>]*)\s*\(.*?\)\s*\+\s*(0x[0-9a-fA-F]+)", msg)
    if m:
        frame = f"{m.group(1)} + {m.group(2).lower()}"
    elif prov == "Application Error" and "Sts2Emulator" in msg:  # a native fault in the emulator's library
        m = re.search(r"Exception code:\s*(0x[0-9a-fA-F]+)", msg)
        frame = f"Sts2Emulator.dll native fault {m.group(1).lower() if m else ''}".strip()
    elif "Sts2Emulator" in msg:
        m = re.search(r"at (Sts2Emulator[\w.`<>]*)", msg)
        frame = m.group(1) if m else "Sts2Emulator"
    if "slaythespire2" in low:
        kind = "game"
        m = re.search(r"^\s+at ([\w.`<>+]+)\(", msg, re.M)  # the managed frame the game died in (a Godot finalizer, say)
        frame = frame or (m.group(1) if m else None)
    elif low.startswith("python"):
        kind = "emulator" if "Sts2Emulator" in msg else "python-other"
    else:
        kind = "other"
    return {"utc": ev.get("utc"), "id": eid, "provider": prov, "app": app, "kind": kind, "top_frame": frame,
            "endturn_25aa": bool(re.search(r"CombatEngine\.EndTurn.*\+\s*0x25aa", msg)),
            "getreadyaction": "ActionQueueSet.GetReadyAction" in msg}


def unique_deaths(deaths: list[dict]) -> list[dict]:
    """One death logs two entries: the .NET Runtime one (with the stack) and an Application Error one (the faulting module),
    a moment apart. An Application Error entry is dropped when a .NET Runtime entry of the same process is within 3 seconds;
    one standing alone (a native fault the runtime never saw) is kept."""
    runtime = [d for d in deaths if d["provider"] == ".NET Runtime"]
    out = list(runtime)
    for d in deaths:
        if d["provider"] == ".NET Runtime":
            continue
        t = parse_utc(d["utc"])
        if not any(r["app"] == d["app"] and abs((parse_utc(r["utc"]) - t).total_seconds()) <= 3.0 for r in runtime):
            out.append(d)
    return out


def powershell_events(start: datetime, end: datetime, runner=subprocess.run) -> dict:
    """Process-death events of the Application log in [start, end], read with Get-WinEvent. Returns {total, events}; raises
    RuntimeError / ValueError / OSError when the log cannot be read. `runner` is injectable for tests."""
    script = (
        "$ErrorActionPreference='SilentlyContinue'\n"
        f"$s=[DateTimeOffset]::Parse('{iso(start)}').LocalDateTime\n"
        f"$e=[DateTimeOffset]::Parse('{iso(end)}').LocalDateTime\n"
        "$all=@(Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$s; EndTime=$e})\n"
        "$sel=@($all | Where-Object { $_.ProviderName -in @('.NET Runtime','Application Error') })\n"
        "$ev=@($sel | ForEach-Object { [pscustomobject]@{ utc=$_.TimeCreated.ToUniversalTime().ToString('o'); id=$_.Id;"
        " provider=$_.ProviderName; msg=(($_.Message -split \"`n\" | Select-Object -First 16) -join \"`n\") } })\n"
        "$o=[pscustomobject]@{ total=$all.Count; events=$ev }\n"
        "ConvertTo-Json -InputObject $o -Compress -Depth 4\n"
    )
    enc = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    p = runner(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc], capture_output=True, text=True,
               timeout=180)
    if p.returncode != 0:
        raise RuntimeError(f"Get-WinEvent failed (rc {p.returncode})")
    data = json.loads(p.stdout)
    ev = data.get("events")
    if isinstance(ev, dict):  # one event comes back as an object, not a list
        ev = [ev]
    return {"total": data.get("total") or 0, "events": ev or []}


def read_winlog(source: str, start: datetime, end: datetime, runner=subprocess.run) -> dict:
    """source: 'none', 'auto' (Get-WinEvent) or a JSON file ({"events": [...]} or a list; entries with utc/id/provider/msg)."""
    if source == "none":
        return {"status": "skipped (--winlog none)"}
    try:
        if source == "auto":
            if sys.platform != "win32":
                return {"status": "not read: not Windows"}
            raw = powershell_events(start, end, runner)
        else:
            data = json.loads(Path(source).read_text(encoding="utf-8"))
            evs = data["events"] if isinstance(data, dict) else data
            inside = [e for e in evs if start <= parse_utc(e["utc"]) <= end]
            total = data.get("total") if isinstance(data, dict) else None
            raw = {"total": total if total is not None else len(inside), "events": inside}
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        return {"status": f"not read: {type(exc).__name__}"}
    deaths = unique_deaths([c for c in (classify_event(e) for e in raw["events"]) if c])
    emu = [d for d in deaths if d["kind"] == "emulator"]
    return {
        "status": "read", "window": [iso(start), iso(end)], "events_in_window": raw["total"], "process_deaths": len(deaths),
        "game_deaths": sum(1 for d in deaths if d["kind"] == "game"),
        "emulator_failfasts": len(emu), "emulator_endturn_0x25aa": sum(1 for d in emu if d["endturn_25aa"]),
        "emulator_getreadyaction": sum(1 for d in emu if d["getreadyaction"]),
        "emulator_by_top_frame": dict(Counter(d["top_frame"] or "?" for d in emu)),
        "other_deaths": sum(1 for d in deaths if d["kind"] in ("python-other", "other")),
        "deaths": [{k: d[k] for k in ("utc", "id", "app", "kind", "top_frame")} for d in sorted(deaths, key=lambda d: d["utc"])],
    }


def match_crashes_to_log(crashes: list[dict], winlog: dict) -> None:
    """Adds `log_entry` (the process-death event within CRASH_MATCH_S of the row's end, or None) to each crash row."""
    deaths = winlog.get("deaths") if winlog.get("status") == "read" else None
    for c in crashes:
        c["log_entry"] = None
        if deaths is None or not c.get("t_end"):
            continue
        t = datetime.fromtimestamp(c["t_end"], timezone.utc)
        near = [d for d in deaths if abs((parse_utc(d["utc"]) - t).total_seconds()) <= CRASH_MATCH_S]
        if near:
            d = min(near, key=lambda d: abs((parse_utc(d["utc"]) - t).total_seconds()))
            c["log_entry"] = {"utc": d["utc"], "app": d["app"], "kind": d["kind"], "top_frame": d["top_frame"]}


# ---------------------------------------------------------------------------------------------------- lab: job, runner, jobs.json
def find_job(lab: Path, date: str) -> Path | None:
    """The night's job record folder: LAB/runs/*nightly-real whose result.json is dated `date` (the last, if resumed)."""
    runs = lab / "runs"
    if not runs.is_dir():
        return None
    best = None
    for d in sorted(runs.glob("*-nightly-real")):
        res = read_json(d / "result.json")
        if res and res.get("date") == date:
            best = d
    return best


def job_figures(job: Path | None) -> dict:
    if job is None:
        return {"found": False}
    jj = read_json(job / "job.json") or {}
    res = read_json(job / "result.json") or {}
    step = (jj.get("steps") or [{}])[0]
    cmd = (step.get("cmds") or {}).get("nightly-real") or {}
    return {"found": True, "name": jj.get("name") or job.name, "tree": (jj.get("main_sha") or "")[:8] or None,
            "start_utc": step.get("started_utc") or jj.get("created_utc"), "end_utc": step.get("finished_utc"),
            "runner_secs": cmd.get("secs"), "rc": cmd.get("rc"), "lab_wall_s": res.get("wall_s"), "resumed": jj.get("resumed")}


def runner_interruptions(lab: Path, start: datetime, end: datetime) -> dict:
    """Lines of the runner log inside [start, end] where the night's step was stopped (user, pause, load, lock)."""
    log = lab / "runner.log"
    if not log.is_file():
        return {"read": False}
    stops = []
    for ln in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(\d{4}-\d\d-\d\dT[\d:]+Z) step nightly-real stopped: (.*)$", ln)
        if m and start <= parse_utc(m.group(1)) <= end:
            stops.append({"utc": m.group(1), "why": m.group(2)[:60]})
    return {"read": True, "stops": stops, "count": len(stops)}


def next_night(lab: Path, start: datetime | None) -> dict:
    jobs = read_json(lab / "jobs.json") or {}
    every = (jobs.get("nightly-real") or {}).get("every_h")
    if not every or start is None:
        return {"known": False}
    nxt = start + timedelta(hours=every)
    return {"known": True, "every_h": every, "earliest_start_utc": iso(nxt),
            "landings_safe_until_utc": iso(nxt.replace(minute=0, second=0, microsecond=0))}


# ---------------------------------------------------------------------------------------------------- lockstep, groups, machine
def reanchor_label(reason: str, corpus_text: str) -> str:
    """A re-anchor failure reason as the lane groups them. The rows clip a monster key; the longest prefix that the rows'
    other mentions of it share completes it."""
    if "no emulator id for" in reason:
        m = re.search(r"'([A-Z0-9_]+)", reason)
        key = m.group(1) if m else "?"
        if key != "?":
            toks = set(re.findall(re.escape(key) + r"[A-Z0-9_]*", corpus_text)) - {key}
            if toks:
                key = os.path.commonprefix(sorted(toks)).rstrip("_")
        return f"no emulator id for {key}"
    if reason.endswith(":to_map"):
        return "to-map"
    if ":diff:" in reason:
        return reason.split(":diff:", 1)[1]
    return reason


def lockstep_figures(summary: dict, corpus_text: str) -> dict:
    fails: Counter = Counter()
    for reason, k in (summary.get("reanchor_fail_reasons") or {}).items():
        fails[reanchor_label(reason, corpus_text)] += k
    dec = summary.get("decisions")
    dv = summary.get("diverged_decisions")
    return {"decisions": dec, "diverged": dv, "divergence_rate": summary.get("divergence_rate"),
            "divergence_pct": rnd(100.0 * dv / dec, 3) if dec and dv is not None else None,
            "reanchors": summary.get("reanchors"), "reanchor_failed": summary.get("reanchor_failed"),
            "reanchor_fail_labels": dict(fails.most_common()), "gaps": summary.get("gaps"), "resumed": summary.get("resumed"),
            "ranked_share": summary.get("ranked_share"), "first_loss_by_reason": summary.get("first_loss_by_reason"),
            "losses_by_reason": summary.get("losses_by_reason"), "decisions_per_s": summary.get("decisions_per_s")}


def hand_count_records(divs: list[dict]) -> Counter:
    """The D11C shape: a combat record whose only difference is .combat.hand, one side holding the other's whole hand plus
    cards (the game has more, or the emulator has more)."""
    c: Counter = Counter()
    for r in divs:
        if r.get("type") != "combat" or len(r.get("diff") or []) != 1 or r["diff"][0][0] != ".combat.hand":
            continue
        a, b = r["diff"][0][1], r["diff"][0][2]
        ca, cb = Counter(a), Counter(b)
        if (ca - cb) and (cb - ca):
            continue
        c["game more" if len(a) > len(b) else "emulator more" if len(b) > len(a) else "same size"] += 1
    return c


def group_figures(block: Path, decisions: int | None, top: int = 10) -> dict:
    ranked = read_json(block / "ranked.json")
    if not ranked:
        return {"present": False}
    groups = ranked["groups"] if isinstance(ranked, dict) else ranked
    summ = ranked.get("summary", {}) if isinstance(ranked, dict) else {}
    total = summ.get("total_weight") or sum(g.get("weight", 0) for g in groups)
    by = {g["id"]: g for g in groups}
    hands = hand_count_records(read_jsonl(block / "divergences.jsonl"))
    d11c = {}
    for gid, name in D11C.items():
        g = by.get(gid)
        d11c[name] = {"id": gid, "rank": g.get("rank") if g else None, "weight": g["weight"] if g else 0,
                      "decisions_affected": g.get("decisions_affected") if g else 0, "records": g.get("divergences") if g else 0}
    both = sum(v["weight"] for v in d11c.values())
    hand = {"game_more": hands["game more"], "emulator_more": hands["emulator more"], "same_size": hands["same size"],
            "per_100k_decisions": rnd(100000.0 * (hands["game more"] + hands["emulator more"]) / decisions, 2) if decisions else None}
    fam = read_json(block / "by_family.json") or {}
    return {
        "present": True, "groups": len(groups), "total_weight": total, "arch_share": summ.get("arch_share"),
        "state_divergences": summ.get("state_divergences"), "mapping_gaps": summ.get("mapping_gaps"),
        "outcome_confirmed": summ.get("outcome_confirmed"), "outcome_proxy": summ.get("outcome_proxy"),
        "top_groups": [{"rank": g.get("rank"), "id": g["id"], "type": (g.get("display") or {}).get("type"),
                        "kinds": (g.get("display") or {}).get("kinds"), "entities": (g.get("display") or {}).get("entities"),
                        "tag": g.get("tag"), "class": g.get("class"), "weight": g["weight"],
                        "decisions_affected": g.get("decisions_affected"), "first_floor": g.get("first_floor"),
                        "outcome_changing_confirmed": g.get("outcome_changing_confirmed")} for g in groups[:top]],
        "top_families": [{k: f.get(k) for k in ("family", "name", "coarse", "weight", "share", "groups")}
                         for f in (fam.get("families") or [])[:5]],
        "family_verdict": (fam.get("summary") or {}).get("verdict"),
        "unassigned_share": (fam.get("summary") or {}).get("unassigned_share"),
        "d11c": d11c, "d11c_together_weight": round(both, 1), "d11c_share": rnd(both / total, 4) if total else None,
        "hand_count": hand,
    }


def machine_figures(path: Path) -> dict:
    rows = read_jsonl(path)
    if not rows:
        return {"present": False}
    cpu = [r["cpu_pct"] for r in rows if "cpu_pct" in r]
    lat = sorted(r["disk_latency_ms"] for r in rows if "disk_latency_ms" in r)
    return {"present": True, "samples": len(rows), "first_utc": rows[0].get("utc"), "last_utc": rows[-1].get("utc"),
            "cpu_pct_mean": rnd(statistics.fmean(cpu), 1) if cpu else None, "cpu_pct_max": max(cpu) if cpu else None,
            "avail_mb_min": min((r["avail_mb"] for r in rows if "avail_mb" in r), default=None),
            "mem_load_pct_max": max((r["mem_load_pct"] for r in rows if "mem_load_pct" in r), default=None),
            "disk_latency_ms_p95": lat[int(0.95 * (len(lat) - 1))] if lat else None,
            "games_max": max((r["games"] for r in rows if "games" in r), default=None)}


# ---------------------------------------------------------------------------------------------------- the report
def paired_figures(cur: dict) -> dict:
    """Real against emulator on the same seeds: floor gap, the Act 1 boss 2x2, and the same with crash rows as floor 0."""
    er = {r["seed"]: r for r in cur["emu_end"]}
    pairs = [(r, er[r["seed"]]) for r in cur["real_end"] if r["seed"] in er]
    out: dict = {"ended": {"seeds": len(pairs)}}
    if pairs:
        diff = [a["floor"] - b["floor"] for a, b in pairs]
        kills = Counter((boss_hit(a, 0)[1], boss_hit(b, 0)[1]) for a, b in pairs)
        agree = kills[(True, True)] + kills[(False, False)]
        out["ended"].update({"floor_real_minus_emu_mean": rnd(statistics.fmean(diff), 4), "floor_sd": rnd(statistics.pstdev(diff), 4),
                             "act1_both": kills[(True, True)], "act1_real_only": kills[(True, False)],
                             "act1_emu_only": kills[(False, True)], "act1_neither": kills[(False, False)],
                             "act1_agreement": rnd(agree / len(pairs), 4)})
    rfl = {r["seed"]: r["floor"] for r in cur["real_end"]}
    rfl.update({r["seed"]: 0 for r in cur["real_crash"]})
    efl = {r["seed"]: r["floor"] for r in cur["emu_end"]}
    efl.update({r["seed"]: 0 for r in cur["emu_crash"]})
    both = sorted(set(rfl) & set(efl))
    out["counted"] = {"seeds": len(both)}
    if both:
        d = [rfl[s] - efl[s] for s in both]
        out["counted"].update({"floor_real_minus_emu_mean": rnd(statistics.fmean(d), 4), "floor_sd": rnd(statistics.pstdev(d), 4),
                               "floor_emu_minus_real_mean": rnd(-statistics.fmean(d), 4)})
    return out


def comparison_entry(entries: list[dict], g_real: Agg, g_emu: Agg) -> dict | None:
    if not entries:
        return None

    def pooled(arm: str) -> Agg:
        out = Agg()
        for h in entries:
            if arm == "emu" and not h["has_emu"]:
                continue
            out = out + night_agg(h, arm)
        return out

    has_emu = any(h["has_emu"] for h in entries)
    return {"generation": entries[0]["generation"], "nights": sorted({h["date"] for h in entries}),
            "real": compare_blocks(g_real, pooled("real")), "emu": compare_blocks(g_emu, pooled("emu")) if has_emu else None}


def build_report(night: Path, agent: str | None, lab: Path, logs: Path | None, winlog_source: str, usage: str | None,
                 now: datetime, runner=subprocess.run) -> dict:
    agents = real_arms(night)
    if agent is None:
        if len(agents) != 1:
            raise SystemExit(f"{night.name}: real arms {agents}: name one with --agent")
        agent = agents[0]
    if not (night / agent / "summary.json").is_file():
        raise SystemExit(f"{night.name}/{agent}: no summary.json yet; the block has not closed, so there is no report to make")
    cur = load_arm_pair(night, agent)
    date = night.name
    summ = read_json(night / agent / "summary.json") or {}
    emu_summ = read_json(night / f"{agent}-emu" / "summary.json") or {}
    result = read_json(night / agent / "result.json") or {}
    compare = read_json(night / agent / "compare.json") or {}
    nightly = summ.get("nightly") or {}
    wall = (read_json(night / agent / "wall.json") or {}).get("wall_s")

    real = arm_figures(cur["real_end"], cur["real_crash"], True)
    emu = arm_figures(cur["emu_end"], cur["emu_crash"], False)
    g_real, g_emu = night_agg(cur, "real"), night_agg(cur, "emu")

    # history: every earlier night's arms, oldest first
    earlier = []
    for nd in list_nights(night.parent):
        if nd.name < date:
            for ag in real_arms(nd):
                earlier.append(load_arm_pair(nd, ag))
    prev_night = [h for h in earlier if h["date"] == max(e["date"] for e in earlier)] if earlier else []
    same_gen = [h for h in earlier if h["generation"] == cur["generation"]]
    older = sorted({h["generation"] for h in earlier if h["generation"] < cur["generation"]})
    prev_gen = [h for h in earlier if older and h["generation"] == older[-1]]
    comparison = {"previous_night": comparison_entry(prev_night, g_real, g_emu),
                  "same_generation_earlier": comparison_entry(same_gen, g_real, g_emu),
                  "previous_generation_pooled": comparison_entry(prev_gen, g_real, g_emu)}

    # the job and the night's window
    jf = job_figures(find_job(lab, date))
    start = parse_utc(jf["start_utc"]) if jf.get("start_utc") else None
    end = parse_utc(jf["end_utc"]) if jf.get("end_utc") else None
    if start is None or end is None:  # no job record: the rows' own times
        ts = [r["t_end"] for r in cur["real_rows"] if r.get("t_end")]
        if ts:
            start = start or datetime.fromtimestamp(min(ts), timezone.utc)
            end = end or datetime.fromtimestamp(max(ts), timezone.utc)
    interruptions = runner_interruptions(lab, start, end) if start and end else {"read": False}

    # the Windows log: this night's window, and the previous night's for the "two nights" line
    if start and end:
        winlog = read_winlog(winlog_source, start - WIN_PAD_BEFORE, end + WIN_PAD_AFTER, runner)
    else:
        winlog = {"status": "not read: the night's window is unknown (no job record, no row times)"}
    prev_winlog = None
    if prev_night and winlog.get("status") == "read":
        pj = job_figures(find_job(lab, prev_night[0]["date"]))
        if pj.get("start_utc") and pj.get("end_utc"):
            prev_winlog = read_winlog(winlog_source, parse_utc(pj["start_utc"]) - WIN_PAD_BEFORE,
                                      parse_utc(pj["end_utc"]) + WIN_PAD_AFTER, runner)
            prev_winlog["date"] = prev_night[0]["date"]
            prev_winlog["played_rows"] = len(prev_night[0]["real_rows"]) + len(prev_night[0]["emu_rows"])

    # crash rows, with the log entry each one matches, and each kind's tally over the earlier nights
    crashes = crash_rows_json(cur["real_crash"])
    match_crashes_to_log(crashes, winlog)
    kinds = Counter(c["kind"] for c in crashes)
    cumulative = {}
    for kind in kinds:
        first = next((h["date"] for h in earlier if any(crash_kind(r.get("error") or "")["kind"] == kind for r in h["real_crash"])), date)
        span = [h for h in earlier if h["date"] >= first] + [cur]
        by_night = {h["date"]: sum(1 for r in h["real_crash"] if crash_kind(r.get("error") or "")["kind"] == kind) for h in span}
        cumulative[kind] = {"since": first, "count": sum(by_night.values()), "real_rows": sum(len(h["real_rows"]) for h in span),
                            "by_night": by_night}
    unfinished = [{"seed": r["seed"], "worker": r.get("w"), "floor": r["floor"], "streak": r.get("streak")}
                  for r in cur["real_end"] if r.get("end") == "fight_unfinished"]
    unfinished_hist = {h["date"]: {"fight_unfinished": sum(1 for r in h["real_end"] if r.get("end") == "fight_unfinished"),
                                   "ended_rows": len(h["real_end"])} for h in earlier}

    # seeds with rows
    seeds_real = {r["seed"] for r in cur["real_rows"] if r.get("seed")}
    seeds_emu = {r["seed"] for r in cur["emu_rows"] if r.get("seed")}
    planned = nightly.get("runs_planned") or result.get("runs") or summ.get("runs")

    # per-fight tables
    fights = {"emu": cells_json(fight_table_from_nodes(cur["emu_end"])), "real": None, "real_notes": None}
    if logs is not None and logs.is_dir() and any(logs.glob("*.log")):
        fl, seen = parse_logs(logs)
        cells, notes, kmap = real_fight_table(fl)
        fights["real"] = cells_json(cells)
        fights["real_notes"] = {"runs_ended_in_logs": seen["runs ended in logs"], "fights": len(fl), "notes": dict(notes),
                                "run_ends_by_last_screen": {k[4:]: v for k, v in sorted(seen.items()) if k.startswith("end ")},
                                "encounter_kinds": dict(Counter(kmap.values())),
                                "event_or_other": sorted(e for e, k in kmap.items() if k in ("event", "other"))}

    history = []
    for h in earlier:
        history.append({"date": h["date"], "agent": h["agent"], "generation": h["generation"], "rows_real": len(h["real_rows"]),
                        "real": agg_block(night_agg(h, "real")), "emu": agg_block(night_agg(h, "emu")) if h["has_emu"] else None})

    # re-anchor failures of tonight's "no emulator id for <monster>" kinds on each earlier night (keys as the rows clip them)
    keys = {m.group(1) for k in (summ.get("reanchor_fail_reasons") or {}) if "no emulator id for" in k
            for m in [re.search(r"'([A-Z0-9_]+)", k)] if m}
    noid = {}
    for h in earlier:
        s = read_json(h["dir"] / h["agent"] / "summary.json") or {}
        noid[h["date"]] = sum(v for k, v in (s.get("reanchor_fail_reasons") or {}).items() if any(f"'{key}" in k for key in keys))
    corpus_path = night / agent / "runs.jsonl"
    corpus_text = corpus_path.read_text(encoding="utf-8", errors="replace") if corpus_path.is_file() else ""
    groups = group_figures(night / agent, summ.get("decisions") or result.get("decisions"))
    group_hist = []
    with_ranked = [h for h in earlier if (h["dir"] / h["agent"] / "ranked.json").is_file()]
    shown = with_ranked[:1] + [h for h in prev_night if h not in with_ranked[:1] and h in with_ranked]
    for h in shown:
        dec = (read_json(h["dir"] / h["agent"] / "result.json") or {}).get("decisions")
        gf = group_figures(h["dir"] / h["agent"], dec)
        group_hist.append({"date": h["date"], "agent": h["agent"], "decisions": dec,
                           **{k: gf.get(k) for k in ("total_weight", "d11c", "hand_count")}})
    hand_trend = {}
    for h in earlier:
        dec = (read_json(h["dir"] / h["agent"] / "result.json") or {}).get("decisions")
        hc = hand_count_records(read_jsonl(h["dir"] / h["agent"] / "divergences.jsonl"))
        if dec and (h["dir"] / h["agent"] / "divergences.jsonl").is_file():
            hand_trend[h["date"]] = rnd(100000.0 * (hc["game more"] + hc["emulator more"]) / dec, 1)

    wr = summ.get("wall_s") or wall
    report = {
        "schema": 1, "generated_utc": iso(now),
        "night": {"folder": f"nightly/{date}", "date": date, "agent": agent, "generation": cur["generation"],
                  "role": nightly.get("role"), "seed_block": nightly.get("seed_block"), "engine": summ.get("engine"),
                  "character": summ.get("character"), "job": jf, "usage": usage,
                  "start_utc": iso(start) if start else None, "end_utc": iso(end) if end else None,
                  "wall_s": {"job_runner": jf.get("runner_secs"), "real_arm": wr, "emulator_arm": emu_summ.get("wall_s")},
                  "wall_min": {"real_arm": rnd(wr / 60, 1) if wr else None,
                               "emulator_arm": rnd(emu_summ["wall_s"] / 60, 1) if emu_summ.get("wall_s") else None},
                  "resumed_rows": summ.get("resumed_rows"), "wall_s_before": summ.get("wall_s_before"),
                  "interruptions": interruptions, "next_night": next_night(lab, start)},
        "runs": {"planned": planned, "real_rows": real["rows"], "real_ended": real["ended"], "real_crash_rows": real["crashes"],
                 "emu_rows": emu["rows"], "emu_ended": emu["ended"], "emu_crash_rows": emu["crashes"],
                 "seeds_with_rows_real": len(seeds_real), "seeds_with_rows_emu": len(seeds_emu),
                 "seeds_with_rows_both": len(seeds_real & seeds_emu)},
        "real": real, "emu": emu, "human_r1": R1, "comparison": comparison, "paired": paired_figures(cur), "fights": fights,
        "crashes": {"rows": crashes, "by_kind": dict(kinds), "cumulative": cumulative},
        "fight_unfinished": {"this_night": unfinished, "earlier_nights": unfinished_hist},
        "lockstep": {**lockstep_figures(summ, corpus_text), "no_emulator_id_failures_by_earlier_night": noid},
        "pool": {"real": {k: summ.get(k) for k in ("died_respawns", "deadline_respawns", "unplayed_after_cap", "wrapup_terminated")}
                 | {"network_connections": len(summ.get("network_connections") or []), "errors_listed": len(summ.get("errors") or [])},
                 "emulator_arm": emu_summ.get("pool")},
        "winlog": winlog, "winlog_previous_night": prev_winlog,
        "groups": groups, "groups_history": group_hist, "hand_count_per_100k_by_night": hand_trend,
        "machine": machine_figures(night / agent / "machine.jsonl"), "history": history,
        "hp_recorded": hp_recorded(cur["real_rows"]) or hp_recorded(cur["emu_rows"]),
    }
    report["cross_checks"] = cross_checks(report, summ, emu_summ, result, compare, nightly)
    report["not_computed"] = not_computed(report, usage)
    pn = prev_night[0] if prev_night else None
    report["tables"] = {"prev_night_date": pn["date"] if pn else None,
                        "prev_real": arm_figures(pn["real_end"], pn["real_crash"], True) if pn else None,
                        "prev_emu": arm_figures(pn["emu_end"], pn["emu_crash"], False) if pn and pn["has_emu"] else None,
                        "prev_emu_cells": cells_json(fight_table_from_nodes(pn["emu_end"])) if pn and pn["has_emu"] else None}
    return report


def cross_checks(rep: dict, summ: dict, emu_summ: dict, result: dict, compare: dict, nightly: dict) -> list[dict]:
    """The rows against the arms' own summary files: what the file holds, what the rows give, whether they agree."""
    out = []

    def chk(name: str, file_value, rows_value, tol: float = 0.0):
        if file_value is None:
            out.append({"check": name, "file": None, "rows": rows_value, "ok": None})
            return
        ok = rows_value is not None and abs(float(file_value) - float(rows_value)) <= tol
        out.append({"check": name, "file": file_value, "rows": rows_value, "ok": bool(ok)})

    real, emu = rep["real"], rep["emu"]
    chk("real ended runs = summary.runs", summ.get("runs"), real["ended"])
    chk("real crash rows = summary.crashes", summ.get("crashes"), real["crashes"])
    chk("real mean floor (ended) = summary.mean_floor", summ.get("mean_floor"), real["mean_floor"], 0.006)
    chk("real mean floor (counted) = summary.nightly.mean_floor", nightly.get("mean_floor"), real["mean_floor_counted"], 0.0006)
    chk("real decisions = result.decisions", result.get("decisions"), real["decisions"])
    chk("real diverged = summary.diverged_decisions", summ.get("diverged_decisions"), real.get("diverged"))
    chk("real re-anchors = summary.reanchors", summ.get("reanchors"), real.get("reanchors"))
    chk("real re-anchors failed = summary.reanchor_failed", summ.get("reanchor_failed"), real.get("reanchor_failed"))
    rf = (summ.get("run_fields") or {}).get("boss_act1") or {}
    chk("real Act 1 boss reached = run_fields.boss_act1.reached", rf.get("reached"), real["act1_reached"])
    chk("real Act 1 boss killed = run_fields.boss_act1.won", rf.get("won"), real["act1_killed"])
    chk("real wins = summary.wins", summ.get("wins"), real["wins"])
    chk("emulator rows = emulator summary.runs", emu_summ.get("runs"), emu["rows"])
    chk("emulator mean floor = emulator summary.floor.mean", (emu_summ.get("floor") or {}).get("mean"), emu["mean_floor"], 0.0006)
    chk("emulator decisions = emulator summary.decisions", emu_summ.get("decisions"), emu["decisions"])
    ef = (emu_summ.get("run_fields") or {}).get("boss_act1") or {}
    chk("emulator Act 1 boss killed = run_fields.boss_act1.won", ef.get("won"), emu["act1_killed"])
    gap = compare.get("floor_gap") or {}
    if gap:
        counted = (rep["paired"].get("counted") or {}).get("floor_emu_minus_real_mean")
        chk("paired floor gap (emulator minus real, crash = 0) = compare.floor_gap.mean", gap.get("mean"), counted, 0.0006)
    return out


def not_computed(rep: dict, usage: str | None) -> list[dict]:
    items = []
    if not usage:
        items.append({"figure": "the usage readout", "source": "the orchestrator's readout at the time; pass --usage"})
    items += [
        {"figure": "the promotion test's floor gain and the statement that the night agrees with it",
         "source": "the promotion run's own report (the score-real job of the promotion day), not in the night folder; the lane quoted it"},
        {"figure": "which fixes the tree holds (pool fix, EndTurn fix)", "source": "git history of the fork; this report gives the tree sha only"},
        {"figure": "the ordinal of the D11F2 proof night and the statements of open work", "source": "the lane's own bookkeeping"},
    ]
    if not rep["hp_recorded"]:
        items.append({"figure": "HP entering a boss, HP lost per fight",
                      "source": "recorded nowhere: no HP field in the rows (boss_damage is the share of the boss's HP removed)"})
    if rep["fights"]["real"] is None:
        items.append({"figure": "per-fight survival of the real arm", "source": "needs the copy of the workers' game logs made while the "
                      "night ran (the block deletes them at its end); none found"})
    if rep["winlog"].get("status") != "read":
        items.append({"figure": "the application-log fail-fast count and the game-side exit entries", "source": rep["winlog"].get("status")})
    if not rep["night"]["job"].get("found"):
        items.append({"figure": "tree sha, start and end, interruptions", "source": "no job record under LAB/runs for this date"})
    return items


# ---------------------------------------------------------------------------------------------------- text output
def table_md(head: list[str], rows: list[list[str]]) -> list[str]:
    def line(cells: list[str]) -> str:  # an empty cell is a single space between pipes, as the lane writes it
        return "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"

    return [line(head), "|" + "---|" * len(head)] + [line(r) for r in rows]


def headline_row(label: str, a: dict) -> list[str]:
    n = a["ended"]
    med = a["median_floor"]
    return [label, str(n), num(a["mean_floor"]), "n/a" if med is None else f"{med:.0f}", f"{pct(a['act1_killed'], n)} ({a['act1_killed']})",
            f"{pct(a['act2_killed'], n)} ({a['act2_killed']})", f"{pct(a['wins'], n)} ({a['wins']})", str(a["crashes"]),
            str(a["chest_stop"])]


def boss_row(label: str, a: dict) -> list[str]:
    n = a["ended"]
    if not a["act1_reached"]:
        return [label, str(n), "0", "n/a", "n/a", "n/a"]
    return [label, str(n), f"{a['act1_reached']} ({pct(a['act1_reached'], n)} of runs)",
            f"{a['act1_killed']} ({pct(a['act1_killed'], a['act1_reached'])} of those)",
            f"{a['act1_picks_mean']:.1f} / {a['act1_picks_median']:.0f}", f"{a['deck_proxy']:.1f}"]


def cells_md(table: list[dict]) -> list[str]:
    rows = [[str(c["act"]), c["kind"], str(c["fights"]), "suppressed" if c["suppressed"] else str(c["survived"]),
             "suppressed" if c["suppressed"] else pct(c["survived"], c["fights"])] for c in table]
    return table_md(["act", "kind", "fights", "survived", "win rate"], rows)


def tables_md(rep: dict) -> list[str]:
    nt, agent = rep["night"], rep["night"]["agent"]
    date, tb = nt["date"], rep["tables"]
    prev, pr, pe = tb["prev_night_date"], tb["prev_real"], tb["prev_emu"]
    L = [f"**Night {date}/{agent}: run numbers**"]
    rows = [headline_row(f"real {date}", rep["real"]), headline_row(f"emu {date}", rep["emu"])]
    if pr:
        rows.append(headline_row(f"real {prev}", pr))
    if pe:
        rows.append(headline_row(f"emu {prev}", pe))
    rows.append(["human R1", "", f"{R1['floor']:.2f}", "", f"{R1['act1'] * 100:.1f}%", f"{R1['act2'] * 100:.1f}%", f"{R1['wins'] * 100:.1f}%", "", ""])
    L += table_md(["arm", "runs", "mean floor", "median", "Act 1 boss kill (of runs)", "Act 2 boss kill (of runs)", "wins", "crashes",
                   "chest-stops"], rows)
    r, d = rep["real"], rep["paired"]["ended"]
    L += ["", f"real arm: decisions {r['decisions']}, diverged {r['diverged']} ({pct(r['diverged'], r['decisions'])}), re-anchors "
          f"{r['reanchors']} (failed {r['reanchor_failed']}); chest-stop = the driver's empty-chest end, kept apart from deaths."]
    if d.get("floor_real_minus_emu_mean") is not None:
        L.append(f"paired seeds {d['seeds']}: floor real-emu mean {d['floor_real_minus_emu_mean']:+.2f} (sd {d['floor_sd']:.2f}); "
                 f"Act 1 boss kill (real, emu): both {d['act1_both']}, real only {d['act1_real_only']}, emu only {d['act1_emu_only']}, "
                 f"neither {d['act1_neither']}")
    L += ["", "**Act 1 boss: of the runs that reach it**"]
    rows = [boss_row(f"real {date}", rep["real"]), boss_row(f"emu {date}", rep["emu"])]
    if pr:
        rows.append(boss_row(f"real {prev}", pr))
    if pe:
        rows.append(boss_row(f"emu {prev}", pe))
    L += table_md(["arm", "runs", "reached", "killed", "card picks before it (mean / median)", "deck proxy (11 + picks)"], rows)
    L.append("HP entering the boss: " + ("not in the night's records (rows keep seeds and outcomes; the game logs carry no HP)."
                                         if not rep["hp_recorded"] else "an HP field exists in the rows (not used here).")
             + " The deck proxy counts card rewards taken on floors 1-16 over the starter deck (10 cards + Ascender's Bane); removals, "
             "transforms and shop or event cards are not recorded, so it is an estimate, not a measurement.")
    L += ["", "**Per-fight survival, emulator arm (from the rows' per-floor node string; cells under 20 fights suppressed)**"]
    L += cells_md(rep["fights"]["emu"])
    if tb["prev_emu_cells"]:
        L += ["", f"emulator arm {prev}, same table:"] + cells_md(tb["prev_emu_cells"])
    L += ["", "**Per-fight survival, real arm (from the workers' game logs copied during the night)**"]
    if rep["fights"]["real"] is not None:
        nt_ = rep["fights"]["real_notes"]
        L.append(f"runs ended in the copied logs: {nt_['runs_ended_in_logs']} (rows: {rep['real']['ended']}); fights {nt_['fights']}; "
                 + "; ".join(f"{k} {v}" for k, v in nt_["notes"].items()))
        L.append("run ends by last open screen: " + "; ".join(f"{k} {v}" for k, v in nt_["run_ends_by_last_screen"].items()))
        L += cells_md(rep["fights"]["real"])
        L.append(f"encounter names by kind: {nt_['encounter_kinds']}; event or other: {nt_['event_or_other']}")
    else:
        L.append("no copied logs: the real arm's per-fight table needs them (nightly_real.py deletes the scratch at the block's end).")
    L.append("HP lost per fight: " + ("not recorded anywhere in the night (neither the rows nor the game logs carry HP), so the table "
                                      "has no HP columns." if not rep["hp_recorded"] else "an HP field exists (not used here)."))
    if rep["groups"].get("present"):
        L += ["", "**D11C groups (hand differs by one basic card): the D11F2 proof**"]
        rows = []
        now_row = {"date": date, "agent": agent, "decisions": rep["lockstep"]["decisions"], "total_weight": rep["groups"]["total_weight"],
                   "d11c": rep["groups"]["d11c"], "hand_count": rep["groups"]["hand_count"]}
        for h in rep["groups_history"] + [now_row]:
            hc = h["hand_count"] or {}
            for name, g in (h["d11c"] or {}).items():
                absent = g["rank"] is None
                rows.append([h["date"], f"{name} {g['id']}", "absent" if absent else str(g["rank"]), "0" if absent else f"{g['weight']:.1f}",
                             str(g["decisions_affected"] or 0), str(g["records"] or 0), f"{(h['total_weight'] or 0):.0f}",
                             str(h["decisions"]), f"{hc.get('game_more', 0)}+{hc.get('emulator_more', 0)}"])
        L += table_md(["night", "group", "rank", "weight", "decisions affected", "records", "total weight", "decisions",
                       "hand-count records (ref more + emu more)"], rows)
    return L


def handoff_line(rep: dict) -> str:
    nt, rl, em, lk, cmpn = rep["night"], rep["real"], rep["emu"], rep["lockstep"], rep["comparison"]
    job, gen, rn = nt["job"], nt["generation"], rep["runs"]
    P: list[str] = [f"- {rep['generated_utc'][:16]}Z morning_report.py (a script draft of the lane W5 MORNING REPORT), night "
                    f"`{job.get('name', '?')}` (folder `{nt['folder']}`; " + (f"tree {job['tree']}; " if job.get("tree") else "")
                    + f"generation {gen}, {n_(rn['planned'])} seeds planned" + (f"; usage {nt['usage']}" if nt.get("usage") else "") + ")."]
    if nt["start_utc"] and nt["end_utc"]:
        wm, itr = nt["wall_min"], nt["interruptions"]
        stops = ("no interruption" if itr.get("count") == 0 else f"{itr['count']} stop(s) of the step in the runner log"
                 if itr.get("read") else "interruptions unknown (no runner log)")
        P.append(f"Ran {hhmm(parse_utc(nt['start_utc']))}Z to {hhmm(parse_utc(nt['end_utc']))}Z (emulator arm "
                 f"{'n/a' if wm['emulator_arm'] is None else round(wm['emulator_arm'])} min, real arm "
                 f"{'n/a' if wm['real_arm'] is None else round(wm['real_arm'])} min, {stops}).")
    P.append(f"**Generation {gen}, real arm, {n_(rl['ended'])} ended runs (all but {rl['crashes']} crash rows):** mean floor "
             f"{num(rl['mean_floor'])} (counted, crashes as floor 0: {num(rl['mean_floor_counted'], 3)}), Act 1 boss kill "
             f"{pct(rl['act1_killed'], rl['ended'])} ({n_(rl['act1_killed'])}), Act 2 boss kill {pct(rl['act2_killed'], rl['ended'])} "
             f"({rl['act2_killed']}), {rl['wins']} wins; emulator arm, {n_(em['ended'])} runs: {num(em['mean_floor'])}, "
             f"{pct(em['act1_killed'], em['ended'])} ({n_(em['act1_killed'])}), {pct(em['act2_killed'], em['ended'])} "
             f"({em['act2_killed']}), {em['wins']} wins.")
    for label in ("previous_generation_pooled", "same_generation_earlier"):
        c = cmpn.get(label)
        if not c:
            continue
        b = c["real"]["base"]
        be = c["emu"]["base"] if c["emu"] else None
        who = f"Generation {c['generation']}" if label == "previous_generation_pooled" else f"Generation {gen}, its earlier nights,"
        txt = (f"{who} pooled over its {len(c['nights'])} real-arm nights ({n_(b['runs'])} runs; seeds differ by night, so this is not a "
               f"paired test): floor {num(b['mean_floor'])}, Act 1 boss kill {pct(b['a1_killed'], b['runs'])} ({n_(b['a1_killed'])}), "
               f"Act 2 boss kill {pct(b['a2_killed'], b['runs'])} ({b['a2_killed']})")
        if be and be["runs"]:
            txt += (f"; on its emulator arm ({n_(be['runs'])} runs) {num(be['mean_floor'])}, {pct(be['a1_killed'], be['runs'])} "
                    f"({n_(be['a1_killed'])}), {pct(be['a2_killed'], be['runs'])} ({be['a2_killed']})")
        P.append(txt + ".")
        r, e = c["real"], c["emu"]
        s = (f"**Real arm against it: {sgn(r['floor_ended']['diff'])} floors (SE {num(r['floor_ended']['se'])}, {num(r['floor_ended']['z'], 1)} SE), "
             f"Act 1 boss kill {sgn(r['act1_of_runs']['diff_pts'], 1)} points (SE {num(r['act1_of_runs']['se_pts'], 1)}, "
             f"{num(r['act1_of_runs']['z'], 1)} SE)")
        if e and e["floor_ended"]["diff"] is not None:
            s += (f"; emulator arm: {sgn(e['floor_ended']['diff'])} floors (SE {num(e['floor_ended']['se'])}), "
                  f"{sgn(e['act1_of_runs']['diff_pts'], 1)} points ({num(e['act1_of_runs']['z'], 1)} SE)")
        P.append(s + ".**")
    once = [f"{lbl}: {pct(cmpn[k]['real']['base']['a1_killed'], cmpn[k]['real']['base']['a1_reached'])}"
            for k, lbl in (("previous_generation_pooled", f"generation {(cmpn.get('previous_generation_pooled') or {}).get('generation')} pooled"),
                           ("same_generation_earlier", "its earlier nights")) if cmpn.get(k)]
    P.append(f"Of the runs that reach the Act 1 boss ({n_(rl['act1_reached'])} of {n_(rl['ended'])}, {pct(rl['act1_reached'], rl['ended'])}), "
             f"generation {gen} kills it in {pct(rl['act1_killed'], rl['act1_reached'])} ("
             + "".join(f"{o}; " for o in once) + f"the emulator arm tonight {pct(em['act1_killed'], em['act1_reached'])}), entering with "
             f"{num(rl['act1_picks_mean'], 1)} card picks on floors 1-16 (deck proxy {num(rl['deck_proxy'], 1)}; HP entering it is recorded "
             f"{'nowhere' if not rep['hp_recorded'] else 'in the rows'}).")
    pn = cmpn.get("previous_night")
    if pn and pn["generation"] == gen:
        r = pn["real"]
        P.append(f"Against the previous night ({pn['nights'][0]}, {n_(r['base']['runs'])} runs): floor {sgn(r['floor_ended']['diff'])} "
                 f"(SE {num(r['floor_ended']['se'])}), Act 1 boss kill {sgn(r['act1_of_runs']['diff_pts'], 1)} points "
                 f"(SE {num(r['act1_of_runs']['se_pts'], 1)}).")
    P.append(f"At {n_(rl['ended'])} runs the margin on an Act 1 rate is {num(margin95_pts(rl['ended']), 1)} points either way (95%).")
    d = rep["paired"]
    pe = d["ended"]
    if pe.get("floor_real_minus_emu_mean") is not None:
        s = (f"Paired inside the night on {n_(pe['seeds'])} seeds: floor real minus emu {sgn(pe['floor_real_minus_emu_mean'])} (sd "
             f"{num(pe['floor_sd'])}); Act 1 boss kill both {pe['act1_both']}, real only {pe['act1_real_only']}, emu only "
             f"{pe['act1_emu_only']}, neither {pe['act1_neither']} (agreement {100 * pe['act1_agreement']:.1f}%).")
        if d.get("counted", {}).get("seeds"):
            s += (f" With crash rows as floor 0 on {n_(d['counted']['seeds'])} seeds the gap, emulator minus real, is "
                  f"{sgn(d['counted']['floor_emu_minus_real_mean'], 3)} (compare.json's floor_gap).")
        P.append(s)
    fr, fe = rep["fights"]["real"], rep["fights"]["emu"]
    a2r, a2e = cell_of(fr, 2, "boss"), cell_of(fe, 2, "boss")
    bits = []
    if a2r and a2e:
        bits.append(f"Act 2 boss: real {a2r['fights']} fights, {a2r['survived']} survived ({pct(a2r['survived'], a2r['fights'])}), emulator "
                    f"{a2e['fights']} / {a2e['survived']} ({pct(a2e['survived'], a2e['fights'])})")
    elif a2e:
        bits.append(f"Act 2 boss (emulator arm, from nodes): {a2e['fights']} fights, {a2e['survived']} survived ({pct(a2e['survived'], a2e['fights'])})")
    a3h, a3e = cell_of(fr, 3, "hallway"), cell_of(fr, 3, "elite")
    if a3h and a3e:
        bits.append(f"Act 3 is reached often enough to show: real hallway {pct(a3h['survived'], a3h['fights'])} of {a3h['fights']}, "
                    f"elite {pct(a3e['survived'], a3e['fights'])} of {a3e['fights']}")
    if bits:
        P.append("; ".join(bits) + ".")
    pool, wl = rep["pool"]["real"], rep["winlog"]
    cnt = ", ".join(f"`{k}` {pool.get(k)}" for k in ("died_respawns", "deadline_respawns", "unplayed_after_cap", "wrapup_terminated"))
    fail = (f"**Pool failure counters:** {n_(rn['seeds_with_rows_both'])} of {n_(rn['planned'])} seeds have rows in both arms; {cnt}; "
            f"{pool['network_connections']} network connections")
    ea = rep["pool"]["emulator_arm"]
    if ea:
        fail += "; emulator-arm pool " + ", ".join(f"{k} {ea.get(k)}" for k in ("died", "timed_out", "raised", "lost"))
    P.append(fail + ".")
    if wl.get("status") == "read":
        w0, w1 = parse_utc(wl["window"][0]), parse_utc(wl["window"][1])
        pw = rep["winlog_previous_night"]
        two = ""
        if pw and pw.get("status") == "read":
            played = rn["real_rows"] + rn["emu_rows"] + pw["played_rows"]
            two = (f"; the window of {pw['date']} holds {pw['emulator_failfasts']} ({pw['emulator_endturn_0x25aa']} at `EndTurn + 0x25aa`, "
                   f"{pw['emulator_getreadyaction']} at `GetReadyAction`), so {n_(played)} played seeds (both arms) on the two nights "
                   f"with {wl['emulator_failfasts'] + pw['emulator_failfasts']} emulator fail-fasts")
        P.append(f"The Windows application log for {hhmm(w0)}Z to {hhmm(w1)}Z holds **{wl['emulator_failfasts']} emulator fail-fast** "
                 f"({wl['emulator_endturn_0x25aa']} at `EndTurn + 0x25aa`, {wl['emulator_getreadyaction']} at `GetReadyAction`; "
                 f"deaths of the game process {wl['game_deaths']}, of other processes {wl['other_deaths']}){two}.")
    else:
        P.append(f"Windows application log: {wl.get('status')}.")
    cr = rep["crashes"]
    if cr["rows"]:
        parts = []
        for kind, k in sorted(cr["by_kind"].items(), key=lambda kv: -kv[1]):
            rows = [c for c in cr["rows"] if c["kind"] == kind]
            if kind == "engine refused action":
                cu = cr["cumulative"].get(kind)
                extra = (f"; that kind has now happened {cu['count']} times in {n_(cu['real_rows'])} real-arm rows since {cu['since']}"
                         if cu else "")
                parts.append(f"{k} `RuntimeError: the engine refused action N in phase P` ("
                             + ", ".join(f"{c['seed']} action {c['action']} phase {c['phase']}" for c in rows) + extra + ")")
            elif kind == "game exited":
                ds = []
                for c in rows:
                    nm = f" = {c['exit_hex']}" + (f" ({c['exit_name']})" if c.get("exit_name") else "")
                    le = c.get("log_entry")
                    fr = f" in {le['top_frame']}" if le and le.get("top_frame") else ""
                    lg = f", Windows log: {le['app']} at {le['utc'][11:19]}Z{fr}" if le else ", no Windows log entry"
                    ds.append(f"{c['seed']} exit {c['exit']}{nm}{lg}")
                parts.append(f"{k} `GameDied` ({'; '.join(ds)})")
            else:
                parts.append(f"{k} {kind} ({', '.join(str(c['seed']) for c in rows)})")
        P.append(f"**{len(cr['rows'])} crash rows ({100.0 * len(cr['rows']) / (rn['real_rows'] or 1):.1f}%):** " + "; ".join(parts) + ".")
    else:
        P.append("**No crash rows.**")
    fu = rep["fight_unfinished"]["this_night"]
    if fu:
        hist = "; ".join(f"{v['fight_unfinished']} of {n_(v['ended_rows'])} on {k[5:]}"
                         for k, v in sorted(rep["fight_unfinished"]["earlier_nights"].items())[-4:])
        P.append("**fight_unfinished:** " + ", ".join(f"seed {u['seed']} (worker {u['worker']}, floor {u['floor']}, "
                 f"{(u['streak'] or {}).get('n')} identical actions in a row on a {(u['streak'] or {}).get('screen')} screen)" for u in fu)
                 + (f"; earlier nights: {hist}" if hist else "") + ".")
    else:
        P.append("No `fight_unfinished` run.")
    fl = ", ".join(f"{v} `{k}`" for k, v in lk["reanchor_fail_labels"].items())
    P.append(f"Lockstep: {n_(lk['decisions'])} decisions, diverged {lk['diverged']} ({num(lk['divergence_pct'])}%), re-anchors "
             f"{lk['reanchors']}, failed {lk['reanchor_failed']}" + (f" ({fl})" if fl else "") + f"; mapping gaps {lk['gaps']}."
             + ("" if not any(lk["no_emulator_id_failures_by_earlier_night"].values()) else
                " The same `no emulator id` failures on earlier nights: " + ", ".join(
                    f"{k[5:]} {v}" for k, v in sorted(lk["no_emulator_id_failures_by_earlier_night"].items())[-4:]) + "."))
    g = rep["groups"]
    if g.get("present"):
        d1, d2, hc = g["d11c"]["Strike"], g["d11c"]["Defend"], g["hand_count"]
        trend = "; ".join(f"{k[5:]}: {v:.0f}" for k, v in sorted(rep["hand_count_per_100k_by_night"].items())[-3:])
        rec = lambda k: f"{k} record" + ("" if k == 1 else "s")  # noqa: E731
        P.append(f"**D11C / D11F2 proof:** Strike rank {d1['rank']}, weight {d1['weight']:.1f} ({rec(d1['records'])}); Defend rank "
                 f"{d2['rank']}, weight {d2['weight']:.1f} ({rec(d2['records'])}); together {g['d11c_together_weight']:.1f}, "
                 f"{100 * g['d11c_share']:.1f}% of the total weight of {n_(round(g['total_weight']))}. Hand-count records (game has more "
                 f"+ emulator has more): {hc['game_more']}+{hc['emulator_more']}, per 100,000 decisions {num(hc['per_100k_decisions'], 0)}"
                 + (f" ({trend})" if trend else "") + ".")
        tops = "; ".join(f"{t['rank']}: {t['type']} {', '.join(t['kinds'] or [])} ({', '.join(dict.fromkeys(filter(None, [t['tag'], t['class']])))}"
                         f", weight {t['weight']:.0f})" for t in g["top_groups"][:3])
        fams = ", ".join(f"{f['family']} {f['name']} {100 * f['share']:.0f}%" for f in g["top_families"][:3])
        P.append(f"Top groups of {n_(g['groups'])}: {tops}. Top families: {fams or 'n/a'}; architectural share "
                 f"{100 * (g['arch_share'] or 0):.0f}% of the weight.")
    P.append("HP entering a boss and per-fight HP are " + ("still recorded nowhere." if not rep["hp_recorded"] else "recorded in the rows (not used here)."))
    nx = nt["next_night"]
    if nx.get("known"):
        e, s = parse_utc(nx["earliest_start_utc"]), parse_utc(nx["landings_safe_until_utc"])
        P.append(f"**Next night:** the job's {nx['every_h']}-hour spacing allows a start from {hhmm(e)}Z on {e.strftime('%m-%d')}; landings "
                 f"are safe only until about {hhmm(s)}Z, then wait for the LAB/nightly/active marker.")
    bad = [c for c in rep["cross_checks"] if c["ok"] is False]
    P.append("The rows agree with the arms' summary files in every check." if not bad else
             "The rows DISAGREE with a summary file in: " + "; ".join(c["check"] for c in bad) + ".")
    P.append("Not computed from the files: " + "; ".join(i["figure"] for i in rep["not_computed"]) + ".")
    P.append("Tables:")
    return " ".join(P) + "\n\n" + "\n".join("  " + ln if ln else "" for ln in tables_md(rep)) + "\n"


def edition_figures(rep: dict) -> str:
    nt, rl, em, lk, pa, cm = rep["night"], rep["real"], rep["emu"], rep["lockstep"], rep["paired"], rep["comparison"]
    L = [f"Edition figures: night {nt['date']} ({nt['agent']}, generation {nt['generation']}), from morning_report.py", ""]
    L.append(f"- floors: real {num(rl['mean_floor'])} on {n_(rl['ended'])} ended runs ({num(rl['mean_floor_counted'], 3)} counted, "
             f"{rl['crashes']} crash rows as floor 0, of {n_(rl['rows'])}); emulator {num(em['mean_floor'])} on {n_(em['ended'])} runs")
    L.append(f"- Act 1 boss kill of runs: real {pct(rl['act1_killed'], rl['ended'])} ({n_(rl['act1_killed'])}), emulator "
             f"{pct(em['act1_killed'], em['ended'])} ({n_(em['act1_killed'])}); once there: real {pct(rl['act1_killed'], rl['act1_reached'])}, "
             f"emulator {pct(em['act1_killed'], em['act1_reached'])} (reached {pct(rl['act1_reached'], rl['ended'])} / "
             f"{pct(em['act1_reached'], em['ended'])})")
    L.append(f"- Act 2 boss kill of runs: real {pct(rl['act2_killed'], rl['ended'])} ({rl['act2_killed']}), emulator "
             f"{pct(em['act2_killed'], em['ended'])} ({em['act2_killed']}); wins {rl['wins']} / {em['wins']}")
    pe = pa["ended"]
    if pe.get("act1_agreement") is not None:
        s = (f"- agreement of the two arms on the Act 1 boss: {100 * pe['act1_agreement']:.1f}% of {n_(pe['seeds'])} seeds (both "
             f"{pe['act1_both']}, real only {pe['act1_real_only']}, emulator only {pe['act1_emu_only']}, neither {pe['act1_neither']}); "
             f"paired floor gap, real minus emulator, {sgn(pe['floor_real_minus_emu_mean'])} on ended seeds")
        if pa.get("counted", {}).get("seeds"):
            s += f", {sgn(pa['counted']['floor_emu_minus_real_mean'], 3)} (emulator minus real, crash = 0) on {n_(pa['counted']['seeds'])} seeds"
        L.append(s)
    L.append(f"- crashes: {rl['crashes']} of {n_(rl['rows'])} real rows, kinds "
             + (", ".join(f"{k} {v}" for k, v in rep["crashes"]["by_kind"].items()) or "none") + f"; emulator arm {em['crashes']}")
    wl = rep["winlog"]
    if wl.get("status") == "read":
        L.append(f"- emulator fail-fasts in the Windows application log for the night's window: {wl['emulator_failfasts']}")
    L.append(f"- lockstep: {n_(lk['decisions'])} decisions, diverged {lk['diverged']} ({lk['divergence_rate']}), re-anchors {lk['reanchors']} / "
             f"{lk['reanchor_failed']} failed, gaps {lk['gaps']}")
    L.append(f"- wall: real arm {n_(nt['wall_s']['real_arm'])} s, emulator arm {n_(nt['wall_s']['emulator_arm'])} s; emulator-arm decisions "
             f"{n_(em['decisions'])}")
    for label, tag in (("previous_generation_pooled", "the previous generation, pooled"), ("same_generation_earlier", "its own earlier nights")):
        c = cm.get(label)
        if c:
            r = c["real"]
            L.append(f"- against {tag} (generation {c['generation']}, {len(c['nights'])} nights, {n_(r['base']['runs'])} runs): "
                     f"{sgn(r['floor_ended']['diff'])} floors ({num(r['floor_ended']['z'], 1)} SE), Act 1 boss kill of runs "
                     f"{sgn(r['act1_of_runs']['diff_pts'], 1)} points ({num(r['act1_of_runs']['z'], 1)} SE); once there "
                     f"{pct(rl['act1_killed'], rl['act1_reached'])} against {pct(r['base']['a1_killed'], r['base']['a1_reached'])}")
    g = rep["groups"]
    if g.get("present"):
        L.append(f"- D11C proof: Strike rank {g['d11c']['Strike']['rank']}, Defend rank {g['d11c']['Defend']['rank']}, together "
                 f"{100 * g['d11c_share']:.1f}% of the weight")
    pgp = cm.get("previous_generation_pooled")
    if pgp:
        r = pgp["real"]
        L += ["", f"One line: Generation {nt['generation']} against generation {pgp['generation']} pooled: {sgn(r['floor_ended']['diff'])} floors "
              f"({num(r['floor_ended']['z'], 1)} SE), Act 1 boss kill of runs {sgn(r['act1_of_runs']['diff_pts'], 1)} points; once there "
              f"{pct(rl['act1_killed'], rl['act1_reached'])}."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------------- --check: a second path
# The figures a reader takes from the report (seeds, ended runs, crash rows by kind, mean floors, the Act 1 boss, agreement)
# recomputed straight from the night's two runs.jsonl files by code that shares nothing with the per-row functions above
# (`read_jsonl`, `split_rows`, `make_agg`, `boss_hit`, `crash_kind`, `is_win`): its own reader, per-seed tables instead of
# row sums, `math.fsum` means, its own crash-text classifier. A figure is a MATCH when the two paths agree (counts exactly,
# means and rates within the report's own rounding to four decimals).
CHECK_TOL = 6e-5


def _stream_rows(path: Path):
    """Yields the dict rows of a JSON-lines file, skipping blank, torn or non-object lines."""
    if not path.is_file():
        return
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw.startswith("{"):
                continue
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield row


def _crash_label(text: str) -> str:
    """The report's crash kinds, decided by the error text's wording (the report matches patterns at the start of it)."""
    low = text.lower()
    if low.startswith("runtimeerror") and "engine refused action" in low:
        return "engine refused action"
    if low.startswith("gamedied") and "game exited" in low:
        return "game exited"
    if low.startswith("worker process exited"):
        return "worker process exited"
    if low.startswith("worker deadline"):
        return "worker deadline"
    if "timeouterror" in low:
        return "timeout"
    return "other"


def _act1_boss(row: dict) -> tuple[bool, bool]:
    """(reached, killed) for the Act 1 boss: any `boss_damage_acts` entry for act 0; killed when its fraction is full."""
    fractions = [e[1] for e in (row.get("boss_damage_acts") or []) if isinstance(e, (list, tuple)) and len(e) >= 2 and e[0] == 0]
    return bool(fractions), bool(fractions) and max(fractions) >= 1.0


def _arm_second_path(path: Path, real: bool) -> dict:
    """Per-arm figures by a per-seed pass. `real`: rows are ended when `ev` says "end" and crashes when it says "crash";
    emulator rows are crashes when their `crash` field is true."""
    seeds: set[str] = set()
    floors: list[float] = []  # one per ended row
    boss: dict[str, tuple[bool, bool]] = {}  # seed -> Act 1 (reached, killed) of its last ended row
    ended_seq: list[tuple[str, bool]] = []  # (seed, killed) of every ended row, in file order
    kinds: Counter = Counter()
    crash_rows = 0
    reached = killed = 0
    for row in _stream_rows(path):
        if row.get("seed"):
            seeds.add(row["seed"])
        is_crash = (row.get("ev") == "crash") if real else bool(row.get("crash"))
        is_end = (row.get("ev") == "end") if real else not row.get("crash")
        if is_crash:
            crash_rows += 1
            kinds[_crash_label(str(row.get("error") or ""))] += 1
        elif is_end:
            floors.append(float(row["floor"]))
            r, k = _act1_boss(row)
            reached += r
            killed += k
            boss[row.get("seed")] = (r, k)
            ended_seq.append((row.get("seed"), k))
    n = len(floors)
    return {"seeds": seeds, "ended": n, "crash_rows": crash_rows, "kinds": dict(kinds), "boss": boss, "ended_seq": ended_seq,
            "mean_ended": math.fsum(floors) / n if n else None,
            "mean_counted": math.fsum(floors) / (n + crash_rows) if n + crash_rows else None,
            "act1_reached": reached, "act1_killed": killed,
            "killed_of_runs": killed / n if n else None, "killed_of_reached": killed / reached if reached else None}


def independent_figures(night: Path, agent: str) -> dict:
    """The check's figures, name -> value, from <night>/<agent>/runs.jsonl and <night>/<agent>-emu/runs.jsonl alone."""
    real = _arm_second_path(night / agent / "runs.jsonl", True)
    emu = _arm_second_path(night / f"{agent}-emu" / "runs.jsonl", False)
    out: dict = {"seeds with rows, real arm": len(real["seeds"]), "seeds with rows, emulator arm": len(emu["seeds"]),
                 "seeds with rows, both arms": len(real["seeds"] & emu["seeds"])}
    for tag, arm in (("real", real), ("emulator", emu)):
        out[f"ended runs, {tag}"] = arm["ended"]
        out[f"crash rows, {tag}"] = arm["crash_rows"]
        out[f"mean floors, ended, {tag}"] = arm["mean_ended"]
        out[f"mean floors, counted (crash = 0), {tag}"] = arm["mean_counted"]
        out[f"Act 1 boss reached, {tag}"] = arm["act1_reached"]
        out[f"Act 1 boss killed, {tag}"] = arm["act1_killed"]
        out[f"Act 1 boss killed, share of runs, {tag}"] = arm["killed_of_runs"]
        out[f"Act 1 boss killed, share of those reached, {tag}"] = arm["killed_of_reached"]
    for kind, k in sorted(real["kinds"].items()):
        out[f"crash rows of kind '{kind}', real"] = k
    paired = [(k, emu["boss"][s][1]) for s, k in real["ended_seq"] if s in emu["boss"]]
    out["paired seeds, ended on both arms"] = len(paired)
    out["Act 1 boss agreement of the arms"] = (sum(1 for a, b in paired if a == b) / len(paired)) if paired else None
    return out


def report_check_figures(rep: dict) -> dict:
    """The same figures as the report's own computation holds them."""
    out: dict = {}
    run = rep["runs"]
    out["seeds with rows, real arm"] = run["seeds_with_rows_real"]
    out["seeds with rows, emulator arm"] = run["seeds_with_rows_emu"]
    out["seeds with rows, both arms"] = run["seeds_with_rows_both"]
    for tag, arm in (("real", rep["real"]), ("emulator", rep["emu"])):
        out[f"ended runs, {tag}"] = arm["ended"]
        out[f"crash rows, {tag}"] = arm["crashes"]
        out[f"mean floors, ended, {tag}"] = arm["mean_floor"]
        out[f"mean floors, counted (crash = 0), {tag}"] = arm["mean_floor_counted"]
        out[f"Act 1 boss reached, {tag}"] = arm["act1_reached"]
        out[f"Act 1 boss killed, {tag}"] = arm["act1_killed"]
        out[f"Act 1 boss killed, share of runs, {tag}"] = arm["act1_killed_of_runs"]
        out[f"Act 1 boss killed, share of those reached, {tag}"] = arm["act1_killed_of_reached"]
    for kind, k in sorted(rep["crashes"]["by_kind"].items()):
        out[f"crash rows of kind '{kind}', real"] = k
    pe = rep["paired"]["ended"]
    out["paired seeds, ended on both arms"] = pe.get("seeds")
    out["Act 1 boss agreement of the arms"] = pe.get("act1_agreement")
    return out


def _same(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    return abs(float(a) - float(b)) <= CHECK_TOL


def check_rows(first: dict, second: dict) -> list[dict]:
    """One row per figure named by either path: {figure, first, second, ok}. A figure only one path has is a mismatch."""
    names = list(first) + [k for k in second if k not in first]
    return [{"figure": k, "first": first.get(k), "second": second.get(k),
             "ok": k in first and k in second and _same(first[k], second[k])} for k in names]


def _show(v) -> str:
    if v is None:
        return "n/a"
    return f"{v:,}" if isinstance(v, int) else f"{v:.4f}"


def check_text(night: Path, agent: str, rows: list[dict]) -> str:
    bad = [r for r in rows if not r["ok"]]
    w = max(len(r["figure"]) for r in rows) if rows else 10
    L = [f"morning_report --check: night {night.name} ({agent}); path 1 is the report's own figures, path 2 recounts the rows "
         f"by separate code", ""]
    L.append(f"{'figure'.ljust(w)}  {'path 1'.rjust(12)}  {'path 2'.rjust(12)}  result")
    for r in rows:
        L.append(f"{r['figure'].ljust(w)}  {_show(r['first']).rjust(12)}  {_show(r['second']).rjust(12)}  "
                 f"{'MATCH' if r['ok'] else 'MISMATCH'}")
    L += ["", f"{len(rows)} figures, {len(bad)} mismatch" + ("" if len(bad) == 1 else "es")
          + (": " + "; ".join(r["figure"] for r in bad) if bad else "")]
    return "\n".join(L)


def run_check(night: Path, agent: str | None, lab: Path, now: datetime) -> tuple[str, int]:
    """(text, exit code): the report's figures against the second path's; 1 when any differ."""
    rep = build_report(night, agent, lab, None, "none", None, now)
    agent = rep["night"]["agent"]
    rows = check_rows(report_check_figures(rep), independent_figures(night, agent))
    return check_text(night, agent, rows), (1 if any(not r["ok"] for r in rows) else 0)


# ---------------------------------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The night's morning report: figures, the HANDOFF line and the edition list.")
    ap.add_argument("night", type=Path, help="a lab night folder, e.g. LAB/nightly/2026-11-03")
    ap.add_argument("--agent", help="the real arm's folder (g<N>) when the night holds more than one")
    ap.add_argument("--lab", type=Path, help="the lab folder (default: two levels above the night)")
    ap.add_argument("--logs", type=Path, help="the copy of the real arm's workers' game logs "
                    "(default: <lab>/../../logs/w5-night-<yyyymmdd>-stdout when it exists)")
    ap.add_argument("--winlog", default="auto", help="auto (Get-WinEvent), none, or a JSON file of events")
    ap.add_argument("--usage", help="the usage readout to print in the line, e.g. '84%% all / 59%% Fable at 00:21Z'")
    ap.add_argument("--now", help="ISO time to stamp the line with (default: now)")
    ap.add_argument("--out", type=Path, help="folder for morning_report.json, handoff_line.md and edition_figures.md")
    ap.add_argument("--check", action="store_true", help="recompute the headline figures by a second, independent code path "
                    "over the rows and print both with MATCH / MISMATCH; exit 1 on any mismatch (writes nothing)")
    a = ap.parse_args(argv)
    night = a.night.resolve()
    if not night.is_dir():
        raise SystemExit(f"{a.night}: not a folder")
    lab = (a.lab or night.parent.parent).resolve()
    if a.check:
        text, code = run_check(night, a.agent, lab, parse_utc(a.now) if a.now else datetime.now(timezone.utc))
        print(text)
        return code
    logs = a.logs
    if logs is None:
        cand = lab.parent.parent / "logs" / f"w5-night-{night.name.replace('-', '')}-stdout"
        logs = cand if cand.is_dir() else None
    now = parse_utc(a.now) if a.now else datetime.now(timezone.utc)
    rep = build_report(night, a.agent, lab, logs, a.winlog, a.usage, now)
    line, ed = handoff_line(rep), edition_figures(rep)
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        (a.out / "morning_report.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        (a.out / "handoff_line.md").write_text(line, encoding="utf-8")
        (a.out / "edition_figures.md").write_text(ed, encoding="utf-8")
        print(ed)
        print(f"wrote morning_report.json, handoff_line.md, edition_figures.md in {a.out.name}/")
    else:
        print(line)
        print(ed)
    return 1 if any(c["ok"] is False for c in rep["cross_checks"]) else 0


if __name__ == "__main__":
    sys.exit(main())
