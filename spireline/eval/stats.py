"""Statistics for Spireline's labels and batteries (design v1.1 §1.4, §4.3, §7.2-7.4).

Fixed-n tools
  wilson_interval            Wilson score interval for a binomial proportion.
  mcnemar_exact              Exact conditional McNemar test (binomial on discordant pairs).
  tost_paired_proportions    Two one-sided tests for equivalence of paired proportions.
  cluster_bootstrap          Percentile bootstrap resampling whole clusters (fights or runs).

Anytime-valid tools (confidence sequences: valid at every t simultaneously, so they may be
checked after every new world and stopped at any data-dependent time)
  eb_confseq / EmpiricalBernsteinCS
      Empirical-Bernstein CS for the mean of observations bounded in [lo, hi]; the paired
      difference of two L0 utilities lies in [-1, 1]. Howard, Ramdas, McAuliffe & Sekhon
      (2021), Ann. Statist. 49(2), arXiv:1810.08240: Theorem 4 (the centred sum
      S_t = sum(X_i - mu) is sub-exponential, hence sub-gamma, with variance process
      V_t = sum (X_i - Xhat_{i-1})^2 for any predictable [lo, hi]-valued Xhat, scale
      c = hi - lo) combined with the polynomial stitched boundary of Theorem 1 / eq. (10):
          S_alpha(v) = k1 sqrt(v l(v)) + k2 c l(v),   v -> max(v, m)
          l(v) = s log log(eta v / m) + log(zeta(s) / (alpha log(eta)^s))
          k1 = (eta^(1/4) + eta^(-1/4)) / sqrt(2),   k2 = (sqrt(eta) + 1) / 2
      applied to X and to -X at alpha/2 each. Defaults eta = 2, s = 1.4.
  betting_confseq / BettingCS
      Hedged-capital betting CS for the mean of [0, 1] observations. Waudby-Smith & Ramdas
      (2024), JRSS-B 86(1), arXiv:2010.09686: K_t^+(m) = prod(1 + lam_i^+(m)(X_i - m)),
      K_t^-(m) = prod(1 - lam_i^-(m)(X_i - m)), K^± = max(theta K^+, (1-theta) K^-),
      CS_t = {m : K_t^±(m) < 1/alpha}, with the predictable plug-in bet
          lam_t = sqrt(2 log(2/alpha) / (sighat^2_{t-1} t log(1 + t))),
          lam^+ = min(lam_t, trunc / m),  lam^- = min(lam_t, trunc / (1 - m)),
          muhat_t = (1/2 + sum X) / (t + 1),  sighat^2_t = (1/4 + sum (X_i - muhat_i)^2) / (t + 1).
      theta = 1/2, trunc = 1/2. Validity: theta K^+ + (1-theta) K^- is a nonnegative
      martingale at m = mu, so Ville's inequality bounds the crossing probability by alpha.

Planning
  n_two_proportions / power_two_proportions   unpaired, two-sided, pooled null variance
      n = [z_{1-a/2} sqrt(2 pbar qbar) + z_{1-b} sqrt(p1 q1 + p2 q2)]^2 / (p1 - p2)^2  (Fleiss).
  n_mcnemar / power_mcnemar   paired, discordance psi, difference delta (Connor 1987)
      n = [z_{1-a/2} sqrt(psi) + z_{1-b} sqrt(psi - delta^2)]^2 / delta^2.
  n_tost_paired / power_tost_paired   paired equivalence at margin D, Wald SE sqrt((psi - d^2)/n)
      true d = 0:  n = (z_{1-a} + z_{1-b/2})^2 psi / D^2.
  mde_paired_mean   (z_{1-a/2} + z_{1-b}) sigma / sqrt(n)   (design §7.2: 2.8 sigma / sqrt(n)).
  n_for_half_width  (z sigma / h)^2   (design §4.3 derivation).

`SampleSize.exact` is the unrounded formula value and `SampleSize.n` its ceiling. The
design's §7.3 table rounds to the nearest integer, so a few entries there are one below
the ceiling (434 vs 435, 293 vs 294, 171 vs 172, 685 vs 686, 1,096 vs 1,097).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from scipy import stats as _st
from scipy.special import zeta as _zeta

# --------------------------------------------------------------------------- helpers


def _z(p: float) -> float:
    return float(_st.norm.ppf(p))


def _check_alpha(alpha: float) -> None:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")


# --------------------------------------------------------------------------- Wilson


def wilson_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (two-sided, level 1 - alpha)."""
    _check_alpha(alpha)
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("need n > 0 and 0 <= k <= n")
    z = _z(1 - alpha / 2)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    lo = 0.0 if k == 0 else max(0.0, centre - half)  # exact endpoints at the boundary
    hi = 1.0 if k == n else min(1.0, centre + half)
    return lo, hi


