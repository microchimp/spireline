# Lane 10: why real-game runs at the Test Subject stalled, and why most lost track

Written 2026-11-20 by lane 10 (Sonnet 5.5). Fork `main` `dbac8428` (driver, stand-in, tests; landed); the engine commit `6538ead6` is on branch `fix/driver-stall-engine`, **not landed**: it needs the full 75-minute gate and the Act 3 replay holds the machine (script below). Words once: the *driver* is our program that plays the real game; the *copy* is our emulator, run beside it; the *stand-in* is the fixed fallback that plays the real game once the copy has lost track of it; the Test Subject is the Act 3 boss with three forms.

## What happens (checked in the code and the rows of the 2026-11-19 block)

When a form falls the Test Subject has nobody alive until its next move (it stands up on its own turn). Two things then go wrong, both from "no creature is alive":

1. **The driver offers a potion that needs an enemy, with no enemy** (`RunPlay.FightLoop`, the potion list: `AnyEnemy` potion with zero living enemies took target -1). The game refuses it (`UsePotionAction` cancels; the potion stays, nothing changes), the copy spends it, tracking is lost, and the stand-in (`lockstep.referee_only_policy`: the first card play, else the first non-end action, no memory) answers the same screen the same way 376 to 394 times until the driver's 400-action cap ends the run as `fight_unfinished`. 13 of the 14 stalled rows (the 14th lost track on an End Turn, a different cause).
2. **The copy offers actions the game does not** (found by the orchestrator's widening; `CombatEngine.ValidActions`). With no enemy standing the game lists only End Turn and what needs no aim; if that is End Turn alone the driver takes it without asking. The copy's list kept every attack card and aimed potion, so the lockstep never saw a lone End Turn to take for the copy: the game went on to the boss's next turn (212 or 313 health) while the copy stood a turn behind (enemy at 0). In 40 of these 45 rows the copy's whole legal list was aimed cards.

The copy never stalls because it has no stand-in: its player picks among all its own moves, End Turn included, and each move changes its state. It reaches the same "nobody alive" state (the Test Subject sits at 0, marked reviving) and ends the turn.

## The rows (95 Test Subject arrivals found in the rows: 84 first-form falls on floor 48, 7 more died in form one, 4 on floor 49; the orchestrator counted 96)

| what ended the run | rows |
|---|---|
| tracking kept to the end | 23 |
| lost: potion at no target (fault 1; all 13 stalled) | 13 |
| lost: copy a turn behind (fault 2) | 45 |
| lost: other differences inside the fight (1 stalled) | 13 |
| lost before the boss | 1 |

**The two fixes cover 58 of the 72 lost rows (81%); with the 23 that never lost track, 81 of 95 (85%) would have been tracked through the first form's fall.** Not known: whether tracking then holds through the later falls (the same fixes apply) and through the 13 other in-fight differences, which are ordinary fidelity gaps (enemy health off by 2 to 28, a hand, 3 to 22 HP after an End Turn). It needs a real block.

## What changed

- `referee/driver/ActionTargets.cs` (new, tested in `driver.Tests`): an enemy-aimed action is offered once per living enemy and not at all when none lives; the fight loop's cards, usable-potion filter and potion actions use it. Cards were already right; potions were not. Other target kinds: only `AnyEnemy` needs a creature chosen (Self and player potions always have the player; ally targets are unplayable alone: `CanPlay` refuses them), so no other kind has the fault. `Combat.cs` and `Setup.cs` (the fight corpus loops) already offer no potion without an enemy and are untouched.
- `referee/lockstep.py`: `StallGuard`. An answer the game ignored at an unchanged state (same hash, screen, actions, context) is not given again: End Turn instead, else the next action; after 3 ignored answers the run ends with `end: "stalled"`, the answer in `stats.stalled` and the row, the game process retired. The 400 cap stays as the last guard. `referee/envproto.py`: the row now also carries the driver's `fight_errors`, which no row carried (19 `fight_unfinished` rows could not be told apart).
- Engine commit (branch): `ValidActions` leaves out an aimed card and an aimed potion while no enemy can be hit; the solver's `AddAimed` no longer keeps a target -1 move. `Step` is unchanged. The hash-pinned files were regenerated.

## Tests and gates (all on the tips named)

Driver: `dotnet build referee/driver/SpirelineReferee.csproj -c Release`: 0 warnings, 0 errors; `dotnet test referee/driver.Tests`: 15 passed (4 new). Python (select gate, last full run under 20 h old): 602 tests on `dbac8428`, 0 new against the 60 known; new files `test_lockstep_stall.py` (15: the guard, the stand-in, `play_run` ending as `stalled` after 2 answers not 400), `test_driver_action_targets.py` (4), a case in `test_envproto.py`. Engine branch: 5 new C# tests (`NoTargetActionsTests`: legal list with and without a standing enemy, a lone End Turn, the solver's list, the boss standing again); 674 C# tests in the narrow set (potions, play legality, boss fights, the hash-pinned scans) passed; the Python select gate passed (601) on the branch with its own published `out/`. **Not run: the full gate** (42-minute C# suite, EmuDump, corpus check): `bash D:/spireline/referee/backlog/act3-week/DRIVER-STALL-engine-gate.sh` waits for a quiet machine, gates the branch and lands it (about 75 minutes; `LAND=0` gates only).

## How to verify

In the next real block (the lab's nightly job, due 11-26): no row ends `fight_unfinished` with a full bar at floor 48; the Test Subject's arrivals end by death or a pass, not `stalled`; the share of Test Subject rows with `lost` set drops from 72 of 95 (it should fall to the 13 other-difference rows plus new ones). `tools/morning_report.py` counts `fight_unfinished` only: it should also list `stalled` (Spireline, not touched here).

## The other 5 `fight_unfinished` rows (floors 37 to 46)

None is a repeat (`streak` 4 to 12), none is near the cap (the whole run asked 289 to 356 decisions; the cap is 400 actions in one fight), four never lost track (271 to 355 of 289 to 356 decisions ranked), and none is at a boss; the fifth lost track at floor 35 on a copy engine fault and again at floor 46 (the copy left the fight, the game did not). So it is not this mechanism; the driver's other exit is `idle_timeout after step N` (the game did not settle after an action; the same family as the Pael's Eye End Turn fix), which the rows could not show. They will now: the row carries `fight_errors`.

## Repeat

```
D:/spireline/venv-gpu/Scripts/python.exe -I D:/spireline/referee/backlog/act3-week/DRIVER-STALL-classify.py   # the table: the last divergence record of each Test Subject row
D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p test_lockstep_stall.py   # from the fork tree
dotnet test referee/driver.Tests/DriverPickLoop.Tests.csproj
```
