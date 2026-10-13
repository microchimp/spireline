# Research notes

Background research behind the [design](../DESIGN.md), gathered on 10–12 October 2026 from primary sources (repos, papers, run data). Where these notes and [DECISIONS.md](../DECISIONS.md) disagree, DECISIONS.md wins.

| File | What it covers |
|---|---|
| [LANDSCAPE.md](LANDSCAPE.md) | Critique of existing Slay the Spire 1 and 2 bots, LLM agents, RL work and simulators, judged on whether they find the best play: a scored matrix, what each family's results actually support, lessons to steal and traps to avoid |
| [UPSTREAM.md](UPSTREAM.md) | What the upstream emulator project (Zamiell → evangambit → r33hab) already does: emulator coverage, verification programme, agent and coach work, and what that leaves for Spireline |
| [SPIRE_CODEX.md](SPIRE_CODEX.md) | The Spire Codex v0.107.1 export as a run-layer test corpus: source, filtering, and aggregate counts (56,137 vanilla A10 runs, 11,350 Defect) |
| [ENEMY_AI.md](ENEMY_AI.md) | Which enemies choose moves at random (18 of 111) and which follow fixed patterns, including every act boss found |
| [COMPUTE.md](COMPUTE.md) | Workload sizes and what they cost on a home PC versus rented CPUs |
| [IDEAS.md](IDEAS.md) | Unverified ideas for making the pipeline more efficient, grouped by stage, with the question to check first for each |
| [dossiers/](dossiers/) | The six raw research dossiers (JSON): tooling, the game, simulators and RL, LLM agents, theory, and Jev. Each fact carries a source URL and a confidence level. |
