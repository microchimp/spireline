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

1. `filter_a10.py` keeps Ascension 10, `game_mode` "standard", not abandoned, one player, no modifiers, build v0.107.1, and drops `player_token` and badges. It dedupes on `run_hash`.
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

## How to use it

- **Run-layer replay:** for each run, start the emulator from the run's seed, make the same choices, and diff every offering screen by screen (map, encounter behind each node, card rewards, relic and potion drops, shop stock and prices, events, Ancients). Fights aren't recorded card by card, so reset the player's holdings to the logged post-fight state and keep checking, as upstream's `scripts/replay_real_run.py` does for local runs.
- **Odds checks:** compare encounter rates per act, card-reward rarity and "?" room outcomes against the emulator's own distributions over many seeds.
- **Fight sanity checks:** per-encounter `damage_taken` and `turns_taken` give coarse distributions to compare against simulated fights. They are confounded by player skill, so they flag gross errors only.