# --------------------------------------------------------------------------- McNemar


@dataclass(frozen=True, slots=True)
class McNemarResult:
    b: int  # pairs where arm A succeeded and arm B failed
    c: int  # pairs where arm B succeeded and arm A failed
    p_value: float


def mcnemar_exact(b: int, c: int) -> McNemarResult:
    """Exact two-sided McNemar: 2 * P(Binom(b + c, 1/2) <= min(b, c)), capped at 1."""
    if b < 0 or c < 0:
        raise ValueError("counts must be non-negative")
    n = b + c
    p = 1.0 if n == 0 else min(1.0, 2.0 * float(_st.binom.cdf(min(b, c), n, 0.5)))
    return McNemarResult(b, c, p)


def discordant_counts(a: Sequence[bool], b: Sequence[bool]) -> tuple[int, int, int]:
    """(b, c, n) for paired binary outcomes: b = A only, c = B only."""
    x, y = np.asarray(a, bool), np.asarray(b, bool)
    if x.shape != y.shape:
        raise ValueError("paired arrays must have the same shape")
    return int(np.sum(x & ~y)), int(np.sum(~x & y)), int(x.size)


# --------------------------------------------------------------------------- TOST


@dataclass(frozen=True, slots=True)
class TOSTResult:
    estimate: float  # p_A - p_B
    se: float
    ci: tuple[float, float]  # the (1 - 2 alpha) interval that TOST is equivalent to
    p_lower: float  # H0: d <= -margin
    p_upper: float  # H0: d >= +margin
    p_value: float
    equivalent: bool
    margin: float
    alpha: float


def tost_paired_proportions(b: int, c: int, n: int, margin: float = 0.05, alpha: float = 0.05) -> TOSTResult:
    """TOST for paired proportions with the Wald SE of the paired difference.

    d = (b - c) / n,  Var(d) = ((b + c)/n - d^2) / n. Equivalence is declared when both
    one-sided tests reject at alpha, which is the same as the (1 - 2 alpha) CI lying
    inside (-margin, +margin).
    """
    _check_alpha(alpha)
    if n <= 0 or b < 0 or c < 0 or b + c > n:
        raise ValueError("need n > 0 and 0 <= b + c <= n")
    if margin <= 0:
        raise ValueError("margin must be positive")
    d = (b - c) / n
    var = max(((b + c) / n - d * d) / n, 0.0)
    se = math.sqrt(var)
    zc = _z(1 - alpha)
    if se == 0.0:
        inside = -margin < d < margin
        p_l = p_u = 0.0 if inside else 1.0
    else:
        p_l = float(_st.norm.sf((d + margin) / se))
        p_u = float(_st.norm.sf((margin - d) / se))
    p = max(p_l, p_u)
    return TOSTResult(d, se, (d - zc * se, d + zc * se), p_l, p_u, p, p < alpha, margin, alpha)


# --------------------------------------------------------------------------- cluster bootstrap


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    estimate: float
    ci: tuple[float, float]
    n_boot: int
    n_clusters: int


