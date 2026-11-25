# Lane 7: the judge's minimum Act 3 gain is now a setting (`--min-gain`)

Written 2026-11-19 by the Sonnet lane. Landed on fork main as `24afec9c` (branch `feat/min-gain`, fast-forward, pushed 09:33Z). Gate: Python-only, full mode, 6,450 tests, 0 new failures against the 60-failure baseline, 4 flakes that pass alone; evidence in `D:/spireline/logs/fork-tests/24afec9c.txt`.

## What changed

The judge promotes a candidate by route A when two things hold on the paired runs: the one-sided lower bound of the gain in runs past the first Act 3 boss is above 0 (alpha 0.005), and the mean gain is at least a minimum, until now a fixed 1.0 per 100 runs. The orchestrator is lowering that minimum to 0.5 (D68 addendum 3). It is now a setting that every judgement records, not a silent edit of the constant (`keep_v2.MIN_GAIN` is still 1.0 and nothing changes it).

* `tools/lab/keep_v2.py`: a `min_gain` argument (default `MIN_GAIN`) on `judge`, `judge_v3`, `route_a`, `route_a_v3`, `seq_call`, `seq_call_v3`, `futility_routes`, `futility_call`, plus `check_min_gain` (finite, at least 0). The funnel's refusal of a dead route A, its early promotion, the futility stop and the extension rule (minimum holds, bound does not) all read the same value, so a candidate cannot be stopped at 1.0 while the verdict would pass it at 0.5.
* `rl/gen_loop.py`: threaded through `keep_v2_verdict`, `funnel`, `futility_check`, `promote`, `rejudge` and `run_promote_subprocess`; `min_gain_of` resolves it (an error under rule v1, which has no such minimum).
* `rl/gen0.py`: `--min-gain <float>` on `train`, `promote` and `rejudge` (default 1.0, at least 0). `train` passes it to its judging child and to the extension's second block, and stops before training if the rule judging is v1.
* Recorded: `keep_v2.min_gain` and `keep_v2.routes.A.min_gain` in every verdict (as before). `decision.min_gain` and the words `min gain 0.5` right after the rule name in the ledger's guard cell (`v3 min gain 0.5 route A | ...`) appear only when the value is not 1.0. I chose "only when not 1.0" because the brief also asks for the default path to write byte-identical decisions; an absent field means 1.0, and `keep_v2.min_gain` always says.

## Figures

* Tests: `tests/python/test_min_gain.py`, 30 tests on constructed data. Block A (4,000 pairs, gain +0.975 per 100, bound about +0.6): refused at 1.0, promoted on route A at 0.5. Block B (2,000 pairs, +0.7, bound below 0): not promoted at 0.5 or at any minimum (the bound decides); under v3 it is an extension at 0.5 and a plain refusal at 1.0; not extended twice, not extended on a block the funnel stopped. The funnel (dead route A, eligibility) and the futility need move with the value.
* Default path unchanged: the same 46 judgements (rejudge, promote, and the funnel, under v1, v2 and v3, on three blocks) written by fork main `4f2757a2` and by the branch compare identical byte for byte (promotion.json, ledger row, funnel looks), apart from a marker I put in the file to tell the trees apart.

## Not done

* `LAB/jobs.json` is the orchestrator's: add the two tokens `"--min-gain", "0.5"` to the train job's `cmd` list (after `"--keep-rule", "v3"`), only after this is on fork main (the lab tree moves to main at its presort); before that the train command would not recognise the flag and the job would fail. Do it before a `ready-*` marker is written.
* Not wired: `rl/round1.py` (the old rounds script) and the retro tools (`tools/verdict_covariate_retro.py`, `ledger_strict.py`, `act3_boss_table.py`) keep the default; they read past blocks under the rule then in force.
* No emulator was run; the check used stubbed arms.

## Repeat the check

From `D:/spireline/fork/wt-min-gain`: `D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p test_min_gain.py` (needs a built `out/`, API 40). A dry run on a real block: `gen0.py rejudge ... --keep-rule v3 --min-gain 0.5 --out DIR`.
