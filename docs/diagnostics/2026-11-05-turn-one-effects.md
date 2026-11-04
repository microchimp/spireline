# Turn-one effects after the Act 2 hand fix: what runs on a fight's first turn, and what is left (audit, 2026-11-05)

Written 2026-11-04 20:15Z (sim-worker, Sonnet). No engine code changed and nothing landed on the fork. Read: fork main `e1e94e19` (the
diff of `8db0b791` and the turn-start code it left: `CombatEngine.cs` `EndTurn`, `StartFirstTurn`, `ContinueFirstTurn`,
`FirstTurnSide`, `SideTurnStart`, `AfterPlayerTurnStartPowers`; `CombatFactory.cs` `Reset`, `DrawOpeningHand`;
`RelicEffects.cs` `ApplyBeforeOpeningHand`, `ApplyFirstTurnAfterSideTurnStart`, `ApplyStartOfPlayerTurn`, `HandDrawBonus`,
`ApplyBeforeHandDraw`, `ApplyAfterPlayerTurnStart`), the decompile for the game's turn start and for every model that hooks it (read,
not quoted), the lockstep records and stdout copies of `LAB/nightly/2026-11-03`, `-04` and `-05` (generation 11; the first two ran trees
before the fix, the third ran `e1e94e19`, which holds it), and two short copy replays on the lab's build of `e1e94e19`. The game was not run.

## 0. In plain words

The question was whether the first turn of a fight, which the copy still deals by a separate hand-written start, misses other things the
game does every turn the way it missed Pollinous Core. The lead named the draw-modifying powers (Clarity, Demesne, Tools of the Trade
and five more) and the powers' turn-start hooks.

**Answer.** Nothing that can happen on a first turn is missing. Every relic that acts at a turn start runs through one shared
function (the hand draw, the before-draw and after-draw hooks, the after-side-turn-start relics) or through a first-turn list whose
entries carry the game's own turn guard. The nights agree: hand records with Pollinous Core held (any turn) fell from 177 (11-03) and 44
(11-04) to **0** (11-05), and with Booming Conch held from 37 and 19 to 1. The powers are a different matter: the copy adds their draw
terms, runs their turn-start hooks and their after-draw hooks only in the later-turn code, so a Clarity, Tools of the Trade or Demesne
standing on the player at a fight's first draw would be ignored. But **none can be there**. The game puts a power on the player
before the first draw only through a relic's combat-start hook (or Rocket's Surrounded), and none of those applies any of the eight draw
powers or a power with a turn-start hook (section 3); the copy empties the player's powers at the start of every fight. The eight come
only from played cards and one potion, which all come after the first draw. So the old path costs nothing today and a fix would be
byte-identical; I did not make one (section 3, "Not fixed", says what it would take and when it starts to matter).

Like a school that rings the bell for lessons two to six from one clock and for lesson one from another: today the pupils are never
in a lesson-one room that needs the second clock, but a new room could be built there.

## 1. The game's turn start, and where each part runs in the copy

The game has one turn start for every turn: relics' and powers' `BeforeSideTurnStart`; the enemies' moves; the block clear (the
player's is skipped on turn one, so Anchor's block stays) and `AfterBlockCleared`; the energy reset and `AfterEnergyReset`;
`BeforeHandDraw`; the hand-draw modifiers and `AfterModifyingHandDraw`; the draw (on turn one the Innate/bottom-of-pile reorder comes
first); `AfterPlayerTurnStart`; then `AfterSideTurnStart`. A fight's first turn is that start, run once combat-start hooks
(`AfterRoomEntered`, `BeforeCombatStart`) are done. The models that hook it (129 relic and 57 power models override at least one hook of the
turn start, the combat start, the hand draw or the energy) fall into the rows below. "Right" means the copy's behaviour on a first
turn equals the game's by reading; "unreachable" means the copy's first-turn code lacks the effect and no game source can create the
state that needs it.

