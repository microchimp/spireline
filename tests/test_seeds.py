import re

from spireline.eval import seeds


def test_seed_shape_and_determinism():
    s = seeds.block_seeds("E", 0, 50)
    assert s == seeds.block_seeds("E", 0, 50)
    assert all(re.fullmatch(r"E[0-9A-HJ-NP-Z]{9}", x) for x in s)  # no I, no O
    assert len(set(s)) == 50


def test_pools_and_blocks_are_disjoint():
    e = [set(seeds.block_seeds("E", b, 2000)) for b in range(20)]
    allE = set().union(*e)
    assert len(allE) == 40_000  # 20 fresh blocks of 2,000, pairwise disjoint
    f = set(seeds.block_seeds("F", 0, 2000))
    assert not (allE & f)


def test_block_hash_is_order_sensitive_and_stable():
    s = seeds.block_seeds("F", 0, 10)
    assert seeds.block_hash(s) == seeds.block_hash(list(s))
    assert seeds.block_hash(s) != seeds.block_hash(s[::-1])
    assert seeds.block_hash(s).startswith("sha256:")
