"""tools/vrun_residuals.py: the residual and gap cells, the elite margin, the recorded Act 1 head and the exploration cost."""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import vrun_residuals as vr  # noqa: E402


def decision(kind_nodes, values, chosen, floor=5, act=0, p_floor=None, dtype="map"):
    if dtype == "map":
        options = [{"kind": "map.node", "node": [i, 1, t]} for i, t in enumerate(kind_nodes)]
    else:
        options = [{"kind": k} for k in kind_nodes]
    return {"type": dtype, "floor": floor, "state": {"act_index": act}, "options": options, "values": values, "chosen": chosen,
            "p_floor": p_floor}


def write_job(root: Path, runs: list[dict]) -> None:
    shards = root / "j-selfplay" / "shards"
    shards.mkdir(parents=True)
    (shards / "shards.json").write_text(json.dumps({"generation": 9}))
    with gzip.open(shards / "r0000.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")


def test_explore_cost_is_zero_for_argmax_and_grows_with_tau():
    assert vr.explore_cost([3.0, 2.0], 0.0, 0.0) == (0.0, 0.0)
    lost, other = vr.explore_cost([3.0, 2.9], 0.1, 0.0)
    p2 = 1 / (1 + math.e)
    assert math.isclose(lost, 0.1 * p2) and math.isclose(other, p2)
    assert vr.explore_cost([3.0, 2.9], 0.25, 0.0)[1] > other


def test_what_taken_splits_map_choices_by_an_elite_on_offer():
    assert vr.what_taken(decision([1, 2], [1.0, 0.5], 0)) == "map:M(E offered)"
    assert vr.what_taken(decision([1, 3], [1.0, 0.5], 0)) == "map:M"
    assert vr.what_taken(decision([2, 1], [1.0, 0.5], 0)) == "map:E"
    assert vr.what_taken(decision(["card.take", "card.skip"], [1.0, 0.5], 1, dtype="card_reward")) == "card.skip"


def test_the_scan_reads_residuals_margins_and_the_recorded_head(tmp_path):
    pf_kill = [0.0] * 17 + [1.0] + [0.0] * 35  # all mass on floor 18: an Act 1 kill
    runs = [{"policy": {"tau": 0.0, "eps": 0.0}, "outcome": {"final_floor": 20, "won": False},
             "decisions": [decision([1, 2], [18.0, 17.0], 0, p_floor=pf_kill)]},
            {"policy": {"tau": 0.0, "eps": 0.0}, "outcome": {"final_floor": 17, "won": False},
             "decisions": [decision([1, 2], [18.5, 18.0], 0, p_floor=pf_kill)]}]
    write_job(tmp_path, runs)
    out = tmp_path / "out.json"
    assert vr.main(["--runs-root", str(tmp_path), "--gens", "9", "--explore", "0.1,0.0", "--out", str(out)]) == 0
    doc = json.loads(out.read_text())
    cell = doc["cells"]["act1|*|*"] if "act1|*|*" in doc["cells"] else None
    assert cell is None  # fewer than 20 decisions: suppressed
    assert doc["runs"] == 2 and doc["decisions"] == 2 and doc["chosen_not_best"] == 0
    assert doc["elite_margin"]["act1"]["n"] == 2 and doc["elite_margin"]["act1"]["taken_share"] == 0.0
    head = doc["recorded_act1_head"]
    assert head["rows"] == 2 and head["kill_rate"] == 0.5 and head["mean_predicted"] == 1.0
    assert doc["explore_act1"]["decisions"] == 2
