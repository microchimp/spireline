# Solver shape review, 2026-10-29

Independent, read-only. The optimisation review (f386ed2) is not redone.

## 1. Recommendation

Take shape (d) with (c) at its core: a fight gym that replays the AI's own fight starts (Act-1 boss first, then Act-2
elites and boss) with fresh draw seeds, first as the instrument that says whether stronger fight play closes the gap,
then as the label source for the prior and value head, with the solver as a part of it (exact last-turn values, a
lethal and forced-survival check at the root, the one-turn enumerator), not a race for exact coverage. Let bounds land
and end the coverage rounds there: a 30x cheaper end-turn move raised exact coverage only from 6.5% to 7.2%, no constant
factor reaches decisions two or more turns from the end, and after more than 24 units no solver piece has produced a
scoreboard number; park dominance. The deciding number (week 1, about 1.5 units, 6 to 9 machine-hours) is the Act-1
boss win rate of a 16x search minus a3-v1's from the same 200 starts, ten seeds each: at +10 points or more build the
gym's training loop; under +3 the gap is the deck and HP the AI brings to the boss, and fight work pauses for the run
layer.

## 2. The four shapes

What the numbers say first:

- **Full exactness cannot scale.** Exact to the fight's end: 43.6% of last-turn decisions, 3.8% with one turn left, 0% with
  two or more. Sizing (W4-S1): four or more turns left is 99% above 10^7 states; at about 400 nodes/s per process that
  is hours per decision. Pruning buys constant factors against an exponential.
- **The current turn is already cheap.** From the engine round's `solves.jsonl` (reported nowhere): horizon 0 (the rest of
  this turn, exact over in-turn chance, leaves at the turn's end) finishes within 0.1 s on 86% of the 696 decisions and
  within 1 s on 90%; horizon 1 within 1 s on 28%, within 10 s on 48%. A turn-level search is affordable today. What it
  lacks is an evaluation at the turn's end.
- **Search strength pays; the fit does not.** 120 against 30 simulations: +0.98 floor, +5.6 Act-1 boss points (W4-S2).
  The prior sweep's 24 cells sit on one plateau. The lever is the labels: visits of a 30-simulation search guided by the
  same prior, from whole-run self-play that rarely reaches the hard fights.
- **CPU is the constraint for every shape, not the GPU.**

| Shape | Agent units | CPU / GPU | Possible gain, by when | Main risk |
|---|---|---|---|---|
| (a) Chess engine: turn search with bounds, dominance, evaluation at the turn's end | 4-6 (S5 leaf protocol, dominance under the harness, evaluation, A/B) | per decision as today; A/B one night-equivalent; GPU for leaf batches | 0 to +1 floor; week 3 at the earliest | No good enough evaluation exists: the value head is unmeasured at turn ends; a hand evaluation is open-ended work with no measure. Alpha-beta proper does not fit a one-player game with chance; what transfers already exists. |
| (b) Learned model on very many fights | 0.2 (`MAX_FIGHTS` 12,800) | none extra; +3 GPU-min per fit | about 0: measured at most 0.05 HP per decision, below an A/B's resolution | The sweep closed this. The net alone has 5.6 HP top-1 regret against the 30-sim search; it cannot replace search. |
| (c) Fight gym (AlphaZero on the fight) | 2.5-3.5 (gym 1, labels and training mix 1, A/B and review 1) | M2 once 6-9 machine-h; then 2-4 machine-h per generation for 16x labels, taken from bug-sweep hours; under 1 GPU-h per generation | bounded by M2's 16x gap; if that is +10 points or more, my estimate is +0.5 to +1.5 floors and +3 to +8 Act-1 boss points in 2-3 weeks | The teacher is only a little stronger (M2 decides); starts from the AI's own runs keep the net blind to decks it never builds; the CPU comes out of the fidelity sweeps. |
| (d) (c) plus the solver as labeller and root check | (c) + 1.5-2 (S5 root and last-turn in-tree, exact last-turn labels) | (c) + about 10 s per last-turn label | (c) + 0 to +0.3 floor from no missed lethal or forced survival (M1 decides) | Exact labels cover endgames only (about 7% of decisions); the weakness is likely long-fight planning. |

