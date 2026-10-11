"""spireline.eval.stats against the design v1.1 §7.3 table and known values.

Formulas (documented in stats.py):
  unpaired  n = [z_{1-a/2} sqrt(2 pbar qbar) + z_{1-b} sqrt(p1 q1 + p2 q2)]^2 / (p1 - p2)^2
  McNemar   n = [z_{1-a/2} sqrt(psi) + z_{1-b} sqrt(psi - d^2)]^2 / d^2          (Connor 1987)
  TOST      n = (z_{1-a} + z_{1-b/2})^2 psi / D^2                                   (true gap 0)
alpha = 0.05, power = 0.80. The §7.3 table rounds the exact value to the nearest integer;
`SampleSize.n` is the ceiling, so we accept n in {table, table + 1} and |exact - table| < 1.
"""

import math

import numpy as np
import pytest

from spireline.eval import stats as S


def _close_to_table(r: S.SampleSize, table: int) -> None:
    assert abs(r.exact - table) < 1.0, (r.exact, table)
    assert r.n in (table, table + 1)
    assert round(r.exact) == table


@pytest.mark.parametrize(
    "p1,p2,table", [(0.20, 0.25, 1094), (0.10, 0.15, 686), (0.05, 0.10, 434), (0.20, 0.30, 293)]
)
def test_unpaired_table(p1, p2, table):
    r = S.n_two_proportions(p1, p2)
    _close_to_table(r, table)
    assert S.power_two_proportions(p1, p2, r.n) == pytest.approx(0.80, abs=0.01)


def test_unpaired_headline_1094():
    assert S.n_two_proportions(0.20, 0.25).n == 1094


@pytest.mark.parametrize("psi,table", [(0.10, 312), (0.15, 469), (0.25, 783), (0.35, 1096)])
def test_mcnemar_table(psi, table):
    r = S.n_mcnemar(0.05, psi)
    _close_to_table(r, table)
    assert S.power_mcnemar(0.05, psi, r.n) == pytest.approx(0.80, abs=0.01)


def test_mcnemar_headline_469():
    assert S.n_mcnemar(0.05, 0.15).n == 469


@pytest.mark.parametrize("psi,table", [(0.05, 171), (0.10, 343), (0.15, 514), (0.20, 685)])
def test_tost_table(psi, table):
    r = S.n_tost_paired(0.05, psi)
    _close_to_table(r, table)
    assert S.power_tost_paired(0.05, psi, r.n) == pytest.approx(0.80, abs=0.01)


def test_tost_headline_343():
    assert S.n_tost_paired(0.05, 0.10).n == 343


def test_tost_nonzero_true_gap_needs_more_pairs():
    r0, r1 = S.n_tost_paired(0.05, 0.10), S.n_tost_paired(0.05, 0.10, true_diff=0.01)
    assert r1.n > r0.n
    assert S.power_tost_paired(0.05, 0.10, r1.n, true_diff=0.01) >= 0.80


def test_wilson_fablebot_71_of_343():
    lo, hi = S.wilson_interval(71, 343)
    assert (round(100 * lo, 1), round(100 * hi, 1)) == (16.7, 25.3)


def test_wilson_edges():
    assert S.wilson_interval(0, 10)[0] == 0.0
    assert S.wilson_interval(10, 10)[1] == 1.0
    with pytest.raises(ValueError):
        S.wilson_interval(11, 10)


def test_mde_paired_mean_matches_7_2():
    assert S.mde_paired_mean(3, 400) == pytest.approx(0.42, abs=0.005)
    assert S.mde_paired_mean(5, 400) == pytest.approx(0.70, abs=0.005)


def test_promotion_mde_is_0_425_not_0_44():
    # §7.3 states MDE ~0.44 floors for sigma 6, n 2000, one-sided alpha 0.01, 80% power.
    # The formula gives 0.425; recorded as a discrepancy in LOG.md (no test asserts 0.44).
    assert S.mde_paired_mean(6, 2000, alpha=0.01, two_sided=False) == pytest.approx(0.425, abs=0.001)


def test_half_width_worlds_match_4_3():
    # §4.3: Tier A at sigma 3-8 L0 points needs 35-246 worlds for h = 1 point, 138-983 for h = 0.5.
    assert math.ceil(S.n_for_half_width(3, 1)) == 35 and math.ceil(S.n_for_half_width(8, 1)) == 246
    assert math.ceil(S.n_for_half_width(3, 0.5)) == 139 and round(S.n_for_half_width(8, 0.5)) == 983


