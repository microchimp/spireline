# Lane 7: the judge's minimum Act 3 gain becomes a parameter

Read `COMMON.md` in this folder first. Worktree `D:/spireline/fork/wt-min-gain`, branch `feat/min-gain`, from fork `main` (at `4f2757a2` or later). Sonnet lane. No heavy work at all (no emulator runs). **Land by 10:10Z on 2026-11-19 or stop without landing and report** (the real-game block then holds the machine until about 21:00Z and the orchestrator lands your branch after it). Memo `MIN-GAIN.md` here, half a page.

## What and why

The judge (`tools/lab/keep_v2.py`, rule `keep-v3-2026-11-18`) promotes a candidate by route A when two checks hold on the pooled paired runs: the one-sided lower bound of the gain in runs past the first Act 3 boss (per 100 runs) is above 0 at alpha 0.005, and the mean gain is at least `MIN_GAIN = 1.0`. The orchestrator is lowering that minimum to 0.5 from the next judgement (D68 addendum 3). It must be a recorded parameter, not a silent edit of the constant.

## Tasks

1. `--min-gain <float>` on `rl/gen0.py train` (default 1.0) and on every other entry point that reaches `keep_v2`'s decision (the re-judge path used as `rejudge --pool-block`; find them with `grep -rn keep_v2 rl/ tools/`). Pass it into the decision functions as a parameter or a small settings object: no mutation of a module global at import, and the default path must produce byte-identical `promotion.json` decisions to today's (the existing `min_gain` fields already in the verdict keep their place).
2. Record it: `decision.min_gain` in the verdict, and the `promotions.tsv` note line gets `min gain 0.5` after the rule name when the value is not 1.0 (unchanged when it is).
3. Tests on a tiny fixture in `tests/python/`: the default reproduces today's decision on a case with mean +0.975 and bound above 0 (refused by the minimum); `--min-gain 0.5` on the same case promotes; a case with mean +0.7 and bound below 0 is still not promoted at 0.5 (the bound check is untouched); the `extend` logic (`keep_v2.py` line about 427: `min_gain` holds and `deep_bound` does not) uses the parameter.
4. Python-only gate and landing per COMMON.md (lock rule: wait, never overwrite). Report in five lines: the sha and gate counts, the exact flag text the orchestrator adds to the lab's `train` job command (the orchestrator edits `LAB/jobs.json`, not you), what is not done, your context size.
