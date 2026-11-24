"""The strict reading of one real-game run row: which bosses did the run go past, and who played them.

Shared by tools/morning_report.py, tools/boss_entry.py and tools/weekly_numbers.py (Act 3 week, lane 8; the reading of who played a boss
fight, lane 23). The morning report's `--check` second path (`_boss_of_act`) writes the same rule again on its own, so a slip in this file
shows up as a mismatch there.

A boss is beaten when the run won, or when its floor is above the boss's floor (lane 1, 2026-11-19; the fork's `keep_v2.went_past`). The
boss's floor is read from the row's own room string when that is complete (floor = string length + 1), else the usual 17 / 33 / 48. A row
that has a boss bar for the act (the fraction of the boss's health the run dealt) and an entry below 1.0 is a lost fight: not beaten. This
is the PLAIN reading (`went_past_plain`).

What a `lost` row is. The referee plays the real game and a copy of it side by side. When the copy no longer matches the game (the referee
"lost track"), the agent can no longer be asked what to do, and a deterministic stand-in plays the real game until the referee gets its
place back (a re-anchor, which happens only at a fight's first decision or a map choice) or to the run's end. The row's `lost` field holds
the reason when the run ended still lost. The row's ending floor and its boss bars come from the game, but what a stand-in played was not
played by the agent being measured.

THE READING (lane 23, 2026-11-24). A boss counts as beaten by our player when the run went past it (plain) AND the player played its fight:
no decision of the fight was answered by the stand-in. Where that is read from, in this order (`fight_reading` returns the answer and
the name of the data it came from):

  boss_fights   a row written by the fork from `f98caf6c` on holds `stats.boss_fights`, one entry per boss fight {act, floor, first,
                decisions, stand_in, first_stand_in}: the fight is the player's when `stand_in` is 0. A loss recovered before a fight does
                not void it, and a loss at the second Act 3 boss does not void the first.
  loss_records  an older row (the 2026-11-19 and 2026-11-20 blocks) holds the divergence records of the run (`divergences`, the same
                records the block's divergences.jsonl holds, one file for the whole block). A record the referee did not re-anchor at once
                opens a LOSS that lasts to the end of its not-ranked span (`not_ranked_span.last`) and, for the last record of a row that
                ended `lost`, to the run's end. A fight is the player's when no loss covers any of its decisions: a loss that opened
                inside the boss's own fight (floor = the boss floor, a combat room) covers it; a loss that opened before it and was never
                recovered covers it; a loss that opened before it and was recovered did not (nothing re-anchors between the two Act 3
                bosses, which have no question between them, so a loss recovered before the second boss was recovered by the first
                boss's start). For the Act 1 and Act 2 bosses a recovered loss can only have run past the boss if its span was long
                enough to cross every floor between and the row had a failed re-anchor (the boss's own fight start must have failed);
                where both hold the reading is `unclear` and counts as not the player's.
  first_loss    the rule before lane 23, and still the fallback where the row holds no usable divergence records: the row's FIRST loss
                (`stats.first_loss.decision`, placed by the `divergences` entry of that decision) is where tracking was lost, and the
                bosses below that floor count and none at or after it. A lost row whose first loss cannot be placed is `unreadable`: it
                beats nothing.

A crash row (`crash` set, or `ev == "crash"`) beats nothing. A row cut off by a deadline (`end` is `fight_unfinished`, or `stalled` since the
stall guard of fork main dbac8428) is read by its floor.

`python tools/strict_rows.py --check <block folder or runs.jsonl> [--bosses ids.json] [--list]` reads a block with the new reading and with the
first-loss reading and prints both and the rows whose credit changed, each with its reason.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

BOSS_FLOORS = (17, 33, 48)  # the floors of the Act 1, Act 2 and first Act 3 bosses (the second Act 3 boss is floor 49)
WIN_ENDS = ("win", "victory", "won")  # the emulator arm writes "win", the real game's end message "victory"
DEADLINE_ENDS = ("fight_unfinished", "stalled")  # a fight the driver cut off at its action cap; a run the stand-in stopped after three ignored answers
ACT3_BOSS_ROSTERS = ("TEST_SUBJECT", "AEONGLASS", "QUEEN+TORCH_HEAD_AMALGAM")  # the encounters of the Act 3 bosses, as the divergence records name them
BASES = ("boss_fights", "loss_records", "first_loss", "unreadable", "no_loss")  # what a row's reading came from (`row_basis`)


def is_win(row: dict[str, Any]) -> bool:
    return bool(row.get("win")) or str(row.get("end") or "").lower() in WIN_ENDS


def is_deadline(row: dict[str, Any]) -> bool:
    """A run the real game did not finish a fight of: `fight_unfinished` or `stalled`. It is an ended row read by its floor, like any other:
    an arrival at the boss of that floor, not past it (a floor above a boss's is past it)."""
    return str(row.get("end") or "") in DEADLINE_ENDS


def is_crash(row: dict[str, Any]) -> bool:
    return bool(row.get("crash")) or row.get("ev") == "crash"


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def row_floor(row: dict[str, Any]) -> int:
    """The row's ending floor; 0 when it is missing or not a number."""
    try:
        return int(row.get("floor") or 0)
    except (TypeError, ValueError):
        return 0


def _stats(row: dict[str, Any]) -> dict[str, Any]:
    st = row.get("stats")
    return st if isinstance(st, dict) else {}


# ---------------------------------------------------------------------------------------------------- the first loss (the old rule)
def loss_floor(row: dict[str, Any]) -> int | None:
    """The floor where the referee FIRST lost track of the game, for a row that ended lost; None for a row that did not, and for a lost row
    whose floor cannot be read. The entry of `divergences` whose `decision` is `stats.first_loss.decision`; failing that the last entry
    at or before that decision that carries a floor."""
    if not row.get("lost"):
        return None
    first = _stats(row).get("first_loss")
    at = first.get("decision") if isinstance(first, dict) else None
    if not _is_int(at):
        return None
    best: tuple[int, int] | None = None  # (decision, floor) of the last entry at or before `at` that has a floor
    for e in row.get("divergences") or []:
        if not isinstance(e, dict) or not _is_int(e.get("decision")) or not _is_int(e.get("floor")) or e["decision"] > at:
            continue
        if e["decision"] == at:
            return int(e["floor"])
        if best is None or e["decision"] >= best[0]:
            best = (e["decision"], int(e["floor"]))
    return best[1] if best else None


def boss_floor(row: dict[str, Any], act: int) -> int | None:
    """The floor of the first boss of 0-based act `act`: from the row's own room string when it is complete (None when the string holds
    no such boss), else 17 / 33 / 48."""
    floor = row_floor(row)
    nodes = row.get("nodes")
    if isinstance(nodes, str) and floor == len(nodes) + 1:
        floors = [i + 2 for i, ch in enumerate(nodes) if ch == "B"]
        return floors[act] if act < len(floors) else None
    return BOSS_FLOORS[act]


def _boss_at(row: dict[str, Any], act: int) -> int:
    """`boss_floor`, with the usual cut where the room string holds no such boss (a win past every boss)."""
    bf = boss_floor(row, act)
    return BOSS_FLOORS[act] if bf is None else bf


# ---------------------------------------------------------------------------------------------------- plain reading
def went_past_plain(row: dict[str, Any], act: int) -> bool:
    """The plain reading: the run went past the first boss of 0-based act `act` (a win, or a floor above the boss's, with the bar rule), with
    no regard to who played the fight."""
    if is_win(row):
        return True
    if is_crash(row):
        return False
    boss = boss_floor(row, act)
    if boss is None:
        return False
    floor = row_floor(row)
    nodes = row.get("nodes")
    if not (isinstance(nodes, str) and floor == len(nodes) + 1):
        for entry in row.get("boss_damage_acts") or []:  # no complete room string: a fight recorded as lost is not beaten
            try:
                a, frac = entry[0], entry[1]
                if int(a) != act:
                    continue
                if frac is None or float(frac) < 1.0:
                    return False
            except (TypeError, ValueError, IndexError, KeyError):
                continue
            break
    return floor > boss


def went_past_first_loss(row: dict[str, Any], act: int) -> bool:
    """The reading before lane 23 (lane 8, 2026-11-20): plain, and for a row that ended lost only the bosses whose floor is below the floor of
    the FIRST loss (nothing when that floor cannot be read, except for a win, which is a win). Kept as the fallback of `fight_reading` and as
    the old reading `--check` sets the new one against."""
    if not went_past_plain(row, act):
        return False
    if not row.get("lost"):
        return True
    at = loss_floor(row)
    if at is None:
        return is_win(row)
    return _boss_at(row, act) < at


# ---------------------------------------------------------------------------------------------------- the loss records
def loss_records(row: dict[str, Any]) -> tuple[list[dict], list[dict]] | None:
    """(every divergence record, the loss records among them) of a row, both in decision order; None when the row's records cannot be used:
    no `divergences` list, or a loss record (one the referee did not re-anchor at once) without an integer decision and floor, or without
    a not-ranked span. A loss record's span is where the loss lasted: `not_ranked_span.last` is its last decision."""
    recs = row.get("divergences")
    if not isinstance(recs, list):
        return None
    out: list[dict] = []
    for d in recs:
        if not isinstance(d, dict) or not _is_int(d.get("decision")):
            return None
        out.append(d)
    out.sort(key=lambda d: d["decision"])
    losses = []
    for d in out:
        if d.get("reanchored"):
            continue
        sp = d.get("not_ranked_span")
        if not isinstance(sp, dict) or not _is_int(d.get("floor")) or not (sp.get("last") is None or _is_int(sp.get("last"))):
            return None
        losses.append(d)
    return out, losses


def _loss_end(d: dict) -> int:
    """The last decision of a loss: the end of its not-ranked span (a loss that no decision was counted into ends at its own decision)."""
    last = d["not_ranked_span"].get("last")
    return d["decision"] if last is None else last


def boss_fights(row: dict[str, Any]) -> list[dict]:
    """`stats.boss_fights` of a row written by the fork from `f98caf6c` on: one entry per boss fight; [] for an older row."""
    bf = _stats(row).get("boss_fights")
    return [e for e in bf if isinstance(e, dict)] if isinstance(bf, list) else []


def _has_loss_signal(row: dict[str, Any]) -> bool:
    st = _stats(row)
    return bool(row.get("lost")) or bool(st.get("first_loss")) or bool(st.get("losses"))


def _fight_floor(row: dict[str, Any], act: int) -> int:
    """The floor of the boss fight to be read: the boss's floor, except that the first Act 3 boss sits one floor on (or more) in the 2 to 3
    in 100 seeds whose Act 3 map is longer: the records then show a fight that is no boss's on floor 48, and the boss is the first
    boss-roster fight the records show above it (else the floor above). Without such a record the boss's floor stands."""
    boss = _boss_at(row, act)
    if act != 2:
        return boss
    recs = row.get("divergences")
    if not isinstance(recs, list):
        return boss
    at = [d for d in recs if isinstance(d, dict) and d.get("floor") == boss and d.get("room") == "combat" and d.get("encounter") is not None]
    if at and all(d["encounter"] not in ACT3_BOSS_ROSTERS for d in at):
        later = sorted(d["floor"] for d in recs if isinstance(d, dict) and _is_int(d.get("floor")) and d["floor"] > boss
                       and d.get("encounter") in ACT3_BOSS_ROSTERS)
        return later[0] if later else boss + 1
    return boss


def fight_reading(row: dict[str, Any], act: int) -> tuple[bool, str]:
    """(the player's, where it was read from): whether the first boss fight of 0-based act `act` was played by our player alone, no decision
    of it answered by the stand-in. The second part is one of `BASES` or "unclear". Defined for any row, whether or not it went past the boss
    (an arrival that died in the fight is the player's too when the stand-in never answered)."""
    boss = _fight_floor(row, act)
    mine = [e for e in boss_fights(row) if e.get("floor") == boss and _is_int(e.get("stand_in"))]
    if mine:
        return all(e["stand_in"] == 0 for e in mine), "boss_fights"
    signal = _has_loss_signal(row)
    recs = loss_records(row)
    if recs is not None and (recs[1] or not signal):
        if not recs[1]:
            return True, "no_loss"
        return _read_losses(row, act, boss, recs[0], recs[1])
    if not row.get("lost"):  # no usable records: the first-loss reading of a row that did not end lost is the plain one
        return True, ("first_loss" if signal else "no_loss")
    at = loss_floor(row)
    if at is None:
        return is_win(row), "unreadable"  # a lost row nothing can place beats nothing, except a win, which is a win
    return _boss_at(row, act) < at, "first_loss"  # exactly the rule before lane 23


def _read_losses(row: dict[str, Any], act: int, boss: int, recs: list[dict], losses: list[dict]) -> tuple[bool, str]:
    """The loss-record reading of one boss fight (see the module note)."""
    failed = _stats(row).get("reanchor_failed")
    last = losses[-1] if row.get("lost") else None  # the loss in force at the run's end
    for d in losses:
        floor = d["floor"]
        if floor > boss:
            continue  # opened after the boss floor: after the fight
        if floor == boss:
            if d.get("room") == "non_combat":
                continue  # opened on the boss floor's reward screens: the fight was over
            return False, "loss_records"
        if d is last:
            return False, "loss_records"  # opened before the boss and never recovered: the stand-in played it
        if act == 2:
            continue  # recovered before the boss, and a recovery needs a fight start or map choice, of which the first Act 3 boss's end has none
        end = _loss_end(d)
        nxt = next((k for k in recs if k["decision"] > end and _is_int(k.get("floor"))), None)
        if nxt is not None and nxt["floor"] <= boss:
            continue  # the referee was tracking again at a record on or before the boss floor
        count = d["not_ranked_span"].get("count")
        if _is_int(count) and count < boss - floor + 1:
            continue  # too few decisions to cross the floors between the loss and the boss
        if failed == 0:
            continue  # no failed re-anchor in the whole run: the boss's own fight start did not fail
        return False, "unclear"
    return True, "loss_records"


def row_basis(row: dict[str, Any]) -> str:
    """What the row's reading comes from: one of `BASES`. "no_loss": the row never lost track. "unreadable": it ended lost and nothing places
    the loss (it beats nothing). "first_loss": the divergence records are missing and the old first-loss rule is used (say so in the output)."""
    if boss_fights(row):
        return "boss_fights"
    signal = _has_loss_signal(row)
    recs = loss_records(row)
    if recs is not None and (recs[1] or not signal):
        return "loss_records" if recs[1] else "no_loss"
    if not signal:
        return "no_loss"
    if row.get("lost") and loss_floor(row) is None:
        return "unreadable"
    return "first_loss"


def loss_floor_unknown(row: dict[str, Any]) -> bool:
    """A real-game row (it has `ev`: "end") that ended lost and has nothing to place the loss by (`row_basis` "unreadable"). The copy arm's
    lost workers (no `ev`, floor 0, no data) are not counted: they are crashes under another name."""
    return row.get("ev") == "end" and bool(row.get("lost")) and row_basis(row) == "unreadable"


def fought_by_player(row: dict[str, Any], act: int) -> bool:
    """Whether the first boss fight of 0-based act `act` was the player's alone (see `fight_reading`)."""
    return fight_reading(row, act)[0]


def went_past(row: dict[str, Any], act: int) -> bool:
    """The strict reading: the run went past the first boss of 0-based act `act`, and our player played its fight (see the module note)."""
    return went_past_plain(row, act) and fight_reading(row, act)[0]


# ---------------------------------------------------------------------------------------------------- arrivals
def arrived(row: dict[str, Any]) -> bool:
    """A run that reached the first Act 3 boss: a win, a floor of 48 or more, or a boss bar for Act 3 (the per-boss table's arrival)."""
    if is_crash(row):
        return False
    if is_win(row) or row_floor(row) >= BOSS_FLOORS[2]:
        return True
    for e in row.get("boss_damage_acts") or []:
        try:
            if int(e[0]) == 2:
                return True
        except (TypeError, ValueError, IndexError, KeyError):
            continue
    return False


# ---------------------------------------------------------------------------------------------------- the block's divergence file
def attach_block_divergences(rows: list[dict[str, Any]], folder: Path) -> int:
    """Rows with no `divergences` key take their records from the block's divergences.jsonl (the file holds the records the rows carry, one
    line each, keyed by `seed`). Returns the number of rows filled; a missing file fills none and the rows are then read by their first
    loss. Rows that carry the key (even an empty list) are left as they are."""
    need = {r.get("seed") for r in rows if isinstance(r, dict) and "divergences" not in r and r.get("ev") == "end" and r.get("seed")}
    path = Path(folder) / "divergences.jsonl"
    if not need or not path.is_file():
        return 0
    by_seed: dict[str, list[dict]] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict) and rec.get("seed") in need:
                by_seed.setdefault(rec["seed"], []).append(rec)
    n = 0
    for r in rows:
        if isinstance(r, dict) and "divergences" not in r and r.get("seed") in need:
            r["divergences"] = by_seed.get(r["seed"], [])
            n += 1
    return n


