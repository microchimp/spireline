# Spire Codex A10 test corpus

Spire Codex publishes community-uploaded Slay the Spire 2 runs as per-version exports. Spireline uses the v0.107.1 export as a **test corpus for the emulator's run layer**: given a run's seed and the player's choices, the emulator should offer exactly what the game offered. The runs are never used as ground truth for strategy, and raw runs are never committed to this repo. Only the aggregate counts below are published.

## Source

| | |
|---|---|
| File | `https://spire-codex.com/exports/runs-v0.107.1.jsonl.gz` (listed in `https://spire-codex.com/api/exports/runs/manifest`) |
| Size | 2,136,544,513 bytes compressed, 638,919 runs |
| sha256 | `55557226ec1023d49d99c88555a2a102706c07281784a5edab038172fea6d9e2` (matches the manifest; downloaded 2026-10-10) |
| Format | One JSON run per line, schema 9, the same as the game's own `.run` history files. `player_token` is empty (no player identity). |
| Terms | No published licence or data terms were found. The developer describes the public API as meant for others to build on, and the site's `robots.txt` allows `/exports`. |

Each run has the seed, build, ascension, character, final deck, relics and potions, and a `map_point_history` with every room: what was offered (card, relic and Ancient choices, with `was_picked`), gold and HP changes, `damage_taken` and `turns_taken`.

## Filtering

Two steps, both in [`tools/spire_codex/`](../../tools/spire_codex/):

1. `filter_a10.py` keeps Ascension 10, `game_mode` "standard", not abandoned, one player, no modifiers, build v0.107.1, and drops `player_token` and badges. It dedupes on `run_hash`. With `--keep-player-token` (off by default) the working file keeps each run's `player_token` and drops only the badges; that file stays under `data/` and is for `strong_players.py` (below).
2. `vanilla_filter.py` keeps only the five base characters and runs whose every card, relic and potion id (deck, relics, potions and every offer) is in the emulator's vanilla id map (`data/id_map.json` in r33hab/sts2, converted from PascalCase to the game's UPPER_SNAKE ids).

| Step | Runs |
|---|---|
| Read | 638,919 |
| Rejected: not A10 | 492,302 |
| Rejected: multiplayer | 53,121 |
| Rejected: abandoned | 30,637 |
| Rejected: not standard mode | 4,279 |
| Rejected: modifiers | 1,305 |
| Kept after step 1 | 57,275 |
| Dropped: modded character | 321 |
| Dropped: modded or unknown content | 817 |
| **Kept after step 2 (vanilla A10)** | **56,137** |

The unknown ids in step 2 are all clearly mod content (for example Archipelago relics, PermaProg, and an expansion card pack), which suggests the id conversion is sound. Mods that change rules without adding new ids can't be detected this way; they will show up as outliers in replays.

## Vanilla A10 runs by character

| Character | Runs | Wins | Win rate |
|---|---|---|---|
| **Defect** | **11,350** | 1,269 | 11.2% |
| Ironclad | 14,448 | 1,630 | 11.3% |
| Silent | 13,526 | 1,538 | 11.4% |
| Necrobinder | 8,853 | 928 | 10.5% |
| Regent | 7,960 | 1,277 | 16.0% |

Uploaders are self-selected, so these win rates are not population averages. That doesn't matter for fidelity testing: a run is either reproduced exactly or it isn't.

## Top killers (A10, all characters, step 1)

Aeonglass (boss), Decimillipede (elite), Infested Prisms (elite), Terror Eel (elite), Kaiser Crab (boss), Test Subject (boss), Knowledge Demon (boss), Waterfall Giant (boss), Bygone Effigy (elite), Queen (boss), The Kin (boss), Vantom (boss). The Decimillipede's segments are a known emulator gap, so it is first on the fidelity list.

Full numbers: [data/spire_codex_a10_v0.107.1_stats.json](data/spire_codex_a10_v0.107.1_stats.json).

## Second download (2026-11-06)

The owner approved one more download of the same build's export (D55 addendum 7). It is a larger file than the first row's: the exports page now lists v0.107.1 at 840,381 runs.

