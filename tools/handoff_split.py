"""Split HANDOFF.md into a short live page and an archive (Act 3 week, lane 6b; the review's "Change 3").

    python tools/handoff_split.py --handoff HANDOFF.md --archive HANDOFF-archive.md [--keep-days 7] [--max-words N]
        [--archive-sections REGEX] [--archive-intros] [--now ISO] [--alerts-header REGEX] (--dry-run | --apply)

The log lines of HANDOFF.md start with a UTC stamp: `- *2026-11-18 12:47Z, orchestrator ...`, `- *2026-10-28T15:55Z, GPU lane ...`,
`- *2026-10-23, late.*` (date only) or `- 2026-10-28T07:05Z lane W5 ...` (no asterisk, time required). A line with a stamp, plus every
line after it up to the next stamped line or the next section header (its indented tables, its blank lines, its undated sub-bullets
such as `- *05:22Z briefs launched*`), is one block. A block whose stamp is older than the cutoff (now minus --keep-days; a date-only
stamp counts as the end of its day) moves to the archive, appended in the file's own order under one dated heading with a `###`
line for the section each block came from. Kept whole, never moved: every section header, the alerts block (the section whose header
matches --alerts-header, default "open alerts"), and every line of a section that comes before its first stamped line (its
introduction, tables and prose) and of sections without stamped lines (the plan sections).

--max-words N (optional) also moves newer blocks, newest kept first, until the live page is at most N words (a "three pages" page is
about 1,500 to 2,000 words); the fixed part (headers, alerts, introductions, plan sections) is not cut, so a page can stay over N.

--archive-sections REGEX (optional) moves the whole body of every section whose header matches (introduction, tables, prose and any
log lines inside, dated or not) and leaves the header with a one-line pointer; the alerts block is never moved. This is the way to
shrink the parts that are not log lines (an old week's review, the plan sections).

--archive-intros (optional) moves, in every section that has stamped blocks, the introduction before its first block too (the week's
headline tables and prose), leaving a pointer line; the alerts block is never touched.

--dry-run (the default) writes nothing and prints the counts. --apply writes, in this order: a backup `<handoff>.<UTC>.bak` of the
original, the archive (appended and flushed), then the live file (a temporary file replaced into place). It stops, touching nothing,
when the file changed between reading and writing (a worker appended a line meanwhile): run it again.

Line breaks: the file's style is kept (CRLF when it has any CRLF) and every line break is written in that style, so a CRLF file comes
out with zero bare LF. Bytes that are not UTF-8 are carried through unchanged. Output names files, not absolute paths.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAMP_ASTERISK_RE = re.compile(r"^- \*(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{1,2}):(\d{2})Z?)?(?!\d)")
STAMP_PLAIN_RE = re.compile(r"^- (\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})Z?(?!\d)")
HEADER_RE = re.compile(r"^#{1,6}\s")
DEFAULT_ALERTS = r"open alerts"
DEFAULT_KEEP_DAYS = 7.0
LONG_AGO = datetime(1970, 1, 1, tzinfo=timezone.utc)


# ------------------------------------------------------------------------------------------------------------ parsing
def parse_stamp(line: str) -> datetime | None:
    """The UTC stamp at the start of a log line, or None. A date without a time is the last second of its day."""
    m = STAMP_ASTERISK_RE.match(line) or STAMP_PLAIN_RE.match(line)
    if not m:
        return None
    y, mo, d, hh, mm = m.groups()
    try:
        if hh is None:
            return datetime(int(y), int(mo), int(d), 23, 59, 59, tzinfo=timezone.utc)
        return datetime(int(y), int(mo), int(d), int(hh), int(mm), tzinfo=timezone.utc)
    except ValueError:
        return None


def words(lines: list[str]) -> int:
    return sum(len(x.split()) for x in lines)


@dataclass
class Block:
    start: int  # index of the block's first line in the original line list
    stamp: datetime  # a log block's stamp; LONG_AGO for a whole section
    section: str  # the header text of the section it sits in ("(top)" before any header)
    lines: list[str] = field(default_factory=list)  # the block's lines, without the blank lines that end a section
    tail: list[str] = field(default_factory=list)  # blank lines left in place when the block ends a section
    kind: str = "log"  # "log" (a stamped block), "section" (a whole section body, --archive-sections) or "intro" (--archive-intros)
    move: bool = False


def decode(data: bytes) -> str:
    return data.decode("utf-8", errors="surrogateescape")


def encode(text: str) -> bytes:
    return text.encode("utf-8", errors="surrogateescape")


def split_lines(text: str) -> tuple[list[str], str, int, int]:
    """(lines, newline style, bare LF count, bare CR count) of a text; a final line break gives a final empty element."""
    crlf = text.count("\r\n")
    bare_lf = text.count("\n") - crlf
    bare_cr = text.count("\r") - crlf
    style = "\r\n" if crlf else "\n"
    return text.replace("\r\n", "\n").split("\n"), style, bare_lf, bare_cr


def section_names(lines: list[str], alerts_re: re.Pattern[str]) -> tuple[list[str], list[bool], list[int]]:
    """Per line: the text of the header of the section it sits in, whether that section is the alerts block, and the header's line index (-1 before any)."""
    names: list[str] = []
    alerts: list[bool] = []
    heads: list[int] = []
    cur, in_alerts, head = "(top)", False, -1
    for i, ln in enumerate(lines):
        if HEADER_RE.match(ln):
            cur = ln.lstrip("#").strip()
            in_alerts = bool(alerts_re.search(cur))
            head = i
        names.append(cur)
        alerts.append(in_alerts)
        heads.append(head)
    return names, alerts, heads