def cluster_bootstrap(
    values: Sequence[float],
    clusters: Sequence,
    *,
    stat: Callable[[np.ndarray], float] | None = None,
    n_boot: int = 4000,
    alpha: float = 0.05,
    seed: int = 0,
) -> BootstrapResult:
    """Percentile CI from resampling whole clusters with replacement (design §7.2).

    `clusters` labels each value with its fight or run. `stat=None` is the pooled mean,
    computed from per-cluster sums (fast path); any other statistic is recomputed on the
    concatenated resample. For paired data pass the per-pair differences as `values`.
    """
    _check_alpha(alpha)
    x = np.asarray(values, float)
    g = np.asarray(clusters)
    if x.ndim != 1 or x.shape != g.shape:
        raise ValueError("values and clusters must be 1-D and the same length")
    if x.size == 0:
        raise ValueError("no data")
    _, inv = np.unique(g, return_inverse=True)
    k = int(inv.max()) + 1
    rng = np.random.default_rng(seed)
    if stat is None:
        sums = np.bincount(inv, weights=x, minlength=k)
        counts = np.bincount(inv, minlength=k).astype(float)
        w = rng.multinomial(k, np.full(k, 1.0 / k), size=n_boot).astype(float)
        boot = (w @ sums) / (w @ counts)
        est = float(x.mean())
    else:
        order = np.argsort(inv, kind="stable")
        bounds = np.searchsorted(inv[order], np.arange(k + 1))
        groups = [x[order[bounds[i] : bounds[i + 1]]] for i in range(k)]
        boot = np.empty(n_boot)
        for j in range(n_boot):
            idx = rng.integers(0, k, k)
            boot[j] = stat(np.concatenate([groups[i] for i in idx]))
        est = float(stat(x))
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return BootstrapResult(est, (float(lo), float(hi)), n_boot, k)


# --------------------------------------------------------------------------- confidence sequences


@dataclass(frozen=True)
class ConfSeq:
    """A confidence sequence: lower[t-1], upper[t-1] after t observations."""

    lower: np.ndarray
    upper: np.ndarray

    def at(self, t: int) -> tuple[float, float]:
        return float(self.lower[..., t - 1]), float(self.upper[..., t - 1])

    @property
    def half_width(self) -> np.ndarray:
        return (self.upper - self.lower) / 2


def stitched_boundary(v: np.ndarray | float, alpha: float, c: float, m: float, eta: float = 2.0, s: float = 1.4):
    """Howard et al. (2021) polynomial stitched sub-gamma boundary S_alpha(max(v, m)), one-sided."""
    _check_alpha(alpha)
    if eta <= 1 or s <= 1 or m <= 0 or c < 0:
        raise ValueError("need eta > 1, s > 1, m > 0, c >= 0")
    vv = np.maximum(np.asarray(v, float), m)
    ell = s * np.log(np.log(eta * vv / m)) + math.log(float(_zeta(s, 1)) / (alpha * math.log(eta) ** s))
    k1 = (eta**0.25 + eta**-0.25) / math.sqrt(2)
    k2 = (math.sqrt(eta) + 1) / 2
    return k1 * np.sqrt(vv * ell) + k2 * c * ell


def eb_confseq(
    x: Sequence[float] | np.ndarray,
    lo: float,
    hi: float,
    alpha: float = 0.05,
    *,
    m: float | None = None,
    eta: float = 2.0,
    s: float = 1.4,
    running_intersection: bool = True,
) -> ConfSeq:
    """Empirical-Bernstein CS (Howard et al. 2021) for the mean of [lo, hi]-bounded data.

    `x` may be 1-D (one stream) or 2-D (independent streams along axis 0, time along axis 1).
    Xhat_{i-1} is the running mean of the first i-1 observations (Xhat_0 = midpoint).
    `m` (default c^2/16) is where the boundary starts to grow; it affects width, not validity.
    """
    a = np.asarray(x, float)
    if a.ndim not in (1, 2) or a.shape[-1] == 0:
        raise ValueError("x must be a non-empty 1-D or 2-D array")
    if hi <= lo:
        raise ValueError("need hi > lo")
    if np.any(a < lo) or np.any(a > hi):
        raise ValueError("observations outside [lo, hi]")
    c = hi - lo
    m = c * c / 16 if m is None else m
    T = a.shape[-1]
    t = np.arange(1, T + 1, dtype=float)
    csum = np.cumsum(a, axis=-1)
    mid = np.full(a.shape[:-1] + (1,), (lo + hi) / 2)
    prev_mean = np.concatenate([mid, csum[..., :-1] / t[:-1]], axis=-1)
    v = np.cumsum((a - prev_mean) ** 2, axis=-1)
    b = stitched_boundary(v, alpha / 2, c, m, eta, s)
    mean = csum / t
    lower = np.clip(mean - b / t, lo, hi)
    upper = np.clip(mean + b / t, lo, hi)
    if running_intersection:
        lower = np.maximum.accumulate(lower, axis=-1)
        upper = np.minimum.accumulate(upper, axis=-1)
    return ConfSeq(lower, upper)


