"""The pooled whole-run reading of fight-only swaps (Act 3 week, lane 26; D68 addendum 7 item 1).

The fight loop promotes a new fight network (v4, v5, v6, v7, ...) when it plays about two points better at its test fights. The run judge
then plays the champion with only that network swapped in ("a fight-only swap") against the champion for 2,000 or more paired whole runs.
Read one at a time each such judgement is noise (2,000 pairs read about plus or minus 1.3 first-Act-3-boss passes per 100 runs). Read together
they say whether a better fighter at the test fights makes a better run player at all. This tool reads every such judgement and prints the
rows and the precision-weighted pooled estimate.

WHAT IT READS (all read-only; `--root` is the project folder, default D:/spireline):

  <root>/referee/agent/gen*/candidate-fight-*/        one folder per fight-only swap candidate. A candidate is a fight-only swap when its
        agent.json says `built.swap` = "fight" (the fork's `gen_loop.fight_only_swap`; `rl/gym_wiring.py` writes it when it builds the
        champion with only its fight network replaced); `built.base` names the champion. A candidate folder without that mark is listed
        under the notes and left out. (gen18/candidate-fight-v3 carries the mark too: the 11-18 judgement of fight v3 over gen17's champion,
        under keep rule v2 and the older win-count gate. It is a row; the pooled figure is also printed without the rows not judged under
        keep rule v3, which is the set the 11-24 review read.)
        promotion*.json   the judgement records (`gen_loop` writes one per judgement; a rejected block that is later finished or re-judged
        leaves the earlier file beside the new one, and a build copies its parent's files in). A record counts for a candidate when its
        `cand_sha` is the candidate's fight network (agent.json `built.prior.policy_sha256`); of those the newest `written` is the row's
        judgement, the others are superseded. No such record: the judgement is pending. A record that is not final (`keep_v2.final` false: a
        block stopped early or extended) is shown and left out of the pool, because a block that stopped on a bound is biased away from 0.
        s1.json, s1/results.json, or the record's own `s1`   the boss-door exam (S1: the first Act 3 boss, passes per 100 ARRIVALS).
  <root>/referee/agent/promotions.tsv                 the ledger (`gen_loop.append_promotion`): decision and route of the candidate's last
        row, used to cross-check the record and as the verdict when a record is missing.
  <root>/referee/gym-loop/loop.log                    the gate's own promotion line ("gate cNNNN: stage K ... promote ...: part h +1.11
        points, SE 0.53 ...; part a3 ..."): the gain at the test fights. part h = the 500 Acts 1 and 2 human starts, part a3 = the 414
        Act 3 boss starts; a fighter promoted under rule v4 (v4) has one figure, the human stratum, written as "h".

WHAT IT PRINTS (every figure with its plus or minus 2 SE; "SE" is a standard error):

  per fighter   the gate gain at the test fights; the whole-run first Act 3 boss passes per 100 runs (the candidate's and the champion's
                counts over the pairs, and the paired difference, candidate minus champion, with its SE); the S1 figure (passes per 100
                arrivals) where one was played; the verdict and the route; and the full-carryover reference, S1 gain x the share of runs
                that arrive at that boss, which is what the whole-run effect would be if the gain at the door carried straight into runs.
  pooled        the precision-weighted mean of the whole-run differences (weight 1 / SE squared) with its SE and 2 SE band, the same for
                S1 where rows exist, the full-carryover reference pooled (pooled S1 x pooled arrival share), and one line comparing the
                pooled upper bound with that reference.

WHERE THE WHOLE-RUN FIGURE COMES FROM, in this order: (1) the record's `keep_v2.margins.B3a` (the judge's own paired figure: the SD of the
per-seed differences over the square root of the pairs; a record from the judge of 2026-11-22 on carries it); (2) the paired figure
recomputed from the arms' per-seed rows (`<cand>/arms/<block>-<config>/runs.jsonl` against the champion's) with the judge's strict reading
of "went past the first Act 3 boss" (`keep_v2.went_past`), which is how a record without margins (v4's) is read; (3) never a guess: a
record with neither is listed without a whole-run figure. `--recompute` forces (2) for every row, to check (1) against the rows.

`--json` prints the report for the machine. `--check` sets the known rows against the 11-24 sceptic review's section 3 (v4 +0.5 plus or minus
about 2.0 on 4,000 pairs; v5 -0.25 plus or minus 1.28; v6 -0.85 plus or minus 1.21; pooled about -0.4 plus or minus 0.8) and exits 1 on a
mismatch beyond the rounding of the review's own figure, 2 when a known row is missing.

No seeds, run ids, block names, host names or absolute paths are printed: the rows are named by fighter and by `gen<N>/<folder>`.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_ROOT = Path("D:/spireline")
Z = 2.0  # the margin every figure carries: plus or minus this many SE
S1_MIN = 1.0  # route S's S1: the door gain is at least this many passes per 100 arrivals ...
S1_Z = NormalDist().inv_cdf(1 - 0.005)  # ... and its mean minus this many SE is above 0 (the fork's keep_v2 S1_MIN / S1_Z)
ACT_BOSS_FLOORS = (17, 33, 48)  # the usual floors of the Act 1, Act 2 and first Act 3 bosses (a complete node string names its own)
FIGHT_SWAP = "fight"  # agent.json `built.swap` of a fight-only swap (gen_loop.FIGHT_SWAP)

# The 11-24 sceptic review, section 3: (value, decimals as printed, plus or minus 2 SE, decimals as printed, pairs). `--check` compares.
REVIEW = {
    "v4": (0.5, 1, 2.0, 1, 4000),
    "v5": (-0.25, 2, 1.28, 2, 2000),
    "v6": (-0.85, 2, 1.21, 2, 2000),
}
REVIEW_POOLED = (-0.4, 1, 0.8, 1)  # of v4, v5, v6 only ("about")


# ------------------------------------------------------------------------------------------------------------------ small helpers


def read_json(path: Path) -> dict[str, Any] | None:
    """The JSON object in `path`, or None when the file is missing, unreadable or not an object."""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def num(x: Any) -> float | None:
    """`x` as a finite float, else None (a bool is not a number here)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return float(x) if math.isfinite(x) else None