# ---------------------------------------------------------------------------------------------------- what changed against the first-loss rule
def reading_change(row: dict[str, Any], act: int) -> tuple[bool, bool, str] | None:
    """None when the new reading and the first-loss reading agree about the boss of 0-based act `act` for this row; else (old, new, reason).
    A reason says which of the two faults it was: a loss recovered before the fight (the first loss of the run was not where the player
    stopped playing), a loss after the fight (at the second boss), or a stand-in decision inside the fight."""
    old, new = went_past_first_loss(row, act), went_past(row, act)
    if old == new:
        return None
    basis = fight_reading(row, act)[1]
    boss = _fight_floor(row, act)
    recs = loss_records(row)
    losses = recs[1] if recs else []
    if new:
        first = loss_floor(row)
        early = any(d["floor"] < boss for d in losses) if recs else (first is not None and first < boss)
        final = losses[-1] if (recs and row.get("lost") and losses) else None
        late = final is not None and (final["floor"] > boss or (final["floor"] == boss and final.get("room") == "non_combat"))
        bits = []
        if early:
            bits.append("recovered before the fight")
        if late:
            second = act == 2 and (final["floor"] == boss + 1 or final.get("encounter") in ACT3_BOSS_ROSTERS)
            bits.append("lost at the second boss" if second else "lost after the fight")
        if not bits:
            bits.append("loss floor unreadable, the fight record is clean" if basis == "boss_fights" else "the first loss was on the boss floor, outside the fight")
        return old, new, "; ".join(bits)
    if basis == "boss_fights":
        n = sum(e["stand_in"] for e in boss_fights(row) if e.get("floor") == boss and _is_int(e.get("stand_in")))
        return old, new, f"the stand-in answered {n} decision{'s' if n != 1 else ''} of the fight"
    if basis == "unclear":
        return old, new, "a loss recovered before the fight may have lasted into it (unclear)"
    return old, new, "a loss inside the fight, recovered after it" if not row.get("lost") else "a loss covers the fight"


