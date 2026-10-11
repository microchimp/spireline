"""Worlds needed to reach a CS half-width, vs the fixed-n figure of design §4.3 (LOG.md 2026-10-10).

Paired L0 differences are simulated as Normal(0, sigma) clipped to the a-priori range [-1, 1].
Run: ~/.venvs/spireline/bin/python scripts/cs_width_probe.py
"""

import numpy as np

from spireline.eval import stats as S

T = 6000
rng = np.random.default_rng(1)
print("sigma(pts)  h(pts)  fixed-n  betting  EB")
for sigma in (0.03, 0.05, 0.08):
    d = np.clip(rng.normal(0, sigma, T), -1, 1)
    eb = S.eb_confseq(d, -1, 1).half_width
    bet = 2 * S.betting_confseq((d + 1) / 2, grid_size=4000).half_width  # back to [-1, 1] units
    for h in (0.01, 0.005):
        first = lambda w: int(np.argmax(w <= h)) + 1 if (w <= h).any() else f">{T}"
        print(f"{sigma * 100:9.0f}  {h * 100:6.1f}  {S.n_for_half_width(sigma, h):7.0f}  {first(bet)!s:>7}  {first(eb)!s:>5}")