def sgn(x: float | None, nd: int = 2) -> str:
    return "n/a" if x is None else f"{x:+.{nd}f}"


def with_margin(x: float | None, se: float | None, nd: int = 2) -> str:
    """`+0.50 +/-1.00`: the figure and its plus or minus 2 SE."""
    if x is None:
        return "n/a"
    return f"{x:+.{nd}f} +/-{Z * se:.{nd}f}" if se is not None else f"{x:+.{nd}f} (no margin)"


def rel_dir(path: Any, agent_root: Path) -> str:
    """`gen<N>/<folder>` of a candidate or champion folder named in a record (absolute, or already relative to the agent root)."""
    p = Path(str(path))
    posix = p.as_posix()
    base = agent_root.as_posix().rstrip("/") + "/"
    if posix.lower().startswith(base.lower()):
        return posix[len(base):]
    parts = p.parts
    return "/".join(parts[-2:]) if len(parts) >= 2 else posix


def day(stamp: Any) -> str | None:
    m = re.match(r"(\d{4}-\d\d-\d\d)", str(stamp or ""))
    return m.group(1) if m else None


def precision_pool(items: Iterable[tuple[float, float]]) -> dict[str, float] | None:
    """The precision-weighted mean of (estimate, SE) pairs, weight 1 / SE squared, with its SE (1 / root of the summed weights) and its
    plus or minus 2 SE. A pair with no usable SE (missing or 0) is not in it. None when no pair is usable."""
    used = [(e, s) for e, s in items if s is not None and s > 0 and math.isfinite(s) and math.isfinite(e)]
    if not used:
        return None
    w = [1.0 / (s * s) for _, s in used]
    total = math.fsum(w)
    mean = math.fsum(wi * e for wi, (e, _) in zip(w, used, strict=True)) / total
    se = 1.0 / math.sqrt(total)
    return {"rows": len(used), "estimate": mean, "se": se, "pm2se": Z * se, "lower": mean - Z * se, "upper": mean + Z * se, "weight": total}


# ------------------------------------------------------------------------------------------------------------------ the strict reading of an arm's row


def boss_floors(nodes: Any) -> list[int]:
    """The floors of the run's boss rooms from its node string: the k-th letter is floor k + 2 (floor 1 has no letter)."""
    return [i + 2 for i, ch in enumerate(nodes) if ch == "B"] if isinstance(nodes, str) else []


def complete_nodes(row: Mapping[str, Any]) -> bool:
    nodes = row.get("nodes")
    return isinstance(nodes, str) and int(row.get("floor") or 0) == len(nodes) + 1


def went_past(row: Mapping[str, Any], act: int) -> bool:
    """The judge's strict rule (keep_v2.went_past, 2026-11-19): the run went past the first boss of act `act` (0, 1 or 2 = the first Act 3
    boss). A win went past all of them; a crashed or lost seed none; otherwise the floor is above the boss's floor, which a complete node
    string names and else is the usual 17 / 33 / 48 (and then a boss bar below 1.0 for the act is a lost fight)."""
    if row.get("win"):
        return True
    if row.get("crash") or row.get("lost"):
        return False
    floor = int(row.get("floor") or 0)
    if complete_nodes(row):
        floors = boss_floors(row["nodes"])
        return act < len(floors) and floor > floors[act]
    acts = row.get("boss_damage_acts")
    if isinstance(acts, list):
        for entry in acts:
            if int(entry[0]) == act:
                if entry[1] is None or entry[1] < 1.0:
                    return False
                break
    return floor > ACT_BOSS_FLOORS[act]


