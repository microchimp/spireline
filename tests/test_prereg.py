"""The DRAFT pre-registration's seed-block hashes must match spireline.eval.seeds."""

import re
from pathlib import Path

from spireline.eval.seeds import manifest

PREREG = Path(__file__).resolve().parents[1] / "eval" / "prereg" / "phase1.yaml"


def test_prereg_block_hashes_match_seed_scheme():
    text = PREREG.read_text()
    listed = dict(re.findall(r'^\s+([EF]\d\d): "(sha256:[0-9a-f]{64})"', text, flags=re.M))
    expected = {**manifest("E", 20, 2000), **manifest("F", 1, 2000)}
    assert listed == expected


def test_prereg_targets_a10_defect_acts_1_to_3():
    import spireline

    text = PREREG.read_text()
    assert re.search(rf"^  ascension: {spireline.ASCENSION}\b", text, flags=re.M)
    assert spireline.ASCENSION == 10
    assert re.search(r"^  acts: \[1, 2, 3\]", text, flags=re.M)
    assert spireline.ACTS == (1, 2, 3)
    assert re.search(r"^  primary_track: D\b", text, flags=re.M)


def test_prereg_is_marked_draft():
    text = PREREG.read_text()
    assert re.search(r"^status: DRAFT$", text, flags=re.M)
