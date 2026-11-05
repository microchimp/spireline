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
ended and counted, the Act 1 boss reached and killed, the arms' agreement, the control variate and the progress score) from the
report and again from a second code path over the rows (see "--check: a second path" below), each with MATCH or MISMATCH; the
exit code is 1 on any mismatch.

The nightly exam's power (2026-11-04): `control_variate` holds the copy arm's floor on each paired seed as a control variate for
the real arm's mean floor (`real.mean_floor_cv` and `_se`, `paired.rho`; the formulas are in `control_variate()`), the saving
1 - rho^2 and the runs a night needs to see a half-floor and a one-floor change; `progress` holds seven measures of the night (the
Act 2 boss beaten of runs, the headline since 2026-11-06; mean floor, Act 1 boss reached, Act 1 killed of those reached, Act 2 reached and killed of those reached, wins) each with its SE, and
their differences against the previous night and the previous generation pooled with SE and z. A night whose real rows did not
record bosses (runs past floor 17 with no Act 1 boss entry) has its boss measures unknown, not 0.

The night block's chance covariate, stage 1 (2026-11-04): `chance_covariate` corrects the real arm's mean floor by the luck of the draw
read from the game-log copies: the act's variant and each hallway, elite and boss encounter the game dealt, valued by a table of the
previous generation's real runs and taken against the draws' own frequencies over the earlier nights (the section "the chance
covariate" below has the rules). It reports the corrected SE beside the raw one, rho and 1 - rho^2, and the mean of the correction, which
is zero when the frequencies are the game's odds (the check). A night without a game-log copy, or with no earlier night to build the
table from, reads "not measured". With --out the table the correction used is written as `chance_table.json`; `--chance-read` prints the
night-by-night table of the reading over every night of the folder (under the report's rule and under a sensitivity rule).

Sources: the arms' `runs.jsonl`, `summary.json`, `result.json`, `compare.json`, `ranked.json`, `by_family.json`,
`divergences.jsonl`, `machine.jsonl`, `wall.json`; the earlier nights' folders (history, the pooled comparison); the lab
runner's log and the job record (start, end, tree, interruptions); `jobs.json` (spacing of the next night); the copy of the
real arm's workers' game logs when one exists (the only record of the real arm's per-fight results; the block deletes the
originals when it closes); and the Windows application log for the night's window (emulator fail-fasts, the game's own
deaths), read with `Get-WinEvent`.

The keep test v2 (fork docs/rl/KEEP_TEST_V2.md; Spireline docs/design/2026-11-05-keep-test-v2.md section 5): the headline is the Act 2 boss
beaten per 100 runs (the night, the previous generation pooled, the difference with its SE and z; `act2_of_runs` is the first measure of
`progress`); the newest row of the promotions ledger is read in one line (`ledger`: rule, frontier, route, the Act 2 boss's kills, deep_f and
its bound, the floor bound, the decision; rows from before the rule read as v1); and on the first night after a route A promotion a
`confirmation` block gives the verdict of the design's section 3 (the night's Act 2 boss kills per 100 runs beat the previous generation's
pooled real-game rate, one-sided 95% lower bound of the unpaired difference above 0, and the mean floor is not below that pool's by more than
1.0 at 95%). The ledger is `<lab>/../agent/promotions.tsv` unless `--agent-root` names the agent folder.

