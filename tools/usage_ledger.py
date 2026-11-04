"""The usage ledger (D52 item 2): what each piece of work cost on the weekly all-models bar, from HANDOFF's usage notes.

    python tools/usage_ledger.py HANDOFF.md [--since DATE] [--now ISO]

HANDOFF lines look like

    - *2026-11-04 01:00Z, worker (D51, loop library move).* **...** ... Usage at start about 1% all; end: 3% all / 2% Fable at 01:05Z.
    - *2026-11-04 01:30Z, orchestrator.* ... Usage 3% all / 2% Fable at 01:30Z (ceiling 65, stop 63).

Every dated line (`- *YYYY-MM-DD[ HH:MMZ][, author].*`) is read for

  * readings: "Usage 3% all / 2% Fable at 01:30Z", "Usage about 93 all / 63 Fable", "usage 15% all / 22% Fable",
    "Usage reading: weekly all models 5%, Fable 8%", "93 in 100": a figure for the all-models bar, one for Fable when given,
    and the time ("at 01:30Z", with or without a date; else the line's own time);
  * items: "Usage at start <figure> [time]; end: <figure> [at time]" (a worker's line). The item's name is the
    parenthesis of the author ("worker (D51, loop library move)" -> "D51, loop library move"). An end of "(orchestrator)"
    is an unfilled placeholder. A start without a time is placed at the latest other reading that shows the same figure (the
    orchestrator's reading the worker was started from), marked with a "~"; a start that finds none stays unknown.

Lines without figures are skipped. The bar resets on Tuesdays at 21:00Z (2026-11-10T21:00Z is one); a week is the span from
one reset to the next. Per item: start, end, the points of the all-models bar used (end figure minus start figure). Items whose
start-to-end intervals overlap another item's use the same bar at the same time, so they print "shared" instead of a number; a
line that says so itself ("shared span with ...") counts too. Per week: the bar at its last reading, the sum of the solo items,
the bar's movement across each group of shared items, and the rest (the orchestrator's own work and anything unreported).
The figures have the bar's whole-point resolution, so a one-point item may be anything from 0 to 2. Output is markdown.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

RESET_WEEKDAY = 1  # Tuesday
RESET_HOUR = 21  # 21:00Z
NUM = r"\d+(?:\.\d+)?"
FIG = (rf"(?P<approx>about\s+|around\s+|~\s*)?(?P<all>{NUM})(?:\s*%|\s+in\s+100)?(?:\s+all(?:\s+models)?)?"
       rf"(?:\s*/\s*(?P<fable>{NUM})(?:\s*%|\s+in\s+100)?\s*Fable)?(?:\s*,\s*Fable\s+(?P<fable2>{NUM})\s*%?)?")
FIG_RE = re.compile(FIG, re.I)
TIME = r"(?:(?P<d>\d{4}-\d{2}-\d{2})[ T]+)?(?P<h>\d{1,2}):(?P<m>\d{2})Z"
TIME_RE = re.compile(rf"(?:\bat\s+|@\s*|\()\s*{TIME}", re.I)
LINE_RE = re.compile(r"^- \*(?P<date>\d{4}-\d{2}-\d{2})(?P<rest>[^*]*)\*")
HEAD_TIME_RE = re.compile(r"^\s*(?P<h>\d{1,2}):(?P<m>\d{2})Z")
READING_RE = re.compile(
    r"\busage(?:\s+(?:page|reading|readings|last\s+read|was|read|reads|now|weekly))*\s*[:=]?\s*(?:weekly\s+)?(?:all\s+models\s+)?"
    + FIG, re.I)
ITEM_RE = re.compile(r"\busage\s+at\s+start\s+(?P<start>.+?)\s*[;,]\s*end\b\s*:?\s*(?P<end>.*)", re.I | re.S)
SHARED_RE = re.compile(r"shared\s+span", re.I)
UNFILLED_RE = re.compile(r"^\s*\(orchestrator\)", re.I)


# ---------------------------------------------------------------------------------------------------- parsing
@dataclass
class Reading:
    when: datetime
    all: float
    fable: float | None
    line: int
    approx: bool = False


@dataclass
class Item:
    label: str
    who: str
    line: int
    line_when: datetime | None
    start_all: float
    start_fable: float | None
    start_when: datetime | None  # explicit, else inferred, else None
    start_inferred: bool
    end_all: float | None
    end_fable: float | None
    end_when: datetime | None
    unfilled: bool
    says_shared: bool
    approx: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def interval(self) -> tuple[datetime, datetime] | None:
        if self.start_when and self.end_when and not self.unfilled:
            return self.start_when, self.end_when
        return None

    @property
    def points(self) -> float | None:
        return None if self.end_all is None else self.end_all - self.start_all

    @property
    def fable_points(self) -> float | None:
        return None if self.end_fable is None or self.start_fable is None else self.end_fable - self.start_fable


def nearest(hh: int, mm: int, anchor: datetime, day: str | None = None) -> datetime:
    """The UTC time hh:mm on `day`, else on the day that puts it nearest to `anchor`."""
    if day:
        return datetime.fromisoformat(day).replace(hour=hh, minute=mm, tzinfo=timezone.utc)
    best = None
    for off in (-1, 0, 1):
        cand = (anchor + timedelta(days=off)).replace(hour=hh, minute=mm, second=0, microsecond=0)
        if best is None or abs(cand - anchor) < abs(best - anchor):
            best = cand
    return best  # type: ignore[return-value]


def time_in(text: str, anchor: datetime) -> datetime | None:
    m = TIME_RE.search(text)
    if not m:
        return None
    return nearest(int(m["h"]), int(m["m"]), anchor, m["d"])


def fig_values(m: re.Match) -> tuple[float, float | None, bool]:
    fable = m["fable"] if m["fable"] is not None else m["fable2"]
    return float(m["all"]), (float(fable) if fable is not None else None), bool(m["approx"])


def item_label(author: str) -> tuple[str, str]:
    """(label, who): "worker C (reset order, D45), part 1" -> ("reset order, D45, part 1", "worker C")."""
    author = author.strip().rstrip(".").strip()
    m = re.match(r"^(?P<who>[^()]*?)\s*\((?P<what>.*)\)(?P<tail>[^()]*)$", author)
    if not m:
        return author, "worker"
    who, what, tail = m["who"].strip(), m["what"].strip(), m["tail"].strip(" ,")
    return (what + (f", {tail}" if tail else "")), (who or "worker")


@dataclass
class Parsed:
    readings: list[Reading]
    items: list[Item]
    lines_read: int
    lines_with_figures: int


def parse_handoff(text: str) -> Parsed:
    readings: list[Reading] = []
    items: list[Item] = []
    n_lines = n_fig = 0
    for no, raw in enumerate(text.splitlines(), 1):
        m = LINE_RE.match(raw)
        if not m:
            continue
        n_lines += 1
        day = datetime.fromisoformat(m["date"]).replace(tzinfo=timezone.utc)
        ht = HEAD_TIME_RE.match(m["rest"])
        line_when = day.replace(hour=int(ht["h"]), minute=int(ht["m"])) if ht else None
        anchor = line_when or day.replace(hour=12)
        rest = m["rest"][ht.end():] if ht else m["rest"]
        author = rest.lstrip(" ,").strip()
        is_orch = author.lower().startswith("orchestrator")
        body = raw[m.end():]
        found = False
        item_span = None

        im = ITEM_RE.search(body)
        if im and not is_orch:
            sm = FIG_RE.match(im["start"])
            if sm:
                found = True
                sa, sf, sapprox = fig_values(sm)
                s_when = time_in(im["start"][sm.end():], anchor)
                end_txt = im["end"][:200]
                unfilled = bool(UNFILLED_RE.match(end_txt))
                em = None if unfilled else FIG_RE.match(end_txt.lstrip(" :"))
                ea = ef = None
                e_when = None
                eapprox = False
                if em:
                    ea, ef, eapprox = fig_values(em)
                    e_when = time_in(end_txt.lstrip(" :")[em.end():em.end() + 90], anchor) or line_when
                label, who = item_label(author)
                items.append(Item(label=label, who=who, line=no, line_when=line_when, start_all=sa, start_fable=sf,
                                  start_when=s_when, start_inferred=False, end_all=ea, end_fable=ef, end_when=e_when,
                                  unfilled=unfilled or em is None, says_shared=bool(SHARED_RE.search(end_txt)),
                                  approx=sapprox or eapprox))
                if em and e_when:
                    readings.append(Reading(e_when, ea, ef, no, eapprox))
                if s_when:
                    readings.append(Reading(s_when, sa, sf, no, sapprox))
                item_span = (im.start(), im.start("end") + (em.end() + 90 if em else 15))

        for rm in READING_RE.finditer(body):
            if item_span and item_span[0] <= rm.start() < item_span[1]:
                continue  # inside the start/end note of an item (the item gave its own end reading above)
            v_all, v_fable, approx = fig_values(rm)
            when = time_in(body[rm.end():rm.end() + 45].split(".")[0], anchor) or line_when
            if when is None:
                continue
            found = True
            readings.append(Reading(when, v_all, v_fable, no, approx))
        n_fig += 1 if found else 0

    # one reading per (time, figures)
    seen, uniq = set(), []
    for r in sorted(readings, key=lambda r: (r.when, r.line)):
        key = (r.when, r.all, r.fable)
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    for it in items:
        if it.start_when is None:
            guess = infer_start(it, uniq)
            if guess:
                it.start_when, it.start_inferred = guess, True
    return Parsed(uniq, items, n_lines, n_fig)


def infer_start(it: Item, readings: list[Reading]) -> datetime | None:
    """The latest reading from another line, no later than the item's end, that shows the item's start figure."""
    limit = it.end_when or it.line_when
    if limit is None:
        return None
    near = [r for r in readings if r.line != it.line and r.when < limit and limit - r.when <= timedelta(hours=48)
            and week_start(r.when) == week_start(limit)]
    for tol in (0.5, 1.5):  # the figure itself first, then a point either way (a reading rounds)
        pool = [r for r in near if abs(r.all - it.start_all) < tol]
        both = [r for r in pool if it.start_fable is not None and r.fable is not None and abs(r.fable - it.start_fable) < tol]
        pool = both or pool
        if pool:
            return max(r.when for r in pool)
    return None


# ---------------------------------------------------------------------------------------------------- weeks and sharing
def week_start(when: datetime) -> datetime:
    """The latest reset (Tuesday 21:00Z) at or before `when`."""
    day = when.replace(hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    day -= timedelta(days=(day.weekday() - RESET_WEEKDAY) % 7)
    return day if day <= when else day - timedelta(days=7)


def overlaps(a: tuple[datetime, datetime], b: tuple[datetime, datetime]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def groups_of_shared(items: list[Item]) -> list[list[Item]]:
    """Connected groups of items whose intervals overlap (items with an interval only); singletons are not returned."""
    timed = [it for it in items if it.interval]
    parent = list(range(len(timed)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(timed)):
        for j in range(i + 1, len(timed)):
            if overlaps(timed[i].interval, timed[j].interval):  # type: ignore[arg-type]
                parent[find(i)] = find(j)
    by_root: dict[int, list[Item]] = {}
    for i, it in enumerate(timed):
        by_root.setdefault(find(i), []).append(it)
    return [g for g in by_root.values() if len(g) > 1]


def classify(items: list[Item]) -> dict[int, str]:
    """line number of each item (+ label) -> 'solo' | 'shared' | 'unfilled' | 'no interval' | 'spans reset'."""
    shared_ids = {id(it) for g in groups_of_shared(items) for it in g}
    out: dict[int, str] = {}
    for it in items:
        if it.unfilled:
            kind = "unfilled"
        elif it.interval is None:
            kind = "shared" if it.says_shared else "no interval"
        elif week_start(it.interval[0]) != week_start(it.interval[1]) or (it.points is not None and it.points < -5):
            kind = "spans reset"
        elif id(it) in shared_ids or it.says_shared:
            kind = "shared"
        else:
            kind = "solo"
        out[id(it)] = kind
    return out


# ---------------------------------------------------------------------------------------------------- output
def z(when: datetime | None, inferred: bool = False) -> str:
    return "?" if when is None else ("~" if inferred else "") + when.strftime("%Y-%m-%d %H:%MZ")


def pts(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x:+.0f}" if abs(x - round(x)) < 1e-9 else f"{x:+.1f}"


def pts_plain(x: float | None) -> str:
    return "n/a" if x is None else (f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.1f}")


def ledger(parsed: Parsed, since: datetime | None, now: datetime, source: str) -> str:
    items = sorted(parsed.items, key=lambda it: (it.end_when or it.line_when or datetime.min.replace(tzinfo=timezone.utc), it.line))
    kinds = classify(parsed.items)
    groups = groups_of_shared(parsed.items)
    group_of = {id(it): n for n, g in enumerate(groups, 1) for it in g}
    if since:
        items = [it for it in items if (it.end_when or it.line_when or since) >= since]
    cur_week = week_start(now)
    L = [f"# Usage ledger: {source}" + (f" (since {since.strftime('%Y-%m-%d')})" if since else ""), ""]
    L.append(f"{parsed.lines_read} dated lines read, {parsed.lines_with_figures} with usage figures; {len(parsed.readings)} readings, "
             f"{len(parsed.items)} items with a start note. Weeks reset Tuesdays 21:00Z; the current week began "
             f"{z(cur_week)}. Points are of the all-models bar (whole-point resolution).")
    L += ["", "## Items", "",
          "| Item | Who | Start | End | All-models points | Fable points | Note |", "|---|---|---|---|---|---|---|"]
    for it in items:
        kind = kinds[id(it)]
        if kind == "solo":
            a, f, note = pts(it.points), pts(it.fable_points), ""
        elif kind == "shared":
            a, f = "shared", "shared"
            others = [o.label[:30] for o in groups[group_of[id(it)] - 1] if o is not it] if id(it) in group_of else []
            note = (f"group {group_of[id(it)]}: overlaps " + "; ".join(others[:2]) + (f" and {len(others) - 2} more" if len(others) > 2 else "")
                    ) if others else "the line says it shared the span"
            if it.says_shared and id(it) in group_of:
                note += " (the line says so too)"
        elif kind == "unfilled":
            a, f, note = "n/a", "n/a", "end figure not filled in"
        elif kind == "spans reset":
            a, f, note = "n/a", "n/a", "start and end are in different weeks"
        else:
            a, f, note = "n/a", "n/a", "start time unknown, so overlap cannot be judged"
        if it.points is not None and kind in ("shared", "spans reset", "no interval"):
            note += f"; figures {pts_plain(it.start_all)} -> {pts_plain(it.end_all)}"
        if it.start_inferred:
            note += "; start time read from the matching reading"
        cell = lambda s: s.replace("|", "/")  # noqa: E731
        label = it.label if len(it.label) <= 60 else it.label[:59] + "~"
        L.append(f"| {cell(label)} | {cell(it.who)} | {z(it.start_when, it.start_inferred)} | {z(it.end_when)} | {a} | {f} | {cell(note.strip('; '))} |")
    if not items:
        L.append("| (none) | | | | | | |")

    if groups:
        L += ["", "## Shared groups", "", "| Group | Items | Window | Bar figures (lowest start -> highest end) | Movement |", "|---|---|---|---|---|"]
        for n, g in enumerate(groups, 1):
            if since and max(it.end_when for it in g) < since:  # type: ignore[type-var]
                continue
            lo, hi = min(it.start_when for it in g), max(it.end_when for it in g)  # type: ignore[type-var]
            fs = [it for it in g if it.end_all is not None]
            a, b = min(it.start_all for it in fs), max(it.end_all for it in fs)  # type: ignore[type-var]
            L.append(f"| {n} | {len(g)} | {z(lo)} to {z(hi)} | {pts_plain(a)} -> {pts_plain(b)} | {pts_plain(b - a)} |")

    # weeks
    readings = parsed.readings
    weeks: dict[datetime, list[Reading]] = {}
    for r in readings:
        weeks.setdefault(week_start(r.when), []).append(r)
    for it in items:
        if it.end_when or it.line_when:
            weeks.setdefault(week_start(it.end_when or it.line_when), [])
    L += ["", "## Weeks", "",
          "| Week (reset) | Readings | Bar at last reading (all / Fable) | Solo items | Shared groups | Items together | Rest (orchestrator, unreported) | Unfilled ends |",
          "|---|---|---|---|---|---|---|---|"]
    for w in sorted(weeks):
        if since and w + timedelta(days=7) <= since:
            continue
        rs = sorted(weeks[w], key=lambda r: r.when)
        tag = " (current)" if w == cur_week else " (last)" if w == cur_week - timedelta(days=7) else ""
        in_week = [it for it in items if (it.end_when or it.line_when) and week_start(it.end_when or it.line_when) == w]
        solo = [it for it in in_week if kinds[id(it)] == "solo"]
        solo_sum = sum(max(0.0, it.points or 0.0) for it in solo)
        grp = []
        lone = [[it] for it in in_week if kinds[id(it)] == "shared" and id(it) not in group_of and it.end_all is not None]
        for g in groups + lone:  # lone: an item whose own line says it shared the span though no other interval overlaps
            gs = [it for it in g if it.end_when and week_start(it.end_when) == w and not it.unfilled]
            if gs:
                grp.append((gs, max(it.end_all for it in gs) - min(it.start_all for it in gs)))  # type: ignore[type-var]
        grp_sum = sum(d for _, d in grp)
        last = rs[-1] if rs else None
        total = last.all if last else None
        rest = None if total is None else total - solo_sum - grp_sum
        unfilled = sum(1 for it in in_week if kinds[id(it)] == "unfilled")
        grp_txt = "; ".join(f"{len(gs)} items {pts_plain(d)} pts" for gs, d in grp) or "none"
        bar = "n/a" if last is None else f"{pts_plain(last.all)}" + (f" / {pts_plain(last.fable)}" if last.fable is not None else "") + f" at {z(last.when)}"
        L.append(f"| {w.strftime('%Y-%m-%d %H:%MZ')}{tag} | {len(rs)} | {bar} | {len(solo)} items, {pts_plain(solo_sum)} pts "
                 f"| {grp_txt} | {pts_plain(solo_sum + grp_sum)} pts | {pts_plain(rest)} pts | {unfilled} |")
    L += ["", "Notes: a solo item is the end figure minus the start figure; a shared group is the bar's movement from its lowest "
          "start figure to its highest end figure, spread over several items that ran at once, so none of its numbers belongs to "
          "one item. Rest is what the bar shows beyond the items (the orchestrator's own turns, workers whose lines carry no "
          "figures, rounding). A leading ~ on a start time marks one read from the matching reading rather than written in the line."]
    return "\n".join(L) + "\n"


def parse_since(text: str | None) -> datetime | None:
    if not text:
        return None
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The usage ledger: per-item cost on the weekly bar, from HANDOFF's usage notes.")
    ap.add_argument("handoff", type=Path, help="HANDOFF.md")
    ap.add_argument("--since", help="only items ending, and weeks ending, after this date (YYYY-MM-DD)")
    ap.add_argument("--now", help="ISO time that decides which week is current (default: now)")
    a = ap.parse_args(argv)
    if not a.handoff.is_file():
        raise SystemExit(f"{a.handoff.name}: not a file")
    parsed = parse_handoff(a.handoff.read_text(encoding="utf-8", errors="replace"))
    now = parse_since(a.now) or datetime.now(timezone.utc)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(ledger(parsed, parse_since(a.since), now, a.handoff.name), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