class EmpiricalBernsteinCS:
    """Streaming form of `eb_confseq` for racing: update() one world at a time."""

    def __init__(self, lo: float, hi: float, alpha: float = 0.05, *, m: float | None = None, eta: float = 2.0, s: float = 1.4):
        if hi <= lo:
            raise ValueError("need hi > lo")
        _check_alpha(alpha)
        self.lo, self.hi, self.alpha, self.eta, self.s = lo, hi, alpha, eta, s
        self.c = hi - lo
        self.m = self.c * self.c / 16 if m is None else m
        self.t = 0
        self.total = 0.0
        self.v = 0.0
        self._lower, self._upper = lo, hi

    def update(self, x: float) -> tuple[float, float]:
        if not self.lo <= x <= self.hi:
            raise ValueError("observation outside [lo, hi]")
        prev_mean = (self.lo + self.hi) / 2 if self.t == 0 else self.total / self.t
        self.t += 1
        self.total += x
        self.v += (x - prev_mean) ** 2
        b = float(stitched_boundary(self.v, self.alpha / 2, self.c, self.m, self.eta, self.s))
        mean = self.total / self.t
        self._lower = max(self._lower, min(self.hi, max(self.lo, mean - b / self.t)))
        self._upper = min(self._upper, min(self.hi, max(self.lo, mean + b / self.t)))
        return self.interval

    @property
    def interval(self) -> tuple[float, float]:
        return self._lower, self._upper


def _plugin_bets(x: np.ndarray, alpha: float) -> np.ndarray:
    """Predictable plug-in bets lam_t (Waudby-Smith & Ramdas), from X_1..X_{t-1} only."""
    T = x.shape[-1]
    t = np.arange(1, T + 1, dtype=float)
    mu_hat = (0.5 + np.cumsum(x)) / (t + 1)
    sig2 = (0.25 + np.cumsum((x - mu_hat) ** 2)) / (t + 1)
    sig2_prev = np.concatenate([[0.25], sig2[:-1]])
    return np.sqrt(2 * math.log(2 / alpha) / (sig2_prev * t * np.log1p(t)))


def _grid(grid_size: int) -> np.ndarray:
    if grid_size < 10:
        raise ValueError("grid_size must be >= 10")
    return (np.arange(grid_size) + 0.5) / grid_size


def betting_confseq(
    x: Sequence[float] | np.ndarray,
    alpha: float = 0.05,
    *,
    grid_size: int = 500,
    trunc: float = 0.5,
    theta: float = 0.5,
    running_intersection: bool = True,
) -> ConfSeq:
    """Hedged-capital betting CS (Waudby-Smith & Ramdas) for the mean of [0, 1] data.

    The CS is computed on a grid of candidate means and widened by one grid step on each
    side, so grid resolution can only make it wider. Binary outcomes and continuous [0, 1]
    outcomes are both fine; rescale other bounded data first (e.g. (d + 1) / 2 for d in [-1, 1]).
    """
    _check_alpha(alpha)
    a = np.asarray(x, float)
    if a.ndim != 1 or a.size == 0:
        raise ValueError("x must be a non-empty 1-D array")
    if np.any(a < 0) or np.any(a > 1):
        raise ValueError("observations outside [0, 1]")
    if not 0 < trunc < 1 or not 0 <= theta <= 1:
        raise ValueError("need 0 < trunc < 1 and 0 <= theta <= 1")
    m = _grid(grid_size)
    step = 1.0 / grid_size
    lam = _plugin_bets(a, alpha)[:, None]
    dev = a[:, None] - m[None, :]
    lam_p = np.minimum(lam, trunc / m[None, :])
    lam_m = np.minimum(lam, trunc / (1 - m[None, :]))
    log_kp = np.cumsum(np.log1p(lam_p * dev), axis=0)
    log_km = np.cumsum(np.log1p(-lam_m * dev), axis=0)
    with np.errstate(divide="ignore"):
        log_k = np.maximum(np.log(theta) + log_kp, np.log1p(-theta) + log_km)
    inside = log_k < math.log(1 / alpha)
    any_in = inside.any(axis=1)
    first = np.argmax(inside, axis=1)
    last = grid_size - 1 - np.argmax(inside[:, ::-1], axis=1)
    lower = np.where(any_in, np.clip(m[first] - step, 0, 1), np.nan)
    upper = np.where(any_in, np.clip(m[last] + step, 0, 1), np.nan)
    if not any_in.all():
        # An empty grid set (possible only far into a miscovering path): collapse to the
        # least-rejected point so the sequence stays defined; coverage tests count it.
        best = m[np.argmin(log_k, axis=1)]
        lower = np.where(any_in, lower, best)
        upper = np.where(any_in, upper, best)
    if running_intersection:
        lower = np.maximum.accumulate(lower)
        upper = np.minimum.accumulate(upper)
        upper = np.maximum(upper, lower)
    return ConfSeq(lower, upper)


