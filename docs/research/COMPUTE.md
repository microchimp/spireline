# Compute budget

Rough sizes of the main workloads, and what they cost on a home PC versus rented CPUs. Everything here is an estimate until the benchmarks in [bench/](../../bench/) are run on the actual machines.

**Assumptions.** About 1 ms per search simulation per core, and 40 to 60 core-seconds per full-length run (a winning A10 run is about 48 floors and about 800 decisions). Both are extrapolated from the upstream emulator's published Apple M4 Max figures: 58 to 72 µs per step, about 0.44 ms per combat search simulation, and 9.3 s per short rules-policy run on one core.

## Workloads

| Workload | CPU needed |
|---|---|
| All oracle labels (silver, gold and macro gold, per the design) | ~600 core-hours |
| Strong fight play: 20 rounds of expert iteration, ~2B simulations | ~560 core-hours |
| Run value: 1M full-length self-play runs | ~11k to 17k core-hours |
| Run value with fights played by a cheaper distilled policy | about a third to a fifth of that |

Per expert-iteration round: 6,400 fights × 25 decisions × 300 simulations ≈ 48M simulations.

## Where to run it

On a home PC, days ≈ core-hours ÷ (effective cores × 24). An older 8-core desktop running around the clock gives roughly 5 to 8 effective cores. That puts labels and fight play at a few days each, and 1M runs at a few months.

Rented CPUs (third-party price snapshots from June to August 2026; check current prices):

| Option | Cores | Price | Per core-hour |
|---|---|---|---|
| Hetzner CCX63, dedicated, on demand | 48 vCPU | ~$1.56/h | ~$0.033 |
| AWS c8g.48xlarge spot (Graviton, ARM) | 192 | ~$2.55/h | ~$0.013 |
| AWS c7a.48xlarge spot (AMD, x86) | 192 | ~$2.98/h | ~$0.016 |

| Workload | Rented cost | One 192-core spot machine |
|---|---|---|
| All oracle labels | ~$8 to $20 | ~3 h |
| Strong fight play | ~$7 to $18 | ~3 h |
| 1M full runs | ~$150 to $550 | ~2.5 to 4 days |

Spot machines are interrupted about 10 to 15% of the time, so jobs checkpoint and resume. The emulator build doesn't need the game's files (its generated tables are committed upstream), so a cloud machine only ever holds the emulator. Keep such machines private, because those tables are derived from the game.

## What compute doesn't buy

- Checks against the real game run at about one action per second and need a machine with the game installed.
- Simulator fidelity work against the real game.
- Engineering time, which is the real budget for a hobby project.

Detecting a 20% → 25% win-rate change needs about 1,094 runs per arm (α 0.05, 80% power). Per-decision regret on 400 benchmark positions detects about 0.4 to 0.7 L0 points. That's why the design measures decisions, not win rates.