Counting rules (the lane's): a run row is `ev == end` (ended) or `ev == crash` (a crash row). "Ended" figures leave crash
rows out; "counted" figures give a crash row floor 0, no win and no boss kill (the lab's convention, `summary.json`
`nightly`). A boss is reached when `boss_damage_acts` lists its act and killed when the fraction is 1.0. Rates of a pool are
over its runs. Standard errors: the sample standard deviation of the floors over sqrt(n), sqrt(p(1-p)/n) for rates,
differences by the sum of the variances (unpaired: the nights play fresh seed blocks), z the difference over its SE. Cells of
the per-fight tables under 20 fights are suppressed (D13). Results hold no host name, user name or absolute path (the folder is
named relative to the lab).
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
BOSS_GAP_MAX = 0.10  # boss figures of a pool are unrecorded when more than this share of its runs past the Act 1 boss lack its entry
# (judged only when at least MIN_CELL runs are past it)
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


def rank_text(name: str, rank) -> str:
    """'Strike rank 2', or 'Strike absent' when the card has no rank that night."""
    return f"{name} absent" if rank is None else f"{name} rank {rank}"


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
    past: int = 0  # ended runs past the Act 1 boss floor (they fought that boss) ...
    bossgap: int = 0  # ... and how many of those carry no Act 1 boss entry (a block whose rows did not record the boss)

    def __add__(self, o: "Agg") -> "Agg":
        return Agg(*(getattr(self, f) + getattr(o, f) for f in self.__dataclass_fields__))

    @property
    def nc(self) -> int:  # runs counted: ended plus crash rows
        return self.n + self.crashes

    @property
    def boss_recorded(self) -> bool:
        """False when the boss fields are empty where they cannot be: a run past the Act 1 boss floor fought that boss, so a block
        whose such runs mostly lack the entry (the real arm of the first night, say) did not record bosses. Its boss rates are
        unknown, not zero."""
        return self.past < MIN_CELL or self.bossgap / self.past <= BOSS_GAP_MAX

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
        if f > ACT1_BOSS_FLOOR:
            g.past += 1
            g.bossgap += 0 if boss_hit(r, 0)[0] else 1
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
        "mean_floor_se": rnd(g.sd() / math.sqrt(g.n), 4) if g.n >= 2 else None,
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
    return {"runs": g.n, "crashes": g.crashes, "boss_recorded": g.boss_recorded, "mean_floor": rnd(g.mean(), 4), "sd_floor": rnd(g.sd(), 4),
            "mean_floor_counted": rnd(g.mean(True), 4), "a1_reached": g.a1r, "a1_killed": g.a1k, "a2_reached": g.a2r,
            "a2_killed": g.a2k, "a1_of_runs": rnd(ratio(g.a1k, g.n), 4), "a1_of_reached": rnd(ratio(g.a1k, g.a1r), 4),
            "a2_of_runs": rnd(ratio(g.a2k, g.n), 4), "wins": g.wins}


def compare_blocks(cur: Agg, base: Agg) -> dict:
    """The night against a base pool, unpaired (fresh seed blocks): every difference carries its SE and z. The Act 1 and Act 2
    kill rates and the floor are the older fields; the reach rates, the Act 2 kill of those reached and the wins were added with
    the progress score."""
    known = cur.boss_recorded and base.boss_recorded

    def boss(ka: int, na: int, kb: int, nb: int) -> dict:  # a boss rate against a pool that did not record bosses is unknown
        return rate_diff(ka, na, kb, nb) if known else rate_diff(0, 0, 0, 0)

    return {"base": agg_block(base), "boss_recorded": {"current": cur.boss_recorded, "base": base.boss_recorded},
            "floor_ended": mean_diff(cur, base), "floor_counted": mean_diff(cur, base, True),
            "act1_of_runs": boss(cur.a1k, cur.n, base.a1k, base.n),
            "act1_of_reached": boss(cur.a1k, cur.a1r, base.a1k, base.a1r),
            "act2_of_runs": boss(cur.a2k, cur.n, base.a2k, base.n),
            "act1_reach": boss(cur.a1r, cur.n, base.a1r, base.n),
            "act2_reach": boss(cur.a2r, cur.n, base.a2r, base.n),
            "act2_of_reached": boss(cur.a2k, cur.a2r, base.a2k, base.a2r),
            "wins": rate_diff(cur.wins, cur.n, base.wins, base.n)}


# ---------------------------------------------------------------------------------------------------- progress score
# The night's progress score: seven measures over the ended runs, each with its standard error, and its difference against a base
# pool (the previous night, the previous generation pooled) with the difference's SE and z. The nights play fresh seed blocks, so
# the differences are unpaired (the SEs add in quadrature). Floors are in floors, the rest in percentage points.
PROGRESS = (
    ("act2_of_runs", "Act 2 boss beaten (of runs)", "points", "act2_of_runs"),  # the headline (keep test v2): per 100 runs, as points
    ("mean_floor", "mean floor", "floors", None),
    ("act1_reach", "Act 1 boss reached (of runs)", "points", "act1_reach"),
    ("act1_kill_of_reached", "Act 1 boss killed (of those reached)", "points", "act1_of_reached"),
    ("act2_reach", "Act 2 boss reached (of runs)", "points", "act2_reach"),
    ("act2_kill_of_reached", "Act 2 boss killed (of those reached)", "points", "act2_of_reached"),
    ("wins", "wins (of runs)", "points", "wins"),
)


def progress_counts(g: Agg) -> dict[str, tuple[int, int]]:
    """The rate measures as (count, over): the Act 1 and Act 2 boss reach and kill, and the wins."""
    return {"act2_of_runs": (g.a2k, g.n), "act1_reach": (g.a1r, g.n), "act1_kill_of_reached": (g.a1k, g.a1r), "act2_reach": (g.a2r, g.n),
            "act2_kill_of_reached": (g.a2k, g.a2r), "wins": (g.wins, g.n)}


def progress_block(g: Agg) -> dict:
    """{measure: {value, se, n, unit}} for the night's ended runs (rates in percent, their SE sqrt(p(1-p)/n) in points), and
    `boss_recorded`: False when the night's rows did not record bosses (the boss measures are then None)."""
    sd = g.sd()
    out = {"mean_floor": {"value": rnd(g.mean(), 4), "se": rnd(sd / math.sqrt(g.n), 4) if sd is not None else None, "n": g.n,
                          "unit": "floors"}}
    for key, (k, n) in progress_counts(g).items():
        p = ratio(k, n) if key == "wins" or g.boss_recorded else None  # unrecorded bosses: unknown, not 0
        out[key] = {"value": rnd(100 * p, 3) if p is not None else None,
                    "se": rnd(100 * math.sqrt(p * (1 - p) / n), 3) if p is not None else None, "n": n, "unit": "points"}
    out["boss_recorded"] = g.boss_recorded
    return out


def progress_vs(entry: dict | None) -> dict | None:
    """The seven measures' differences against one comparison entry's base: {measure: {diff, se, z}} from its `real` block."""
    if not entry:
        return None
    blk = entry["real"]
    out = {"mean_floor": {k: blk["floor_ended"][k] for k in ("diff", "se", "z")}}
    for key, _label, _unit, field in PROGRESS:
        if key == "mean_floor":
            continue
        d = blk[field]
        out[key] = {"diff": d["diff_pts"], "se": d["se_pts"], "z": d["z"]}
    return {"generation": entry["generation"], "nights": entry["nights"], "base_runs": entry["real"]["base"]["runs"],
            "base_boss_recorded": blk["boss_recorded"]["base"], "diffs": out}


# ---------------------------------------------------------------------------------------------------- control variate
def _fmean(xs: list[float]) -> float:
    return math.fsum(xs) / len(xs)


def control_variate(y: list[float], x: list[float], x_all: list[float]) -> dict:
    """The copy arm as a control variate for the real arm's mean floor (regression estimator with a covariate mean taken from a
    larger sample: double sampling).

    y, x: the real and the copy floor of each paired seed (equal length n). x_all: the copy floor of every copy run that ended,
    paired or not (N >= n; the paired copy runs are among them). With the regression y = a + b x + e on the pairs,

        theta = mean(y) - b * (mean(x) - mean(x_all)),      SE(theta)^2 = s_e^2 / n + b^2 s_x(all)^2 / N,

    s_e^2 the residual variance (n - 2 degrees of freedom). When N = n the correction term is zero (mean(x) is mean(x_all)), theta
    is the raw mean and SE(theta) is the raw SE: the copy runs can only help beyond the pairs. With the copy mean known exactly
    (N -> infinity) the SE is s_e / sqrt(n), the raw SE times sqrt(1 - rho^2): the variance saving is 1 - rho^2.
    `variance_factor` is (1 - rho^2) + rho^2 n / N, the share of the raw variance left at this n and N (large-sample)."""
    n = len(y)
    out: dict = {"pairs": n, "copy_runs": len(x_all), "extra_copy_runs": max(0, len(x_all) - n), "real_mean_paired": None,
                 "copy_mean_paired": None, "copy_mean_all": None, "beta": None, "rho": None, "sd_floor": None, "raw_se": None,
                 "mean_cv": None,
                 "se_cv": None, "se_cv_known_copy_mean": None, "saving": None, "variance_factor": None}
    if n < 3 or len(x) != n or len(x_all) < n:
        return out
    big_n = len(x_all)
    my, mx, mxa = _fmean(y), _fmean(x), _fmean(x_all)
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    raw_se = math.sqrt(syy / (n - 1) / n)
    out.update(real_mean_paired=my, copy_mean_paired=mx, copy_mean_all=mxa, raw_se=raw_se, sd_floor=math.sqrt(syy / (n - 1)))
    if sxx <= 0.0:  # the copy floors do not vary: no slope to fit, nothing to adjust
        out.update(mean_cv=my, se_cv=raw_se, se_cv_known_copy_mean=raw_se)
        return out
    beta = sxy / sxx
    rho = sxy / math.sqrt(sxx * syy) if syy > 0.0 else None
    s2_res = max(0.0, syy - sxy * sxy / sxx) / (n - 2)
    s2_x_all = math.fsum((a - mxa) ** 2 for a in x_all) / (big_n - 1)
    out.update(beta=beta, rho=rho, mean_cv=my - beta * (mx - mxa),
               se_cv=math.sqrt(s2_res / n + beta * beta * s2_x_all / big_n), se_cv_known_copy_mean=math.sqrt(s2_res / n))
    if rho is not None:
        out.update(saving=1.0 - rho * rho, variance_factor=(1.0 - rho * rho) + rho * rho * n / big_n)
    return out


POWER_BASIS = ("real runs per night, ended; two nights of fresh seed blocks and equal size compared unpaired, two-sided 5% level, "
               "80% power; 'vs_fixed_reference' is half (a night against a reference with no error)")


def runs_to_see(sd: float, delta: float, factor: float = 1.0, nights: int = 2, alpha: float = 0.05, power: float = 0.8) -> int:
    """Runs per night to see a change of `delta` floors with probability `power` at level `alpha` (two-sided): the difference of
    `nights` nights' means has variance nights * factor * sd^2 / n, so n = nights * factor * ((z_a + z_b) sd / delta)^2."""
    nd = statistics.NormalDist()
    z = nd.inv_cdf(1.0 - alpha / 2.0) + nd.inv_cdf(power)
    return math.ceil(nights * factor * (z * sd / delta) ** 2)


def power_figures(sd: float | None, cv: dict) -> dict | None:
    """Runs a night needs to see a half-floor and a one-floor change, raw and with the control variate (at this night's
    pairs-to-copy-runs ratio, and with the copy mean known exactly)."""
    if sd is None:
        return None
    rho, n, big_n = cv.get("rho"), cv.get("pairs") or 0, cv.get("copy_runs") or 0
    f_now = cv.get("variance_factor")
    f_lim = None if rho is None else 1.0 - rho * rho
    out: dict = {"basis": POWER_BASIS, "sd_floor": rnd(sd, 4), "variance_factor_this_design": rnd(f_now, 4),
                 "variance_factor_copy_mean_known": rnd(f_lim, 4)}
    for key, delta in (("half_floor", 0.5), ("one_floor", 1.0)):
        out[key] = {"raw": runs_to_see(sd, delta),
                    "adjusted_this_design": None if f_now is None else runs_to_see(sd, delta, f_now),
                    "adjusted_copy_mean_known": None if f_lim is None else runs_to_see(sd, delta, f_lim),
                    "vs_fixed_reference_raw": runs_to_see(sd, delta, nights=1)}
    return out


def paired_pairs(cur: dict) -> list[tuple[dict, dict]]:
    """(real row, emulator row) of every seed that ended on both arms."""
    er = {r["seed"]: r for r in cur["emu_end"]}
    return [(r, er[r["seed"]]) for r in cur["real_end"] if r["seed"] in er]


def control_variate_figures(cur: dict) -> dict:
    """The night's control-variate block: the pairs' regression, the adjusted mean and SE, the saving and the power table.
    `available` is False when the night has no copy arm (or no seed ended on both arms)."""
    pairs = paired_pairs(cur)
    x_all = [float(r["floor"]) for r in {r["seed"]: r for r in cur["emu_end"]}.values()]
    if not pairs:
        return {"available": False, "reason": "no copy-arm run ended on a seed the real arm ended" if cur["has_emu"]
                else "no copy arm rows for this night", "pairs": 0, "copy_runs": len(x_all), "extra_copy_runs": len(x_all)}
    y, x = [float(a["floor"]) for a, _ in pairs], [float(b["floor"]) for _, b in pairs]
    cv = control_variate(y, x, x_all)
    sd = cv["sd_floor"]  # None under three pairs
    out = {"available": True, **{k: (rnd(v, 4) if isinstance(v, float) else v) for k, v in cv.items()}}
    out["adjustment"] = rnd(cv["mean_cv"] - cv["real_mean_paired"], 4) if cv["mean_cv"] is not None else None
    if cv["extra_copy_runs"] == 0:
        out["note"] = ("no copy run beyond the pairs: the copy mean of the pairs is the copy mean of all, so the adjustment term is "
                       "zero and the adjusted mean and SE are the raw ones; the saving needs copy runs the real arm did not play")
    else:
        out["note"] = (f"{cv['extra_copy_runs']} copy runs beyond the {cv['pairs']} pairs: they tighten the copy mean; the saving "
                       f"reaches 1 - rho^2 only if the copy mean were known exactly")
    out["power"] = power_figures(sd, cv)
    return out


# ---------------------------------------------------------------------------------------------------- the chance covariate, stage 1
# The night block's yardstick, run-level chance terms (2026-11-04, brief 4c; docs/design/2026-11-04-training-design.md section 4.4).
# The real arm's floor is a skill part plus luck: which Act 1 the game rolled, which encounters each room drew, which boss waited. The
# draws are the game's, not the agent's, so a term "the value after the draw minus its expectation over the pool's odds" has mean
# zero for any agent and any value table (AIVAT's property). Valued with a table fixed before the night (the previous generation's
# real runs: mean final floor of the runs that met each encounter), the sum of a run's terms is a covariate of known mean zero for the
# run's floor; subtracting beta x it keeps the night's mean unbiased and removes the share of the variance the draws explain. Only
# chance terms enter (not the run head's value of a state, which would subtract skill too). Stage 2 (the draws inside the fights) needs
# per-decision states the past nights did not keep and is not read here.
#
# What counts as a draw (read from the game-log copies, parse_logs): every combat room of a run, by its encounter id's pool: boss
# (_BOSS), elite (_ELITE), hallway weak (_WEAK, the act's first rooms) and hallway normal (_NORMAL, and the unsuffixed pool names such
# as OVERGROWTH_CRAWLERS); an event's fight (_EVENT_ENCOUNTER) is a choice, not a draw, and is left out. The act is the number of bosses
# passed. The act's variant (Act 1 is rolled from two pools of encounters and bosses) is found in the table's own runs: encounters
# that share a run's act are one variant (connected components), and a run's variant is that of its first known encounter; the draw of
# the variant is a term too (its value: mean final floor of the table's runs that played it).
CHANCE_KINDS = ("variant", "hallway", "elite", "boss")
CHANCE_BASIS = ("chance terms only (the act's variant, each hallway, elite and boss encounter drawn from the pool of its act and variant); "
                "value of a draw = mean final floor of the table's runs that met it (pool mean when the cell holds under "
                f"{MIN_CELL} draws); expectation = the table's own draw frequencies; table = the previous generation's real runs with a "
                "game-log copy, fixed before the night; corrected mean = mean - beta x mean(correction), SE = residual SD / sqrt(n)")
CHANCE_Z_FLAG = 3.0  # the mean of the correction should sit within this many SE of zero


def chance_class(encounter: str) -> str | None:
    """The pool a combat room's encounter was drawn from: boss, elite, weak, normal; None for an event's fight (a choice)."""
    if encounter.endswith("_BOSS"):
        return "boss"
    if encounter.endswith("_ELITE"):
        return "elite"
    if encounter.endswith("_EVENT_ENCOUNTER"):
        return None
    if encounter.endswith("_WEAK"):
        return "weak"
    return "normal"


def chance_kind(cls: str) -> str:
    return "hallway" if cls in ("weak", "normal") else cls


def chance_events(encounters: list[str]) -> list[tuple[int, str, str]]:
    """(act, pool class, encounter id) of each draw of a run, in room order; the act is 1 plus the bosses passed."""
    act, out = 1, []
    for enc in encounters:
        cls = chance_class(enc)
        if cls is not None:
            out.append((act, cls, enc))
        if enc.endswith("_BOSS"):
            act += 1
    return out


def encounters_by_seed(fights: list[dict]) -> dict[str, list[str]]:
    """parse_logs records -> {seed: encounter ids in room order}."""
    by: dict[str, list[dict]] = defaultdict(list)
    for f in fights:
        by[f["seed"]].append(f)
    return {s: [f["encounter"] for f in sorted(fs, key=lambda f: f["i"])] for s, fs in by.items()}


def _cell_values(cells: dict[str, list[float]], odds: dict[str, int], min_cell: int) -> tuple[dict[str, dict], float, float]:
    """cells: key -> [n, sum of floors] over the value runs; odds: key -> number of draws over the odds runs. Returns (key -> {n,
    mean_floor, odds_n, value}, the value runs' pool mean, the expectation of the values under the odds' frequencies (the value runs'
    own when the odds runs hold none)). A cell under `min_cell` draws takes the pool mean as its value."""
    total = sum(c[0] for c in cells.values())
    pool_mean = sum(c[1] for c in cells.values()) / total
    out = {}
    for key in sorted(set(cells) | set(odds)):
        n, s = cells.get(key, (0, 0.0))
        out[key] = {"n": int(n), "mean_floor": round(s / n, 6) if n else None, "odds_n": int(odds.get(key, 0)),
                    "value": round(s / n if n >= min_cell else pool_mean, 6)}
    weight = "odds_n" if sum(odds.values()) else "n"
    wsum = sum(v[weight] for v in out.values())
    return out, pool_mean, sum(v[weight] / wsum * v["value"] for v in out.values())


def build_chance_table(runs: list[tuple[list[tuple[int, str, str]], float]], min_cell: int = MIN_CELL,
                       odds_runs: list[tuple[list[tuple[int, str, str]], float]] | None = None) -> dict:
    """The value table from earlier real runs: runs = [(chance_events(run), final floor)] give each draw its value (mean final floor of
    the runs that met it); `odds_runs` (default: the same runs) give the draws' frequencies, the odds the expectation is taken under:
    the draws are the game's, so any earlier night serves, whichever agent played it. Keys are strings so the table is JSON as it
    stands (`<act>|<encounter>`, `<act>|<variant>`, `<act>|<variant>|<pool class>`). A pool or act none of the value runs met has no
    value and no entry: its draws are "unknown" to the table."""
    same = odds_runs is None
    odds_runs = runs if same else odds_runs
    parent: dict[tuple[int, str], tuple[int, str]] = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for events, _ in (runs if same else runs + odds_runs):
        first: dict[int, str] = {}
        for act, _cls, enc in events:
            find((act, enc))
            if act in first:
                parent[find((act, enc))] = find((act, first[act]))
            else:
                first[act] = enc
    members: dict[tuple[int, str], list[str]] = defaultdict(list)
    for key in list(parent):
        members[find(key)].append(key[1])
    label_of: dict[tuple[int, str], str] = {}
    for root, encs in members.items():
        for e in encs:
            label_of[(root[0], e)] = min(encs)

    def tally(rs):
        variants: dict[tuple[int, str], list[float]] = defaultdict(lambda: [0, 0.0])
        pools: dict[tuple[int, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
        n_events = 0
        for events, floor in rs:
            seen_acts: set[int] = set()
            for act, cls, enc in events:
                lab = label_of[(act, enc)]
                if act not in seen_acts:
                    seen_acts.add(act)
                    variants[(act, lab)][0] += 1
                    variants[(act, lab)][1] += floor
                cell = pools[(act, lab, cls)][enc]
                cell[0] += 1
                cell[1] += floor
                n_events += 1
        return variants, pools, n_events

    v_val, p_val, n_events = tally(runs)
    v_odds, p_odds, n_odds_events = (v_val, p_val, n_events) if same else tally(odds_runs)
    table: dict = {"min_cell": min_cell, "runs": len(runs), "draws": n_events, "odds_runs": len(odds_runs), "odds_draws": n_odds_events,
                   "variant_of": {f"{a}|{e}": lab for (a, e), lab in sorted(label_of.items())},
                   "variants": {}, "variant_expect": {}, "pools": {}}
    for act in sorted({a for a, _ in v_val}):
        vals, _mean, expect = _cell_values({lab: v_val[(a, lab)] for a, lab in v_val if a == act},
                                           {lab: v_odds[(a, lab)][0] for a, lab in v_odds if a == act}, min_cell)
        table["variant_expect"][str(act)] = round(expect, 6)
        for lab, v in vals.items():
            table["variants"][f"{act}|{lab}"] = {**v, "members": sorted(e for (a, e), l in label_of.items() if a == act and l == lab)}
    for (act, lab, cls), cells in sorted(p_val.items()):
        odds = {e: c[0] for e, c in p_odds.get((act, lab, cls), {}).items()}
        vals, mean, expect = _cell_values(cells, odds, min_cell)
        table["pools"][f"{act}|{lab}|{cls}"] = {"n": sum(v["n"] for v in vals.values()), "mean_floor": round(mean, 6),
                                                "expect": round(expect, 6), "cells": vals}
    return table


def chance_terms(table: dict, events: list[tuple[int, str, str]]) -> dict:
    """A run's correction by kind (variant, hallway, elite, boss), their sum, the draws counted and those the table does not know
    (an encounter or act it has never seen: left out of the sum, counted). Each pool is drawn from without replacement within an act
    (an encounter never came twice in an act's weak, normal or elite pool in nine nights of logs), so a draw's expectation is taken over
    the pool's encounters not yet drawn in that act, at the odds' frequencies: the value of the draw minus that expectation has mean zero
    given the run's earlier draws, whatever the run's later fate (a run that died on a hard encounter has not drawn it again)."""
    out: dict = {k: 0.0 for k in CHANCE_KINDS}
    variant_of_act: dict[int, str] = {}
    for act, _cls, enc in events:
        lab = table["variant_of"].get(f"{act}|{enc}")
        if lab is not None and act not in variant_of_act and f"{act}|{lab}" in table["variants"]:
            variant_of_act[act] = lab
    for act, lab in variant_of_act.items():
        out["variant"] += table["variants"][f"{act}|{lab}"]["value"] - table["variant_expect"][str(act)]
    unknown = 0
    drawn: dict[tuple[int, str], set[str]] = defaultdict(set)
    for act, cls, enc in events:
        pool = table["pools"].get(f"{act}|{variant_of_act[act]}|{cls}") if act in variant_of_act else None
        cell = pool["cells"].get(enc) if pool else None
        if cell is None:
            unknown += 1
            continue
        weight = "odds_n" if any(v["odds_n"] for v in pool["cells"].values()) else "n"
        rest = [v for e, v in pool["cells"].items() if e not in drawn[(act, cls)] and v[weight] > 0]
        drawn[(act, cls)].add(enc)
        if not rest:
            unknown += 1
            continue
        out[chance_kind(cls)] += cell["value"] - sum(v[weight] * v["value"] for v in rest) / sum(v[weight] for v in rest)
    out["total"] = math.fsum(out[k] for k in CHANCE_KINDS)
    out["draws"], out["unknown"] = len(events), unknown
    return out


def _share_left(y: list[float], x: list[float]) -> float | None:
    """1 - rho^2 of x against y (the share of y's variance left after a least-squares adjustment on x); None when x or y is flat."""
    n = len(y)
    if n < 3:
        return None
    mx, my = _fmean(x), _fmean(y)
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    return 1.0 - sxy * sxy / (sxx * syy)


def chance_adjustment(y: list[float], c: list[float], by_kind: dict[str, list[float]] | None = None, odds_runs: int | None = None) -> dict:
    """The real floors y and their corrections c (mean zero when the odds are the game's): raw mean and SE, the correction's mean (it
    should be near zero: SE and z), the slope and correlation, the corrected mean y - beta c and its SE, the share of the variance left
    1 - rho^2, the plain AIVAT form y - c (no fitted slope), and each kind's share alone.

    The odds were estimated from `odds_runs` earlier runs (None: known exactly). Then the correction's mean carries their sampling
    error too, SD(c) sqrt(1/n + 1/odds_runs), and the corrected mean's variance gains beta^2 SD(c)^2 / odds_runs beside the residual
    s_e^2 / n (n - 2 degrees of freedom): the double-sampling form of `control_variate`, with the draws' frequencies as the larger sample."""
    n = len(y)
    out: dict = {"n": n, "mean_raw": None, "sd_floor": None, "raw_se": None, "mean_correction": None, "se_correction": None,
                 "z_correction": None, "beta": None, "rho": None, "mean_corrected": None, "se_corrected": None,
                 "share_left": None, "mean_aivat": None, "se_aivat": None, "share_left_by_kind": {}}
    if n < 3 or len(c) != n:
        return out
    odds_term = 0.0 if not odds_runs else 1.0 / odds_runs
    my, mc = _fmean(y), _fmean(c)
    sxx = math.fsum((a - mc) ** 2 for a in c)
    syy = math.fsum((b - my) ** 2 for b in y)
    sxy = math.fsum((a - mc) * (b - my) for a, b in zip(c, y))
    raw_se = math.sqrt(syy / (n - 1) / n)
    var_c = sxx / (n - 1)
    se_c = math.sqrt(var_c * (1.0 / n + odds_term))
    out.update(mean_raw=my, sd_floor=math.sqrt(syy / (n - 1)), raw_se=raw_se, mean_correction=mc, se_correction=se_c,
               z_correction=(mc / se_c) if se_c > 0 else None)
    d = [b - a for a, b in zip(c, y)]
    md = _fmean(d)
    out.update(mean_aivat=md, se_aivat=math.sqrt(math.fsum((v - md) ** 2 for v in d) / (n - 1) / n + var_c * odds_term))
    if sxx <= 0.0:  # no draw varied: nothing to adjust
        out.update(mean_corrected=my, se_corrected=raw_se, share_left=1.0)
        return out
    beta = sxy / sxx
    s2_res = max(0.0, syy - sxy * sxy / sxx) / (n - 2)
    out.update(beta=beta, mean_corrected=my - beta * mc, se_corrected=math.sqrt(s2_res / n + beta * beta * var_c * odds_term))
    if syy > 0.0:
        rho = sxy / math.sqrt(sxx * syy)
        out.update(rho=rho, share_left=1.0 - rho * rho)
    for kind, xs in (by_kind or {}).items():
        out["share_left_by_kind"][kind] = _share_left(y, xs)
    return out


def chance_power(sd: float, share_left: float | None) -> dict:
    """Runs a night needs to see a half-floor and a one-floor change (the power basis of POWER_BASIS), raw and corrected."""
    return {key: {"raw": runs_to_see(sd, delta), "corrected": None if share_left is None else runs_to_see(sd, delta, share_left)}
            for key, delta in (("half_floor", 0.5), ("one_floor", 1.0))}


def logs_dir_of(logs_root: Path | None, date: str) -> Path | None:
    """The copy of a night's workers' game logs under `logs_root`, when there is one with logs in it."""
    if logs_root is None:
        return None
    cand = logs_root / f"w5-night-{date.replace('-', '')}-stdout"
    return cand if cand.is_dir() and any(cand.glob("*.log")) else None


def chance_night_runs(h: dict, logs: Path, cache: dict | None = None, fights: list[dict] | None = None
                      ) -> list[tuple[str, list[tuple[int, str, str]], int]]:
    """(seed, chance events, final floor) of each ended real run of night `h` that its game-log copy holds."""
    key = f"{h['date']}|{h['agent']}"
    if cache is not None and key in cache:
        return cache[key]
    enc = encounters_by_seed(fights if fights is not None else parse_logs(logs)[0])
    floors = {r["seed"]: r["floor"] for r in h["real_end"] if r.get("seed")}
    out = [(s, chance_events(enc[s]), floors[s]) for s in sorted(enc) if s in floors]
    if cache is not None:
        cache[key] = out
    return out


def chance_table_nights(cur: dict, others: list[dict], logs_root: Path | None, rule: str = "previous_generation"
                        ) -> tuple[list[dict], list[dict], str]:
    """(value nights, odds nights, the rule in words). "previous_generation" (the rule of the report): the draws are valued by the
    nights of the highest generation below the night's own that have a game-log copy, and the odds are the draws' frequencies over every
    earlier night with a copy (the game's odds do not depend on who played). "other_nights": every other night with a copy, later ones
    too, for both (a sensitivity reading, never a rule: it uses nights the night's table could not have had)."""
    if rule == "previous_generation":
        earlier = [h for h in others if h["date"] < cur["date"] and logs_dir_of(logs_root, h["date"])]
        older = sorted({h["generation"] for h in others if h["date"] < cur["date"] and h["generation"] < cur["generation"]})
        if not older:
            return [], [], "no earlier generation"
        gen = older[-1]
        value = [h for h in earlier if h["generation"] == gen]
        return value, earlier, f"values from the previous generation (g{gen}), odds from every earlier night with a game-log copy"
    every = [h for h in others if h["date"] != cur["date"] and logs_dir_of(logs_root, h["date"])]
    return every, every, "values and odds from every other night with a game-log copy (sensitivity reading, not the rule)"


def chance_covariate_figures(cur: dict, fights: list[dict] | None, others: list[dict], logs_root: Path | None,
                             rule: str = "previous_generation", cache: dict | None = None) -> dict:
    """The night's stage-1 block: `available` False with the reason ("not measured: ...") when the night has no game-log copy or no
    table can be built; else the table, the corrections' check (mean near zero) and the corrected SE beside the raw one."""
    base = {"available": False, "stage": 1, "basis": CHANCE_BASIS, "rule": rule}
    cache = {} if cache is None else cache
    if not fights:
        return {**base, "status": "not measured: no copy of this night's game logs (the encounter ids of the rooms are only there)"}
    nights, odds_nights, how = chance_table_nights(cur, others, logs_root, rule)
    if not nights:
        return {**base, "status": f"not measured: no table can be fixed before the night ({how}: no night with a game-log copy)"}

    def runs_of(hs: list[dict]) -> list[tuple[list[tuple[int, str, str]], int]]:
        return [(ev, floor) for h in hs for _s, ev, floor in chance_night_runs(h, logs_dir_of(logs_root, h["date"]), cache)]

    table = build_chance_table(runs_of(nights), MIN_CELL, runs_of(odds_nights))
    own = chance_night_runs(cur, Path("."), cache, fights)
    y, c, kinds = [], [], {k: [] for k in CHANCE_KINDS}
    draws = unknown = 0
    for _s, ev, floor in own:
        t = chance_terms(table, ev)
        y.append(float(floor))
        c.append(t["total"])
        for k in CHANCE_KINDS:
            kinds[k].append(t[k])
        draws += t["draws"]
        unknown += t["unknown"]
    adj = chance_adjustment(y, c, kinds, table["odds_runs"])
    if adj["n"] < 3:
        return {**base, "status": "not measured: fewer than three runs in the game-log copy"}
    by_kind = {}
    for k in CHANCE_KINDS:
        by_kind[k] = {"mean_correction": rnd(_fmean(kinds[k]), 4), "sd_correction": rnd(statistics.pstdev(kinds[k]), 4),
                      "share_left_alone": rnd(adj["share_left_by_kind"].get(k), 4)}
    ended = len(cur["real_end"])
    odds_ok = adj["z_correction"] is None or abs(adj["z_correction"]) <= CHANCE_Z_FLAG
    return {**base, "available": True, "status": "measured",
            "table_nights": sorted(h["date"] for h in nights), "table_generation": nights[0]["generation"],
            "odds_nights": sorted(h["date"] for h in odds_nights), "table_rule": how,
            "table_runs": table["runs"], "table_draws": table["draws"], "odds_runs": table["odds_runs"],
            "runs_used": adj["n"], "ended_runs": ended, "coverage": rnd(adj["n"] / ended, 4) if ended else None,
            "draws": draws, "unknown_draws": unknown,
            "odds_check": {"mean_correction": rnd(adj["mean_correction"], 4), "se": rnd(adj["se_correction"], 4),
                           "z": rnd(adj["z_correction"], 3), "within_3_se": odds_ok,
                           "note": "the correction has mean zero when the table's frequencies are the game's odds (SE counts the odds' own sampling "
                                   "error); the copy arm's rows hold no encounter ids, so the check is read on the real arm's own draws"},
            "sd_floor": rnd(adj["sd_floor"], 4), "raw_mean": rnd(adj["mean_raw"], 4), "raw_se": rnd(adj["raw_se"], 4),
            "beta": rnd(adj["beta"], 4), "rho": rnd(adj["rho"], 4), "share_left": rnd(adj["share_left"], 4),
            "corrected_mean": rnd(adj["mean_corrected"], 4), "corrected_se": rnd(adj["se_corrected"], 4),
            "se_ratio": rnd(adj["se_corrected"] / adj["raw_se"], 4) if adj["raw_se"] else None,
            "aivat_mean": rnd(adj["mean_aivat"], 4), "aivat_se": rnd(adj["se_aivat"], 4), "by_kind": by_kind,
            "power": chance_power(adj["sd_floor"], adj["share_left"]) if adj["sd_floor"] else None, "table": table}


def chance_pooled(rows: list[dict]) -> dict:
    """Pooled over the nights' figures that were measured: Fisher z of rho weighted by n - 3, then the share of variance left 1 - rho^2."""
    ok = [r for r in rows if r.get("available") and r.get("rho") is not None]
    if not ok:
        return {"nights": 0, "runs": 0, "rho": None, "share_left": None}
    w = [r["runs_used"] - 3 for r in ok]
    z = sum(wi * math.atanh(r["rho"]) for wi, r in zip(w, ok)) / sum(w)
    rho = math.tanh(z)
    return {"nights": len(ok), "runs": sum(r["runs_used"] for r in ok), "rho": rnd(rho, 4), "share_left": rnd(1.0 - rho * rho, 4)}


def chance_reading(parent: Path, logs_root: Path | None, rules: tuple[str, ...] = ("previous_generation", "other_nights")) -> dict:
    """Stage 1 on every night under `parent` (a lab's nightly folder), each under each table rule; each game-log copy is read once."""
    entries = [load_arm_pair(nd, real_arms(nd)[0]) for nd in list_nights(parent) if real_arms(nd)]
    fights_of: dict[str, list[dict]] = {}
    cache: dict = {}
    for h in entries:
        d = logs_dir_of(logs_root, h["date"])
        if d is not None:
            fights_of[h["date"]] = parse_logs(d)[0]
            chance_night_runs(h, d, cache, fights_of[h["date"]])
    out: dict = {"nights": [h["date"] for h in entries], "by_rule": {}}
    for rule in rules:
        rows = [{"date": h["date"], "generation": h["generation"],
                 **chance_covariate_figures(h, fights_of.get(h["date"]), [e for e in entries if e is not h], logs_root, rule, cache)}
                for h in entries]
        out["by_rule"][rule] = {"nights": rows, "pooled": chance_pooled(rows)}
    return out


def chance_reading_md(reading: dict) -> str:
    L: list[str] = []
    for rule, blk in reading["by_rule"].items():
        L += [f"Table rule `{rule}`:", ""]
        head = ["night", "gen", "table from", "runs (of ended)", "sd of floors", "raw mean (SE)", "corrected mean (SE)", "corrected SE / raw SE",
                "rho", "1 - rho^2", "AIVAT form SE", "mean of the correction (z)", "unknown draws", "one floor: raw", "one floor: corrected"]
        rows = []
        for r in blk["nights"]:
            if not r.get("available"):
                rows.append([r["date"][5:], str(r["generation"]), r["status"]] + [""] * (len(head) - 3))
                continue
            oc, p = r["odds_check"], r["power"]["one_floor"]
            rows.append([r["date"][5:], str(r["generation"]), "+".join(d[5:] for d in r["table_nights"]) + f" (g{r['table_generation']})",
                         f"{n_(r['runs_used'])} ({n_(r['ended_runs'])})", num(r["sd_floor"]), f"{num(r['raw_mean'])} ({num(r['raw_se'], 3)})",
                         f"{num(r['corrected_mean'])} ({num(r['corrected_se'], 3)})", num(r["se_ratio"], 3), num(r["rho"], 3), num(r["share_left"], 3),
                         num(r["aivat_se"], 3), f"{sgn(oc['mean_correction'], 3)} (z {sgn(oc['z'], 1)})", f"{r['unknown_draws']} of {n_(r['draws'])}",
                         n_(p["raw"]), n_(p["corrected"])])
        L += table_md(head, rows)
        pl = blk["pooled"]
        L += ["", f"Pooled over {pl['nights']} nights ({n_(pl['runs'])} runs, Fisher z): rho {num(pl['rho'], 3)}, 1 - rho^2 = {num(pl['share_left'], 3)}", ""]
    return "\n".join(L)


def chance_lines(rep: dict) -> list[str]:
    """The edition's lines for the stage-1 covariate."""
    cc = rep["chance_covariate"]
    if not cc.get("available"):
        return [f"- chance covariate, stage 1 (the draws of the game as covariate for the real arm's floor): {cc['status']}"]
    oc, p = cc["odds_check"], (cc["power"] or {}).get("one_floor") or {}
    s = (f"- chance covariate, stage 1 (act variant, hallway, elite and boss draws valued by the table of "
         f"{'+'.join(d[5:] for d in cc['table_nights'])}, generation {cc['table_generation']}; {n_(cc['runs_used'])} of {n_(cc['ended_runs'])} ended "
         f"runs): real mean floor {num(cc['raw_mean'])} (SE {num(cc['raw_se'], 3)}) raw and {num(cc['corrected_mean'])} (SE {num(cc['corrected_se'], 3)}) "
         f"corrected; rho {num(cc['rho'], 3)}, 1 - rho^2 = {num(cc['share_left'], 3)} of the variance left; the correction averages "
         f"{sgn(oc['mean_correction'], 3)} (SE {num(oc['se'], 3)}, z {sgn(oc['z'], 1)})")
    if not oc["within_3_se"]:
        s += "; THE MEAN IS OUTSIDE 3 SE, the table's frequencies are not the game's odds"
    if p:
        s += f"; one floor needs {n_(p['raw'])} real runs a night raw, {n_(p['corrected'])} corrected"
    return [s]


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
    pairs = paired_pairs(cur)
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


# ---------------------------------------------------------------------------------------------------- the headline, the ledger, the confirmation
CONFIRM_Z = 1.645  # one-sided 95%: the confirmation's two bounds
CONFIRM_FLOOR_MARGIN = 1.0  # the night's mean floor may be below the previous generation's pool by this much (95% lower bound)


def read_ledger(path: Path) -> list[dict]:
    """The rows of the promotions ledger by column name, oldest first; [] when the file is not there. Rows written before a column
    existed have no such key (`.get` reads them as empty: a row without `rule` is v1)."""
    if not path.is_file():
        return []
    lines = [x for x in path.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
    head = lines[0].split("\t") if lines else []
    return [dict(zip(head, x.split("\t"), strict=False)) for x in lines[1:]]


def _ledger_num(row: dict, key: str) -> float | None:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return None


def ledger_figures(rows: list[dict]) -> dict:
    """The newest ledger row (the file is append-only: the last) as figures and as one line; `available` False when there is no ledger."""
    if not rows:
        return {"available": False, "line": "no promotions ledger was found"}
    r = rows[-1]
    v2 = (r.get("rule") or "") == "v2"
    seeds, d_floor, floor_lo = r.get("seeds") or "?", _ledger_num(r, "d_floor"), _ledger_num(r, "floor_lower")
    head = (f"Newest ledger row ({(r.get('written') or '?')[:16]}Z, block {r.get('seed_block') or '?'}, generation {r.get('cand_gen') or '?'} "
            f"against {r.get('base_gen') or '?'}, {seeds} seeds): ")
    if v2:
        k2c, k2b = r.get("k2_cand") or "?", r.get("k2_base") or "?"
        d_deep, deep_lo, f95 = _ledger_num(r, "d_deep"), _ledger_num(r, "deep_lower"), _ledger_num(r, "floor_lower95")
        body = (f"rule v2, frontier {r.get('frontier') or '?'}, route {r.get('route') or 'none'}, Act 2 boss {k2c} against {k2b}, "
                f"deep {sgn(d_deep)} per 100 (0.005 bound {sgn(deep_lo)}), floor 95% lower bound {sgn(f95)}, decision {r.get('decision') or '?'}")
    else:
        body = (f"rule v1 (the floor test), floor {sgn(d_floor)} (99% lower bound {sgn(floor_lo)}), Act 1 boss {r.get('boss_cand') or '?'} against "
                f"{r.get('boss_base') or '?'}, Act 2 boss kills not recorded in the row, decision {r.get('decision') or '?'}")
    return {"available": True, "rows": len(rows), "rule": "v2" if v2 else "v1", "written": r.get("written"), "seed_block": r.get("seed_block"),
            "cand_gen": r.get("cand_gen"), "base_gen": r.get("base_gen"), "seeds": r.get("seeds"), "decision": r.get("decision"),
            "frontier": r.get("frontier") or None, "route": r.get("route") or None, "k2_cand": r.get("k2_cand") or None,
            "k2_base": r.get("k2_base") or None, "d_deep": _ledger_num(r, "d_deep"), "deep_lower": _ledger_num(r, "deep_lower"),
            "floor_lower95": _ledger_num(r, "floor_lower95"), "d_floor": d_floor, "floor_lower": floor_lo, "line": head + body + "."}


def act2_headline(rep: dict) -> str:
    """The headline: the Act 2 boss beaten per 100 runs, the night against the previous generation pooled, with the difference, SE and z."""
    rl, pgp = rep["real"], rep["comparison"].get("previous_generation_pooled")
    if not rep["progress"]["measures"]["boss_recorded"]:
        return "Act 2 boss beaten per 100 runs: unknown (this night's rows did not record the boss fights)"
    s = f"Act 2 boss beaten per 100 runs: {num(100.0 * rl['act2_killed'] / rl['ended'] if rl['ended'] else None)} ({rl['act2_killed']} of {n_(rl['ended'])} ended runs)"
    if pgp:
        b, d = pgp["real"]["base"], pgp["real"]["act2_of_runs"]
        if d["diff_pts"] is None:
            return s + f"; generation {pgp['generation']} pooled: unknown (its rows did not record the boss fights)"
        s += (f"; generation {pgp['generation']} pooled over its {len(pgp['nights'])} real-arm nights {num(100.0 * b['a2_killed'] / b['runs'] if b['runs'] else None)} "
              f"({b['a2_killed']} of {n_(b['runs'])}); difference {sgn(d['diff_pts'])} points (SE {num(d['se_pts'])}, z {sgn(d['z'], 1)})")
    else:
        s += "; no earlier generation to compare with"
    return s


def confirmation_block(rep: dict, rows: list[dict]) -> dict | None:
    """The design's section 3 verdict on the first night after a route A promotion, or None when this night is not one: the ledger's newest
    promoted row is of this night's generation, was judged by the keep test v2 and found route A (`route` holds an A), and no earlier night
    of this generation exists. Confirmed when the night's Act 2 boss kills per 100 runs beat the previous generation's pooled real-game rate
    (the one-sided 95% lower bound of the unpaired difference is above 0) and its mean floor (ended runs) is not below that pool's by more
    than 1.0 at 95% (the lower bound of the difference is at least -1.0). A route F promotion is not confirmed (the copy agrees on floors)."""
    gen = rep["night"]["generation"]
    promoted = [r for r in rows if r.get("decision") == "promoted" and str(r.get("cand_gen")) == str(gen)]
    if not promoted or rep["comparison"].get("same_generation_earlier"):
        return None
    row = promoted[-1]
    if (row.get("rule") or "") != "v2" or "A" not in (row.get("route") or ""):
        return None
    out = {"applies": True, "generation": gen, "promoted_block": row.get("seed_block"), "promoted_written": row.get("written"),
           "route": row.get("route"), "frontier": row.get("frontier") or None, "z": CONFIRM_Z, "floor_margin": CONFIRM_FLOOR_MARGIN}
    pgp = rep["comparison"].get("previous_generation_pooled")
    if not pgp or not rep["progress"]["measures"]["boss_recorded"]:
        return {**out, "verdict": "not measured", "why": "no earlier night of the previous generation to pool, or the boss fights were not recorded"}
    a2, fl, b = pgp["real"]["act2_of_runs"], pgp["real"]["floor_ended"], pgp["real"]["base"]
    if a2["diff_pts"] is None or fl["diff"] is None:
        return {**out, "verdict": "not measured", "why": "the previous generation's pool has no boss record or too few runs for a difference"}
    rl = rep["real"]
    a2_lower, fl_lower = a2["diff_pts"] - CONFIRM_Z * a2["se_pts"], fl["diff"] - CONFIRM_Z * fl["se"]
    act2_ok, floor_ok = a2_lower > 0, fl_lower >= -CONFIRM_FLOOR_MARGIN
    failed = [name for name, ok in (("the Act 2 boss rate", act2_ok), ("the mean floor", floor_ok)) if not ok]
    return {**out, "previous_generation": pgp["generation"], "previous_nights": pgp["nights"],
            "act2": {"night_per_100": rnd(100.0 * rl["act2_killed"] / rl["ended"], 3) if rl["ended"] else None, "night_kills": rl["act2_killed"],
                     "night_runs": rl["ended"], "pool_per_100": rnd(100.0 * b["a2_killed"] / b["runs"], 3) if b["runs"] else None,
                     "pool_kills": b["a2_killed"], "pool_runs": b["runs"], "diff_pts": a2["diff_pts"], "se_pts": a2["se_pts"], "z": a2["z"],
                     "lower95": rnd(a2_lower, 3), "holds": act2_ok},
            "floor": {"night": rl["mean_floor"], "pool": b["mean_floor"], "diff": fl["diff"], "se": fl["se"], "z": fl["z"],
                      "lower95": rnd(fl_lower, 3), "holds": floor_ok},
            "verdict": "confirmed" if not failed else "NOT confirmed", "failed": failed}


def confirmation_text(c: dict) -> str:
    """One sentence for the confirmation block."""
    head = (f"Confirmation of the route {c['route']} promotion of generation {c['generation']} ({c['promoted_block']}; frontier {c.get('frontier') or '?'}): ")
    if c["verdict"] == "not measured":
        return head + f"not measured, {c['why']}."
    a, f = c["act2"], c["floor"]
    return (head + f"**{c['verdict']}.** Act 2 boss beaten {num(a['night_per_100'])} per 100 runs ({a['night_kills']} of {n_(a['night_runs'])}) against "
            f"generation {c['previous_generation']} pooled {num(a['pool_per_100'])} ({a['pool_kills']} of {n_(a['pool_runs'])}): {sgn(a['diff_pts'])} points, "
            f"one-sided 95% lower bound {sgn(a['lower95'])} (needs above 0); mean floor {num(f['night'])} against {num(f['pool'])}: {sgn(f['diff'])}, "
            f"lower bound {sgn(f['lower95'])} (needs at least {-c['floor_margin']:+.1f})"
            + (f". On a failure the orchestrator restores the previous current.json (DECISIONS); failed: {', '.join(c['failed'])}" if c["failed"] else "") + ".")


def build_report(night: Path, agent: str | None, lab: Path, logs: Path | None, winlog_source: str, usage: str | None,
                 now: datetime, runner=subprocess.run, logs_root: Path | None = None, agent_root: Path | None = None) -> dict:
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
    # the control variate (the copy arm's floors on the same seeds), the pairs' correlation, and the progress score
    cv = control_variate_figures(cur)
    paired = paired_figures(cur)
    paired["rho"], paired["beta"] = cv.get("rho"), cv.get("beta")
    real["mean_floor_cv"], real["mean_floor_cv_se"] = cv.get("mean_cv"), cv.get("se_cv")
    progress = {"unit_note": "floors for the mean floor; percentage points for the rest (value, SE and differences)",
                "measures": progress_block(g_real), "previous_night": progress_vs(comparison["previous_night"]),
                "previous_generation_pooled": progress_vs(comparison["previous_generation_pooled"])}

    # the promotions ledger (`<lab>/../agent/promotions.tsv`): its newest row in one line, and the confirmation after a route A promotion
    ledger_rows = read_ledger((agent_root or lab.parent / "agent") / "promotions.tsv")
    ledger = ledger_figures(ledger_rows)

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
    # the copy arm may play only a prefix of the block's seeds (--emu-runs N); pairing is judged on that prefix
    emu_planned = nightly.get("emu_runs_planned") or planned

    # per-fight tables
    fights = {"emu": cells_json(fight_table_from_nodes(cur["emu_end"])), "real": None, "real_notes": None}
    night_fights = None
    if logs is not None and logs.is_dir() and any(logs.glob("*.log")):
        fl, seen = parse_logs(logs)
        night_fights = fl
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
        "runs": {"planned": planned, "emu_planned": emu_planned, "real_rows": real["rows"], "real_ended": real["ended"], "real_crash_rows": real["crashes"],
                 "emu_rows": emu["rows"], "emu_ended": emu["ended"], "emu_crash_rows": emu["crashes"],
                 "seeds_with_rows_real": len(seeds_real), "seeds_with_rows_emu": len(seeds_emu),
                 "seeds_with_rows_both": len(seeds_real & seeds_emu)},
        "real": real, "emu": emu, "human_r1": R1, "comparison": comparison, "paired": paired, "control_variate": cv,
        "chance_covariate": chance_covariate_figures(cur, night_fights, earlier, logs_root),
        "progress": progress, "fights": fights, "ledger": ledger,
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
    report["act2_headline"] = act2_headline(report)
    report["confirmation"] = confirmation_block(report, ledger_rows)
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
    if not rep["hp_recorded"]:
        items.append({"figure": "fight-quality measures per fight kind in the real arm (damage taken per hallway fight, damage dealt per "
                      "energy spent, block wasted)",
                      "source": "recorded nowhere: no row field and no game-log line carries player HP, energy spent or block (the "
                      "logs list card plays without costs or numbers). The lockstep reads them at every combat decision (the referee's "
                      "observation holds player HP, block and energy, each hand card's cost and the enemies' HP and block), but "
                      "rl/run_fields.RunFields keeps only the boss fight's enemy HP; a per-fight record there is the lead (fork change)"})
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
    P.append(f"**{rep['act2_headline']}.**")
    if rep.get("confirmation"):
        P.append(confirmation_text(rep["confirmation"]))
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
    both_planned = min(rn["planned"], rn.get("emu_planned") or rn["planned"]) if rn.get("planned") else rn.get("emu_planned")
    prefix = (f" (the copy arm plays {n_(rn['emu_planned'])} of the {n_(rn['planned'])} seeds)"
              if rn.get("emu_planned") and rn.get("planned") and rn["emu_planned"] < rn["planned"] else "")
    fail = (f"**Pool failure counters:** {n_(rn['seeds_with_rows_both'])} of {n_(both_planned)} seeds have rows in both arms{prefix}; {cnt}; "
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
        P.append(f"**D11C / D11F2 proof:** {rank_text('Strike', d1['rank'])}, weight {d1['weight']:.1f} ({rec(d1['records'])}); "
                 f"{rank_text('Defend', d2['rank'])}, weight {d2['weight']:.1f} ({rec(d2['records'])}); together {g['d11c_together_weight']:.1f}, "
                 f"{100 * g['d11c_share']:.1f}% of the total weight of {n_(round(g['total_weight']))}. Hand-count records (game has more "
                 f"+ emulator has more): {hc['game_more']}+{hc['emulator_more']}, per 100,000 decisions {num(hc['per_100k_decisions'], 0)}"
                 + (f" ({trend})" if trend else "") + ".")
        tops = "; ".join(f"{t['rank']}: {t['type']} {', '.join(t['kinds'] or [])} ({', '.join(dict.fromkeys(filter(None, [t['tag'], t['class']])))}"
                         f", weight {t['weight']:.0f})" for t in g["top_groups"][:3])
        fams = ", ".join(f"{f['family']} {f['name']} {100 * f['share']:.0f}%" for f in g["top_families"][:3])
        P.append(f"Top groups of {n_(g['groups'])}: {tops}. Top families: {fams or 'n/a'}; architectural share "
                 f"{100 * (g['arch_share'] or 0):.0f}% of the weight.")
    P.append(rep["ledger"]["line"])
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


def control_variate_lines(rep: dict) -> list[str]:
    cv, rl = rep["control_variate"], rep["real"]
    if not cv.get("available"):
        return [f"- control variate (the copy arm's floors as covariate for the real arm's): not computed, {cv.get('reason')}"]
    s = (f"- control variate (the copy arm's floor on the same seed as covariate; ended runs): real mean floor {num(cv['real_mean_paired'])} "
         f"(SE {num(cv['raw_se'])}) raw and {num(cv['mean_cv'])} (SE {num(cv['se_cv'])}) adjusted on {n_(cv['pairs'])} pairs "
         f"(all {n_(rl['ended'])} ended runs: {num(rl['mean_floor'])}, SE {num(rl['mean_floor_se'])})")
    if cv.get("rho") is not None:
        s += (f"; seed correlation rho {num(cv['rho'], 3)}, slope {num(cv['beta'], 3)}; implied saving 1 - rho^2 = {num(cv['saving'], 3)} of the "
              f"variance ({pct(round(1000 * cv['rho'] ** 2), 1000)} fewer real runs for the same SE) with the copy mean known exactly "
              f"(SE then {num(cv['se_cv_known_copy_mean'])})")
    L = [s + f". {cv['note'][0].upper() + cv['note'][1:]}."]
    p = cv.get("power")
    if p:
        h, o = p["half_floor"], p["one_floor"]
        L.append(f"- real runs a night needs to see a change (two nights of fresh seeds compared, 80% power, 5% level, sd {num(p['sd_floor'])}): "
                 f"half a floor {n_(h['raw'])} raw, {n_(h['adjusted_this_design'])} adjusted as run, {n_(h['adjusted_copy_mean_known'])} with the "
                 f"copy mean known exactly; one floor {n_(o['raw'])}, {n_(o['adjusted_this_design'])}, {n_(o['adjusted_copy_mean_known'])}")
    return L


def progress_lines(rep: dict) -> list[str]:
    """The progress score: each measure with its SE, then its difference against the previous night and the previous generation
    pooled, each with SE and z (unpaired: the nights play fresh seed blocks)."""
    pr = rep["progress"]
    L = [f"Progress score (ended runs; value (SE); difference against each base (SE, z); {pr['unit_note']}):"]
    bases = [(k, tag) for k, tag in (("previous_night", "previous night"), ("previous_generation_pooled", "previous generation pooled"))]
    for key, label, unit, _field in PROGRESS:
        m = pr["measures"][key]
        d = 2 if unit == "floors" else 1
        s = f"- {label}: {num(m['value'], d)} (SE {num(m['se'], d)})"
        for bkey, tag in bases:
            b = pr[bkey]
            if b is None:
                s += f"; against the {tag}: none"
                continue
            x = b["diffs"][key]
            s += (f"; against the {tag} ({'+'.join(dt[5:] for dt in b['nights']) if len(b['nights']) < 4 else str(len(b['nights'])) + ' nights'}, "
                  f"generation {b['generation']}, {n_(b['base_runs'])} runs) {sgn(x['diff'], d)} (SE {num(x['se'], d)}, z {sgn(x['z'], 1)})")
        L.append(s)
    if not pr["measures"]["boss_recorded"]:
        L.append("- this night's rows did not record the boss fights (runs past floor 17 carry no Act 1 boss entry): its boss measures are unknown")
    for bkey, tag in bases:
        if pr[bkey] is not None and not pr[bkey]["base_boss_recorded"]:
            L.append(f"- the {tag} did not record the boss fights (runs past floor 17 carry no Act 1 boss entry): boss differences against it are unknown")
    return L


def edition_figures(rep: dict) -> str:
    nt, rl, em, lk, pa, cm = rep["night"], rep["real"], rep["emu"], rep["lockstep"], rep["paired"], rep["comparison"]
    L = [f"Edition figures: night {nt['date']} ({nt['agent']}, generation {nt['generation']}), from morning_report.py", ""]
    L.append(f"- {rep['act2_headline']}")
    if rep.get("confirmation"):
        L.append(f"- {confirmation_text(rep['confirmation'])}")
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
    L += control_variate_lines(rep)
    L += chance_lines(rep)
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
        L.append(f"- D11C proof: {rank_text('Strike', g['d11c']['Strike']['rank'])}, {rank_text('Defend', g['d11c']['Defend']['rank'])}, together "
                 f"{100 * g['d11c_share']:.1f}% of the weight")
    L.append(f"- {rep['ledger']['line']}")
    L += [""] + progress_lines(rep)
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
# means and rates within the report's own rounding to four decimals). The second path also recomputes the control variate (the
# pairs' correlation and slope by statistics.correlation / linear_regression, the adjusted mean and its SEs from explicit
# residuals) and the progress score (each measure and its differences against the previous night and the previous generation
# pooled, found by its own scan of the earlier nights' folders); figures the report rounds to three decimals (points, z) are
# compared to within half of that rounding.
CHECK_TOL = 6e-5
CHECK_TOL_3 = 6e-4


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


def _boss_of_act(row: dict, act: int) -> tuple[bool, bool]:
    """(reached, killed) for the boss of 0-based act `act`: any `boss_damage_acts` entry for it; killed when its fraction is full."""
    fractions = [e[1] for e in (row.get("boss_damage_acts") or []) if isinstance(e, (list, tuple)) and len(e) >= 2 and e[0] == act]
    return bool(fractions), bool(fractions) and max(fractions) >= 1.0


def _act1_boss(row: dict) -> tuple[bool, bool]:
    """(reached, killed) for the Act 1 boss."""
    return _boss_of_act(row, 0)


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
    by_seed: dict[str, float] = {}  # seed -> floor of its last ended row
    act2 = [0, 0]  # Act 2 boss reached, killed
    past = gap = 0  # ended runs past the Act 1 boss floor, and those of them with no Act 1 boss entry
    wins = 0
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
            by_seed[row.get("seed")] = float(row["floor"])
            if row["floor"] > ACT1_BOSS_FLOOR:
                past += 1
                gap += 0 if r else 1
            r2, k2 = _boss_of_act(row, 1)
            act2[0] += r2
            act2[1] += k2
            wins += 1 if (row.get("end") == "win" or row.get("win") is True) else 0
    n = len(floors)
    return {"seeds": seeds, "ended": n, "crash_rows": crash_rows, "kinds": dict(kinds), "boss": boss, "ended_seq": ended_seq,
            "mean_ended": math.fsum(floors) / n if n else None,
            "mean_counted": math.fsum(floors) / (n + crash_rows) if n + crash_rows else None,
            "act1_reached": reached, "act1_killed": killed,
            "killed_of_runs": killed / n if n else None, "killed_of_reached": killed / reached if reached else None,
            "floors": floors, "by_seed": by_seed, "act2_reached": act2[0], "act2_killed": act2[1], "wins": wins,
            "past": past, "gap": gap}


# -- the chance covariate by a second route: its own log reader, set-merging for the variants, per-cell lists of floors, and the
# regression by the standard library; it shares no function with the section above.
CHANCE_NAMES = {
    "runs_used": "chance covariate: runs used (ended, in the game-log copy)",
    "draws": "chance covariate: draws",
    "unknown_draws": "chance covariate: draws the table does not know",
    "table_runs": "chance covariate: runs that value the draws",
    "odds_runs": "chance covariate: runs that give the odds",
    "raw_mean": "chance covariate: mean floor, raw",
    "raw_se": "chance covariate: SE of the raw mean floor",
    "beta": "chance covariate: slope of the floor on the correction",
    "rho": "chance covariate: correlation of the floor with the correction",
    "share_left": "chance covariate: share of the variance left (1 - rho^2)",
    "mean_correction": "chance covariate: mean of the correction",
    "corrected_mean": "chance covariate: mean floor, corrected",
    "corrected_se": "chance covariate: SE of the corrected mean floor",
    "aivat_se": "chance covariate: SE of the plain AIVAT form (floor minus correction)",
}


def _chance_figures_first(rep: dict) -> dict:
    """CHANCE_NAMES figures as the report's chance block holds them (none when the night was not measured)."""
    cc = rep["chance_covariate"]
    if not cc.get("available"):
        return {}
    out = {name: cc.get(key) for key, name in CHANCE_NAMES.items() if key != "mean_correction"}
    out[CHANCE_NAMES["mean_correction"]] = cc["odds_check"]["mean_correction"]
    return out


def _read_draws_second(logs: Path) -> dict[str, list[str]]:
    """seed -> the encounter ids of its combat rooms in order, by a line scan of a game-log copy (a run ends at its `ended:` line)."""
    out: dict[str, list[str]] = {}
    for fn in sorted(logs.glob("*.log")):
        rooms: list[str] = []
        for line in fn.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("[referee] run decision 0 "):
                rooms = []
            elif line.startswith("[INFO] Creating NCombatRoom") and "encounter=" in line:
                name = ""
                for ch in line.split("encounter=", 1)[1]:
                    if not (ch.isupper() or ch.isdigit() or ch == "_"):
                        break
                    name += ch
                rooms.append(name)
            elif line.startswith("[referee] run ") and " ended: " in line:
                out[line.split()[2]] = rooms
                rooms = []
    return out


def _draws_second(rooms: list[str]) -> list[tuple[int, str, str]]:
    """(act, pool, encounter) of the draws among a run's rooms; an event's fight is no draw, a boss closes the act."""
    out, act = [], 1
    for name in rooms:
        if not name.endswith("_EVENT_ENCOUNTER"):
            pool = "boss" if name.endswith("_BOSS") else "elite" if name.endswith("_ELITE") else "weak" if name.endswith("_WEAK") else "normal"
            out.append((act, pool, name))
        if name.endswith("_BOSS"):
            act += 1
    return out


def _night_runs_second(folder: Path, agent: str, logs_root: Path) -> list[tuple[list[tuple[int, str, str]], float]] | None:
    """The night's (draws, final floor) of every ended real run in its game-log copy; None when it has no copy."""
    logs = logs_root / f"w5-night-{folder.name.replace('-', '')}-stdout"
    if not logs.is_dir() or not any(logs.glob("*.log")):
        return None
    floors = {}
    for row in _stream_rows(folder / agent / "runs.jsonl"):
        if row.get("ev") == "end" and row.get("seed"):
            floors[row["seed"]] = float(row["floor"])
    rooms = _read_draws_second(logs)
    return [(_draws_second(rooms[sd]), floors[sd]) for sd in sorted(rooms) if sd in floors]


def _chance_second_path(night: Path, agent: str, logs_root: Path | None) -> dict:
    """CHANCE_NAMES figures for `night`: the previous generation's nights value the draws, every earlier night with a copy gives the
    odds; {} when the night has no copy, no valuing night exists or fewer than three runs are left."""
    if logs_root is None:
        return {}
    own = _night_runs_second(night, agent, logs_root)
    if not own or len(own) < 3:
        return {}
    gen = int(agent[1:])
    earlier: list[tuple[Path, str, int]] = []
    for folder in sorted(p for p in night.parent.iterdir() if p.is_dir() and DATE_RE.match(p.name) and p.name < night.name):
        for sub in sorted(q.name for q in folder.iterdir() if q.is_dir() and re.fullmatch(r"g\d+", q.name) and (q / "runs.jsonl").is_file()):
            earlier.append((folder, sub, int(sub[1:])))
    below = sorted({g for _f, _a, g in earlier if g < gen})
    if not below:
        return {}
    value_runs, odds_runs = [], []
    for folder, sub, g in earlier:
        runs = _night_runs_second(folder, sub, logs_root)
        if runs is None:
            continue
        odds_runs += runs
        if g == below[-1]:
            value_runs += runs
    if not value_runs:
        return {}
    # variants: encounters met in one act of one run belong together; groups merge when they share an encounter
    group_of: dict[tuple[int, str], int] = {}
    next_id = 0
    for draws, _floor in value_runs + odds_runs:
        for act in sorted({a for a, _p, _e in draws}):
            keys = {(act, e) for a, _p, e in draws if a == act}
            ids = {group_of[k] for k in keys if k in group_of}
            gid = min(ids) if ids else next_id
            next_id += 0 if ids else 1
            for k, v in list(group_of.items()):
                if v in ids:
                    group_of[k] = gid
            for k in keys:
                group_of[k] = gid
    name_of_group: dict[int, str] = {}
    for (a, e), gid in group_of.items():
        name_of_group[gid] = min(name_of_group.get(gid, e), e)
    variant = {k: name_of_group[v] for k, v in group_of.items()}

    def value_of(floors: list[float], mean_all: float) -> float:
        return statistics.fmean(floors) if len(floors) >= MIN_CELL else mean_all

    v_floors: dict[tuple[int, str], list[float]] = defaultdict(list)  # (act, variant) -> floor of each run that played it
    c_floors: dict[tuple[int, str, str, str], list[float]] = defaultdict(list)  # (act, variant, pool, enc) -> floors of its draws
    for draws, floor in value_runs:
        for act in sorted({a for a, _p, _e in draws}):
            v_floors[(act, variant[(act, next(e for a, _p, e in draws if a == act))])].append(floor)
        for act, pool, enc in draws:
            c_floors[(act, variant[(act, enc)], pool, enc)].append(floor)
    v_odds: Counter = Counter()
    c_odds: Counter = Counter()
    for draws, _floor in odds_runs:
        for act in sorted({a for a, _p, _e in draws}):
            v_odds[(act, variant[(act, next(e for a, _p, e in draws if a == act))])] += 1
        for act, pool, enc in draws:
            c_odds[(act, variant[(act, enc)], pool, enc)] += 1
    act_mean = {act: statistics.fmean([f for (a, _v), fs in v_floors.items() if a == act for f in fs]) for act in {a for a, _v in v_floors}}
    v_value = {k: value_of(fs, act_mean[k[0]]) for k, fs in v_floors.items()}
    for k in v_odds:  # a variant only the odds runs met has no value of its own: the act's mean (an act no valuing run met has none)
        if k[0] in act_mean:
            v_value.setdefault(k, act_mean[k[0]])
    pool_mean: dict[tuple[int, str, str], float] = {}
    for pk in {(a, v, p) for (a, v, p, _e) in c_floors}:
        pool_mean[pk] = statistics.fmean([f for k, fs in c_floors.items() if k[:3] == pk for f in fs])
    c_value = {k: value_of(fs, pool_mean[k[:3]]) for k, fs in c_floors.items()}
    for k in c_odds:
        if k[:3] in pool_mean:
            c_value.setdefault(k, pool_mean[k[:3]])
    n_odds = len(odds_runs)
    ys, cs, draws_n, unknown_n = [], [], 0, 0
    for draws, floor in own:
        total = 0.0
        first_variant: dict[int, str] = {}
        for act, _p, enc in draws:
            if act not in first_variant and (act, enc) in variant and (act, variant[(act, enc)]) in v_value:
                first_variant[act] = variant[(act, enc)]
        for act, v in first_variant.items():
            keys = [k for k in v_value if k[0] == act]
            w = {k: v_odds[k] for k in keys} if any(v_odds[k] for k in keys) else {k: len(v_floors.get(k, ())) for k in keys}
            total += v_value[(act, v)] - sum(w[k] * v_value[k] for k in keys) / sum(w.values())
        seen: dict[tuple[int, str], set[str]] = defaultdict(set)
        for act, pool, enc in draws:
            draws_n += 1
            if act not in first_variant or (act, first_variant[act], pool, enc) not in c_value:
                unknown_n += 1
                continue
            pk = (act, first_variant[act], pool)
            members = [k for k in c_value if k[:3] == pk]
            use_odds = any(c_odds[k] for k in members)
            w = {k: (c_odds[k] if use_odds else len(c_floors.get(k, ()))) for k in members}
            rest = [k for k in members if k[3] not in seen[(act, pool)] and w[k] > 0]
            seen[(act, pool)].add(enc)
            if not rest:
                unknown_n += 1
                continue
            total += c_value[pk + (enc,)] - sum(w[k] * c_value[k] for k in rest) / sum(w[k] for k in rest)
        ys.append(floor)
        cs.append(total)
    n = len(ys)
    out = {name: None for name in CHANCE_NAMES.values()}
    out[CHANCE_NAMES["runs_used"]], out[CHANCE_NAMES["draws"]], out[CHANCE_NAMES["unknown_draws"]] = n, draws_n, unknown_n
    out[CHANCE_NAMES["table_runs"]], out[CHANCE_NAMES["odds_runs"]] = len(value_runs), n_odds
    my, mc = statistics.fmean(ys), statistics.fmean(cs)
    out[CHANCE_NAMES["raw_mean"]], out[CHANCE_NAMES["raw_se"]] = my, statistics.stdev(ys) / math.sqrt(n)
    out[CHANCE_NAMES["mean_correction"]] = mc
    var_c = statistics.variance(cs)
    diff = [a - b for a, b in zip(ys, cs)]
    out[CHANCE_NAMES["aivat_se"]] = math.sqrt(statistics.variance(diff) / n + var_c / n_odds)
    if var_c <= 0.0:
        out[CHANCE_NAMES["corrected_mean"]], out[CHANCE_NAMES["corrected_se"]] = my, out[CHANCE_NAMES["raw_se"]]
        out[CHANCE_NAMES["share_left"]] = 1.0
        return out
    fit = statistics.linear_regression(cs, ys)
    resid = [b - (fit.intercept + fit.slope * a) for a, b in zip(cs, ys)]
    s2 = math.fsum(r * r for r in resid) / (n - 2)
    out[CHANCE_NAMES["beta"]] = fit.slope
    out[CHANCE_NAMES["corrected_mean"]] = my - fit.slope * mc
    out[CHANCE_NAMES["corrected_se"]] = math.sqrt(s2 / n + fit.slope ** 2 * var_c / n_odds)
    if statistics.pvariance(ys) > 0.0:
        rho = statistics.correlation(cs, ys)
        out[CHANCE_NAMES["rho"]], out[CHANCE_NAMES["share_left"]] = rho, 1.0 - rho * rho
    return out


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
    out["SE of mean floor, ended, real"] = statistics.stdev(real["floors"]) / math.sqrt(real["ended"]) if real["ended"] >= 2 else None
    out.update(_cv_second_path(real["by_seed"], emu["by_seed"]))
    out.update(_progress_second_path(night, agent, real))
    return out


# -- the control variate by a second route: the standard library's correlation and least-squares fit, residuals written out
CV_NAMES = {
    "pairs": "control variate: pairs ended on both arms",
    "copy_runs": "control variate: copy runs ended (all seeds)",
    "extra_copy_runs": "control variate: copy runs beyond the pairs",
    "beta": "control variate: slope of the real floor on the copy floor (beta)",
    "rho": "control variate: seed correlation (rho)",
    "sd_floor": "control variate: SD of the real floors (the pairs)",
    "variance_factor": "control variate: share of the variance left at this design",
    "real_mean_paired": "control variate: mean floor, real, raw (the pairs)",
    "raw_se": "control variate: SE of the raw mean floor (the pairs)",
    "mean_cv": "control variate: mean floor, real, adjusted",
    "se_cv": "control variate: SE of the adjusted mean floor",
    "se_cv_known_copy_mean": "control variate: SE with the copy mean known exactly",
    "saving": "control variate: implied saving (1 - rho^2)",
}


POWER_NAMES = {(key, field): f"control variate: runs a night needs to see {what}, {how}"
               for key, what in (("half_floor", "half a floor"), ("one_floor", "one floor"))
               for field, how in (("raw", "raw"), ("adjusted_this_design", "adjusted as run"),
                                  ("adjusted_copy_mean_known", "adjusted, copy mean known"),
                                  ("vs_fixed_reference_raw", "raw, against a fixed reference"))}
Z_TWO_SIDED_5_POWER_80 = 1.959963984540054 + 0.8416212335729143  # written out; the report takes it from statistics.NormalDist


def _cv_second_path(real_by_seed: dict[str, float], emu_by_seed: dict[str, float]) -> dict:
    """CV_NAMES figures from the two arms' floors by seed. Fewer than three pairs gives counts only; a copy arm whose floors do not
    vary gives the raw mean and SE (no slope)."""
    seeds = sorted(set(real_by_seed) & set(emu_by_seed))
    y = [real_by_seed[sd] for sd in seeds]
    x = [emu_by_seed[sd] for sd in seeds]
    x_all = list(emu_by_seed.values())
    n, big_n = len(seeds), len(x_all)
    out = {name: None for name in list(CV_NAMES.values()) + list(POWER_NAMES.values())}
    out[CV_NAMES["pairs"]], out[CV_NAMES["copy_runs"]], out[CV_NAMES["extra_copy_runs"]] = n, big_n, max(0, big_n - n)
    if n < 3:
        return out
    my, mx, mxa = statistics.fmean(y), statistics.fmean(x), statistics.fmean(x_all)
    raw_se = statistics.stdev(y) / math.sqrt(n)
    out[CV_NAMES["real_mean_paired"]], out[CV_NAMES["raw_se"]] = my, raw_se
    sd_y = statistics.stdev(y)
    out[CV_NAMES["sd_floor"]] = sd_y

    def runs(delta: float, factor: float = 1.0, nights: int = 2) -> int:  # 2 (z sd / delta)^2 x share of variance left, rounded up
        return math.ceil(nights * factor * (Z_TWO_SIDED_5_POWER_80 * sd_y / delta) ** 2)

    for key, delta in (("half_floor", 0.5), ("one_floor", 1.0)):
        out[POWER_NAMES[(key, "raw")]] = runs(delta)
        out[POWER_NAMES[(key, "vs_fixed_reference_raw")]] = runs(delta, nights=1)
    if statistics.pvariance(x) <= 0.0:
        out[CV_NAMES["mean_cv"]], out[CV_NAMES["se_cv"]], out[CV_NAMES["se_cv_known_copy_mean"]] = my, raw_se, raw_se
        return out
    fit = statistics.linear_regression(x, y)
    beta, alpha = fit.slope, fit.intercept
    resid = [b - (alpha + beta * a) for a, b in zip(x, y)]
    s2 = math.fsum(r * r for r in resid) / (n - 2)
    var_all = statistics.variance(x_all)
    out[CV_NAMES["beta"]] = beta
    out[CV_NAMES["mean_cv"]] = my - beta * (mx - mxa)
    out[CV_NAMES["se_cv"]] = math.sqrt(s2 / n + beta * beta * var_all / big_n)
    out[CV_NAMES["se_cv_known_copy_mean"]] = math.sqrt(s2 / n)
    if statistics.pvariance(y) > 0.0:
        rho = statistics.correlation(x, y)
        out[CV_NAMES["rho"]], out[CV_NAMES["saving"]] = rho, 1.0 - rho * rho
        out[CV_NAMES["variance_factor"]] = (1.0 - rho * rho) + rho * rho * n / big_n
        for key, delta in (("half_floor", 0.5), ("one_floor", 1.0)):
            out[POWER_NAMES[(key, "adjusted_this_design")]] = runs(delta, out[CV_NAMES["variance_factor"]])
            out[POWER_NAMES[(key, "adjusted_copy_mean_known")]] = runs(delta, 1.0 - rho * rho)
    return out


# -- the progress score by a second route: the earlier nights are found by a scan of the folders and pooled from their rows
def _prog_name(label: str, unit: str, what: str) -> str:
    return f"progress: {label}{' (points)' if unit == 'points' else ''}, {what}"


BASE_TAGS = (("previous_night", "previous night"), ("previous_generation_pooled", "previous generation pooled"))


def _pool_second(parts: list[dict]) -> dict:
    return {"floors": [f for q in parts for f in q["floors"]],
            **{k: sum(q[k] for q in parts) for k in ("act1_reached", "act1_killed", "act2_reached", "act2_killed", "wins", "past", "gap")}}


def _boss_known_second(st: dict) -> bool:
    return st["past"] < MIN_CELL or st["gap"] / st["past"] <= BOSS_GAP_MAX


def _rates_second(st: dict) -> dict[str, tuple[int, int]]:
    n = len(st["floors"])
    return {"act2_of_runs": (st["act2_killed"], n), "act1_reach": (st["act1_reached"], n),
            "act1_kill_of_reached": (st["act1_killed"], st["act1_reached"]),
            "act2_reach": (st["act2_reached"], n), "act2_kill_of_reached": (st["act2_killed"], st["act2_reached"]),
            "wins": (st["wins"], n)}


def _bases_second(night: Path, agent: str) -> dict[str, dict | None]:
    """The previous night (the newest earlier date holding a real arm; its arms pooled) and the previous generation pooled (the
    arms of the highest generation below this one, every night), as pooled row sums; None when there is no such pool."""
    m = re.fullmatch(r"g(\d+)", agent)
    gen = int(m.group(1)) if m else 0
    arms: list[tuple[str, int, dict]] = []
    try:
        folders = sorted(night.parent.iterdir())
    except OSError:
        folders = []
    for d in folders:
        if not (d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name) and d.name < night.name):
            continue
        for a in sorted(d.iterdir()):
            ma = re.fullmatch(r"g(\d+)", a.name)
            if a.is_dir() and ma and (a / "runs.jsonl").is_file():
                arms.append((d.name, int(ma.group(1)), _arm_second_path(a / "runs.jsonl", True)))
    out: dict[str, dict | None] = {"previous_night": None, "previous_generation_pooled": None}
    if arms:
        last = max(a[0] for a in arms)
        out["previous_night"] = _pool_second([a[2] for a in arms if a[0] == last])
        below = [a[1] for a in arms if a[1] < gen]
        if below:
            out["previous_generation_pooled"] = _pool_second([a[2] for a in arms if a[1] == max(below)])
    return out


def _value_second(st: dict, key: str) -> tuple[float | None, float | None]:
    """(value, SE) of one progress measure over a pool's ended runs: the mean floor in floors, a rate in points."""
    if key == "mean_floor":
        fl = st["floors"]
        return (statistics.fmean(fl) if fl else None, statistics.stdev(fl) / math.sqrt(len(fl)) if len(fl) >= 2 else None)
    k, n = _rates_second(st)[key]
    if not n or (key != "wins" and not _boss_known_second(st)):
        return None, None
    p = k / n
    return 100.0 * p, 100.0 * math.sqrt(p * (1.0 - p) / n)


def _diff_second(cur: dict, base: dict, key: str) -> tuple[float | None, float | None, float | None]:
    """(difference, SE, z) of one measure, current pool minus base pool, unpaired."""
    if key == "mean_floor":
        a, b = cur["floors"], base["floors"]
        if len(a) < 2 or len(b) < 2:
            return None, None, None
        d = statistics.fmean(a) - statistics.fmean(b)
        se = math.sqrt(statistics.variance(a) / len(a) + statistics.variance(b) / len(b))
        return d, se, (d / se if se else None)
    (k1, n1), (k2, n2) = _rates_second(cur)[key], _rates_second(base)[key]
    if not n1 or not n2 or (key != "wins" and not (_boss_known_second(cur) and _boss_known_second(base))):
        return None, None, None
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt(p1 * (1.0 - p1) / n1 + p2 * (1.0 - p2) / n2)
    return 100.0 * (p1 - p2), 100.0 * se, ((p1 - p2) / se if se else None)


def _progress_second_path(night: Path, agent: str, real: dict) -> dict:
    cur = _pool_second([real])
    bases = _bases_second(night, agent)
    out: dict = {}
    for key, label, unit, _field in PROGRESS:
        out[_prog_name(label, unit, "value")], out[_prog_name(label, unit, "SE")] = _value_second(cur, key)
        for bkey, tag in BASE_TAGS:
            names = [_prog_name(label, unit, f"against {tag}, {w}") for w in ("difference", "SE", "z")]
            vals = _diff_second(cur, bases[bkey], key) if bases[bkey] is not None else (None, None, None)
            out.update(zip(names, vals))
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
    out["SE of mean floor, ended, real"] = rep["real"]["mean_floor_se"]
    cv = rep["control_variate"]
    for key, name in CV_NAMES.items():
        out[name] = cv.get(key)
    for (key, field), name in POWER_NAMES.items():
        out[name] = ((cv.get("power") or {}).get(key) or {}).get(field)
    pr = rep["progress"]
    for key, label, unit, _field in PROGRESS:
        m = pr["measures"][key]
        out[_prog_name(label, unit, "value")], out[_prog_name(label, unit, "SE")] = m["value"], m["se"]
        for bkey, tag in BASE_TAGS:
            d = ((pr[bkey] or {}).get("diffs") or {}).get(key) or {}
            for w, f in (("difference", "diff"), ("SE", "se"), ("z", "z")):
                out[_prog_name(label, unit, f"against {tag}, {w}")] = d.get(f)
    out.update(_chance_figures_first(rep))
    return out


def _same(a, b, tol: float = CHECK_TOL) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    return abs(float(a) - float(b)) <= tol


def _tol_of(figure: str) -> float:
    """The report rounds points and z to three decimals, everything else to four."""
    return CHECK_TOL_3 if "(points)" in figure or figure.endswith(", z") else CHECK_TOL


def check_rows(first: dict, second: dict) -> list[dict]:
    """One row per figure named by either path: {figure, first, second, ok}. A figure only one path has is a mismatch."""
    names = list(first) + [k for k in second if k not in first]
    return [{"figure": k, "first": first.get(k), "second": second.get(k),
             "ok": k in first and k in second and _same(first[k], second[k], _tol_of(k))} for k in names]


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


def run_check(night: Path, agent: str | None, lab: Path, now: datetime, rep: dict | None = None) -> tuple[str, int]:
    """(text, exit code): the report's figures against the second path's; 1 when any differ.
    `rep` is a report already built for the night (main builds one for every mode so --out can write it); else one is built here."""
    logs_root = lab.parent.parent / "logs"
    if rep is None:
        cand = logs_root / f"w5-night-{night.name.replace('-', '')}-stdout"
        rep = build_report(night, agent, lab, cand if cand.is_dir() else None, "none", None, now, logs_root=logs_root)
    agent = rep["night"]["agent"]
    second = independent_figures(night, agent)
    second.update(_chance_second_path(night, agent, logs_root))  # the game-log copies: the chance covariate, when the night has one
    rows = check_rows(report_check_figures(rep), second)
    return check_text(night, agent, rows), (1 if any(not r["ok"] for r in rows) else 0)


# ---------------------------------------------------------------------------------------------------- CLI
def write_report_files(out: Path, rep: dict) -> str:
    """The --out files of the night's report (every mode writes them): the names written, comma-joined."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "morning_report.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    (out / "handoff_line.md").write_text(handoff_line(rep), encoding="utf-8")
    (out / "edition_figures.md").write_text(edition_figures(rep), encoding="utf-8")
    wrote = "morning_report.json, handoff_line.md, edition_figures.md"
    if rep["chance_covariate"].get("available"):  # the table the night's correction used, fixed before the night, beside the report
        (out / "chance_table.json").write_text(json.dumps(rep["chance_covariate"]["table"], indent=1) + "\n", encoding="utf-8")
        wrote += ", chance_table.json"
    return wrote


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The night's morning report: figures, the HANDOFF line and the edition list.")
    ap.add_argument("night", type=Path, help="a lab night folder, e.g. LAB/nightly/2026-11-03")
    ap.add_argument("--agent", help="the real arm's folder (g<N>) when the night holds more than one")
    ap.add_argument("--lab", type=Path, help="the lab folder (default: two levels above the night)")
    ap.add_argument("--agent-root", type=Path, help="the agent folder holding promotions.tsv (default: <lab>/../agent)")
    ap.add_argument("--logs", type=Path, help="the copy of the real arm's workers' game logs "
                    "(default: <lab>/../../logs/w5-night-<yyyymmdd>-stdout when it exists)")
    ap.add_argument("--winlog", default=None, help="auto (Get-WinEvent; the default), none (the default with --check), or a JSON file of events")
    ap.add_argument("--usage", help="the usage readout to print in the line, e.g. '84%% all / 59%% Fable at 00:21Z'")
    ap.add_argument("--now", help="ISO time to stamp the line with (default: now)")
    ap.add_argument("--out", type=Path, help="folder for morning_report.json, handoff_line.md and edition_figures.md "
                    "(every mode writes them; chance_table.json too when the night has one)")
    ap.add_argument("--chance-read", action="store_true", help="read the night block's chance covariate (stage 1) on every night under "
                    "the night folder's parent: the table of raw SE, corrected SE and 1 - rho^2 per night under each table rule "
                    "(with --out: chance_reading.md and .json)")
    ap.add_argument("--check", action="store_true", help="recompute the headline figures by a second, independent code path "
                    "over the rows and print both with MATCH / MISMATCH; exit 1 on any mismatch")
    a = ap.parse_args(argv)
    night = a.night.resolve()
    if not night.is_dir():
        raise SystemExit(f"{a.night}: not a folder")
    lab = (a.lab or night.parent.parent).resolve()
    logs_root = lab.parent.parent / "logs"
    now = parse_utc(a.now) if a.now else datetime.now(timezone.utc)

    def build() -> dict:
        logs = a.logs
        if logs is None:
            cand = logs_root / f"w5-night-{night.name.replace('-', '')}-stdout"
            logs = cand if cand.is_dir() else None
        return build_report(night, a.agent, lab, logs, a.winlog or ("none" if a.check else "auto"), a.usage, now, logs_root=logs_root,
                            agent_root=a.agent_root.resolve() if a.agent_root else None)

    def wrote_line(wrote: str) -> None:
        print(f"wrote {wrote} in {a.out.name}/")

    if a.check:
        rep = build()
        text, code = run_check(night, a.agent, lab, now, rep)
        print(text)
        if a.out:
            wrote_line(write_report_files(a.out, rep))
        return code
    if a.chance_read:
        reading = chance_reading(night.parent, logs_root)
        text = chance_reading_md(reading)
        print(text)
        if a.out:
            a.out.mkdir(parents=True, exist_ok=True)
            (a.out / "chance_reading.md").write_text(text + "\n", encoding="utf-8")
            slim = {rule: {"nights": [{k: v for k, v in r.items() if k != "table"} for r in blk["nights"]], "pooled": blk["pooled"]}
                    for rule, blk in reading["by_rule"].items()}
            (a.out / "chance_reading.json").write_text(json.dumps({"nights": reading["nights"], "by_rule": slim}, indent=1) + "\n",
                                                       encoding="utf-8")
            wrote = "chance_reading.md, chance_reading.json"
            try:  # the night's own report beside the reading, when its block has closed
                wrote = write_report_files(a.out, build()) + ", " + wrote
            except SystemExit as e:
                print(f"report files not written: {e}")
            wrote_line(wrote)
        return 0
    rep = build()
    if a.out:
        wrote = write_report_files(a.out, rep)
        print(edition_figures(rep))
        wrote_line(wrote)
    else:
        print(handoff_line(rep))
        print(edition_figures(rep))
    return 1 if any(c["ok"] is False for c in rep["cross_checks"]) else 0


if __name__ == "__main__":
    sys.exit(main())