def arrived_b3a(row: Mapping[str, Any]) -> bool:
    """Whether the run arrived at the first Act 3 boss (keep_v2.arrived_b3a): a win did; a crashed or lost seed did not; a complete node
    string has a third boss room; any other row reached floor 48."""
    if row.get("win"):
        return True
    if row.get("crash") or row.get("lost"):
        return False
    if complete_nodes(row):
        return len(boss_floors(row["nodes"])) >= 3
    return int(row.get("floor") or 0) >= ACT_BOSS_FLOORS[2]


def read_arm(folder: Path) -> dict[str, Mapping[str, Any]] | None:
    """An arm's rows by seed (the later row of a seed wins, as the judge's pairing does), None when its runs.jsonl is missing or empty."""
    path = folder / "runs.jsonl"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    rows: dict[str, Mapping[str, Any]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict) and r.get("seed") is not None:
            rows[str(r["seed"])] = r
    return rows or None


def paired_b3a(cand_blocks: Sequence[dict[str, Mapping[str, Any]]], base_blocks: Sequence[dict[str, Mapping[str, Any]]]) -> dict[str, Any] | None:
    """The first Act 3 boss passes of two arms over the seeds both played, block by block: counts, the paired difference per 100 runs
    (the mean of the per-seed differences x 100), its SE (SD with n - 1 over the root of n: what the judge's `margins` prints), and the
    arrivals of each arm. None under two pairs."""
    diffs: list[float] = []
    cand = base = arr_c = arr_b = 0
    for c, b in zip(cand_blocks, base_blocks, strict=True):
        for seed in sorted(set(c) & set(b)):
            pc, pb = int(went_past(c[seed], 2)), int(went_past(b[seed], 2))
            diffs.append(100.0 * (pc - pb))
            cand += pc
            base += pb
            arr_c += int(arrived_b3a(c[seed]))
            arr_b += int(arrived_b3a(b[seed]))
    n = len(diffs)
    if n < 2:
        return None
    mean = math.fsum(diffs) / n
    var = math.fsum((x - mean) ** 2 for x in diffs) / (n - 1)
    return {"pairs": n, "cand": cand, "base": base, "diff": mean, "se": math.sqrt(var) / math.sqrt(n), "arrivals_cand": arr_c, "arrivals_base": arr_b}


# ------------------------------------------------------------------------------------------------------------------ the sources


def candidate_dirs(agent_root: Path) -> list[Path]:
    """Every `gen*/candidate-fight-*` folder, in fighter order (v4, v5, ...)."""
    found = [p for p in agent_root.glob("gen*/candidate-fight-*") if p.is_dir()]

    def key(p: Path) -> tuple[int, str]:
        m = re.search(r"-v(\d+)$", p.name)
        return (int(m.group(1)) if m else 10**6, p.parent.name + "/" + p.name)

    return sorted(found, key=key)


def identity(cand_dir: Path, agent_root: Path) -> dict[str, Any] | None:
    """Who the candidate is, or None when it is not marked a fight-only swap (`agent.json` `built.swap`)."""
    meta = read_json(cand_dir / "agent.json")
    built = meta.get("built") if meta else None
    if not isinstance(built, dict) or built.get("swap") != FIGHT_SWAP:
        return None
    prior, base = built.get("prior") or {}, built.get("base") or {}
    why = str(built.get("why") or "")
    m_name = re.search(r"-(v\d+)$", cand_dir.name)
    tag = str(built.get("tag") or "")
    name = m_name.group(1) if m_name else (tag.split("-")[-1] if tag else cand_dir.name)
    m_ck = re.search(r"checkpoint (c\d+)", why)
    m_when = re.search(r"promoted\s*(\d{4}-\d\d-\d\dT[\d:]+Z)", why)
    return {"name": name, "dir": f"{cand_dir.parent.name}/{cand_dir.name}", "path": cand_dir,
            "policy": prior.get("policy_sha256"), "checkpoint": m_ck.group(1) if m_ck else None, "promoted": day(m_when.group(1)) if m_when else None,
            "champion": rel_dir(base.get("dir"), agent_root) if base.get("dir") else None, "champion_policy": base.get("policy_sha256")}


def pick_record(cand_dir: Path, policy: str | None) -> tuple[dict[str, Any] | None, int, int]:
    """(the newest judgement record naming this candidate's fight network, how many older ones it supersedes, how many records in the
    folder name another candidate: a build copies its parent's files in)."""
    mine: list[dict[str, Any]] = []
    other = 0
    for p in sorted(cand_dir.glob("promotion*.json")):
        r = read_json(p)
        if r is None:
            continue
        if policy and r.get("cand_sha") == policy:
            mine.append(r)
        else:
            other += 1
    if not mine:
        return None, 0, other
    mine.sort(key=lambda r: str(r.get("written") or ""))
    return mine[-1], len(mine) - 1, other


