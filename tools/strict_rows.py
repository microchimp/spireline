"""The strict reading of one real-game run row: which bosses did the run go past, and who played them.

Shared by tools/morning_report.py, tools/boss_entry.py and tools/weekly_numbers.py (Act 3 week, lane 8). The morning report's `--check`
second path (`_boss_of_act`) writes the same rule again on its own, so a slip in this file shows up as a mismatch there.

A boss is beaten when the run won, or when its floor is above the boss's floor (lane 1, 2026-11-19; the fork's `keep_v2.went_past`). The
boss's floor is read from the row's own room string when that is complete (floor = string length + 1), else the usual 17 / 33 / 48. A row
that has a boss bar for the act (the fraction of the boss's health the run dealt) and an entry below 1.0 is a lost fight: not beaten.

What a `lost` row is. The referee plays the real game and a copy of it side by side. When the copy no longer matches the game (the referee
"lost track"), the agent can no longer be asked what to do, and a deterministic stand-in plays the rest of the run on the real game. The
row's `lost` field holds the reason when the run ended still lost; `stats.first_loss.decision` is the decision where tracking was first
lost, and the `divergences` entry of that decision carries the floor. The row's ending floor and its boss bars come from the game, but
everything after the loss was played by the stand-in, not by the agent being measured. So a lost row is credited with the bosses whose floor
is BELOW the floor where tracking was lost, and with nothing at or after it (a boss fought on the loss floor was played partly by the
stand-in). Before this rule a lost row beat nothing at all, which came from the copy arm, where `lost` meant a worker that returned no
data (floor 0). A lost row whose loss floor cannot be found keeps that old reading (beats nothing) and is counted as `loss floor unknown`.
A crash row (`crash` set, or `ev == "crash"`) beats nothing. A row cut off by a deadline (`end` is `fight_unfinished`, or `stalled` since the stall guard of fork main dbac8428) is read by its floor.
"""

from __future__ import annotations

from typing import Any

BOSS_FLOORS = (17, 33, 48)  # the floors of the Act 1, Act 2 and first Act 3 bosses (the second Act 3 boss is floor 49)
WIN_ENDS = ("win", "victory", "won")  # the emulator arm writes "win", the real game's end message "victory"
DEADLINE_ENDS = ("fight_unfinished", "stalled")  # a fight the driver cut off at its action cap; a run the stand-in stopped after three ignored answers


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


def loss_floor(row: dict[str, Any]) -> int | None:
    """The floor where the referee lost track of the game, for a row that ended lost; None for a row that did not, and for a lost row
    whose floor cannot be read. The entry of `divergences` whose `decision` is `stats.first_loss.decision`; failing that the last entry
    at or before that decision that carries a floor."""
    if not row.get("lost"):
        return None
    first = (row.get("stats") or {}).get("first_loss")
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


def loss_floor_unknown(row: dict[str, Any]) -> bool:
    """A real-game row (it has `ev`: "end") that ended lost and has no readable loss floor. The copy arm's lost workers (no `ev`, floor 0,
    no data) are not counted: they are crashes under another name."""
    return row.get("ev") == "end" and bool(row.get("lost")) and loss_floor(row) is None


def boss_floor(row: dict[str, Any], act: int) -> int | None:
    """The floor of the first boss of 0-based act `act`: from the row's own room string when it is complete (None when the string holds
    no such boss), else 17 / 33 / 48."""
    floor = row_floor(row)
    nodes = row.get("nodes")
    if isinstance(nodes, str) and floor == len(nodes) + 1:
        floors = [i + 2 for i, ch in enumerate(nodes) if ch == "B"]
        return floors[act] if act < len(floors) else None
    return BOSS_FLOORS[act]


def went_past(row: dict[str, Any], act: int) -> bool:
    """The strict reading: the run went past the first boss of 0-based act `act`, and the agent played it (see the module note)."""
    if is_win(row):  # a won run beat every boss, except those at or after a known loss floor (the stand-in played them)
        at = loss_floor(row)
        bf = boss_floor(row, act)
        return at is None or (BOSS_FLOORS[act] if bf is None else bf) < at
    if is_crash(row):
        return False
    floor = row_floor(row)
    at = None
    if row.get("lost"):
        at = loss_floor(row)
        if at is None:
            return False  # lost, loss floor unknown: beats nothing, as before
    boss = boss_floor(row, act)
    if boss is None:
        return False
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
    if floor <= boss:
        return False
    return at is None or boss < at