| # | Effect (game hook) | Copy, turn one | Copy, later turns | Verdict | Night records (11-03 / 11-04 / 11-05) |
| --- | --- | --- | --- | --- | --- |
| 1 | Relics' hand-draw modifiers: Snecko Eye, Pael's Blood, Fiddle, Ring of the Drake, Pocketwatch, Pollinous Core, Ring of the Snake, Bag of Preparation, Booming Conch (room), Big Mushroom | `RelicEffects.HandDrawBonus(state, 1)` in `DrawOpeningHand` | the same function, `state.Turn + 1` | right (8db0b791) | core held: 177 / 44 / **0**; conch held: 37 / 19 / 1 |
| 2 | Pollinous Core's count (side-turn-start tick) and reset to zero on paying | `ApplyBeforeOpeningHand` phase 4, `AfterModifyingHandDraw` in `DrawOpeningHand` | `EndTurn` tick, `AfterModifyingHandDraw` | right (8db0b791); two replays confirm (section 4) | in row 1 |
| 3 | Turn-one draw-pile reorder: Innate to the top, bottom-of-pile enchantments, draw count raised to the Innate count, capped at 10 (turn one only in the game) | `ApplyTurnOneDrawPileReorder` inside `DrawOpeningHand` | none (the game has none) | right | none of the 26 same-size turn-one hand records differs by an Innate card |
| 4 | Powers' hand-draw terms: Machine Learning, Pale Blue Dot, Tyranny, Tools of the Trade, Demesne, Draw Cards Next Turn, Clarity, Mind Rot | **not in the opening draw** | in the `handDraw` sum in `EndTurn` | old path, **unreachable** | none possible |
| 5 | `BeforeHandDraw` relics: Blessed Antler, Funerary Mask, Jeweled Mask, Ninja Scroll, Radiant Pearl, Toasty Mittens, Toolbox | `ApplyBeforeHandDraw(state, 1, ...)` in `ContinueFirstTurn` | the same function, turn + 1 | right (each entry checks the turn, as the game's do) | no record names one |
| 6 | `BeforeHandDraw` powers: Infinite Blades, Hello World, Creative AI, Foregone Conclusion, Spectrum Shift, Call of the Void, Sentry Mode, Nightmare | not run | `EndTurn` | old path, **unreachable** | none possible |
| 7 | `AfterPlayerTurnStart` relics: Bellows, Choices Paradox, Emotion Chip, Festive Popper, Gambling Chip, Mercury Hourglass, Mr. Struggles, Pendulum, Royal Poison, Vexing Puzzlebox, Blood Vial (late) | `ApplyAfterPlayerTurnStart(state, 1, ...)` (+ late pass) | the same functions, turn + 1 | right | one record holds Gambling Chip + Pendulum (11-05, see section 3) |
| 8 | `AfterPlayerTurnStart` powers: Entropy, Tyranny, Tools of the Trade (screens), Inferno, Rolling Boulder, Crimson Mantle, Loop, Summon Next Turn | not run | `AfterPlayerTurnStartPowers` | old path, **unreachable** | none possible |
| 9 | `AfterRoomEntered` / `BeforeCombatStart` relics (Anchor, Snecko Eye, Girya, Vajra, Gorget, Data Disk, Sling of Courage, Tea sets, Phylactery, ...) and the powers they apply (Strength, Dexterity, Thorns, Focus, Confused, Plating) | `ApplyBeforeOpeningHand` phases 1 to 3, in the game's phase order; room flag set by `Reset(eliteRoom: ...)` | n/a | right | no record names one as the cause |
| 10 | `BeforeSideTurnStart` relics with a turn-one guard: Bag of Marbles, Red Mask, Cracked Core, Twisted Funnel, Power Cell | `ApplyBeforeOpeningHand` phase 4 | the game's guard keeps them off later turns | right | none |
| 11 | `BeforeSideTurnStart` relics that reset a per-turn tally: Kunai, Shuriken, Ornamental Fan, Orichalcum (+ fake), Rainbow Ring, Velvet Choker, Brilliant Scarf, Beating Remnant, Demon Tongue, Mini Regent, Music Box, Ripple Basin, Letter Opener | `ApplyStartOfPlayerTurn` (runs after the draw on turn one, before it on later turns; nothing in the draw reads these tallies) | `ApplyStartOfPlayerTurn` | equivalent: a fight starts at zero | none |
| 12 | Block clear and `AfterBlockCleared` (Horn Cleat turn 2, Captain's Wheel turn 3, Sparkling Rouge turn 3; Barricade/Blur/Sturdy Clamp) | not run (the game does not clear the player's block on turn one; the guarded relics do nothing on turn one) | `EndTurn` | right | none |
| 13 | Energy reset, `ModifyMaxEnergy`, `ShouldPlayerResetEnergy` (Ice Cream), `AfterEnergyReset` relics (Art of War turn 2+, Venerable Tea Set) | `Reset` + `ApplyBeforeOpeningHand` phase 5 | `EndTurn` (`ShouldResetEnergy`, `EffectiveMaxEnergyForTurn`) | right | energy matches in the Lantern record; the lockstep does not compare it elsewhere |
| 14 | `AfterEnergyReset` powers: Radiance, Lightning Rod, Next Turn Energy, Genesis, Star Next Turn, Spinner | not run | `EndTurn` | old path, **unreachable** | none possible |
| 15 | `AfterSideTurnStart` relics with a turn-one guard: Akabeko, Big Hat, Bone Tea, Booming Conch (energy), Bread, Divine Destiny, Fencing Manual, Infused Core, Lantern, Orange Dough, Runic Capacitor, Symbiotic Virus, Very Hot Cocoa | `ApplyFirstTurnAfterSideTurnStart` | the game's guard keeps them off later turns | right | none |
| 16 | `AfterSideTurnStart` relics without one: Brimstone, Crossbow, Happy Flower (+ fake), Sai, Seal of Gold, Pael's Tears, Pael's Legion (cooldown), Phylactery Unbound, Candelabra and Chandelier (guarded in the relic) | `ApplyAfterSideTurnStart` from `FirstTurnSide` | the same function from `SideTurnStart` | right | none |
| 17 | `AfterSideTurnStart` / `BeforeSideTurnStart` powers: Demon Form, Furnace, Clarity and Draw Cards Next Turn (removal), Poison, Wraith Form, Noxious Fumes, Countdown, Neurosurge, Reflect, Shadow Step, Biased Cognition, Coolant, Feral, Blur, Aggression, Void Form, Prep Time | not run | `EndTurn` and `SideTurnStart` | old path, **unreachable** | none possible |
| 18 | Player Plating (Gorget): the game does not decay it on turn one | no decay | decays by one | right | none |
| 19 | Enemy side of the first turn: moves rolled (`ChooseIntents`), Turret Operator's Rampart block, Plating's round-one block, Hardened Shell | `Reset`, `GrantRampartBlock` in `FirstTurnSide`, `CombatFactory` at creation | `EndTurn` | right (earlier fixes) | enemy HP records are a different family |
| 20 | Orbs' turn-start passive (Plasma) | not run; no relic channels a Plasma orb | `EndTurn` | unreachable | none possible |
| 21 | Auto-played cards (Imbued) | `QueueCombatStartAutoPlays` after the draw | n/a | right (game: after the draw) | none |

Rows 4, 6, 8, 14, 17 and 20 are the old path. Rows 1 to 3, 5, 7, 9 to 13, 15, 16, 18, 19 and 21 are right on a first turn. There are two kinds of "right": shared functions (1, 2, 5, 7, 16) and first-turn lists whose every entry the game itself guards to turn one (9, 10, 15, 21); a
new relic with an unguarded turn-start hook has to be written into the shared function, and `ApplyAfterSideTurnStart` is where such a
relic goes (`ApplyFirstTurnAfterSideTurnStart` would restrict it to turn one).

## 2. Evidence from the nights

Method (`turn_one_audit.py`, appendix A): every record whose first differing field is `.combat.hand`; turn one by the record's `turn`;
shape by the two hands' sizes (the game holds more or fewer cards, or the same number of different cards); the relics the run holds from
the game's stdout copy (Neow pick, event option naming a relic, relic reward; the room of floor N is the N-th map decision). Shop and
treasure relics are not named in the log, so "neither" means "none seen". The three nights have different seeds and different run
counts; compare the rates, not the counts.

| night (tree) | runs | decisions | hand records, all | turn one | turn one, size differs | ... holding core | ... holding conch | ... neither | turn one, same size | later turns, size differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11-03 (before the fix) | 1,992 | 353,637 | 288 | 120 | 103 | 57 | 29 | 17 | 17 | 154 |
| 11-04 (before the fix) | 489 | 87,707 | 79 | 31 | 27 | 16 | 10 | 1 | 4 | 39 |
| 11-05 (`e1e94e19`, the fix) | 499 | 88,409 | 25 | 7 | **2** | 0 | 1 | 1 | 5 | 16 |

Per 1,000 decisions: turn-one size-differs 0.29, 0.31, **0.023**; all hand records 0.81, 0.90, 0.28; turn-one same-size 0.048, 0.046, 0.057
(flat across the fix). Records holding Pollinous Core at any turn: 177 of 108 core runs, 44 of 21 core runs, **0** of 27 core runs.
The fix removed what it was written for, and at the turn that matters here.

The seven turn-one hand records of 11-05, the first night on the fix:

- Five are the same number of different cards (draw order at the fight's first decision); run holdings seen in the log: Silver Crucible,
  Tea of Discourtesy and Gorget; none; Ember Tea; Winged Boots; Silver Crucible, Regal Pillow and Red Skull. The same-size class is
  0.05 per 1,000 decisions on all three nights, so it is not the fix and not a turn-start effect we know of: no common relic, and none
  of the 26 same-size turn-one records over the three nights differs by an Innate card.
- One holds Booming Conch and Lantern in a Monster room (Mawler, floor 15, Act 1): the copy's hand has one card more than the game's, the
  energy is equal (4 on both), so it is not Conch (hallway, no payment in the game) and not Lantern. Unexplained (section 3).
- One is a Decimillipede fight at floor 29 holding Gambling Chip and Pendulum: the game is mid-turn at 0 energy with a different hand
  (Shrug It Off had just been played), and the copy shows a fresh hand at 4 energy, the whole hand and 15 HP different. Not a draw
  shape. Unexplained (section 3).

Turn-one records with no field difference at all (a play or choice the copy refused, or a different screen phase) are 33 / 2 / 10.
Of them the refusals are 10 / 1 / 4; the four of 11-05 are mid-turn states (the game at 0 to 1 energy after plays) with a hand that
already differs, not a turn-start shape; the phase ones (23 / 1 / 5) are fight-start screens, a different family.
The 16 later-turn size-differing records of 11-05 are all mid-turn (after a play or a potion, turns 2 to 5) and none holds Pollinous
Core or Booming Conch by the log: the card-draw family, outside this audit.

## 3. What is still wrong or not settled

**Reachability of the eight draw powers and of the turn-start power hooks.** Searched in the decompile for every model that applies
any of the eight powers (Machine Learning, Pale Blue Dot, Tyranny, Tools of the Trade, Demesne, Draw Cards Next Turn, Clarity, Mind
Rot): the cards of the same names, Glow, Predator and Relax (Draw Cards Next Turn), and the Clarity potion. No relic, event, enemy,
modifier or character start applies one. The combat-start hooks (`Hook.BeforeCombatStart`, `AfterRoomEntered`, creatures' room-entry
hooks) are listened to only by relics, a few powers and the monsters; the powers the relics apply there are Strength, Dexterity,
Thorns, Focus, Confused and Plating, and every monster's room-entry power goes on itself except Rocket's Surrounded, which goes
on the player and has no turn-start hook. So on a first turn the player holds at most those six, none of which has a hand-draw term, and Plating's decay is guarded off turn one by the game. The copy's `Reset` empties the
player's powers, then applies those same six (and Surrounded for a back-attack roster, which has no turn hook). Rows 4, 6, 8, 14, 17
and 20 therefore differ from the game only in states no fight can reach. The game's potions and cards come after the first draw. The
practice starts (`rl/practice_mix.py`) begin mid-fight; the re-anchor puts the game's state at the first decision, after the draw.
`run_debug_set_player` sets cards, relics, potions and counters and no powers.

**Not fixed, and why.** Routing the powers' terms into one function would change the copy's output in no reachable state (a byte proof
against main would show every pair identical), yet `CombatEngine.cs` is an engine file: the hash-pinned files to regenerate, then the 85-minute
gate. It would also have to bring `AfterPlayerTurnStartPowers` and the `SideTurnStart` power loop into `ContinueFirstTurn`'s
hold-and-resume machine (a screen held by Toolbox or Gambling Chip pauses turn one between phases), which is more than a rule. If a
game patch ever adds a combat-start source for one of these powers (the next decompile refresh is the moment), re-run the source
search (appendix B); the first hit makes this worth doing.

**Open, small, unexplained.** (a) The Mawler record above (11-05 `UCRNVK83TU`, decision 88: Booming Conch + Lantern, copy one card
over). The copy-side cause is not visible from the record (no powers, relics or deck in it); the other 18 Conch-holding runs of the
night had no hand record on any turn. (b) The Decimillipede record (11-05 `PF5YRHZZDX`, decision 230). Both are one record in 88,409 decisions; I did not
chase them.

**Evidence limits.** The relic lists come from the game's log, not from the record: Neow picks, event options and relic rewards are named,
shop and treasure relics are not (each of the 7 turn-one records has two to five unnamed shop or chest relic sources). "Core" and "conch" counts are
therefore lower bounds, and the "neither" column of 11-03 (17) probably holds core runs whose relic came from a shop or chest. The
11-03 night ran many more decisions than the other two, so per-decision rates are the fair comparison. The replays of section 4 are copy-only;
the game's side of them is its rule from the decompile (the 2026-11-04 diagnosis), not a game run.

## 4. Reproduction

- Counts: `python -I turn_one_audit.py` (appendix A) with the emulator interpreter; it reads `LAB/nightly/<night>/g11/divergences.jsonl`,
  `summary.json` and the stdout copies `logs/w5-night-<date>-stdout`, and prints the per-night tallies of section 2.
- Hook table and reachability: `python -I hook_sources.py` (appendix B) lists, from the decompile, the models that override a turn-start,
  combat-start, hand-draw or energy hook (129 relics, 57 powers), the powers applied by models with a combat-start hook (relics, powers,
  modifiers: whole file; monsters: the room-entry methods only), and every model outside its own file that names each of the eight
  draw powers (cards, one potion, and the two powers that mention each other in their descriptions). Re-run it after a decompile refresh.
- The copy's rows were read in `CombatEngine.cs` (`EndTurn` for later turns; `StartFirstTurn`, `ContinueFirstTurn`, `FirstTurnSide` for
  turn one), `CombatFactory.cs` (`Reset`, `DrawOpeningHand`) and `RelicEffects.cs` (the functions named in the header).
- Copy replays on the lab's build of `e1e94e19` (the 2026-11-04 diagnosis, appendix, run with `-I -B` after copying the DLL to a
  scratch folder): replay A (seed R6J25H4ECA, Chompers) now shows the core at count 1, 2, 3 in the earlier fight and a **7-card hand
  on turn one** of the next fight with the core back to 0, then 5, 5, 5 at counts 1, 2, 3; replay B (seed J7CPAG3V4S) shows 5, 5, 5, **7**
  (count back to 0), 5 at turns 1 to 5. Before the fix replay A showed 5 on turn one and 7 on turn three, replay B 7 on turn five.

