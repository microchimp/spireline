"""Simulated coverage of both confidence sequences under optional stopping (design §1.4).

A confidence sequence is valid if P(mu in CS_t for all t) >= 1 - alpha. Time-uniform
coverage implies coverage at any stopping time, including the adversarial one used here:
stop at the first t where the interval misses mu (or at T if it never does). So we measure
the fraction of seeded paths whose interval covers mu at every t <= T, and require >= 95%.

Positive control: a fixed-n 95% Wald interval re-checked after every observation (the
"peeking" the design forbids) must fail this test on the same paths, which shows the
harness can detect an anytime-invalid procedure.

Budget: the whole module runs in a few seconds; it must stay under 20 s.
"""

import time

import numpy as np
import pytest

from spireline.eval import stats as S

ALPHA = 0.05


def _time_uniform_coverage(lower: np.ndarray, upper: np.ndarray, mu: float) -> float:
    covered = (lower <= mu) & (mu <= upper)
    return float(np.mean(covered.all(axis=-1)))


def _peeking_wald_coverage(x: np.ndarray, mu: float, t0: int = 10) -> float:
    t = np.arange(1, x.shape[1] + 1)
    mean = np.cumsum(x, axis=1) / t
    var = np.maximum(np.cumsum(x * x, axis=1) / t - mean**2, 1e-12)
    half = 1.959964 * np.sqrt(var / t)
    lo, hi = (mean - half)[:, t0 - 1 :], (mean + half)[:, t0 - 1 :]
    return _time_uniform_coverage(lo, hi, mu)


@pytest.mark.slow
def test_empirical_bernstein_cs_coverage_under_optional_stopping():
    start = time.perf_counter()
    rng = np.random.default_rng(20261010)
    P, T = 2000, 1000
    cases = []
    # (1) paired Bernoulli outcomes (a win/loss battery): d = A - B in {-1, 0, 1};
    #     B copies A with prob 0.85, else is an independent Bernoulli(0.25): E[d] = 0.0075
    a = rng.random((P, T)) < 0.30
    b = np.where(rng.random((P, T)) < 0.85, a, rng.random((P, T)) < 0.25)
    d = a.astype(float) - b.astype(float)
    cases.append(("paired Bernoulli", d, float(0.30 - (0.85 * 0.30 + 0.15 * 0.25))))
    # (2) paired L0-like utilities: two correlated Beta draws in [0, 1], difference in [-1, 1]
    u = rng.beta(5, 2, (P, T))
    v = np.clip(u + rng.normal(-0.02, 0.06, (P, T)), 0, 1)
    # E[u - v] under clipping has no closed form; take it from a 4M-draw independent sample
    # (Monte Carlo error ~3e-5, far below any CS width here).
    big_u = np.random.default_rng(1).beta(5, 2, 4_000_000)
    big_v = np.clip(big_u + np.random.default_rng(2).normal(-0.02, 0.06, 4_000_000), 0, 1)
    cases.append(("paired Beta utilities", u - v, float(np.mean(big_u - big_v))))
    for name, x, mu in cases:
        cs = S.eb_confseq(x, -1.0, 1.0, ALPHA)
        cov = _time_uniform_coverage(cs.lower, cs.upper, mu)
        assert cov >= 0.95, (name, cov)
        peek = _peeking_wald_coverage(x, mu)
        assert peek < 0.93, (name, peek)  # positive control: peeking a fixed-n CI fails
    assert time.perf_counter() - start < 20


@pytest.mark.slow
def test_betting_cs_coverage_under_optional_stopping():
    start = time.perf_counter()
    rng = np.random.default_rng(1010)
    P, T, G = 1000, 500, 250  # P=2000 offline: coverage 0.967-0.990 (LOG.md)
    for name, draw, mu in (
        ("Bernoulli(0.2)", lambda: (rng.random(T) < 0.2).astype(float), 0.2),
        ("Beta(2, 5)", lambda: rng.beta(2, 5, T), 2 / 7),
    ):
        xs = np.stack([draw() for _ in range(P)])
        lows, highs = np.empty((P, T)), np.empty((P, T))
        for i in range(P):
            cs = S.betting_confseq(xs[i], ALPHA, grid_size=G)
            lows[i], highs[i] = cs.lower, cs.upper
        cov = _time_uniform_coverage(lows, highs, mu)
        assert cov >= 0.95, (name, cov)
        peek = _peeking_wald_coverage(xs, mu)
        assert peek < 0.93, (name, peek)
    assert time.perf_counter() - start < 20