| | |
|---|---|
| File | `https://spire-codex.com/exports/runs-v0.107.1.jsonl.gz`, saved in its own folder `data/spire-codex/2026-11-06/` (the October file beside it is untouched) |
| Size | 2,816,341,088 bytes compressed, 840,381 runs (every line read and parsed; 0 unparseable) |
| sha256 | `0e5babe6ba138da4242f21694f4ba0743088fa01c4dde4223ec8cf6283e8e7d8`, equal to the manifest's (manifest generated 2026-11-05T02:04:41Z; the manifest's size and run count match too). Downloaded 2026-11-06. |
| `player_token` | **null in all 840,381 runs** (the same as the first row; checked on the raw lines of the whole file). `players[0].id` is 1 in every kept run. Nothing in a row names or links a player. |
| Source tag | 15,424 of the kept runs carry `_sts: "slay-the-stats/v1.2.0"` (the uploading tool), 3,272 a `_spirecodex_damage` block. Neither identifies a player. |

The copy of the first download on disk is a later fetch than the first row describes (dated 2026-10-13: 2,188,745,918 bytes, sha256 `92b3cc4010578877436f951fce892a48df58ee78d896ebc58a532ec2f74995cd` as recorded beside it; the human prior's build log of 2026-11-05 reads 653,733 lines from it). Seven of the 2,924 October exam ids are not among the new file's vanilla Ironclad A10 runs (dropped upstream or by the filters); they stay exam.

### Filtering the new file (the same two steps, `filter_a10.py --keep-player-token`, then `vanilla_filter.py`)

| Step | Runs |
|---|---|
| Read | 840,381 |
| Rejected: not A10 | 647,603 |
| Rejected: multiplayer | 70,123 |
| Rejected: abandoned | 40,627 |
| Rejected: not standard mode | 5,897 |
| Rejected: modifiers | 1,844 |
| Kept after step 1 | 74,287 |
| Dropped: modded character | 369 |
| Dropped: modded or unknown content | 1,055 |
| **Kept after step 2 (vanilla A10)** | **72,863** |

| Character (vanilla A10) | Runs | Wins | Win rate |
|---|---|---|---|
| Defect | 14,659 | 1,529 | 10.4% |
| **Ironclad** | **18,125** | 1,953 | 10.8% |
| Silent | 18,393 | 2,197 | 11.9% |
| Necrobinder | 11,447 | 1,323 | 11.6% |
| Regent | 10,239 | 1,519 | 14.8% |

Ironclad A10 by fifth (D38 addendum 1's rule, unchanged: a fixed hash of the run id, `tools/boss_entry.py`; new runs join the fifths by it, so an October run keeps its fifth; fifth 0 is the exam; `tools/spire_codex/fifths.py` counts them):

| Fifth | Runs | Wins | Act 1 boss beaten per 100 | Act 2 boss beaten per 100 |
|---|---|---|---|---|
| 0 (exam, counted for the record only) | 3,588 | 388 | 54.7 | 29.4 |
| 1 | 3,625 | 399 | 53.7 | 28.1 |
| 2 | 3,605 | 402 | 56.6 | 30.0 |
| 3 | 3,736 | 388 | 54.0 | 27.6 |
| 4 | 3,571 | 376 | 54.4 | 28.6 |
| Fifths 1 to 4 (training and validation) | 14,537 | 1,565 | 54.7 | 28.6 |

The exam id list for the larger file is `data/spire-codex/human-exam-fifth-ids-2026-11-06.txt`: the October ids united with the fifth-0 runs of the new file, 3,595 ids (3,588 in the file's fifth 0, plus the 7 October ids not among its Ironclad A10 runs). The October list is kept as it was. Source of all counts: Spire Codex public run export for v0.107.1.

### Strong players

The brief for this download wanted a strong-player set ranked by `player_token`. There is no token to rank by: see [2026-11-06-strong-players.md](2026-11-06-strong-players.md). `tools/spire_codex/strong_players.py` is written and tested for an export that carries tokens.

## How to use it

- **Run-layer replay:** for each run, start the emulator from the run's seed, make the same choices, and diff every offering screen by screen (map, encounter behind each node, card rewards, relic and potion drops, shop stock and prices, events, Ancients). Fights aren't recorded card by card, so reset the player's holdings to the logged post-fight state and keep checking, as upstream's `scripts/replay_real_run.py` does for local runs.
- **Odds checks:** compare encounter rates per act, card-reward rarity and "?" room outcomes against the emulator's own distributions over many seeds.
- **Fight sanity checks:** per-encounter `damage_taken` and `turns_taken` give coarse distributions to compare against simulated fights. They are confounded by player skill, so they flag gross errors only.