Per agent unit: (c) about 0.2-0.5 floor if the headroom exists; (a) 0 to 0.2; (b) 0; further coverage rounds 0 until S5
and S7 exist. These are my estimates scaled from the 30-against-120 block, not measurements. Once gym labels exist,
rerun the sweep's size factor (about 2 GPU-hours): its flat result was measured on noisy labels.

## 3. Measure first

**M1, oracle regret (0.3 unit, under 1 machine-hour).** On decisions the solver settles exactly (the 696, then the
real arm's stream from tonight): a3-v1's L0 loss against the exact best move, and missed lethals or forced survivals
per 100 fights. The coverage output lacks the played move and the root action values; add both. Under 1 miss per 100
fights and 0.2 HP regret per fight, S5 is a labeller only.

**M2, fight-layer headroom (1-1.5 units, 6-9 machine-hours). The deciding number.** Build the gym: 200 Act-1 boss starts
and the Act-2 elite and boss starts of one or two nights, from the emulator-arm replays of the night seeds (cross-check
against the real arm's stream as it lands). Play each start ten times with fresh draw and roll seeds, the same seeds in
every arm, under a3-v1, 4x and 16x simulations, search determinized as today. With 2,000 paired boss fights the standard
error of the difference is about 1.5 points. Read the Act-1 boss win rate, 16x minus a3-v1:

- **+10 points or more:** the fight layer is the lever; build (c), then (d).
- **+3 to +10:** gym labels only (no new player pieces), and equal effort on the run layer.
- **under +3:** the gap is what the AI brings to the boss (deck, upgrades, HP); fight-layer work pauses after bounds.

Read 4x too: at +5 points or more, spending 4x only in boss and elite fights is the cheapest scoreboard gain on offer
(a3-v1's "not by stakes" came from the 200-position dev set the sweep showed too small); one 500-seed block tests it.

**M3, value at the turn's end (0.3 unit, with M2).** Score the value head and a3-v1's 30-playout mean at horizon-0
leaves against the gym's ten-seed mean outcome. Shape (a) opens only if the value head beats the playouts.

## 4. Bounds and dominance

- **Bounds: let it land.** Stopping mid-round wastes the work, and bounds also cut horizon 1, which any depth-limited use
  needs. Add to its report the times to finish horizons 0 and 1 and the exact last-turn share. It is the last coverage
  round.
- **Dominance: do not start.** Keep the brief. Re-aim it only if M3 opens the turn search, with horizon 1 within 1 s
  (28% today) as its target instead of exact coverage; its non-monotone-reader risk must still clear the harness.
- **Next solver work:** M1's two output fields; then S5 root-only (an exact lethal or forced-survival check at horizon 0)
  if M1 finds misses; then exact last-turn labels for the gym. S7's A/B tests whatever player change M2 justifies, not
  the oracle alone.

## 5. Inconsistent or missing

1. **"Nearly the whole gap is the Act-2 boss" does not hold.** In the human reference (gen 5), humans kill the Act-1 boss in
   74% of runs that reach it, the AI in 29.5%, though the AI reaches it more often (83% against 74%). The Act-1 boss is
   the first wall and has the data: 327 of the 696 coverage decisions; Act 2 has one boss fight and two elites.
2. The AI's HP and deck size entering the boss are not recorded; humans enter at 54 of 81. Without them, fight against
   deck is a guess. M2 answers it statistically: it is D35's attribution question, which the solver cannot answer while
   0 of 40 fights solve whole.
3. Reported nowhere: the horizon-0 and horizon-1 timings (they sit in `solves.jsonl`), and the value head's quality at
   any horizon, which S5's leaf protocol depends on.
4. The prior's regret is measured against the 30-sim search it guides; nothing compares it with a stronger teacher. M1
   gives that for free on solved positions.
5. "Four of seven pieces landed" undercounts (S6 is measured). The two still missing, S5 and S7, are the only ones that
   touch the scoreboard.
6. D6 and the owner's correction bind the gym: labels from expected values and real-odds outcomes only, never hindsight;
   the gym's search keeps `resample=True` so a replay's seed never leaks the draw order. D13: no Codex runs in the gym.
7. The "real decisions" are emulator-arm replays of night seeds (0.54% divergence): acceptable, but say so.