class BettingCS:
    """Streaming form of `betting_confseq` for racing."""

    def __init__(self, alpha: float = 0.05, *, grid_size: int = 500, trunc: float = 0.5, theta: float = 0.5):
        _check_alpha(alpha)
        self.alpha, self.trunc, self.theta = alpha, trunc, theta
        self.m = _grid(grid_size)
        self.step = 1.0 / grid_size
        self.t = 0
        self.sum_x = 0.0
        self.sum_sq = 0.0
        self.sig2_prev = 0.25
        self.log_kp = np.zeros_like(self.m)
        self.log_km = np.zeros_like(self.m)
        self._lower, self._upper_raw = 0.0, 1.0

    def update(self, x: float) -> tuple[float, float]:
        if not 0 <= x <= 1:
            raise ValueError("observation outside [0, 1]")
        self.t += 1
        t = self.t
        lam = math.sqrt(2 * math.log(2 / self.alpha) / (self.sig2_prev * t * math.log1p(t)))
        dev = x - self.m
        self.log_kp += np.log1p(np.minimum(lam, self.trunc / self.m) * dev)
        self.log_km += np.log1p(-np.minimum(lam, self.trunc / (1 - self.m)) * dev)
        self.sum_x += x
        mu_hat = (0.5 + self.sum_x) / (t + 1)
        self.sum_sq += (x - mu_hat) ** 2
        self.sig2_prev = (0.25 + self.sum_sq) / (t + 1)
        with np.errstate(divide="ignore"):
            log_k = np.maximum(math.log(self.theta) + self.log_kp, math.log1p(-self.theta) + self.log_km)
        inside = np.flatnonzero(log_k < math.log(1 / self.alpha))
        if inside.size:
            lo = max(0.0, self.m[inside[0]] - self.step)
            hi = min(1.0, self.m[inside[-1]] + self.step)
        else:
            lo = hi = float(self.m[np.argmin(log_k)])
        self._lower = max(self._lower, lo)
        self._upper_raw = min(self._upper_raw, hi)
        return self.interval

    @property
    def interval(self) -> tuple[float, float]:
        return self._lower, max(self._upper_raw, self._lower)


# --------------------------------------------------------------------------- planning


@dataclass(frozen=True, slots=True)
class SampleSize:
    n: int  # ceiling of `exact`
    exact: float
    formula: str


def n_two_proportions(p1: float, p2: float, alpha: float = 0.05, power: float = 0.80) -> SampleSize:
    """Per-arm n for an unpaired two-sided test of p1 vs p2 (pooled null variance, no CC)."""
    _check_alpha(alpha)
    if p1 == p2:
        raise ValueError("p1 == p2")
    za, zb = _z(1 - alpha / 2), _z(power)
    pbar = (p1 + p2) / 2
    num = za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    exact = num * num / (p1 - p2) ** 2
    return SampleSize(math.ceil(exact - 1e-9), exact, "Fleiss, two-sided, pooled null variance, no continuity correction")


def power_two_proportions(p1: float, p2: float, n: int, alpha: float = 0.05) -> float:
    za = _z(1 - alpha / 2)
    pbar = (p1 + p2) / 2
    z = (abs(p1 - p2) * math.sqrt(n) - za * math.sqrt(2 * pbar * (1 - pbar))) / math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return float(_st.norm.cdf(z))


