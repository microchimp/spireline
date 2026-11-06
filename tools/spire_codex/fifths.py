"""Put the human corpus's Ironclad Ascension 10 runs into their fifths, by the rule of D38 addendum 1, and count them.

Usage: python3 -I fifths.py <a10_vanilla.jsonl.gz> <old_exam_ids.txt> <out_dir>

The rule (tools/boss_entry.py `exam_bucket`): a run's fifth is a fixed hash of its id (`run_hash`, else `seed:start_time`) modulo 5;
fifth 0 is the exam for ever, fifths 1 to 3 train and fifth 4 validates. New runs join the fifths by the same rule, so a run that
was in the October export has the same fifth now. `old_exam_ids.txt` is the October ids file: its ids stay exam (the union, as
`human_starts.is_exam`), and the script reports how many of them are still in the file and that each one is in bucket 0.

Writes `exam_ids.txt` (the old ids united with the bucket-0 runs of this file, sorted) and `fifths.json` (counts only: runs, wins, and
Act 1 / Act 2 boss kills per fifth). Aggregates only; the ids list stays under data/ beside the corpus.
"""

import collections
import gzip
import hashlib
import json
import os
import sys

EXAM_SALT = "spireline-d38-exam-fifth|"
CHARACTER = "CHARACTER.IRONCLAD"


def exam_bucket(run_id: str) -> int:
    return int(hashlib.sha256((EXAM_SALT + str(run_id)).encode()).hexdigest()[:8], 16) % 5


def run_id(r: dict) -> str:
    return str(r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}")


def human_ok(r: dict) -> bool:
    pl = r.get("players") or []
    return (r.get("ascension") == 10 and r.get("game_mode") == "standard" and not r.get("was_abandoned") and not r.get("modifiers")
            and len(pl) == 1 and pl[0].get("character") == CHARACTER)


def boss_kills(r: dict) -> tuple[int, int]:
    acts = r.get("map_point_history") or []
    win = bool(r.get("win"))
    return int(win or (len(acts) >= 2 and bool(acts[1]))), int(win or (len(acts) >= 3 and bool(acts[2])))


def main(src: str, old_ids_path: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    old = {x.strip() for x in open(old_ids_path, encoding="utf-8").read().split() if x.strip()}
    cells: dict[int, list[int]] = collections.defaultdict(lambda: [0, 0, 0, 0])  # runs, wins, act1 kills, act2 kills
    exam_new: set[str] = set()
    seen_old: set[str] = set()
    lines = 0
    opener = gzip.open if src.endswith(".gz") else open
    with opener(src, "rt", encoding="utf-8") as fh:
        for line in fh:
            lines += 1
            if '"CHARACTER.IRONCLAD"' not in line:
                continue
            r = json.loads(line)
            if not human_ok(r):
                continue
            rid = run_id(r)
            f = exam_bucket(rid)
            c = cells[f]
            a1, a2 = boss_kills(r)
            c[0] += 1
            c[1] += int(bool(r.get("win")))
            c[2] += a1
            c[3] += a2
            if f == 0:
                exam_new.add(rid)
            if rid in old:
                seen_old.add(rid)
    union = sorted(old | exam_new)
    with open(os.path.join(out_dir, "exam_ids.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(union) + "\n")
    out = {
        "lines": lines,
        "fifths": {str(f): {"runs": c[0], "wins": c[1], "act1_boss_kills": c[2], "act2_boss_kills": c[3]} for f, c in sorted(cells.items())},
        "ironclad_a10_runs": sum(c[0] for c in cells.values()),
        "exam_ids_old": len(old),
        "exam_ids_old_still_in_file": len(seen_old),
        "exam_ids_old_in_bucket_0": sum(1 for i in old if exam_bucket(i) == 0),
        "exam_ids_new_bucket_0_in_file": len(exam_new),
        "exam_ids_union": len(union),
        "old_exam_runs_added_to": len(exam_new - old),
    }
    with open(os.path.join(out_dir, "fifths.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: fifths.py <a10_vanilla.jsonl.gz> <old_exam_ids.txt> <out_dir>")
    main(*sys.argv[1:4])
