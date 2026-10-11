"""Seed pools and seed-block hashes for pre-registration (design v1.1 §5.2, §7.4).

Seeds use the game's alphabet, 0-9A-Z without I and O (the game folds those into 1 and 0:
r33hab/sts2 src/Sts2Emulator/Core/Rng/SeedHelper.cs:12-24), at the game's default length 10
(r33hab/sts2 scripts/capture_sweep.py:61). The scheme mirrors r33hab's eval sets
(rl/run_train/DESIGN.md:1603-1609) with Spireline's own tag, so the pools cannot coincide
with r33hab's files except by chance:

    seed(pool, block, i) = pool + 9 base-34 digits of
        blake2b(f"spireline-v1:{pool}:{block}:{i}", digest_size=16), read little-endian,
        least significant digit first; a seed already in the block is skipped.

    block_hash(seeds) = "sha256:" + sha256("\\n".join(seeds) + "\\n")

Pools, disjoint by first character: T (train), E (evaluation: 20 fresh blocks of 2,000, one
per promotion, never reused), F (final test: 2,000, touched once per phase gate), P (oracle
positions). These seeds drive the emulator only; the live game's seed is never read.
"""

from __future__ import annotations

import hashlib

ALPHABET = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
SEED_LENGTH = 10
TAG = "spireline-v1"
POOLS = {"T": "train", "E": "evaluation", "F": "final test", "P": "oracle positions"}


def seed_at(pool: str, block: int, i: int, tag: str = TAG) -> str:
    if pool not in POOLS:
        raise ValueError(f"unknown pool {pool!r}")
    n = int.from_bytes(hashlib.blake2b(f"{tag}:{pool}:{block}:{i}".encode(), digest_size=16).digest(), "little")
    digits = []
    for _ in range(SEED_LENGTH - 1):
        n, r = divmod(n, len(ALPHABET))
        digits.append(ALPHABET[r])
    return pool + "".join(digits)


def block_seeds(pool: str, block: int, size: int, tag: str = TAG) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    i = 0
    while len(out) < size:
        s = seed_at(pool, block, i, tag)
        i += 1
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def block_hash(seeds: list[str]) -> str:
    return "sha256:" + hashlib.sha256(("\n".join(seeds) + "\n").encode("ascii")).hexdigest()


def manifest(pool: str, blocks: int, size: int, tag: str = TAG) -> dict[str, str]:
    """{f"{pool}{block:02d}": block_hash} for blocks 0..blocks-1."""
    return {f"{pool}{b:02d}": block_hash(block_seeds(pool, b, size, tag)) for b in range(blocks)}


if __name__ == "__main__":  # print the pre-registration block hashes
    for pool, n_blocks in (("E", 20), ("F", 1)):
        for name, h in manifest(pool, n_blocks, 2000).items():
            print(name, h)