def find_blocks(lines: list[str], alerts_re: re.Pattern[str], whole_re: re.Pattern[str] | None = None,
                intros: bool = False) -> tuple[list[Block], list[str], list[bool]]:
    """The movable blocks (never in the alerts block), each line's section header text and whether it is in the alerts block."""
    names, alerts, heads = section_names(lines, alerts_re)
    n = len(lines)
    blocks: list[Block] = []
    taken = [False] * n  # lines inside a whole-section block: no log block starts there
    if whole_re is not None:
        h = 0
        while h < n:
            if HEADER_RE.match(lines[h]) and not alerts[h] and whole_re.search(names[h]):
                e = h + 1
                while e < n and not HEADER_RE.match(lines[e]):
                    e += 1
                body = lines[h + 1:e]
                lead = 0
                while lead < len(body) and body[lead].strip() == "":
                    lead += 1
                core = body[lead:]
                tail: list[str] = []
                while core and core[-1].strip() == "":
                    tail.insert(0, core.pop())
                if core:
                    blocks.append(Block(start=h + 1 + lead, stamp=LONG_AGO, section=names[h], lines=core, tail=tail, kind="section"))
                    for k in range(h + 1 + lead, h + 1 + lead + len(core)):
                        taken[k] = True
                h = e
            else:
                h += 1
    i = 0
    while i < n:
        ln = lines[i]
        st = None if taken[i] or alerts[i] or HEADER_RE.match(ln) else parse_stamp(ln)
        if st is None:
            i += 1
            continue
        j = i + 1
        while j < n and not HEADER_RE.match(lines[j]) and parse_stamp(lines[j]) is None:
            j += 1
        body = lines[i:j]
        tail = []
        if j >= n or HEADER_RE.match(lines[j]):  # the block ends its section: its trailing blank lines stay, so a header keeps its gap
            while len(body) > 1 and body[-1].strip() == "":
                tail.insert(0, body.pop())
        blocks.append(Block(start=i, stamp=st, section=names[i], lines=body, tail=tail))
        i = j
    if intros:
        first: dict[int, Block] = {}
        for b in blocks:
            if b.kind == "log" and heads[b.start] >= 0:
                first.setdefault(heads[b.start], b)
        for h, b in sorted(first.items()):
            body = lines[h + 1:b.start]
            lead = 0
            while lead < len(body) and body[lead].strip() == "":
                lead += 1
            core = body[lead:]
            tail = []
            while core and core[-1].strip() == "":
                tail.insert(0, core.pop())
            if core:
                blocks.append(Block(start=h + 1 + lead, stamp=LONG_AGO, section=names[h], lines=core, tail=tail, kind="intro"))
    blocks.sort(key=lambda b: b.start)
    return blocks, names, alerts


# ------------------------------------------------------------------------------------------------------------ the plan
@dataclass
class Plan:
    handoff: Path
    archive: Path
    now: datetime
    cutoff: datetime
    keep_days: float
    max_words: int | None
    style: str
    bare_lf: int
    bare_cr: int
    lines: list[str]
    blocks: list[Block]
    live_lines: list[str]
    moved: list[Block]
    pointers: int
    source_sha: str
    source_size: int
    alerts_lines: int
    alerts_words: int

    @property
    def moved_words(self) -> int:
        return sum(words(b.lines) for b in self.moved)

    @property
    def moved_lines(self) -> int:
        return sum(len(b.lines) for b in self.moved)