def whole_run(rec: Mapping[str, Any], ident: Mapping[str, Any], agent_root: Path, recompute: bool) -> tuple[dict[str, Any] | None, list[str]]:
    """The first Act 3 boss passes per 100 runs of a record: from its margins, else from the arms' rows. (figure or None, notes)"""
    notes: list[str] = []
    cand_dir = Path(ident["path"])
    if not recompute:
        marg = (rec.get("keep_v2") or {}).get("margins") if isinstance(rec.get("keep_v2"), dict) else None
        b = marg.get("B3a") if isinstance(marg, dict) else None
        arr = marg.get("arrivals") if isinstance(marg, dict) else None
        if isinstance(b, dict) and num(b.get("diff")) is not None and num(b.get("se")) is not None and num(marg.get("pairs")):
            return {"source": "record margins", "pairs": int(marg["pairs"]), "cand": b.get("cand"), "base": b.get("base"),
                    "diff": float(b["diff"]), "se": float(b["se"]),
                    "arrivals_cand": arr.get("cand") if isinstance(arr, dict) else None,
                    "arrivals_base": arr.get("base") if isinstance(arr, dict) else None}, notes
    base_agent = (rec.get("base") or {}).get("agent") or {}
    base_dir = agent_root / rel_dir(base_agent.get("dir") or ident.get("champion") or "", agent_root)
    blocks = [str(b["block"]) for b in ((rec.get("pooled") or {}).get("blocks") or []) if isinstance(b, dict) and b.get("block")]
    blocks = blocks or ([str(rec["seed_block"])] if rec.get("seed_block") else [])
    config = str(rec.get("config") or "")
    cand_blocks, base_blocks = [], []
    for blk in blocks:
        c, b2 = read_arm(cand_dir / "arms" / f"{blk}-{config}"), read_arm(base_dir / "arms" / f"{blk}-{config}")
        if c is None or b2 is None:
            notes.append("whole-run figure unavailable: the record holds no margins and an arm's rows are missing")
            return None, notes
        cand_blocks.append(c)
        base_blocks.append(b2)
    fig = paired_b3a(cand_blocks, base_blocks) if blocks else None
    if fig is None:
        notes.append("whole-run figure unavailable: under two pairs")
        return None, notes
    fig["source"] = "arms re-read" if recompute else "arms re-read (the record holds no margins)"
    paired = num(rec.get("paired_seeds"))
    if paired is not None and int(paired) != fig["pairs"]:
        notes.append(f"the arms hold {fig['pairs']} pairs, the record says {int(paired)}")
    return fig, notes


def s1_figure(ident: Mapping[str, Any], rec: Mapping[str, Any] | None) -> tuple[dict[str, Any] | None, list[str]]:
    """The candidate's boss-door exam: from its folder's s1.json, else the record's own `s1`, else s1/results.json's first_boss figure."""
    notes: list[str] = []
    cand_dir = Path(ident["path"])
    sources: list[tuple[str, dict[str, Any] | None]] = [("s1.json", read_json(cand_dir / "s1.json")), ("record", (rec or {}).get("s1") if isinstance((rec or {}).get("s1"), dict) else None)]
    res = read_json(cand_dir / "s1" / "results.json")
    if res and isinstance(res.get("first_boss"), dict):
        fb = res["first_boss"]
        sources.append(("s1/results.json", {"mean": fb.get("points"), "se": fb.get("se_points"), "starts": fb.get("starts"), "pairs": fb.get("pairs"),
                                            "candidate": (res.get("candidate") or {}).get("policy_sha256"),
                                            "complete": fb.get("complete"), "holds": (fb.get("reads") or {}).get("hold")}))
    for label, s in sources:
        if not s or num(s.get("mean")) is None or num(s.get("se")) is None:
            continue
        named = s.get("candidate")
        if named and ident.get("policy") and named != ident["policy"]:
            notes.append(f"{label} names another candidate's network and is not used")
            continue
        if s.get("complete") is False:
            notes.append(f"{label} is an incomplete exam and is not used")
            continue
        mean, se = float(s["mean"]), float(s["se"])
        holds = s.get("holds")
        if holds is None:
            holds = mean >= S1_MIN and mean - S1_Z * se > 0
        return {"gain": mean, "se": se, "pm2se": Z * se, "starts": s.get("starts"), "pairs": s.get("pairs"), "holds": bool(holds)}, notes
    return None, notes


GATE_LINE = re.compile(r"gate (c\d+): stage (\d) \(([^)]*)\) (promote|continue|reject)")
PART = re.compile(r"part (\w+) [\d.]+ / [\d.]+ \(([+-]\d+(?:\.\d+)?) points, SE (\d+(?:\.\d+)?)")
PLAIN = re.compile(r"\(([+-]\d+(?:\.\d+)?) points, SE (\d+(?:\.\d+)?)\)")