def n_mcnemar(delta: float, discordance: float, alpha: float = 0.05, power: float = 0.80) -> SampleSize:
    """Number of pairs for McNemar at difference delta = p10 - p01 and discordance psi = p10 + p01."""
    _check_alpha(alpha)
    if not 0 < abs(delta) < discordance <= 1:
        raise ValueError("need 0 < |delta| < discordance <= 1")
    za, zb = _z(1 - alpha / 2), _z(power)
    num = za * math.sqrt(discordance) + zb * math.sqrt(discordance - delta * delta)
    exact = num * num / (delta * delta)
    return SampleSize(math.ceil(exact - 1e-9), exact, "Connor (1987), two-sided")


def power_mcnemar(delta: float, discordance: float, n: int, alpha: float = 0.05) -> float:
    za = _z(1 - alpha / 2)
    z = (abs(delta) * math.sqrt(n) - za * math.sqrt(discordance)) / math.sqrt(discordance - delta * delta)
    return float(_st.norm.cdf(z))


def n_tost_paired(
    margin: float, discordance: float, true_diff: float = 0.0, alpha: float = 0.05, power: float = 0.80
) -> SampleSize:
    """Pairs for TOST equivalence of paired proportions at +/- margin (Wald SE)."""
    _check_alpha(alpha)
    if not 0 <= abs(true_diff) < margin:
        raise ValueError("need |true_diff| < margin")
    var1 = discordance - true_diff * true_diff
    if var1 <= 0:
        raise ValueError("discordance must exceed true_diff^2")
    za = _z(1 - alpha)
    if true_diff == 0:
        zb = _z(1 - (1 - power) / 2)
        exact = (za + zb) ** 2 * var1 / margin**2
        formula = "TOST, true gap 0: (z_{1-a} + z_{1-b/2})^2 psi / margin^2"
    else:
        # Solve power_tost_paired(n) = power; start from the one-sided approximation.
        zb = _z(power)
        n0 = (za + zb) ** 2 * var1 / (margin - abs(true_diff)) ** 2
        lo, hi = 1.0, max(2.0, 4 * n0)
        while power_tost_paired(margin, discordance, hi, true_diff, alpha) < power:
            lo, hi = hi, 2 * hi
        for _ in range(200):
            mid = (lo + hi) / 2
            if power_tost_paired(margin, discordance, mid, true_diff, alpha) >= power:
                hi = mid
            else:
                lo = mid
        exact = hi
        formula = "TOST, true gap != 0: numerical inversion of the two-sided power"
    return SampleSize(math.ceil(exact - 1e-9), exact, formula)


def power_tost_paired(margin: float, discordance: float, n: float, true_diff: float = 0.0, alpha: float = 0.05) -> float:
    za = _z(1 - alpha)
    se = math.sqrt((discordance - true_diff * true_diff) / n)
    p = _st.norm.cdf((margin - true_diff) / se - za) + _st.norm.cdf((margin + true_diff) / se - za) - 1
    return float(max(0.0, p))


def mde_paired_mean(sigma: float, n: int, alpha: float = 0.05, power: float = 0.80, two_sided: bool = True) -> float:
    """Minimum detectable mean difference for a paired z-test: (z_a + z_b) sigma / sqrt(n)."""
    _check_alpha(alpha)
    za = _z(1 - alpha / 2) if two_sided else _z(1 - alpha)
    return (za + _z(power)) * sigma / math.sqrt(n)


def n_for_half_width(sigma: float, half_width: float, alpha: float = 0.05) -> float:
    """Fixed-n worlds for a normal-theory half-width h at paired SD sigma: (z sigma / h)^2."""
    return (_z(1 - alpha / 2) * sigma / half_width) ** 2


__all__ = [
    "wilson_interval",
    "McNemarResult",
    "mcnemar_exact",
    "discordant_counts",
    "TOSTResult",
    "tost_paired_proportions",
    "BootstrapResult",
    "cluster_bootstrap",
    "ConfSeq",
    "stitched_boundary",
    "eb_confseq",
    "EmpiricalBernsteinCS",
    "betting_confseq",
    "BettingCS",
    "SampleSize",
    "n_two_proportions",
    "power_two_proportions",
    "n_mcnemar",
    "power_mcnemar",
    "n_tost_paired",
    "power_tost_paired",
    "mde_paired_mean",
    "n_for_half_width",
]