def make_plan(handoff: Path, archive: Path, keep_days: float, now: datetime, max_words: int | None = None,
              alerts_header: str = DEFAULT_ALERTS, archive_sections: str | None = None, intros: bool = False) -> Plan:
    raw = handoff.read_bytes()
    lines, style, bare_lf, bare_cr = split_lines(decode(raw))
    alerts_re = re.compile(alerts_header, re.I)
    whole_re = re.compile(archive_sections, re.I) if archive_sections else None
    blocks, _names, alerts = find_blocks(lines, alerts_re, whole_re, intros)
    cutoff = now - timedelta(days=keep_days)
    for b in blocks:
        b.move = b.kind != "log" or b.stamp < cutoff
    if max_words is not None:
        in_block = {b.start + k for b in blocks for k in range(len(b.lines))}
        budget = max_words - words([ln for i, ln in enumerate(lines) if i not in in_block])  # headers, alerts, introductions, plan sections
        used = 0
        full = False
        for b in sorted((b for b in blocks if not b.move), key=lambda b: (b.stamp, b.start), reverse=True):
            w = words(b.lines)
            if not full and used + w <= budget:
                used += w
            else:
                full = True  # the newest blocks that fit are kept; this one and every older one move
                b.move = True
    moved = [b for b in blocks if b.move]
    drop = {b.start + k for b in moved for k in range(len(b.lines))}
    pointers = {b.start: "*(%s: the %s moved to %s on %s)*" % (b.section[:40], "body of this section" if b.kind == "section" else "introduction",
                                                                archive.name, now.strftime("%Y-%m-%d"))
                for b in moved if b.kind != "log"}
    live: list[str] = []
    for i, ln in enumerate(lines):
        if i in pointers:
            live.append(pointers[i])
        if i not in drop:
            live.append(ln)
    a_lines = [ln for ln, a in zip(lines, alerts) if a]
    return Plan(handoff=handoff, archive=archive, now=now, cutoff=cutoff, keep_days=keep_days, max_words=max_words, style=style,
                bare_lf=bare_lf, bare_cr=bare_cr, lines=lines, blocks=blocks, live_lines=live, moved=moved, pointers=len(pointers),
                source_sha=hashlib.sha256(raw).hexdigest(), source_size=len(raw), alerts_lines=len(a_lines), alerts_words=words(a_lines))


def archive_text(plan: Plan, style: str) -> str:
    """The text appended to the archive: one dated heading, then the moved blocks grouped under the section each came from (file order)."""
    out = ["", "## Archived %s from %s: log lines stamped before %s%s (%d blocks)" % (
        plan.now.strftime("%Y-%m-%d %H:%MZ"), plan.handoff.name, plan.cutoff.strftime("%Y-%m-%d %H:%MZ"),
        ", and whole sections or introductions" if any(b.kind != "log" for b in plan.moved) else "", len(plan.moved)), ""]
    last = None
    for b in plan.moved:
        if b.section != last:
            out += ["### " + b.section, ""]
            last = b.section
        out += b.lines
        if b.lines and b.lines[-1].strip() != "":
            out.append("")
    return style.join(out) + style


def live_text(plan: Plan) -> str:
    return plan.style.join(plan.live_lines)


# ------------------------------------------------------------------------------------------------------------ the report
def stamp_text(t: datetime | None) -> str:
    return "none" if t is None else t.strftime("%Y-%m-%d %H:%MZ")


def report(plan: Plan, applied: bool) -> str:
    live_words = words(plan.live_lines)
    log_blocks = [b for b in plan.blocks if b.kind == "log"]
    moved_log = [b for b in plan.moved if b.kind == "log"]
    kept = [b for b in log_blocks if not b.move]
    sec: dict[str, list[int]] = {}
    for b in plan.blocks:
        row = sec.setdefault(b.section, [0, 0, 0, 0])
        row[0 if b.move else 2] += 1
        row[1 if b.move else 3] += len(b.lines)
    out = [
        "handoff_split: %s" % ("APPLIED" if applied else "dry run (nothing written)"),
        "cutoff: %s (keep %g days, now %s)%s" % (stamp_text(plan.cutoff), plan.keep_days, stamp_text(plan.now),
                                                  "; also --max-words %d" % plan.max_words if plan.max_words else ""),
        "stamped blocks: %d; moving %d; keeping %d (%d lines, %d words)" % (
            len(log_blocks), len(moved_log), len(kept), sum(len(b.lines) for b in kept), sum(words(b.lines) for b in kept)),
        "whole sections moved: %d; introductions moved: %d" % (sum(1 for b in plan.moved if b.kind == "section"), sum(1 for b in plan.moved if b.kind == "intro")),
        "moved in all: %d blocks, %d lines, %d words" % (len(plan.moved), plan.moved_lines, plan.moved_words),
        "newest log block moved: %s; oldest log block kept: %s" % (stamp_text(max((b.stamp for b in moved_log), default=None)),
                                                                  stamp_text(min((b.stamp for b in kept), default=None))),
        "alerts block kept whole: %d lines, %d words" % (plan.alerts_lines, plan.alerts_words),
        "live file: %d lines, %d words, %d bytes (before: %d lines, %d words, %d bytes)" % (
            len(plan.live_lines), live_words, len(encode(live_text(plan))), len(plan.lines), words(plan.lines), plan.source_size),
        "archive: %s %d lines of blocks to %s%s" % ("appended" if applied else "would append", plan.moved_lines, plan.archive.name,
                                                    "" if applied else (" (exists)" if plan.archive.exists() else " (new file)")),
        "line breaks: %s; bare LF in the input: %d, in the output: 0%s" % (
            "CRLF" if plan.style == "\r\n" else "LF", plan.bare_lf if plan.style == "\r\n" else 0,
            "; %d lone CR left as they were" % plan.bare_cr if plan.bare_cr else ""),
    ]
    if sec:
        out.append("sections with blocks (moved / kept):")
        for name, (mb, ml, kb, kl) in sec.items():
            out.append("  %s: moved %d (%d lines), kept %d (%d lines)" % (name[:60], mb, ml, kb, kl))
    if live_words > 2000:
        out.append("note: the live page is %d words (three pages is about 1,500 to 2,000): a shorter --keep-days, --max-words, "
                   "--archive-sections or shorter lane lines would bring it down" % live_words)
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------------------ apply
class Changed(RuntimeError):
    pass


