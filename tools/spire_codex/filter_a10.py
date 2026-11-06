"""Stream the Spire Codex v0.107.1 export and keep A10 standard single-player runs.

Usage: python3 -I filter_a10.py <export.jsonl.gz> <out_dir> [--keep-player-token]

Keeps runs with ascension 10, game_mode "standard", not abandoned, one player,
no modifiers, build v0.107.1. Drops `player_token` and per-player `badges`, and
dedupes on `run_hash` (falling back to seed + start_time). Writes
a10_standard_single.jsonl.gz and stats.json into out_dir.

`--keep-player-token` (off by default, so the published path is unchanged) keeps
each run's `player_token` in the working file, for the strong-player set
(tools/spire_codex/strong_players.py). Badges are dropped either way. A working
file written with the flag holds pseudonymous player ids: it stays under data/,
is never committed or published, and stats.json carries only counts.
"""

import collections
import gzip
import json
import os
import sys
import time


def main(src: str, out_dir: str, keep_player_token: bool = False) -> None:
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "a10_standard_single.jsonl.gz")
    seen = set()
    total = kept = dupes = bad = 0
    by_char = collections.Counter()
    wins_by_char = collections.Counter()
    killers = collections.Counter()
    reasons = collections.Counter()
    with_token = 0
    started = time.time()
    with gzip.open(src, "rt", encoding="utf-8") as f, gzip.open(out_path, "wt", encoding="utf-8") as out:
        for line in f:
            total += 1
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if r.get("ascension") != 10:
                reasons["ascension"] += 1
                continue
            if r.get("game_mode") != "standard":
                reasons["game_mode"] += 1
                continue
            if r.get("was_abandoned"):
                reasons["abandoned"] += 1
                continue
            players = r.get("players") or []
            if len(players) != 1:
                reasons["multiplayer"] += 1
                continue
            if r.get("modifiers"):
                reasons["modifiers"] += 1
                continue
            if r.get("build_id") != "v0.107.1":
                reasons["build"] += 1
                continue
            key = r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}"
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            if keep_player_token:
                with_token += bool(r.get("player_token"))
            else:
                r.pop("player_token", None)
            for p in players:
                p.pop("badges", None)
            out.write(json.dumps(r, separators=(",", ":")) + "\n")
            kept += 1
            ch = players[0].get("character", "?")
            by_char[ch] += 1
            if r.get("win"):
                wins_by_char[ch] += 1
            else:
                killers[r.get("killed_by_encounter") or r.get("killed_by_event") or "?"] += 1
            if total % 100000 == 0:
                print(f"{total:,} read, {kept:,} kept, {time.time() - started:.0f}s", flush=True)
    stats = {
        "source": os.path.basename(src),
        "read": total,
        "kept": kept,
        "duplicates_dropped": dupes,
        "unparseable": bad,
        "rejected_by": dict(reasons),
        "by_character": {c: {"runs": n, "wins": wins_by_char[c]} for c, n in by_char.most_common()},
        "top_killers_all_characters": killers.most_common(25),
        "seconds": round(time.time() - started, 1),
    }
    if keep_player_token:
        stats["player_token_kept"] = True
        stats["kept_with_player_token"] = with_token
    with open(os.path.join(out_dir, "stats.json"), "w") as fh:
        json.dump(stats, fh, indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) != 2 or flags - {"--keep-player-token"}:
        sys.exit("usage: filter_a10.py <export.jsonl.gz> <out_dir> [--keep-player-token]")
    main(args[0], args[1], "--keep-player-token" in flags)
