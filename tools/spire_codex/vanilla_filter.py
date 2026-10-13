"""Keep only vanilla-content runs from the A10 subset.

Usage: python3 -I vanilla_filter.py <id_map.json> <a10.jsonl.gz> <out_dir>

A run is kept when its character is one of the five base characters and every
card, relic and potion id it mentions (final deck, relics, potions, and every
card/relic offered along the way) is in the emulator's vanilla id map. Ids are
compared after converting the emulator's PascalCase names to the game's
UPPER_SNAKE form. The most frequent unknown ids are reported so conversion
misses are visible.
"""

import collections
import gzip
import json
import os
import re
import sys

BASE = {"CHARACTER.IRONCLAD", "CHARACTER.SILENT", "CHARACTER.DEFECT",
        "CHARACTER.NECROBINDER", "CHARACTER.REGENT"}


def snake(name: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    s = re.sub(r"(?<=[A-Za-z])(?=[0-9])", "_", s)
    return s.upper()


def ids_in(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and (v.startswith("CARD.") or v.startswith("RELIC.") or v.startswith("POTION.")):
                out.add(v)
            else:
                ids_in(v, out)
    elif isinstance(obj, list):
        for v in obj:
            ids_in(v, out)


def main(id_map_path, src, out_dir):
    m = json.load(open(id_map_path))
    vanilla = set()
    for kind, prefix in (("cards", "CARD."), ("relics", "RELIC."), ("potions", "POTION.")):
        for name in m[kind]:
            vanilla.add(prefix + snake(name))
    unknown = collections.Counter()
    kept = collections.Counter()
    wins = collections.Counter()
    dropped = collections.Counter()
    out_path = os.path.join(out_dir, "a10_vanilla.jsonl.gz")
    with gzip.open(src, "rt") as f, gzip.open(out_path, "wt") as out:
        for line in f:
            r = json.loads(line)
            ch = r["players"][0].get("character")
            if ch not in BASE:
                dropped["modded character"] += 1
                continue
            seen = set()
            ids_in(r, seen)
            bad = [i for i in seen if i not in vanilla]
            if bad:
                dropped["modded or unknown content"] += 1
                unknown.update(bad)
                continue
            out.write(line)
            kept[ch] += 1
            if r.get("win"):
                wins[ch] += 1
    stats = {
        "kept_by_character": {c: {"runs": kept[c], "wins": wins[c]} for c in sorted(kept)},
        "dropped": dict(dropped),
        "top_unknown_ids": unknown.most_common(40),
    }
    with open(os.path.join(out_dir, "vanilla_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