# ---------------------------------------------------------------------------------------------------- --check
BOSS_NAMES = {"AEONGLASS_BOSS": "Aeonglass", "QUEEN_BOSS": "the Queen", "TEST_SUBJECT_BOSS": "the Test Subject"}


def read_block(path: Path) -> tuple[list[dict], list[dict], int]:
    """(ended rows, crash rows, rows that took their records from the block's divergences.jsonl) of a block's real-arm runs.jsonl."""
    path = Path(path)
    runs = path / "runs.jsonl" if path.is_dir() else path
    rows: list[dict] = []
    with open(runs, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                rows.append(r)
    filled = attach_block_divergences(rows, runs.parent)
    return [r for r in rows if r.get("ev") == "end"], [r for r in rows if r.get("ev") == "crash"], filled


def _per100(k: int, n: int) -> str:
    return f"{100.0 * k / n:.1f}" if n else "n/a"


def block_reading(ended: list[dict], bosses: dict[str, list[str]] | None = None) -> dict[str, Any]:
    """The first Act 3 boss read both ways over a block's ended rows. Arrivals, passes (new and first-loss readings), the arrivals whose
    fight our player played to the end ("finished"), those with a stand-in decision in the fight ("lost track"), the rows whose credit
    changed (any act) with their reasons, how each lost row was read, and the same per boss when `bosses` (seed -> [first, second]) is given."""
    arr = [r for r in ended if arrived(r)]
    out: dict[str, Any] = {"ended": len(ended), "arrivals": len(arr)}
    out["passes"] = sum(went_past(r, 2) for r in arr)
    out["passes_first_loss"] = sum(went_past_first_loss(r, 2) for r in arr)
    mine = [r for r in arr if fought_by_player(r, 2)]
    out["finished"] = len(mine)
    out["finished_passes"] = sum(went_past(r, 2) for r in mine)
    out["lost_track"] = len(arr) - len(mine)
    out["lost_track_by_basis"] = dict(Counter(fight_reading(r, 2)[1] for r in arr if not fought_by_player(r, 2)))
    out["lost_rows_by_basis"] = dict(Counter(row_basis(r) for r in ended if r.get("lost")))
    out["unclear"] = sum(1 for r in ended for a in (0, 1, 2) if went_past_plain(r, a) and fight_reading(r, a)[1] == "unclear")
    out["acts"] = {}
    changes: list[dict] = []
    for a in (0, 1, 2):
        old = sum(went_past_first_loss(r, a) for r in ended)
        new = sum(went_past(r, a) for r in ended)
        out["acts"][a + 1] = {"first_loss": old, "new": new, "plain": sum(went_past_plain(r, a) for r in ended)}
        for r in ended:
            ch = reading_change(r, a)
            if ch:
                changes.append({"seed": r.get("seed"), "act": a + 1, "old": ch[0], "new": ch[1], "reason": ch[2]})
    out["changes"] = changes
    if bosses:
        per: dict[str, dict[str, int]] = {}
        for r in arr:
            name = BOSS_NAMES.get((bosses.get(r.get("seed")) or ["?"])[0], "unknown")
            c = per.setdefault(name, dict.fromkeys(("arrivals", "passes", "passes_first_loss", "finished", "finished_passes", "lost_track"), 0))
            c["arrivals"] += 1
            c["passes"] += int(went_past(r, 2))
            c["passes_first_loss"] += int(went_past_first_loss(r, 2))
            if fought_by_player(r, 2):
                c["finished"] += 1
                c["finished_passes"] += int(went_past(r, 2))
            else:
                c["lost_track"] += 1
        out["per_boss"] = dict(sorted(per.items()))
    return out


def check_text(name: str, ended: list[dict], crashes: list[dict], filled: int, bosses: dict[str, list[str]] | None, listing: bool) -> str:
    g = block_reading(ended, bosses)
    n, ar = g["ended"], g["arrivals"]
    L = [f"strict_rows --check: {name}: {n} ended rows, {len(crashes)} crash rows, {ar} arrivals at the first Act 3 boss", ""]
    L.append("how the lost rows were read: " + (", ".join(f"{k} {v}" for k, v in sorted(g["lost_rows_by_basis"].items())) or "none"))
    if filled:
        L.append(f"  {filled} rows took their loss records from the block's divergences.jsonl")
    fb = g["lost_rows_by_basis"].get("first_loss", 0) + g["lost_rows_by_basis"].get("unreadable", 0)
    if fb:
        L.append(f"  FALLBACK: {fb} lost rows have no usable loss records and are read by their first loss (the rule before lane 23)"
                 f" or, when that is unreadable too, count nothing")
    L.append("")
    L.append("boss beaten by our player, rows credited (first-loss reading -> new reading; plain reading in brackets):")
    for a, v in g["acts"].items():
        L.append(f"  Act {a} boss: {v['first_loss']} -> {v['new']}  (plain {v['plain']})")
    L.append("")
    L.append(f"first Act 3 boss: passes {g['passes']} of {ar} arrivals = {_per100(g['passes'], ar)} per 100 "
             f"(first-loss reading {g['passes_first_loss']} of {ar} = {_per100(g['passes_first_loss'], ar)})")
    L.append(f"  fights our player played to the end: {g['finished']} of {ar}; passes among them {g['finished_passes']} of {g['finished']} "
             f"= {_per100(g['finished_passes'], g['finished'])} per 100")
    L.append(f"  lost-track arrivals (a stand-in answered part of the fight): {g['lost_track']} of {ar}"
             + (f" ({', '.join(f'{k} {v}' for k, v in sorted(g['lost_track_by_basis'].items()))})" if g["lost_track_by_basis"] else ""))
    if g["unclear"]:
        L.append(f"  {g['unclear']} (row, boss) readings are unclear and count as not the player's")
    for name_, c in (g.get("per_boss") or {}).items():
        L.append(f"  {name_}: passes {c['passes']} of {c['arrivals']} arrivals; of the fights our player finished {c['finished_passes']} of "
                 f"{c['finished']}; lost-track {c['lost_track']} of {c['arrivals']} (first-loss reading passes {c['passes_first_loss']})")
    L.append("")
    ch = g["changes"]
    L.append(f"rows whose credit changed against the first-loss reading: {len({(c['seed'], c['act']) for c in ch})} (row, boss) pairs, "
             f"{sum(1 for c in ch if c['new'])} credited now and {sum(1 for c in ch if not c['new'])} no longer")
    by = Counter((c["act"], c["new"], c["reason"]) for c in ch)
    for (act, new, reason), k in sorted(by.items()):
        L.append(f"  Act {act} boss, {'credited now' if new else 'no longer credited'}: {k} ({reason})")
    if listing:
        L.append("")
        for c in sorted(ch, key=lambda c: (c["act"], str(c["seed"]))):
            L.append(f"  {c['seed']} Act {c['act']} {'old yes' if c['old'] else 'old no'} -> {'yes' if c['new'] else 'no'}: {c['reason']}")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read a real block's rows with the strict reading and set it against the first-loss reading.")
    ap.add_argument("--check", required=True, type=Path, help="a block's real-arm folder (g<N>) or its runs.jsonl")
    ap.add_argument("--bosses", type=Path, help="a JSON file {seed: [first Act 3 boss, second]} to split the first Act 3 boss by name")
    ap.add_argument("--list", action="store_true", help="list every changed row")
    a = ap.parse_args(argv)
    ended, crashes, filled = read_block(a.check)
    bosses = json.loads(a.bosses.read_text(encoding="utf-8")) if a.bosses else None
    folder = a.check if a.check.is_dir() else a.check.parent
    print(check_text(f"{folder.parent.name}/{folder.name}", ended, crashes, filled, bosses, a.list))
    return 0


if __name__ == "__main__":
    sys.exit(main())