## Appendix A: `turn_one_audit.py`

```python
"""Turn-one hand records by shape and by the turn-start relics the run is known to hold. Reads only.
python -I turn_one_audit.py   (edit NIGHTS if the folders move)"""
import collections, glob, json, re

LAB = 'D:/spireline/referee/LAB/nightly/'
LOGS = 'D:/spireline/logs/w5-night-%s-stdout'
NIGHTS = {'2026-11-03': '20261103', '2026-11-04': '20261104', '2026-11-05': '20261105'}
HOLD = ('POLLINOUS_CORE', 'BOOMING_CONCH')


def runs_from_logs(date):
    """seed -> list of (map decisions so far, relic id): the Neow pick, an event option or reward that names a relic."""
    out = {}
    for fn in sorted(glob.glob(LOGS % date + '/*.log')):
        seg = None
        for line in open(fn, encoding='utf-8', errors='replace'):
            if line.startswith('[referee] run decision 0 start'):
                seg = {'maps': 0, 'got': []}
            elif seg is not None and (m := re.match(r'\[referee\] run (\w+) ended', line)):
                out[m.group(1)] = seg
                seg = None
            elif seg is not None and (m := re.match(r'\[referee\] run decision \d+ (\w+) (.*)', line)):
                kind, rest = m.group(1), m.group(2).strip()
                if kind == 'map':
                    seg['maps'] += 1
                elif kind == 'neow':
                    seg['got'].append((seg['maps'], rest.strip('"')))
                elif kind == 'event':
                    seg['got'].append((seg['maps'], rest.strip('"').split('.')[-1]))
                elif kind == 'rewards' and (m := re.search(r'"type":"relic","id":"(\w+)"', rest)):
                    seg['got'].append((seg['maps'], m.group(1)))
    return out


def held(seg, floor):
    """Relic ids named in the log before the floor's room (the floor-th map decision)."""
    return {rid for maps, rid in seg['got'] if maps < floor} if seg else set()


def hand(diff):
    cards = lambda side: collections.Counter(tuple(json.loads(c) if isinstance(c, str) else c)[0] for c in side)
    return cards(diff[1]), cards(diff[2])  # (game, copy)


for night, date in NIGHTS.items():
    runs = runs_from_logs(date)
    rows = [json.loads(l) for l in open(LAB + night + '/g11/divergences.jsonl', encoding='utf-8')]
    c = collections.Counter()
    for r in rows:
        d = r.get('diff') or []
        if not d or d[0][0] != '.combat.hand':
            continue
        g, e = hand(d[0])
        shape = 'same-size' if sum(g.values()) == sum(e.values()) else 'size-differs'
        who = held(runs.get(r['run']), r['floor'])
        key = 't1' if r['turn'] == 1 else 'later'
        c[key, shape] += 1
        c['all'] += 1
        for rid in HOLD:
            c['any-turn holding ' + rid] += rid in who
        if key == 't1' and shape == 'size-differs':
            c['t1 size-differs: ' + ('core' if 'POLLINOUS_CORE' in who else 'conch' if 'BOOMING_CONCH' in who else 'neither')] += 1
    c['runs holding core'] = sum(any(rid == 'POLLINOUS_CORE' for _, rid in s['got']) for s in runs.values())
    c['runs holding conch'] = sum(any(rid == 'BOOMING_CONCH' for _, rid in s['got']) for s in runs.values())
    summ = json.load(open(LAB + night + '/g11/summary.json'))
    print(night, 'runs', summ['runs'], 'decisions', summ['decisions'])
    for k, v in sorted(c.items(), key=str):
        print('   ', k, v)
```