def test_mcnemar_exact_known_values():
    assert S.mcnemar_exact(10, 2).p_value == pytest.approx(2 * 79 / 4096)
    assert S.mcnemar_exact(5, 5).p_value == 1.0
    assert S.mcnemar_exact(0, 0).p_value == 1.0
    assert S.mcnemar_exact(2, 10).p_value == S.mcnemar_exact(10, 2).p_value
    b, c, n = S.discordant_counts([1, 1, 0, 0, 1], [1, 0, 1, 0, 0])
    assert (b, c, n) == (2, 1, 5)


def test_tost_equivalence_decisions():
    # identical arms, 2,000 pairs, 10% discordance: equivalent at +/-5 pp
    big = S.tost_paired_proportions(100, 100, 2000, margin=0.05)
    assert big.equivalent and big.estimate == 0.0 and big.ci[0] > -0.05 and big.ci[1] < 0.05
    # same rates, 40 pairs: not enough to show equivalence
    small = S.tost_paired_proportions(2, 2, 40, margin=0.05)
    assert not small.equivalent
    # a real 8 pp gap is never equivalent at +/-5 pp
    gap = S.tost_paired_proportions(260, 100, 2000, margin=0.05)
    assert not gap.equivalent and gap.estimate == pytest.approx(0.08)


def test_cluster_bootstrap_widens_with_clustering():
    rng = np.random.default_rng(0)
    k, per = 60, 20
    effects = rng.normal(0, 1, k)
    values = np.repeat(effects, per) + rng.normal(0, 0.2, k * per)
    clusters = np.repeat(np.arange(k), per)
    clustered = S.cluster_bootstrap(values, clusters, seed=1)
    naive = S.cluster_bootstrap(values, np.arange(k * per), seed=1)
    w_c = clustered.ci[1] - clustered.ci[0]
    w_n = naive.ci[1] - naive.ci[0]
    assert w_c > 2.5 * w_n  # design effect ~ 1 + (per - 1) * ICC is large here
    assert clustered.n_clusters == k and naive.n_clusters == k * per
    again = S.cluster_bootstrap(values, clusters, seed=1)
    assert again.ci == clustered.ci  # seeded


def test_cluster_bootstrap_generic_stat_matches_mean_path():
    rng = np.random.default_rng(3)
    values = rng.normal(0, 1, 300)
    clusters = rng.integers(0, 30, 300)
    fast = S.cluster_bootstrap(values, clusters, n_boot=2000, seed=5)
    slow = S.cluster_bootstrap(values, clusters, n_boot=2000, seed=5, stat=np.median)
    assert fast.estimate == pytest.approx(values.mean())
    assert slow.estimate == pytest.approx(np.median(values))
    assert fast.ci[0] < fast.estimate < fast.ci[1]
    assert slow.ci[0] <= slow.estimate <= slow.ci[1]


def test_streaming_cs_match_batch():
    rng = np.random.default_rng(11)
    d = np.clip(rng.normal(0.02, 0.1, 300), -1, 1)
    batch = S.eb_confseq(d, -1, 1)
    eb = S.EmpiricalBernsteinCS(-1, 1)
    for t, x in enumerate(d, 1):
        lo, hi = eb.update(float(x))
        assert (lo, hi) == pytest.approx(batch.at(t), abs=1e-12)
    y = rng.beta(2, 5, 300)
    bb = S.betting_confseq(y, grid_size=200)
    bs = S.BettingCS(grid_size=200)
    for t, x in enumerate(y, 1):
        lo, hi = bs.update(float(x))
        assert (lo, hi) == pytest.approx(bb.at(t), abs=1e-12)


def test_cs_shrink_and_validate_inputs():
    rng = np.random.default_rng(5)
    x = rng.binomial(1, 0.3, 2000).astype(float)
    eb = S.eb_confseq(x, 0, 1)
    bet = S.betting_confseq(x)
    for cs in (eb, bet):
        assert cs.half_width[99] > cs.half_width[1999]
        lo, hi = cs.at(2000)
        assert lo < 0.3 < hi and hi - lo < 0.15
    with pytest.raises(ValueError):
        S.eb_confseq([0.5, 1.5], 0, 1)
    with pytest.raises(ValueError):
        S.betting_confseq([-0.1, 0.5])


def test_stitched_boundary_at_m_is_the_epoch_zero_bound():
    # l(m) = log(zeta(s) / alpha): the first epoch spends alpha / zeta(s).
    from scipy.special import zeta

    m, c, a, eta, s = 1.0, 0.0, 0.05, 2.0, 1.4
    b = float(S.stitched_boundary(m, a, c, m, eta, s))
    k1 = (eta**0.25 + eta**-0.25) / math.sqrt(2)
    assert b == pytest.approx(k1 * math.sqrt(m * math.log(zeta(s, 1) / a)))
