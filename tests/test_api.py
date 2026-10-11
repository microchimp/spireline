"""The §1.4 output contract, units ladder and verdict rules in spireline.api."""

import pytest

from spireline import api
from spireline.api import Decision, OptionRow, Verdict, classify_verdict


def _decision(**kw):
    base = dict(
        decision_id="run-7f3a:f12:card_reward",
        game_build=23811903,
        engine_sha="b745217+patches@3",
        oracle_cfg="sha256:0",
        info_state_hash="9b2d",
        track="D",
        mode="LABEL-B-gold",
        value_level="L1",
        value_units=api.l1_units(1),
        options=(
            OptionRow("Take A", 61.2, (59.4, 63.0), 620),
            OptionRow("Take B", 58.9, (57.2, 60.6), 620),
            OptionRow("Skip", None, None, 0, pruned_at="screen:V_run+deckfights"),
        ),
        best="Take A",
        p_best=0.95,
        gap=2.3,
        gap_cs95=(0.4, 4.2),
        ci_method="empirical-Bernstein CS (time-uniform)",
        epsilon=2.0,
        verdict=Verdict.DECISIVE,
        regret_ucb95_if_follow=0.0,
        ai_state="particles(k=64)",
    )
    base.update(kw)
    return Decision(**base)


def test_contract_has_every_design_field():
    c = _decision().to_contract()
    design_fields = {
        "decision_id", "game_build", "engine_sha", "oracle_cfg", "info_state_hash", "track", "mode",
        "value_level", "value_units", "options", "best", "p_best", "gap", "gap_cs95", "ci_method", "epsilon",
        "verdict", "regret_ucb95_if_follow", "regret_bound_scope", "screen_recall_dev", "pi_ref", "horizon",
        "stability", "continuation_sensitive", "currency_sensitive", "vpi_clairvoyant", "ai_state",
        "fidelity_flags", "prior", "wall_s", "usd",
    }
    assert design_fields <= set(c)
    assert c["options"][2] == {"a": "Skip", "q": None, "cs95": None, "n_worlds": 0, "pruned_at": "screen:V_run+deckfights"}
    assert c["value_units"] == "pp P(clear act 1)" and c["verdict"] == "DECISIVE"


def test_units_ladder_is_enforced():
    with pytest.raises(ValueError):
        _decision(value_level="L0", value_units="pp P(win)")  # L0 is never P(win)
    _decision(mode="LABEL-A-silver", value_level="L0", value_units=api.L0_UNITS, epsilon=1.0)
    with pytest.raises(ValueError):
        _decision(value_level="L2", value_units="L0 points")


def test_contract_guards():
    with pytest.raises(ValueError):
        _decision(verdict=Verdict.UNSUPPORTED)  # needs a fidelity flag saying why
    _decision(verdict=Verdict.UNSUPPORTED, fidelity_flags=("uncaptured_card:FOO",))
    with pytest.raises(ValueError):
        _decision(mode="LABEL-A-gold", value_level="L0", value_units=api.L0_UNITS, ai_state="ai_state_assumed")
    with pytest.raises(ValueError):
        _decision(options=(OptionRow("x", None, None, 5),))


def test_verdict_rules():
    eps = 1.0
    assert classify_verdict(2.0, (0.3, 3.7), eps, budget_exhausted=False) is Verdict.DECISIVE
    assert classify_verdict(0.5, (0.1, 0.9), eps, budget_exhausted=False) is Verdict.CLOSE  # LCB>0 but gap<eps
    assert classify_verdict(0.1, (-0.6, 0.8), eps, budget_exhausted=False) is Verdict.CLOSE
    assert classify_verdict(0.8, (-0.5, 2.1), eps, budget_exhausted=False) is None
    assert classify_verdict(0.8, (-0.5, 2.1), eps, budget_exhausted=True) is Verdict.UNCERTAIN
    assert classify_verdict(5.0, (4.0, 6.0), eps, budget_exhausted=False, unsupported=True) is Verdict.UNSUPPORTED
    with pytest.raises(ValueError):
        classify_verdict(0.0, (1.0, -1.0), eps, budget_exhausted=True)


def test_l0_utility_and_regret_bound():
    assert api.l0_utility(True, 50, 2, 80) == 0.0
    assert api.l0_utility(False, 40, 0, 80) == pytest.approx(0.75)
    assert api.l0_utility(False, 75, 2, 80) == 1.0  # capped at 1
    assert api.regret_ucb(0.4, [0.2, 0.7]) == pytest.approx(0.3)
    assert api.regret_ucb(0.4, [0.1]) == 0.0


def test_epsilon_table_matches_design():
    assert api.EPSILON["LABEL-A-gold"][2] == 0.5
    assert {k: v[2] for k, v in api.EPSILON.items() if v[0] == "L0" and k != "LABEL-A-gold"} == {
        "QUICK-combat": 1.0, "DEEP-combat": 1.0, "LABEL-A-silver": 1.0}
    assert api.EPSILON["QUICK-macro"][2] == api.EPSILON["LABEL-B-gold"][2] == 2.0


def test_budget_requires_fixed_counts_when_deterministic():
    api.Budget(mode="PLAY", sims=120)
    with pytest.raises(ValueError):
        api.Budget(mode="QUICK", max_core_s=10.0)
    api.Budget(mode="QUICK", max_core_s=10.0, deterministic=False)


def test_protocols_are_runtime_checkable():
    class UniformPrior:
        name, version = "uniform", "0"

        def __call__(self, I, legal):
            import numpy as np

            return api.PriorOut(np.zeros(len(legal)), "uniform")

    assert isinstance(UniformPrior(), api.Prior)
    assert not isinstance(object(), api.Engine)