def gate_gains(loop_log: Path, checkpoint: str | None) -> list[dict[str, Any]] | None:
    """The gain at the test fights from the gate's own promote line for `checkpoint` (the last one if the loop wrote more): one entry a part,
    {part: "h" or "a3", gain, se, pm2se} in points. A line without parts (rule v4's one human-stratum figure) reads as part "h". None when
    the log or the line is missing."""
    if not checkpoint:
        return None
    try:
        text = loop_log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    found: list[dict[str, Any]] | None = None
    marker = f"gate {checkpoint}: stage "
    for line in text.splitlines():
        if marker not in line:
            continue
        m = GATE_LINE.search(line)
        if not m or m.group(4) != "promote":
            continue
        tail = line[m.end():]
        parts = [{"part": p, "gain": float(g), "se": float(s), "pm2se": Z * float(s)} for p, g, s in PART.findall(tail)]
        if not parts:
            plain = PLAIN.search(tail)
            if plain:
                parts = [{"part": "h", "gain": float(plain.group(1)), "se": float(plain.group(2)), "pm2se": Z * float(plain.group(2))}]
        if parts:
            found = parts
    return found


def read_ledger(agent_root: Path) -> list[dict[str, str]]:
    path = agent_root / "promotions.tsv"
    try:
        with path.open(encoding="utf-8", errors="replace", newline="") as fh:
            return [dict(r) for r in csv.DictReader(fh, delimiter="\t")]
    except OSError:
        return []


def ledger_row(rows: Sequence[Mapping[str, str]], cand_name: str, policy: str | None) -> Mapping[str, str] | None:
    mine = [r for r in rows if r.get("cand_dir") == cand_name and (not r.get("cand_sha") or not policy or r["cand_sha"] == policy)]
    return max(mine, key=lambda r: r.get("written") or "") if mine else None


# ------------------------------------------------------------------------------------------------------------------ the report


def build_row(ident: dict[str, Any], agent_root: Path, loop_log: Path, ledger: Sequence[Mapping[str, str]], recompute: bool) -> dict[str, Any]:
    cand_dir = Path(ident["path"])
    rec, superseded, other = pick_record(cand_dir, ident.get("policy"))
    notes: list[str] = []
    if other:
        notes.append(f"{other} record file(s) in the folder name another candidate's network and are not read")
    if superseded:
        notes.append(f"{superseded} earlier judgement record(s) of this candidate are superseded by the newest")
    row: dict[str, Any] = {"fighter": ident["name"], "candidate": ident["dir"], "champion": ident["champion"], "promoted": ident["promoted"],
                           "judged": day(rec.get("written")) if rec else None, "gate": gate_gains(loop_log, ident.get("checkpoint")),
                           "whole_run": None, "s1": None, "verdict": "pending", "route": "pending", "keep_rule": None, "provisional": False, "carryover": None}
    led = ledger_row(ledger, cand_dir.name, ident.get("policy"))
    if rec:
        verdict = str(rec.get("decision_text") or "").strip() or "unknown"
        route = str((rec.get("decision") or {}).get("route") or "") if isinstance(rec.get("decision"), dict) else ""
        row["verdict"] = verdict
        row["route"] = route or ("none held" if verdict == "rejected" else "-")
        kv = rec.get("keep_v2") if isinstance(rec.get("keep_v2"), dict) else {}
        row["keep_rule"] = "v3" if str(kv.get("rule") or "").startswith("keep-v3") else (str(kv.get("rule") or rec.get("keep_rule") or "") or None)
        fig, wnotes = whole_run(rec, ident, agent_root, recompute)
        notes += wnotes
        if kv.get("final") is False:
            row["provisional"] = True
            notes.append("the record is not final (the block was extended or stopped early): its whole-run figure is shown and not pooled")
        if fig and fig["source"].startswith("arms") and not kv.get("boss_reading"):
            notes.append("the record predates the strict boss reading (2026-11-19); the whole-run figure is the arms' rows read under it")
        if fig:
            pairs = fig["pairs"]
            ac, ab = fig.get("arrivals_cand"), fig.get("arrivals_base")
            fig.update(pm2se=Z * fig["se"], cand_per_100=100.0 * fig["cand"] / pairs if num(fig.get("cand")) is not None else None,
                       base_per_100=100.0 * fig["base"] / pairs if num(fig.get("base")) is not None else None,
                       arrival_share=(ac + ab) / (2.0 * pairs) if num(ac) is not None and num(ab) is not None else None)
            row["whole_run"] = fig
        if led and led.get("decision") and led["decision"] != verdict:
            notes.append(f"the ledger's last row says {led['decision']}, the record says {verdict}")
    elif led:
        row["verdict"] = led.get("decision") or "unknown"
        row["route"] = led.get("route") or "-"
        notes.append("no judgement record: verdict from the ledger")
    else:
        notes.append("no judgement record yet: the whole-run reading is pending")
    s1, snotes = s1_figure(ident, rec)
    notes += snotes
    row["s1"] = s1
    wr = row["whole_run"]
    if s1 and wr and wr.get("arrival_share") is not None:
        share = wr["arrival_share"]
        row["carryover"] = {"estimate": s1["gain"] * share, "se": s1["se"] * share, "pm2se": Z * s1["se"] * share}
    row["notes"] = notes
    return row


