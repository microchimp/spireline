<!--
The one-page weekly scoreboard (the Tuesday edition; D68, Act 3 week). The paper itself is not edited by this file.

How it is filled (run from D:/spireline/spireline; Python is the repo's own, never `uv run`):

  1. The numbers. One command reads the lab's files, prints the table, and writes weekly-numbers-<date>.json and .md:
       .venv/Scripts/python.exe -I tools/weekly_numbers.py --out-dir D:/spireline/referee/backlog/weekly
  2. This page. Every {{key.path}} below is a value in that JSON; {{key.path:2}} rounds to 2 decimals; a value the files do not hold
     prints "no data" (never a guess). Filled page, to a file:
       .venv/Scripts/python.exe -I tools/weekly_numbers.py --fill docs/paper/SCOREBOARD-TEMPLATE.md --no-write > D:/spireline/referee/backlog/weekly/scoreboard-<date>.md
  3. The landings, one line each (edit the list down to what matters; each line is "what changed and the number it moved"):
       git -C D:/spireline/fork/sts2 log main --since="<last Tuesday 21:00Z>" --format="- %h %s" | cut -c1-140
       git -C D:/spireline/spireline log main --since="<last Tuesday 21:00Z>" --format="- %h %s" | cut -c1-140
  4. The decisions waiting on the owner (the ones HANDOFF's alerts block marks as the owner's):
       grep -n -i "owner" D:/spireline/referee/backlog/HANDOFF.md | head -20 | cut -c1-200
       grep -n "^## D" docs/DECISIONS.md | tail -5

The comment is dropped when the page is filled. Keep the page to one screen: no section grows past what is below.
-->

# Scoreboard, {{generated}}

Our AI is generation {{champion.generation}}. "The copy" is our rebuilt version of the game, where the AI practises and is judged; "the real game" is the game itself. Every rate is per 100 runs, with the range the true figure probably sits in (95 in 100) and how many runs it rests on. Humans are every finished Ironclad run at Ascension 10 in the public record (Spire Codex public run export for v0.107.1).

## The five numbers

| # | What we count | Our AI | Average human | Rests on |
|---|---|---|---|---|
| 1 | Wins in the real game | {{n1.wins.per100:2}} ({{n1.wins.lo:2}} to {{n1.wins.hi:2}}); {{n1.wins.k}} wins | {{n1.humans_per_100}} ({{n1.humans_quits_as_losses_per_100}} counting quits) | {{n1.wins.n}} real runs of generation {{n1.generation}}, block of {{n1.block_date}}, {{n1.age_days}} days old; a real block of the champion: {{n1.champion_has_real_block}} |
| 2 | Gets past the first Act 3 boss (a win, or a floor above 48): real game | {{n2.real_all.per_100_runs.per100:2}} per 100 runs ({{n2.real_all.per_100_runs.lo:2}} to {{n2.real_all.per_100_runs.hi:2}}); {{n2.real_all.per_100_arrivals.per100:1}} per 100 that reach it | {{n2.humans_per_100_runs}} per 100 runs; {{n2.humans_per_100_arrivals}} per 100 that reach it | {{n2.real_all.runs}} real runs of generation {{n2.generation}}, {{n2.real_all.arrivals}} reached the boss |
| 2 | The same, on the copy, on the seeds both hold | {{n2.copy_paired.per_100_runs.per100:2}} per 100 runs ({{n2.copy_paired.per_100_runs.lo:2}} to {{n2.copy_paired.per_100_runs.hi:2}}); {{n2.copy_paired.per_100_arrivals.per100:1}} per 100 that reach it | as above | {{n2.paired_seeds}} pairs, {{n2.copy_paired.arrivals}} reached the boss on the copy and {{n2.real_paired.arrivals}} in the real game |
| 3 | How honest the copy is: both arms end in the same act | {{n3.rows.3.same_act.per100:1}} per 100 pairs ({{n3.rows.3.same_act.lo:1}} to {{n3.rows.3.same_act.hi:1}}); Act 1 {{n3.rows.0.same_act.per100:1}}, Act 2 {{n3.rows.1.same_act.per100:1}}; copy minus real {{n3.rows.3.floor_diff.mean:2}} floors | the copy should match the game | {{n3.pairs}} pairs of generation {{n3.generation}}; alarm (a move of more than 2 points in Act 1 or 2 since the previous block): {{n3.alarm.text}} |
| 4 | Distance to winning humans, on the seeds a human won | {{n4.floors_behind_on_human_won_seeds.mean:1}} floors behind ({{n4.floors_behind_on_human_won_seeds.lo:1}} to {{n4.floors_behind_on_human_won_seeds.hi:1}}); won {{n4.seeds_won_by_some_draw}} of {{n4.seeds_human_won}} of those seeds | won all of them, by definition | exam of generation {{n4.exam_generation}}, {{n4.age_days}} days old (the champion is {{champion.generation}}) |
| 5 | This week's champion against last week's, same copy seeds: past the first Act 3 boss | {{n5.headline.champion_passed_per100:2}} against {{n5.headline.previous_passed_per100:2}}; difference {{n5.headline.diff_passed_per100:2}} (standard error {{n5.headline.diff_passed_se:2}}); wins {{n5.headline.champion_wins_per100:2}} against {{n5.headline.previous_wins_per100:2}} | - | {{n5.headline.pairs}} pairs, basis: {{n5.headline.basis}} |

A "fresh" pair is a seed no judgement of this champion used to pick it; until fresh pairs exist the gain shown is the best of several candidates and reads high.

## The stop rule (by {{stop_rule.stop_date}}, {{stop_rule.days_left}} days left)

First Act 3 boss passed per 100 that reach it: **{{stop_rule.now_per_100_arrivals:1}}** now (started at {{stop_rule.start_per_100_arrivals}}; the target is {{stop_rule.target_per_100_arrivals}}), or wins at **{{stop_rule.now_wins_per_100:2}}** per 100 (the target is {{stop_rule.target_wins_per_100}}). Fresh pairs so far: {{stop_rule.fresh_pairs}} of the {{stop_rule.pairs_needed}} the rule asks for. A real-game block of the champion confirms it: {{stop_rule.real_block_of_champion}}.

## What landed this week (one line each: what changed and the number it moved)

- (fill from the two git commands above)

## What waits on the owner

- (fill from the two commands above; leave it empty when nothing waits)