## Appendix B: `hook_sources.py`

```python
"""Which models hook a turn start, and what can put one of the draw powers on the player before the first draw. Reads the decompile only.
python -I hook_sources.py"""
import os
import re

ROOT = 'D:/spireline/referee/decompiled/MegaCrit.Sts2.Core.Models.'
TURN_HOOKS = ('BeforeCombatStart', 'AfterRoomEntered', 'BeforeSideTurnStart', 'AfterSideTurnStart', 'AfterEnergyReset', 'BeforeHandDraw',
              'ModifyHandDraw', 'ModifyHandDrawLate', 'AfterModifyingHandDraw', 'AfterPlayerTurnStart', 'AfterPlayerTurnStartLate',
              'AfterBlockCleared', 'ShouldPlayerResetEnergy', 'ModifyMaxEnergy')
COMBAT_START = ('BeforeCombatStart', 'AfterRoomEntered', 'AfterAddedToRoom')
DRAW_POWERS = ('MachineLearning', 'PaleBlueDot', 'Tyranny', 'ToolsOfTheTrade', 'Demesne', 'DrawCardsNextTurn', 'Clarity', 'MindRot')
OVERRIDE = r'override\s+(?:async\s+)?[\w<>\[\]?]+\s+'


def overrides(text, hooks):
    return [h for h in hooks if re.search(OVERRIDE + h + r'\b', text)]


def files(kind):
    d = ROOT + kind + '/'
    return [(f[:-3], open(d + f, encoding='utf-8', errors='replace').read()) for f in sorted(os.listdir(d)) if f.endswith('.cs')]


for kind in ('Relics', 'Powers'):
    print(kind, 'overriding a turn-start, combat-start, draw or energy hook:', sum(bool(overrides(t, TURN_HOOKS)) for _, t in files(kind)))

# Powers a file applies anywhere in it, for relics, powers and modifiers with a combat-start hook (over-approximate); for monsters
# only inside the room-entry methods, since a monster applies powers in its moves too.
applied = {}
for kind in ('Relics', 'Powers', 'Modifiers', 'Monsters'):
    for name, text in files(kind):
        if kind == 'Monsters':
            text = ' '.join(m.group(0) for m in re.finditer(OVERRIDE + '(?:' + '|'.join(COMBAT_START) + r')\b.*?\n\t}', text, re.S))
        elif not overrides(text, COMBAT_START):
            continue
        applied.setdefault(kind, set()).update(re.findall(r'PowerCmd\.Apply<(\w+)>', text))
for kind, powers in applied.items():
    print('powers applied by', kind, 'with a combat-start hook:', sorted(powers))

# Whatever names a draw power outside its own file: the cards and the potion that play it, and the two powers that mention each other.
for power in DRAW_POWERS:
    users = []
    for kind in ('Relics', 'Cards', 'Potions', 'Powers', 'Modifiers', 'Monsters', 'Events', 'Enchantments', 'Afflictions', 'Characters'):
        if os.path.isdir(ROOT + kind):
            users += [kind + '/' + n for n, t in files(kind) if re.search(r'\b' + power + r'Power\b', t) and n != power + 'Power']
    print(power, 'named by:', users)
```