def apply_plan(plan: Plan) -> Path | None:
    """Write the plan. Returns the backup path (None when there was nothing to move). Raises Changed when the file changed since it was read."""
    if not plan.moved:
        return None
    raw = plan.handoff.read_bytes()
    if hashlib.sha256(raw).hexdigest() != plan.source_sha:
        raise Changed("%s changed since it was read; nothing was written, run again" % plan.handoff.name)
    # nothing may be lost or doubled: every original line is in exactly one of live and moved (plus the pointer lines added)
    if len(plan.live_lines) + plan.moved_lines != len(plan.lines) + plan.pointers:
        raise RuntimeError("line count check failed (%d + %d != %d + %d)" % (len(plan.live_lines), plan.moved_lines, len(plan.lines), plan.pointers))
    bak = plan.handoff.with_name("%s.%s.bak" % (plan.handoff.name, plan.now.strftime("%Y%m%dT%H%MZ")))
    shutil.copy2(plan.handoff, bak)
    # the archive keeps the style it already has; a new archive takes the live file's
    a_style = plan.style
    if plan.archive.exists():
        head = plan.archive.read_bytes()
        a_style = "\r\n" if b"\r\n" in head else ("\n" if head else plan.style)
    plan.archive.parent.mkdir(parents=True, exist_ok=True)
    with open(plan.archive, "ab") as fh:
        fh.write(encode(archive_text(plan, a_style)))
        fh.flush()
        os.fsync(fh.fileno())
    tmp = plan.handoff.with_name(plan.handoff.name + ".split-tmp")
    tmp.write_bytes(encode(live_text(plan)))
    os.replace(tmp, plan.handoff)
    return bak


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Move old log blocks of HANDOFF.md to an archive file")
    ap.add_argument("--handoff", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--keep-days", type=float, default=DEFAULT_KEEP_DAYS)
    ap.add_argument("--max-words", type=int, help="also move newer blocks (newest kept first) until the live page is at most this many words")
    ap.add_argument("--archive-sections", help="regex of section headers whose whole body moves (a pointer line stays under the header)")
    ap.add_argument("--archive-intros", action="store_true", help="also move each log section's introduction (a pointer line stays)")
    ap.add_argument("--now", help="UTC time (ISO) the cutoff is counted from (default now)")
    ap.add_argument("--alerts-header", default=DEFAULT_ALERTS, help="regex of the alerts block's header (kept whole)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="print the counts and write nothing (the default)")
    g.add_argument("--apply", action="store_true", help="write the archive and the live file, with a .bak copy of the original")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc) if not a.now else datetime.fromisoformat(a.now.replace("Z", "+00:00"))
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    handoff, archive = Path(a.handoff), Path(a.archive)
    if not handoff.is_file():
        print("handoff_split: %s not found" % handoff.name, file=sys.stderr)
        return 2
    plan = make_plan(handoff, archive, a.keep_days, now, a.max_words, a.alerts_header, a.archive_sections, a.archive_intros)
    if a.apply:
        try:
            bak = apply_plan(plan)
        except Changed as e:
            print("handoff_split: " + str(e), file=sys.stderr)
            return 3
        print(report(plan, True))
        print("backup: %s" % (bak.name if bak else "none (nothing to move)"))
    else:
        print(report(plan, False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
