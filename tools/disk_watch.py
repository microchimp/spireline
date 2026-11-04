"""Read-only disk report for the lab machine (housekeeping, 2026-11-04).

    python tools/disk_watch.py [--warn-pct 15] [--drives C: D:] [--ssd C:/spireline-ssd] [--no-old] [--diff] [--check]

Prints, as plain text:

  1. free space on each drive (total, used, free, percent free) and a WARNING line when the free share is under
     --warn-pct (default 15);
  2. the size of the SSD folder (files, folders, bytes; default C:/spireline-ssd);
  3. for each old copy left behind by the move to the SSD, its files and bytes next to those of the folder its
     replacement junction points to (default: referee/runs.old-2026-11-03 against C:/spireline-ssd/runs, corpus.old
     against corpus, refset.old against refset), with the difference. With --diff it also lists how many files of the
     old copy are missing from the target (by path under the folder) and how many are there with another size.

It reads directory entries and file sizes only: it writes nothing, deletes nothing and moves nothing, and a folder link
(junction or symlink) met inside a tree is counted once and not followed. The size walk of the old copies takes a
while on large trees (--no-old skips it). Exit status is 0, or 1 with --check when a drive is under the threshold.
Paths print relative to the lab root (default D:/spireline) or as given for the SSD; no user or host name appears.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

DEFAULT_ROOT = Path("D:/spireline")
DEFAULT_DRIVES = ("C:/", "D:/")
DEFAULT_SSD = Path("C:/spireline-ssd")
OLD_COPIES = (  # (old copy under the lab root, junction name, target under the SSD folder)
    ("referee/runs.old-2026-11-03", "referee/LAB/runs", "runs"),
    ("referee/corpus.old-2026-11-03", "referee/corpus", "corpus"),
    ("referee/refset.old-2026-11-03", "referee/refset", "refset"),
)
GIB = 1024 ** 3
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def gib(n: int) -> str:
    return f"{n / GIB:,.1f} GiB"


def sgib(n: int) -> str:
    return f"{n / GIB:+,.2f} GiB"


def is_link(entry: os.DirEntry) -> bool:
    """A symlink or a junction (any reparse point): not followed, counted on its own."""
    try:
        if entry.is_symlink():
            return True
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return False
    return bool(getattr(st, "st_file_attributes", 0) & REPARSE)


def walk(top: Path, keep_files: bool = False) -> dict:
    """Files, folders and bytes under `top`; links inside are counted in `links` and not entered."""
    out = {"exists": top.is_dir(), "files": 0, "dirs": 0, "bytes": 0, "links": 0, "errors": 0, "listing": {}}
    if not out["exists"]:
        return out
    stack: list[tuple[Path, str]] = [(top, "")]
    while stack:
        folder, prefix = stack.pop()
        try:
            with os.scandir(folder) as it:
                entries = list(it)
        except OSError:
            out["errors"] += 1
            continue
        for e in entries:
            if is_link(e):
                out["links"] += 1
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    out["dirs"] += 1
                    stack.append((Path(e.path), prefix + e.name + "/"))
                elif e.is_file(follow_symlinks=False):
                    size = e.stat(follow_symlinks=False).st_size
                    out["files"] += 1
                    out["bytes"] += size
                    if keep_files:
                        out["listing"][prefix + e.name] = size
            except OSError:
                out["errors"] += 1
    return out


def tree_line(label: str, s: dict) -> str:
    if not s["exists"]:
        return f"  {label}: not found"
    extra = (f", {s['links']} folder link(s) not followed" if s["links"] else "") + \
            (f", {s['errors']} unreadable" if s["errors"] else "")
    return f"  {label}: {s['files']:,} files in {s['dirs']:,} folders, {gib(s['bytes'])} ({s['bytes']:,} bytes){extra}"


def drive_lines(drives, warn_pct: float) -> tuple[list[str], list[str]]:
    lines, warnings = ["free space"], []
    for d in drives:
        try:
            u = shutil.disk_usage(d)
        except OSError:
            lines.append(f"  {str(d).rstrip('/')} not readable")
            continue
        name = str(d).rstrip("/" + chr(92))
        pct = 100.0 * u.free / u.total if u.total else 0.0
        lines.append(f"  {name} {gib(u.free)} free of {gib(u.total)} ({pct:.1f}% free; {gib(u.used)} used)")
        if pct < warn_pct:
            warnings.append(f"WARNING: {name} has {pct:.1f}% free, under {warn_pct:g}% "
                            f"({gib(u.free)} of {gib(u.total)})")
    return lines, warnings


def old_copy_lines(root: Path, ssd: Path, diff: bool) -> list[str]:
    lines = ["old copies against the SSD folders their junctions point to (read-only; nothing deleted)"]
    for old_rel, junction, target in OLD_COPIES:
        old, new = root / old_rel, ssd / target
        lines.append(f"{old_rel}  against  {ssd.name}/{target}  (junction {junction})")
        so, sn = walk(old, keep_files=diff), walk(new, keep_files=diff)
        lines.append(tree_line("old copy", so))
        lines.append(tree_line("SSD target", sn))
        if so["exists"] and sn["exists"]:
            lines.append(f"  old minus target: {so['files'] - sn['files']:+,} files, {sgib(so['bytes'] - sn['bytes'])} "
                         f"({so['bytes'] - sn['bytes']:+,} bytes)")
            if diff:
                missing = [k for k in so["listing"] if k not in sn["listing"]]
                resized = [k for k, v in so["listing"].items() if k in sn["listing"] and sn["listing"][k] != v]
                extra = sum(1 for k in sn["listing"] if k not in so["listing"])
                miss_bytes = sum(so["listing"][k] for k in missing)
                lines.append(f"  by path: {len(missing):,} old files missing from the target ({gib(miss_bytes)}), "
                             f"{len(resized):,} present with another size, {extra:,} target files not in the old copy")
                for k in sorted(missing)[:5]:
                    lines.append(f"    missing example: {k}")
                for k in sorted(resized)[:5]:
                    lines.append(f"    other size: {k} (old {so['listing'][k]:,} bytes, target {sn['listing'][k]:,} bytes)")
    return lines


def build(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    root = (args.root or DEFAULT_ROOT)
    ssd = args.ssd or DEFAULT_SSD
    lines, warnings = drive_lines(args.drives or DEFAULT_DRIVES, args.warn_pct)
    lines += warnings
    lines.append(f"SSD folder {ssd.as_posix()}")
    lines.append(tree_line("total", walk(ssd)))
    for name in sorted(p.name for p in ssd.iterdir() if p.is_dir()) if ssd.is_dir() else []:
        lines.append(tree_line(name, walk(ssd / name)))
    if not args.no_old:
        lines += old_copy_lines(root, ssd, args.diff)
    return lines, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only disk report: free space, SSD folder size, old copies.")
    ap.add_argument("--warn-pct", type=float, default=15.0, help="warn when a drive has less than this share free")
    ap.add_argument("--drives", nargs="+", metavar="DRIVE", help="drives to report (default C:/ D:/)")
    ap.add_argument("--ssd", type=Path, help="the SSD folder (default C:/spireline-ssd)")
    ap.add_argument("--root", type=Path, help="the lab root holding the old copies (default D:/spireline)")
    ap.add_argument("--no-old", action="store_true", help="skip the old-copy size walk")
    ap.add_argument("--diff", action="store_true", help="also compare old copy and target by path and size")
    ap.add_argument("--check", action="store_true", help="exit 1 when a drive is under the threshold")
    args = ap.parse_args(argv)
    lines, warnings = build(args)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print("\n".join(lines))
    return 1 if (args.check and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