def build_report(root: Path, recompute: bool = False) -> dict[str, Any]:
    agent_root = root / "referee" / "agent"
    loop_log = root / "referee" / "gym-loop" / "loop.log"
    ledger = read_ledger(agent_root)
    rows: list[dict[str, Any]] = []
    left_out: list[str] = []
    for d in candidate_dirs(agent_root):
        ident = identity(d, agent_root)
        if ident is None:
            left_out.append(f"{d.parent.name}/{d.name}")
            continue
        rows.append(build_row(ident, agent_root, loop_log, ledger, recompute))
    report: dict[str, Any] = {"unit": "first Act 3 boss passes per 100 runs (door: per 100 arrivals); plus or minus 2 SE", "rows": rows,
                              "left_out": [f"{n}: not marked a fight-only swap in its agent.json" for n in left_out],
                              "pooled": pooled(rows)}
    return report


def pooled(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    whole = [r for r in rows if r.get("whole_run") and not r.get("provisional")]
    wr = precision_pool((r["whole_run"]["diff"], r["whole_run"]["se"]) for r in whole)
    if wr:
        wr["pairs"] = sum(r["whole_run"]["pairs"] for r in whole if r["whole_run"]["se"] and r["whole_run"]["se"] > 0)
        wr["fighters"] = [r["fighter"] for r in whole if r["whole_run"]["se"] and r["whole_run"]["se"] > 0]
    door_rows = [r for r in rows if r.get("s1")]
    door = precision_pool((r["s1"]["gain"], r["s1"]["se"]) for r in door_rows)
    if door:
        door["fighters"] = [r["fighter"] for r in door_rows if r["s1"]["se"] > 0]
        door["starts"] = sum(int(r["s1"]["starts"]) for r in door_rows if r["s1"]["se"] > 0 and num(r["s1"].get("starts")) is not None)
    shared = [r["whole_run"] for r in whole if r["whole_run"].get("arrival_share") is not None]
    share = (math.fsum(w["arrival_share"] * w["pairs"] for w in shared) / sum(w["pairs"] for w in shared)) if shared else None
    carry = None
    if door and share is not None:
        carry = {"estimate": door["estimate"] * share, "se": door["se"] * share, "pm2se": Z * door["se"] * share, "arrival_share": share}
    v3 = [r for r in whole if r.get("keep_rule") == "v3"]
    wr3 = precision_pool((r["whole_run"]["diff"], r["whole_run"]["se"]) for r in v3) if len(v3) < len(whole) else None
    if wr3:
        wr3["pairs"] = sum(r["whole_run"]["pairs"] for r in v3 if r["whole_run"]["se"] and r["whole_run"]["se"] > 0)
        wr3["fighters"] = [r["fighter"] for r in v3 if r["whole_run"]["se"] and r["whole_run"]["se"] > 0]
    out: dict[str, Any] = {"whole_run": wr, "whole_run_keep_v3": wr3, "door": door, "full_carryover": carry, "reading": None, "rows_to_settle": None}
    if wr and carry:
        if wr["upper"] < carry["estimate"]:
            out["reading"] = "excluded: the pooled upper bound is below the full-carryover reference"
        else:
            out["reading"] = "not excluded: the pooled upper bound is not below the full-carryover reference"
        # An extrapolation, not a measurement: rows like the average one so far that would bring 2 SE down to the reference.
        if carry["estimate"] > 0:
            need = (Z / carry["estimate"]) ** 2
            per_row = wr["weight"] / wr["rows"]
            out["rows_to_settle"] = max(0, math.ceil(need / per_row - wr["rows"]))
    return out


# ------------------------------------------------------------------------------------------------------------------ text


def table(header: Sequence[str], body: Sequence[Sequence[str]]) -> list[str]:
    widths = [max(len(str(r[i])) for r in [header, *body]) for i in range(len(header))]
    fmt = lambda r: "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)).rstrip()  # noqa: E731
    return [fmt(header), fmt(["-" * w for w in widths]), *[fmt(r) for r in body]]


def gate_text(gate: Sequence[Mapping[str, Any]] | None) -> str:
    if not gate:
        return "n/a"
    return "; ".join(f"{g['part']} {with_margin(g['gain'], g['se'])}" for g in gate)


def render(report: Mapping[str, Any]) -> str:
    rows = report["rows"]
    L: list[str] = ["Pooled reading of fight-only swaps (every figure plus or minus 2 SE)", ""]
    L.append("Per fighter: gain at the gate's test fights (points; h = Acts 1 and 2 human starts, a3 = Act 3 boss starts), the boss-door exam (S1, "
             "first Act 3 boss, passes per 100 arrivals), the judge's verdict.")
    L += table(["fighter", "promoted", "judged", "champion", "gate gain (points)", "door S1 per 100 arrivals", "verdict", "route"],
               [[r["fighter"], r["promoted"] or "n/a", r["judged"] or "n/a", r["champion"] or "n/a", gate_text(r["gate"]),
                 ("none played" if not r["s1"] else f"{with_margin(r['s1']['gain'], r['s1']['se'])} ({r['s1']['starts']} starts; "
                  f"{'holds' if r['s1']['holds'] else 'does not hold'})"), r["verdict"], r["route"]] for r in rows])
    L += ["", "Whole runs: first Act 3 boss passes per 100 runs, candidate against champion on the same seeds."]
    body = []
    for r in rows:
        w = r["whole_run"]
        if not w:
            body.append([r["fighter"], "pending" if r["verdict"] == "pending" else "n/a", "", "", "", "", "", ""])
            continue
        c = r["carryover"]
        body.append([r["fighter"], f"{w['pairs']:,}" + (" (provisional)" if r.get("provisional") else ""), f"{w['cand']} ({w['cand_per_100']:.2f})" if w.get("cand_per_100") is not None else "n/a",
                     f"{w['base']} ({w['base_per_100']:.2f})" if w.get("base_per_100") is not None else "n/a",
                     with_margin(w["diff"], w["se"]), f"{w['se']:.2f}",
                     f"{100 * w['arrival_share']:.1f}" if w.get("arrival_share") is not None else "n/a",
                     with_margin(c["estimate"], c["se"]) if c else "n/a"])
    L += table(["fighter", "pairs", "candidate passes (per 100)", "champion passes (per 100)", "paired difference", "SE", "arrive %", "full carryover"], body)
    p = report["pooled"]
    L.append("")
    if p["whole_run"]:
        w = p["whole_run"]
        L.append(f"pooled whole run ({', '.join(w['fighters'])}; {w['pairs']:,} pairs): {with_margin(w['estimate'], w['se'])} per 100 runs (SE {w['se']:.2f}; "
                 f"band {sgn(w['lower'])} to {sgn(w['upper'])})")
    else:
        L.append("pooled whole run: no row with a whole-run figure yet")
    if p.get("whole_run_keep_v3"):
        w = p["whole_run_keep_v3"]
        L.append(f"  of which judged under keep rule v3 ({', '.join(w['fighters'])}; {w['pairs']:,} pairs): {with_margin(w['estimate'], w['se'])} per 100 runs "
                 f"(SE {w['se']:.2f}; band {sgn(w['lower'])} to {sgn(w['upper'])})")
    if p["door"]:
        d = p["door"]
        L.append(f"pooled door S1 ({', '.join(d['fighters'])}; {d['starts']:,} starts): {with_margin(d['estimate'], d['se'])} per 100 arrivals (SE {d['se']:.2f})")
    else:
        L.append("pooled door S1: no row with an S1 figure yet")
    if p["full_carryover"]:
        c = p["full_carryover"]
        L.append(f"full carryover (pooled door gain x {100 * c['arrival_share']:.1f}% of runs arriving): {with_margin(c['estimate'], c['se'])} per 100 runs")
    if p["reading"]:
        L.append(f"reading: {p['reading']}")
    if p["rows_to_settle"] is not None:
        L.append(f"extrapolation only: about {p['rows_to_settle']} more rows like the average so far would bring the pooled 2 SE down to the reference")
    L.append("")
    L.append(summary_line(report))
    notes = [f"{r['fighter']}: {n}" for r in rows for n in r["notes"]] + list(report["left_out"])
    if notes:
        L += ["", "notes:", *[f"  {n}" for n in notes]]
    pending = [r["fighter"] for r in rows if r["verdict"] == "pending"]
    if pending:
        L.append(f"  pending (no whole-run record yet): {', '.join(pending)}")
    return "\n".join(L)


def summary_line(report: Mapping[str, Any]) -> str:
    p = report["pooled"]
    w, c = p["whole_run"], p["full_carryover"]
    if not w:
        return "pooled whole-run effect: no rows yet"
    s = (f"pooled whole-run effect {sgn(w['estimate'])} per 100 runs, 2 SE {w['pm2se']:.2f}, {w['rows']} rows, {w['pairs']:,} pairs; "
         f"upper bound {sgn(w['upper'])}")
    if c:
        s += f" against a full-carryover reference of {sgn(c['estimate'])} (2 SE {c['pm2se']:.2f})"
    return s


# ------------------------------------------------------------------------------------------------------------------ --check


def close(value: float | None, expected: float, decimals: int) -> bool:
    """Whether `value` rounds to the review's printed `expected` at its decimals (the review's own rounding, with a hair of slack)."""
    return value is not None and abs(value - expected) <= 0.5 * 10 ** (-decimals) + 1e-9


def check(report: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Set the known rows against the review. (figures, exit code): 0 all match, 1 a mismatch beyond rounding, 2 a known row missing."""
    by = {r["fighter"]: r for r in report["rows"]}
    figures: list[dict[str, Any]] = []
    code = 0
    for name, (val, vd, margin, md, pairs) in REVIEW.items():
        w = (by.get(name) or {}).get("whole_run")
        if not w:
            figures.append({"figure": f"{name} whole-run effect", "review": f"{val:+.{vd}f} +/-{margin:.{md}f} on {pairs} pairs", "tool": "missing", "ok": None})
            code = max(code, 2)
            continue
        for label, got, exp, nd, signed in ((f"{name} effect", w["diff"], val, vd, True), (f"{name} plus or minus 2 SE", w["pm2se"], margin, md, False),
                                            (f"{name} pairs", float(w["pairs"]), float(pairs), 0, False)):
            ok = close(got, exp, nd)
            figures.append({"figure": label, "review": f"{exp:{'+' if signed else ''}.{nd}f}", "tool": f"{got:{'+' if signed else ''}.{max(nd, 2) if nd else 0}f}", "ok": ok})
            if not ok:
                code = max(code, 1)
    known = [by[n]["whole_run"] for n in REVIEW if by.get(n) and by[n].get("whole_run")]
    if len(known) == len(REVIEW):
        pool3 = precision_pool((w["diff"], w["se"]) for w in known)
        val, vd, margin, md = REVIEW_POOLED
        for label, got, exp, nd, signed in (("pooled effect (v4, v5, v6)", pool3["estimate"], val, vd, True), ("pooled plus or minus 2 SE", pool3["pm2se"], margin, md, False)):
            ok = close(got, exp, nd)
            figures.append({"figure": label, "review": f"{exp:{'+' if signed else ''}.{nd}f}", "tool": f"{got:{'+' if signed else ''}.{max(nd, 2)}f}", "ok": ok})
            if not ok:
                code = max(code, 1)
    else:
        figures.append({"figure": "pooled (v4, v5, v6)", "review": f"{REVIEW_POOLED[0]:+.1f} +/-{REVIEW_POOLED[2]:.1f}", "tool": "missing", "ok": None})
        code = max(code, 2)
    return figures, code


def check_text(report: Mapping[str, Any]) -> tuple[str, int]:
    figures, code = check(report)
    L = ["--check against the 11-24 sceptic review, section 3 (whole-run effect, first Act 3 boss passes per 100 runs)", ""]
    L += table(["figure", "review", "tool", "result"], [[f["figure"], f["review"], f["tool"], "missing" if f["ok"] is None else ("ok" if f["ok"] else "MISMATCH")] for f in figures])
    by = {r["fighter"]: r for r in report["rows"]}
    if code == 1 and all(by.get(n) and by[n].get("whole_run") for n in REVIEW):
        # Where a mismatch comes from: the review's pooled follows from its own v4 margin, so say what v4's own paired margin does to it.
        items = {n: (by[n]["whole_run"]["diff"], by[n]["whole_run"]["se"]) for n in REVIEW}
        as_review = precision_pool([(items["v4"][0], REVIEW["v4"][2] / Z), items["v5"], items["v6"]])
        own = precision_pool(items.values())
        L += ["", f"with the review's v4 margin read as 2 SE = {REVIEW['v4'][2]:.1f} the pooled reads {with_margin(as_review['estimate'], as_review['se'])} "
                  f"(the review: {REVIEW_POOLED[0]:+.1f} +/-{REVIEW_POOLED[2]:.1f}); with v4's own paired margin it reads {with_margin(own['estimate'], own['se'])}",
              f"v4's figure here is from: {by['v4']['whole_run']['source']}"]
    L.append("")
    L.append({0: "check: all figures match the review beyond rounding", 1: "check: MISMATCH beyond rounding (exit 1)", 2: "check: a known row is missing (exit 2)"}[code])
    return "\n".join(L), code


# ------------------------------------------------------------------------------------------------------------------ main


def json_safe(x: Any) -> Any:
    """The report with every non-finite number as null and the folder paths dropped (nothing absolute reaches the output)."""
    if isinstance(x, dict):
        return {k: json_safe(v) for k, v in x.items() if k != "path"}
    if isinstance(x, (list, tuple)):
        return [json_safe(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The pooled whole-run reading of fight-only swaps (the fight loop's promoted fighters, judged in whole runs).")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="the project folder holding referee/agent and referee/gym-loop (default D:/spireline)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--check", action="store_true", help="set the known rows against the 11-24 review's figures; exit 1 on a mismatch beyond rounding, 2 when a row is missing")
    ap.add_argument("--recompute", action="store_true", help="read every whole-run figure from the arms' rows instead of the record's margins")
    a = ap.parse_args(argv)
    if not (a.root / "referee" / "agent").is_dir():
        print("pooled_fight_swaps: no referee/agent folder under --root", file=sys.stderr)
        return 2
    report = build_report(a.root, a.recompute)
    if a.check:
        text, code = check_text(report)
        if a.json:
            figures, code = check(report)
            print(json.dumps(json_safe({"check": figures, "exit": code}), indent=2, allow_nan=False))
        else:
            print(text)
        return code
    if a.json:
        print(json.dumps(json_safe(report), indent=2, allow_nan=False))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
