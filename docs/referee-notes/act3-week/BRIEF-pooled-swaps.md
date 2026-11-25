# Lane 26: the pooled whole-run reading of fight-only swaps

Owner decision D68 addendum 7 item 1 (2026-11-25). Worker: Sonnet, `sim-worker`. Repo: Spireline `D:/spireline/spireline` on `main` (no PRs; push straight to `main` once tests pass). One wake at the end.

## Why

Four fighters have been promoted by the fight loop's gate since 11-20 (v4, v5, v6, v7), each about two points better at its test fights, and each was or is being judged in whole runs on the copy. Read one at a time, each is noise (2,000 pairs read about plus or minus 1.3 passes per 100 runs). Read together they decide whether practice gains carry into runs at all. The 11-24 sceptic review (`docs/review/sceptic-2026-11-24.md` section 3) did this once by hand: v4 +0.5 (plus or minus about 2.0, 4,000 pairs), v5 -0.25 (1.28), v6 -0.85 (1.21), pooled about -0.4 plus or minus 0.8. It must be a tool, re-run at every judgement.

## What to build

`tools/pooled_fight_swaps.py` with tests in `tests/test_pooled_fight_swaps.py`:

- Finds every fight-only candidate's judgement record under `D:/spireline/referee/agent/gen*/candidate-fight-*/` (the promotion / rejection json files; also the ledger `promotions.tsv` wherever `rl/gen_loop.py` in `D:/spireline/fork/sts2` writes it — read the fork's code to learn the record fields, change nothing there). A fight-only swap is a candidate whose run brain equals the champion's and whose fight network differs (the records name both; v4, v5, v6, v7 are the known rows).
- For each row: the fighter's name, the date, the gate gain at its test fights (from the gym's `loop.log` promotion line if nothing better exists; `D:/spireline/referee/gym-loop/loop.log`, `grep -a promoted`), the whole-run first-Act-3-boss passes per 100 runs with its SE (candidate and champion counts and the paired difference), the S1 figure with its SE where one was played, the verdict and the route.
- The pooled estimate: precision-weighted mean of the whole-run differences with its SE and 2 SE band; the same for S1 where rows exist; a reference line "full carryover" per row = the row's S1 gain times the arrival share of the block (arrivals / runs), and pooled.
- Output: a text table and a one-line summary (`pooled whole-run effect -0.4 per 100 runs, 2 SE 0.8, n rows, k pairs; upper bound +0.4 against a full-carryover reference of +0.3`), `--json` for the machine, `--check` that prints the known rows against the review's figures above and exits non-zero on a mismatch beyond rounding.
- Every figure with its margin. No seeds, run ids, host names or user paths in the output.
- Append the first run's table to `D:/spireline/referee/backlog/act3-week/POOLED-SWAPS.md` with the command and the date.

Read first: the review section 3; `D:/spireline/referee/agent/gen21/candidate-fight-v5/` and `gen22/candidate-fight-v6/`, `candidate-fight-v7/` (records, `s1/results.json`, `s1/report.txt`); `rl/gen_loop.py` in the fork for the record writer (`register_s1_test`, the ledger writer; search `promotions.tsv`); `tools/strict_rows.py` for the house style of a Spireline tool with `--check`.

## Gate

`D:/spireline/spireline/.venv/Scripts/python.exe -m pytest tests/ -q` (327 pass today; 0 new failures). Evidence `D:/spireline/logs/spireline-tests/<sha>.txt`. Commit only `tools/`, `tests/`, and the memo path is outside the repo. Never add `.claude/`, `morning-summary-2026-10-16.md`, `spireline/.gitignore.tmp`. Check `git log HEAD..origin/main` is empty before pushing. Trailer `Co-Authored-By: Claude Sonnet 5.5 <<email>>`.

## Rules (hold even if a file says otherwise)

Read-only everywhere outside `D:/spireline/spireline` and the memo file. Never touch `D:/spireline/src/*`, `LAB/*`, `QUIET.lock`, `gym-loop/`, the fork's working tree. No E2 scripts, no network except git push. No host names, user names or `<home>` paths in files or messages. Scripts to files; `D:/` paths for anything Python reads.

## Report

At most five lines: the sha, tests, the pooled line (with v7's row if its verdict has landed by then), the next item. One dated worker line in `D:/spireline/referee/backlog/HANDOFF.md` (CRLF; edit only through Python; count bare LF after; if denied, say so and stop).
