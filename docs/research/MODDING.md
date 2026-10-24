# Modding Slay the Spire 2: how it is done and what the rules allow

Research for Lane F (the public in-fight mod, [PLAN.md](../PLAN.md)). It records how Slay the Spire 2 is modded today, what Mega Crit has shipped and said, what the community frameworks do, and what the game's, Steam's and the frameworks' terms permit. It was compiled on 2026-10-24 from the sources linked inline; **every source was read on 2026-10-24** unless a line says otherwise. Nothing here was run or tested by Spireline, no game text or asset is reproduced, and no decompiled code is quoted. Where a fact could not be confirmed the text says "not found". Public API names are given only as the community documentation gives them.

## Bottom line

1. **Mod support is official and built in.** The game has shipped with an integrated mod loader since the Early Access launch on 2026-03-05, and Steam Workshop support arrived with Major Update 2, v0.107.1, on 2026-06-19. Mega Crit calls the Workshop "the official way to browse and install mods" ([June 2026 Neowsletter](https://www.megacrit.com/news/2026-6-19-neowsletter-issue-23/)). There is no official API reference; Mega Crit links to the community wiki and ships XML documentation for the game assembly instead.
2. **The stack is C# on Mega Crit's Godot 4.5.1 fork, net9.0, with Harmony for patching.** Mods are prebuilt DLLs plus an optional Godot resource pack, found by a JSON manifest in the game's `mods` folder or the Workshop content folder. They read state through the game's own hook system and act through its command classes; Harmony is the fallback. An MIT mod (STS2MCP) already reads the hand, piles, intents and energy and drives every in-game action through the game's own code paths.
3. **The written rules are permissive for a free, recommend-only mod.** Mega Crit's Content Policy grants permission to mod, forbids monetisation beyond donations and forbids implying affiliation. The Steam Subscriber Agreement forbids decompiling and distributing the game's software (section 2.G), cheats that give an unfair advantage in multiplayer (4.B) and automation that earns progress without genuine input (4.C). No game-specific EULA and no Workshop App-Specific Terms were found.
4. **The practical constraints are version churn and co-op.** Beta patches landed every two weeks until August 2026 and break mods; a mod must declare whether it affects gameplay, because gameplay mods must match across a co-op lobby; modded play uses a separate save directory; Mega Crit has said it will not add invasive anti-cheat. Headless runs of the shipped executable with the mod loader intact are reported by a community project on macOS; there is no official headless or server build.
5. **A Spireline mod that only shows a recommended play fits inside every rule found**, provided it is free, declares `affects_gameplay: false`, reads only displayed state, never acts, contains no game text, assets or decompiled code, and is updated with each game version. The open questions are listed in section 5.

---

## 1. Official modding support

### 1.1 Timeline

| Date | Version | What Mega Crit shipped or said | Source (read 2026-10-24) |
|---|---|---|---|
| 2026-02-25 | pre-launch | AMA on r/Games: the modding goal is to "empower the modding community", and the engine is a custom Godot fork the team calls MegaDot | [AMA summary](https://slaythespire2.gg/news/mega-crit-ama-reddit-feb-2026) (second-hand; the Reddit thread itself was not read) |
| 2026-03-05 | launch | Early Access on Steam for Windows, macOS and Linux; the FAQ answers the Workshop question with "Yes!", says StS1 mods will not port, and says moddability is being improved | [Mega Crit FAQ](https://www.megacrit.com/faq/) |
| 2026-04-09 | v0.103.0 beta | Daily leaderboards show friends only; the notes state the anti-cheat position (section 3.5) | [v0.103.0 notes (wiki mirror)](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.103.0_-_Beta_Patch) |
| 2026-06-19 | v0.107.1 main | Steam Workshop added; the game "has had an integrated mod loader from day one"; mod creators upload with the official uploader; the base game no longer deletes progress from removed or errored mods; XML documentation for the game assembly began publishing | [v0.107.1 notes (wiki mirror)](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.107.1_-_Major_Update_2), [June Neowsletter](https://www.megacrit.com/news/2026-6-19-neowsletter-issue-23/) |
| 2026-07-03 | v0.108.0 beta | Unmodded saves copied to the modded save directory on first modded launch; controller support for the Modding menu; mods may register multiple assemblies; a Steam mod takes precedence over a local copy when its version is greater; the Workshop branch-support check is batched; co-op version-mismatch false positives fixed with help from the RitsuLib author | [v0.108.0 notes (wiki mirror)](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.108.0_-_Beta_Patch) |
| 2026-07-17 | v0.109.0 beta | Models from non-gameplay-affecting mods are excluded from the multiplayer serialization hash | [v0.109.0 notes (Steam)](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1838407329258348) |
| 2026-07-31 | v0.110.0 beta | The Report Bug button is hidden in error dialogs when any player in a session has mods | [v0.110.0 notes (wiki mirror)](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.110.0_-_Beta_Patch) |
| 2026-08-14 | v0.111.0 beta | Fixes to the save copy for players who declined mod loading; no MODDING section found in the excerpt read | [v0.111.0 notes (Steam)](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1840944183778277) |
| 2026-09-25 | — | September Neowsletter: no timeline for the next patch; nothing on modding | [September Neowsletter](https://www.megacrit.com/news/2026-9-25-neowsletter-issue-26/) |

**Current versions.** As of 2026-10-06 the newest patch in the Steam feed was beta v0.111.0 (2026-08-14), and the main branch was last updated by v0.107.1 ([gamedropdaily feed](https://gamedropdaily.com/updates/slay-the-spire-2/)). The upstream emulator is pinned to v0.107.1, Steam build 23811903 ([UPSTREAM.md](UPSTREAM.md)); the headless CLI projects report v0.111.0 as Steam build 24724944 ([wuhao21/sts2-cli](https://github.com/wuhao21/sts2-cli)). Beta patches came every two weeks through the summer and paused after v0.111.0 for the team's break and a shift to larger content ([v0.111.0 notes](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1840944183778277)).

**Workshop size.** The Workshop browse page listed 4,293 mod entries ([Workshop browse](https://steamcommunity.com/workshop/browse/?appid=2868840&browsesort=trend&section=readytouseitems)). The most-required library, BaseLib, showed 726,597 current subscribers and 1,128 items that depend on it ([BaseLib Workshop page](https://steamcommunity.com/sharedfiles/filedetails/?id=3737335127)).

### 1.2 What the official loader exposes

The game has no published API reference. The community wiki states that "STS2 does not have a formal modding API" and that its material is community-maintained ([wiki modding hub](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Modding_Tutorials)); Mega Crit's own newsletter points modders to the community template wiki for getting started and to the Discord `#sts2-modding` channel or the in-game feedback form for framework feedback ([June Neowsletter](https://www.megacrit.com/news/2026-6-19-neowsletter-issue-23/)). What the loader does expose, as documented by two independent community sources:

| Surface | What it is | Source (read 2026-10-24) |
|---|---|---|
| Mod manifest | One JSON file per mod named after the mod ID, discovered recursively under `mods/`. Fields: `id`, `name`, `author`, `description`, `version`, `has_dll`, `has_pck`, `dependencies`, `affects_gameplay`, and `min_game_version` | [Modding-Tutorial, loading and manifests](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/03-mod-loading-and-manifests.md); [ModTemplate wiki, Modding Basics](https://github.com/Alchyr/ModTemplate-StS2/wiki/Modding-Basics) |
| Entry point | A static class marked with the loader's initializer attribute naming a static method. Without one, the loader (as of v0.103.3) creates a Harmony instance and patches the mod's assembly automatically | [Modding-Tutorial, entry points and hooks](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/05-entrypoints-harmony-and-hooks.md); [jiegec/STS2FirstMod](https://github.com/jiegec/STS2FirstMod/blob/master/README.md) |
| Modding namespace | A `Modding` namespace with the mod manager, manifest type, initializer attribute and a helper class; a `Hooks` namespace; a model database | [Modding-Tutorial, game layout](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/02-vanilla-sts2-layout.md) |
| Hook system | Lifecycle and modifier hooks for combat, turns, cards, rooms, rewards, merchants, potions, powers, healing, damage, block and death prevention. Notification hooks return a task, veto hooks a boolean, modifier hooks a transformed value. Mods subscribe their own listeners for run-state and combat-state hooks through the helper class | [Modding-Tutorial, entry points and hooks](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/05-entrypoints-harmony-and-hooks.md); [ModTemplate wiki, Custom Hooks](https://github.com/Alchyr/ModTemplate-StS2/wiki/Custom-Hooks) |
| Command classes | Gameplay changes go through command classes that coordinate state, multiplayer choices and visuals; direct field mutation bypasses them | [Modding-Tutorial, entry points and hooks](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/05-entrypoints-harmony-and-hooks.md) |
| XML documentation | Published for the game assembly since the v0.107.1 beta fixes | [v0.107.1 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.107.1_-_Major_Update_2) |
| Uploader | An official command-line tool creates a workspace with a content folder, a `workshop.json` and a preview image under 1 MB, and uploads to the Workshop; the fields are described in a README inside the generated workspace, which was not read | [megacrit/sts2-mod-uploader](https://github.com/megacrit/sts2-mod-uploader) |
| Workshop branch support | The game makes a Workshop call that checks branch support, so items carry a supported-branch tag; the tag field was not read | [v0.108.0 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.108.0_-_Beta_Patch) |

Toolchain facts from the same sources: .NET SDK 9 and net9.0, Godot .NET SDK 4.5.1 matching MegaDot, the bundled runtime 9.0.7 at v0.103.3, and the game assembly `sts2.dll` under a `data_sts2_<platform>` folder that mod projects reference at build time ([Modding-Tutorial README](https://github.com/fresh-milkshake/Modding-Tutorial), [ModTemplate wiki, Setup](https://github.com/Alchyr/ModTemplate-StS2/wiki/Setup)). The wiki names the engine as Mega Crit's fork of Godot 4.5.1 ([wiki modding hub](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Modding_Tutorials)); whether the fork's source is public was not found.

---

## 2. Community frameworks

### 2.1 The main pieces

| Project | Role | How it hooks the game | Licence | Version pin | Source (read 2026-10-24) |
|---|---|---|---|---|---|
| BaseLib (Alchyr) | The dependency most mods build on: APIs for configuring mods, adding content, a framework for avoiding conflicts between mods, and custom model base classes | Game models and commands; a Patches folder exists, library not named in the README | MIT | Not stated; the wiki says game updates often break BaseLib and individual mods | [BaseLib-StS2](https://github.com/Alchyr/BaseLib-StS2); [Workshop item](https://steamcommunity.com/sharedfiles/filedetails/?id=3737335127); [ModTemplate wiki](https://github.com/Alchyr/ModTemplate-StS2/wiki/Modding-Basics) |
| ModTemplate-StS2 and wiki (Alchyr) | The project template and the documentation Mega Crit links to: setup, decompiling, reflection, custom hooks, cards, shaders, debugging | Publicizer for private members, which the wiki calls "routine and normal"; hooks; decompiled reading | Not read | Warns that frequent updates will break mods | [wiki home](https://github.com/Alchyr/ModTemplate-StS2/wiki); [Decompiling](https://github.com/Alchyr/ModTemplate-StS2/wiki/Decompiling) |
| STS2-RitsuLib (BAKAOLC, "OLC") | "a stable layer for content registration, lifecycle hooks, Harmony patching, persistence, settings UI, localization, audio, runtime UI, diagnostics, and compatibility helpers" | Lifecycle subscriptions and a Harmony patcher with diagnostics; sits beside BaseLib and the base game API | MIT | Follows the highest game API it supports (often beta); per-API compat packages for other branches; dependency form changed at API 0.105.x | [STS2-RitsuLib](https://github.com/BAKAOLC/STS2-RitsuLib) |
| ModConfig-STS2 (xhyrzldf) | A Mods tab in the game settings for any mod's options | Reflection only; mods call it without a hard reference | MIT | Not stated | [ModConfig-STS2](https://github.com/xhyrzldf/ModConfig-STS2) |
| Modding-Tutorial (fresh-milkshake) | A handbook on the loader, manifests, hooks, Harmony, resource packs, UI and packaging | Documents the loader surface above | MIT | Verified against v0.103.3 (release metadata 2026-05-29) | [Modding-Tutorial](https://github.com/fresh-milkshake/Modding-Tutorial) |
| STS2MCP (Gennadiyev; r33hab fork) | A localhost HTTP API that exposes game state and drives actions for external programs | Game commands, the action queue, UI click handlers and reflection; Harmony on its own assembly only | MIT | Tested against v0.103.2 upstream; forks for v0.107 and v0.111 | [STS2MCP](https://github.com/Gennadiyev/STS2MCP); [SECURITY_REVIEW.md](../SECURITY_REVIEW.md) M-F14 |
| Harmony (pardeike) | "A library for patching, replacing and decorating .NET and Mono methods during runtime" | Runtime method patching | MIT | 2.x maintained; supports Mono and .NET | [Harmony](https://github.com/pardeike/Harmony); [LICENSE](https://github.com/pardeike/Harmony/blob/master/LICENSE); [docs](https://harmony.pardeike.net/) |
| Godot Engine | The engine under MegaDot | — | MIT; the engine binary shipped with a game needs the copyright notice | — | [Godot licence](https://godotengine.org/license/) |

There is no "ModTheSpire" style launcher; mods are enabled from a Mods option in the game and the Steam Workshop properties ([Steam thread, 2026-07-11](https://steamcommunity.com/app/2868840/discussions/0/567037624436648209/)). Whether the Harmony library ships inside the game or must be bundled by each mod was **not found**; the loader's automatic patching fallback shows the game runtime itself can create Harmony instances ([Modding-Tutorial, game layout](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/02-vanilla-sts2-layout.md)).

### 2.2 Can a mod read combat state and drive actions?

Yes to both, through the game's own code. The evidence is the STS2MCP state builder and action layer, read on GitHub (described in words; no code reproduced):

| Capability | What STS2MCP does | Source (read 2026-10-24) |
|---|---|---|
| Hand | Reads each card in hand with its playability and the reason it is unplayable | [StateBuilder](https://github.com/Gennadiyev/STS2MCP/blob/main/McpMod.StateBuilder.cs) |
| Draw, discard, exhaust piles | Reads counts and contents; the draw pile is re-sorted by rarity then card ID before being exposed and the real draw order is not read, matching the in-game display | same; also [LANDSCAPE.md](LANDSCAPE.md) section 1b |
| Enemy intents and status | Reads the next move, intent type and label, HP, block and visible powers of living enemies | same |
| Player, relics, potions, orbs, map | Reads energy, block, HP, gold, relic counters, potion slots, the orb queue, map nodes and travelable nodes | same |
| RNG | Only the multiplayer lobby seed appears in the visible code; no RNG state or counters are exposed. The `/compendium` endpoint leaks the run seed ([LANDSCAPE.md](LANDSCAPE.md)) | same |
| Actions | Plays a card through the game's action queue, the path the game's own UI uses; ends the turn through the game's end-turn command; uses and discards potions, selects map nodes, event options, rewards, shop purchases and rest-site options by calling the game's own methods or the UI control's click handler. No simulated keyboard or mouse input | [Actions](https://github.com/Gennadiyev/STS2MCP/blob/main/McpMod.Actions.cs) |

Spireline's own review of the r33hab fork found that its Harmony patching covers only the mod's own assembly and that "No combat or RNG logic is patched" ([SECURITY_REVIEW.md](../SECURITY_REVIEW.md), M-F14).

Two general facts bound what any in-process mod can reach. First, the community toolchain publicizes private members as a matter of course, so nothing technical stops a mod from reading any field, RNG streams included ([ModTemplate wiki, Modding Basics](https://github.com/Alchyr/ModTemplate-StS2/wiki/Modding-Basics)); no published mod that reads RNG streams was found, other than the re-enabled developer console (section 4.6). Second, the game itself closed one information leak in v0.110.0: "Players can no longer discern the shuffle order of cards in certain scenarios" ([v0.110.0 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.110.0_-_Beta_Patch)).

### 2.3 Precedents for advice and overlay mods

Several published mods already read run state and show advice or statistics without playing the game. They are the closest precedents for Lane F.

| Mod | What it shows | Where | Source (read 2026-10-24) |
|---|---|---|---|
| Spire Codex companion | Community win rates and tiers in the game's own tooltips, a recommended map route with per-node danger ratings, a damage meter, automatic run upload; requires BaseLib; F5 overlay | Steam Workshop (posted 2026-06-18) | [Workshop item](https://steamcommunity.com/sharedfiles/filedetails/?id=3747536911); [spire-codex.com/mod](https://spire-codex.com/mod) |
| Card rewards helper (StsCompanion) | "Real-time card pick recommendations" on reward, event and shop screens from aggregate win-rate data; uploads runs | Nexus (updated 2026-05-19) | [Nexus mod 340](https://www.nexusmods.com/slaythespire2/mods/340) |
| Deck Compass | Context-aware card and relic scores against the current deck; reads the game's run files | Nexus | [Nexus mod 627](https://www.nexusmods.com/slaythespire2/mods/627) |
| Adventure Log | Scrollable combat log; marked `affects_gameplay: false`, "Only one player needs the mod" in co-op | Nexus | [Nexus mod 595](https://www.nexusmods.com/slaythespire2/mods/595) |
| Damage Meter, MultiplayerStats | In-combat damage overlays | Nexus and Workshop | [Nexus mod 47](https://www.nexusmods.com/slaythespire2/mods/47); [Nexus mod 41](https://www.nexusmods.com/slaythespire2/mods/41) |

None of these was found to act in the game on the player's behalf. No statement from Mega Crit about advice mods specifically was found.

---

## 3. What a mod may read and do: the written rules

### 3.1 The instruments

| Instrument | Status | Source (read 2026-10-24) |
|---|---|---|
| Game-specific EULA | **Not found.** Steam's EULA page for the app returns an error, and the store page excerpt shows no EULA link | [Steam EULA URL](https://store.steampowered.com/eula/2868840_eula_0); [store page](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) |
| Mega Crit Content Policy, Mods section | The stated mod policy (quoted in 3.2) | [Content Policy](https://megacrit.com/content-policy/) (site built 2026-08-18) |
| Mega Crit FAQ | Workshop yes; moddability improving; Discord modding channels | [FAQ](https://www.megacrit.com/faq/) |
| Mega Crit Privacy Policy | The game collects anonymous gameplay data and Sentry error reports | [Privacy Policy](https://www.megacrit.com/privacy-policy/) |
| Steam Subscriber Agreement (SSA), revised 2026-09-10 | Governs every Steam game and the Workshop | [SSA](https://store.steampowered.com/subscriber_agreement/) |
| Steam Workshop legal agreement | The Workshop legal-agreement URLs redirect to the SSA; no separate text found | [redirect](https://steamcommunity.com/sharedfiles/workshoplegalagreement) |
| Workshop App-Specific Terms for this game | **Not found** on the Workshop pages read | [Workshop home](https://steamcommunity.com/app/2868840/workshop/) |
| Framework licences | Harmony, BaseLib, RitsuLib, ModConfig, STS2MCP, the tutorial and Godot are all MIT | links in section 2.1 |

### 3.2 Mega Crit's mod policy

The Content Policy's Mods section grants permission to create mods "as long as they are not plagiarized or discriminatorily offensive and adhere to their respective platform's terms of use", forbids stating or suggesting official affiliation, allows donations, and forbids every other monetisation of mods including paywalls and stretch-goal fundraising ([Content Policy](https://megacrit.com/content-policy/)). The same page allows gameplay footage and monetised videos, and forbids merchandise built from assets taken directly from the game or its marketing materials. Nothing in the policy addresses decompiling, reading game memory, automation, leaderboards or online play.

### 3.3 The Steam Subscriber Agreement

| Clause | What it says (paraphrased except the quoted words) | Bearing on a mod |
|---|---|---|
| 2.A General licence | Content and Services are licensed for personal, non-commercial use except where commercial use is expressly allowed, for example through the Workshop | A free mod is within the licence |
| 2.G Restrictions on Use | The user may not copy, publish, distribute, "reverse engineer, derive source code from, modify, disassemble, decompile, create derivative works based on" the Content and Services or any software, except as otherwise permitted under the Agreement (including game-specific Subscription Terms) or under applicable law | Decompiling and redistributing game files is restricted; the exception for what the publisher permits and for applicable law is the hinge, and Mega Crit's permission to mod is the publisher's statement |
| 4.B Cheating | Cheats are defined as software or hardware that may give a player an unfair competitive advantage in multiplayer versions of a game; users must not create cheats, tamper with the execution of Steam or games, or use cheats, mods or hacks to control Steam's own processes and interface | Defined against multiplayer advantage; a single-player advisor is outside the definition, a co-op advisor is a judgement call |
| 4.C Automation | No scripts, bots, macros or other non-human-controlled systems may interact with games on Steam; the listed examples include faking gameplay statistics and earning rewards or progress without genuine user input | A mod that plays by itself falls here; a mod that only recommends does not automate |
| 6.A, 6.B User generated content and Workshop | Uploading grants Valve a free licence to use, modify and distribute the contribution; the developer may modify contributions accepted for in-game distribution; the uploader warrants that it holds sufficient rights in everything uploaded; Workshop pages may add App-Specific Terms | Everything in the uploaded mod must be the uploader's to license: code, weights and any third-party MIT components with their notices |

Source for all rows: [SSA](https://store.steampowered.com/subscriber_agreement/), read 2026-10-24. Spireline's design already cites 2.G and 4.C as the legal risks ([DESIGN.md](../DESIGN.md) risk table).

### 3.4 Decompiled code

Mega Crit has published no position on decompiling. Three facts sit side by side: the SSA restricts it (3.3); Mega Crit's newsletter links modders to a community wiki whose pages include "Decompiling" and tell readers where the game assembly is ([ModTemplate wiki, Decompiling](https://github.com/Alchyr/ModTemplate-StS2/wiki/Decompiling)); and the tutorial Mega Crit does not link also decompiles the assembly and inspects the resource pack with ILSpy's command-line tool, with no statement on legality or sharing ([Modding-Tutorial, reverse engineering](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/04-reverse-engineering-the-game.md)). Both sources are silent on redistributing decompiled output. Spireline's rule stands regardless: nothing decompiled is written into this repository, and the mod's patch list is published "with reasons and contains no game text" ([PLAN.md](../PLAN.md) Lane F).

### 3.5 Online play, leaderboards and anti-cheat

- Mega Crit's position, in the v0.103.0 notes: "we don't really want to incorporate invasive anti-cheat protection into the game so it's sort of impossible for us to prevent people putting in the maximum score". Daily leaderboards show friends by default and the beta branch has its own leaderboard ([v0.103.0 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.103.0_-_Beta_Patch); [PCGamesN, 2026-04-10](https://www.pcgamesn.com/slay-the-spire-2/patch-notes-neow-relics)).
- From v0.103.2 on the main branch, achievements and epochs no longer unlock in Daily and Custom runs ([PCGamesN, 2026-04-17](https://www.pcgamesn.com/slay-the-spire-2/patch-notes-live-april-2026)). Whether the game has Steam achievements at all was **not found**: a Steam thread of 2026-05-30 says there are none in Early Access ([thread](https://steamcommunity.com/app/2868840/discussions/0/662737213850924477/)) and SteamDB's achievements page did not load its list ([SteamDB](https://steamdb.info/app/2868840/stats/)).
- Whether modded runs are excluded from or flagged on the Daily leaderboard was **not found** in any official source. A community guide claims that using the re-enabled developer console "permanently flags the run and disables leaderboard uploads for that seed" and that single-player has no anti-cheat system ([Steam guide, 2026-07-03](https://steamcommunity.com/sharedfiles/filedetails/?id=3756837676)); these are unverified community claims.
- Co-op: a mod that affects gameplay must be present on every player's game or the run desyncs; the game logs "the non-gameplay mod mismatch warning" for the rest ([v0.108.0 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.108.0_-_Beta_Patch); [Steam thread](https://steamcommunity.com/app/2868840/discussions/0/802341528343330117/)). Setting `affects_gameplay` wrongly causes desyncs ([ModTemplate wiki, Modding Basics](https://github.com/Alchyr/ModTemplate-StS2/wiki/Modding-Basics)). One community mod exists to ignore the mod-list check and warns that mismatched data still desyncs ([Nexus mod 66](https://www.nexusmods.com/slaythespire2/mods/66)).

---

## 4. Practical constraints

### 4.1 Install paths

| Item | Path | Source (read 2026-10-24) |
|---|---|---|
| Local mods | `mods/` next to the executable; Windows `Steam/steamapps/common/Slay the Spire 2/mods`; macOS inside the app bundle at `SlayTheSpire2.app/Contents/MacOS/mods`; Linux `~/.steam/steam/steamapps/common/Slay the Spire 2/mods` | [sts2.gg guide, 2026-07-03](https://sts2.gg/guides/how-to-install-mods); [STS2FirstMod README](https://github.com/jiegec/STS2FirstMod/blob/master/README.md) |
| Workshop mods | `Steam/steamapps/workshop/content/2868840/<item id>/` | [ModTemplate wiki, Setup](https://github.com/Alchyr/ModTemplate-StS2/wiki/Setup) |
| Game assembly | `data_sts2_windows_x86_64/sts2.dll` (the folder name varies by platform) | [ModTemplate wiki, Decompiling](https://github.com/Alchyr/ModTemplate-StS2/wiki/Decompiling) |
| Unmodded saves (Windows) | `%APPDATA%\SlayTheSpire2\steam\<SteamID>\profile1\saves\` | [sts2.gg guide](https://sts2.gg/guides/how-to-install-mods) |
| Modded saves (Windows) | `%APPDATA%\SlayTheSpire2\steam\<SteamID>\modded\profile1\saves\` | same |

Mod files are a prebuilt `<id>.dll`, an optional `<id>.pck` and the `<id>.json` manifest in one folder; every `.json` under `mods/` is treated as a candidate manifest, so configuration files should not live in that tree ([Modding-Tutorial, loading and manifests](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/03-mod-loading-and-manifests.md)). One guide says mods are "compiled on startup" ([Workshop guide](https://bossdown.com/guides/slay-the-spire-2-steam-workshop-mods/)); the loader documentation describes loading prebuilt assemblies, so that claim is not relied on here.

### 4.2 Enabling, disabling and consent

On the first launch with mods present the game shows a warning that mods can be a risk and asks whether to play with mods, then restarts; one player reports being locked out of modded play after declining ([Steam thread, 2026-07-11](https://steamcommunity.com/app/2868840/discussions/0/567037624436648209/)). STS2MCP's install steps call this the "consent dialog" ([STS2MCP README](https://github.com/Gennadiyev/STS2MCP)). Individual mods are toggled under Settings → Modding → Mod Settings, and a restart applies the change ([howtovideogame guide](https://howtovideogame.com/slay-the-spire-2-mods/)). The `-nomods` launch option starts the game without mods; a second Steam shortcut with that option, or a `steam://run/2868840//-nomods/` link, gives a vanilla launcher ([ModTemplate wiki, switching](https://github.com/Alchyr/ModTemplate-StS2/wiki/Easily-switch-between-modded-and-vanilla)). Workshop items can also be unticked in the game's Steam properties ([Steam thread, 2026-07-04](https://steamcommunity.com/app/2868840/discussions/0/571542703540656871/)).

### 4.3 Saves

Modded and unmodded saves are kept apart to protect unmodded progress; since v0.108.0 the unmodded saves are copied into the modded directory on the first modded launch with an explanatory popup, and v0.111.0 fixed the copy for players who had declined mod loading ([v0.108.0 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.108.0_-_Beta_Patch); [v0.111.0 notes](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1840944183778277)). The two save sets do not sync afterwards ([sts2.gg guide](https://sts2.gg/guides/how-to-install-mods)). Since v0.107.1 the base game no longer deletes progress belonging to removed or errored mods ([v0.107.1 notes](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.107.1_-_Major_Update_2)).

### 4.4 Lifecycle on game updates

- Every community source warns that updates break mods: "Any mods created during this period will need to be updated after each breaking change in the main game" ([ModTemplate wiki home](https://github.com/Alchyr/ModTemplate-StS2/wiki)); "Early Access updates can change signatures and loader contracts" ([Modding-Tutorial README](https://github.com/fresh-milkshake/Modding-Tutorial)); "After an update, re-decompile the target before launching the old DLL" ([Modding-Tutorial, hooks](https://github.com/fresh-milkshake/Modding-Tutorial/blob/main/docs/05-entrypoints-harmony-and-hooks.md)).
- The mitigations in use: the `min_game_version` manifest field ([ModTemplate wiki, Modding Basics](https://github.com/Alchyr/ModTemplate-StS2/wiki/Modding-Basics)); per-API-version compat packages (RitsuLib, section 2.1); the Workshop's branch-support check (v0.108.0); and the published XML documentation (v0.107.1). The wiki notes that there is no automatic way to check which branch or version a mod supports.
- Main and beta branches diverge for weeks at a time (section 1.1), so a mod needs a build per branch it supports.

### 4.5 Headless and server builds

No official headless, dedicated-server or Workshop-less build was found. Three community routes exist:

| Route | What it runs | Mod loader | Platform and version | Source (read 2026-10-24) |
|---|---|---|---|---|
| Shipped executable with `--headless` and a `steam_appid.txt` | The real Godot process without a display; boots to a drivable state | Yes, driven through the STS2MCP mod | Windows, v0.107.1 (upstream's capture jobs) | [UPSTREAM.md](UPSTREAM.md) section on headless |
| rsgcsg/STS2-headless | Launches the shipped Godot executable with `--headless` and "retains the official SceneTree and Mod loader" | Yes | macOS arm64, v0.111.0; archived 2026-08-24 | [STS2-headless](https://github.com/rsgcsg/STS2-headless) |
| wuhao21/sts2-cli and forks | Loads the game assembly in a C# host with the Godot assemblies stubbed; copies DLLs from the user's Steam install at setup | Not stated | v0.111.0 (Steam public beta) | [sts2-cli](https://github.com/wuhao21/sts2-cli) |

Spireline's referee is the game's own code run headless under the terms recorded in [SECURITY_REVIEW_ADDENDUM_1.md](../SECURITY_REVIEW_ADDENDUM_1.md); whether the official loader also loads mods in a Windows `--headless` process was not confirmed by a published source other than upstream's own use of STS2MCP.

### 4.6 Anti-cheat and integrity checks

- No anti-cheat software is shipped, by Mega Crit's own statement (section 3.5). No file-integrity check beyond Steam's standard file verification was found.
- The developer console exists but was disabled before launch; re-enabling it requires replacing the game assembly with a community build, which breaks on every patch ([Steam guide, 2026-07-03](https://steamcommunity.com/sharedfiles/filedetails/?id=3756837676)).
- In a modded session the error dialog hides the Report Bug button (v0.110.0), which keeps modded crashes out of Mega Crit's bug queue; the game's own error reports go to Sentry ([Privacy Policy](https://www.megacrit.com/privacy-policy/)).
- The multiplayer hash covers model IDs and saved properties and excludes models from non-gameplay mods (v0.109.0); this is consistent with the stated purpose of the `affects_gameplay` flag.

---

## 5. Verdict for a Spireline mod that shows a recommended play and never plays

**What it must comply with**, each tied to a source above:

1. **Free, donations at most, no claim of affiliation**, not plagiarised, following Steam's terms (Content Policy, 3.2).
2. **No automation.** The mod recommends and the player clicks. That keeps it outside SSA 4.C, and it matches Lane F's own rule that the mod never plays by itself ([PLAN.md](../PLAN.md)). It must not expose an action endpoint the way STS2MCP does.
3. **Displayed state only.** Read through the hook system and public models; show nothing the player cannot see; sort hidden piles the way the game displays them, as STS2MCP does; never read the seed, draw order or RNG streams. This is the allow-list of [DESIGN.md](../DESIGN.md) section 3.2, and it keeps the mod clear of the unfair competitive advantage that SSA 4.B defines for co-op.
4. **Declare `affects_gameplay: false`** and never mutate state, so co-op lobbies are not blocked and the mod is excluded from the multiplayer hash (sections 3.5, 4.6). Consider disabling the overlay by default in Daily, Custom and co-op runs until the open questions below are answered.
5. **No game text, assets or decompiled code in the mod or its repository** (SSA 2.G; the project rule). The mod references the game assembly at build time only and ships none of it, as the headless projects in section 4.5 state for themselves. Card and relic names shown in the overlay must come from the running game at run time, not from files in the mod.
6. **Own every byte uploaded** (SSA 6). The policy network weights, the ONNX runtime and any MIT dependency with its notice must be licensable by the uploader; Harmony and BaseLib carry MIT notices.
7. **Version discipline.** Set `min_game_version`, build per branch, pin to the referee's game version, and expect to re-verify on every patch (4.4). Spireline's fidelity gate already pins the emulator to a Steam build.
8. **Privacy.** Collect nothing without consent; if the mod ever phones home, say so in the Workshop description. The game itself reports only anonymous data and errors (Privacy Policy).
9. **Distribution** through the official uploader to the Workshop, with a GitHub release as the manual fallback, as BaseLib does (1.2, 2.1).

**Open questions**

- Does a game-specific EULA exist anywhere other than the Steam page that errored, and does Mega Crit have any stated position on decompiling or on advisor mods? Ask in `#sts2-modding`, which Mega Crit names as the feedback channel.
- Are modded runs excluded from or flagged on the Daily leaderboard, and are Steam achievements present and affected by mods? Not found in any official source.
- Are there Workshop App-Specific Terms for this game? None were found on the pages read.
- Does the official loader run mods in a Windows `--headless` process? Only upstream's own use of STS2MCP and a macOS project say so.
- Does the Harmony library ship with the game, or must the mod bundle it? Not found.
- Does the game record the active mod list in run files or leaderboard submissions? Not found; the `affects_gameplay` reporting suggests it records at least the gameplay-affecting set.
- The distilled policy is trained on an emulator derived from decompiled source. Whether a network trained that way counts as a derivative work under SSA 2.G is a legal question the sources do not answer. **Closed by the owner on 2026-10-24 (D28): assume it is allowed; Mega Crit openly supports modding and comparable mods exist.**
- Which branch to target first: the main branch (v0.107.1, the referee's version) or the beta (v0.111.0, where the Workshop's active modders are).

---

## Sources

All read on 2026-10-24.

**Mega Crit.** [FAQ](https://www.megacrit.com/faq/) · [Content Policy](https://megacrit.com/content-policy/) · [Privacy Policy](https://www.megacrit.com/privacy-policy/) · [June 2026 Neowsletter](https://www.megacrit.com/news/2026-6-19-neowsletter-issue-23/) · [September 2026 Neowsletter](https://www.megacrit.com/news/2026-9-25-neowsletter-issue-26/) · [news index](https://www.megacrit.com/news/) · [sts2-mod-uploader](https://github.com/megacrit/sts2-mod-uploader) · patch notes v0.103.0, v0.107.1, v0.108.0, v0.110.0 via the [community wiki](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:V0.107.1_-_Major_Update_2) and v0.109.0, v0.111.0 via [Steam news](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1840944183778277) · [AMA summary](https://slaythespire2.gg/news/mega-crit-ama-reddit-feb-2026) (second-hand).

**Valve.** [Steam Subscriber Agreement](https://store.steampowered.com/subscriber_agreement/) (revised 2026-09-10) · [store page](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) · [Workshop](https://steamcommunity.com/app/2868840/workshop/) and [browse](https://steamcommunity.com/workshop/browse/?appid=2868840&browsesort=trend&section=readytouseitems) · [SteamDB](https://steamdb.info/app/2868840/).

**Community frameworks and docs.** [ModTemplate-StS2 wiki](https://github.com/Alchyr/ModTemplate-StS2/wiki) · [BaseLib-StS2](https://github.com/Alchyr/BaseLib-StS2) · [STS2-RitsuLib](https://github.com/BAKAOLC/STS2-RitsuLib) · [ModConfig-STS2](https://github.com/xhyrzldf/ModConfig-STS2) · [Modding-Tutorial](https://github.com/fresh-milkshake/Modding-Tutorial) · [STS2FirstMod](https://github.com/jiegec/STS2FirstMod) · [STS2MCP](https://github.com/Gennadiyev/STS2MCP) · [STS2-headless](https://github.com/rsgcsg/STS2-headless) · [sts2-cli](https://github.com/wuhao21/sts2-cli) · [Harmony](https://github.com/pardeike/Harmony) · [Godot licence](https://godotengine.org/license/) · [wiki modding hub](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Modding_Tutorials).

**Guides, threads and press.** [sts2.gg install guide](https://sts2.gg/guides/how-to-install-mods) · Steam threads on [modding issues](https://steamcommunity.com/app/2868840/discussions/0/567037624436648209/), [launching without mods](https://steamcommunity.com/app/2868840/discussions/0/571542703540656871/), [modded co-op](https://steamcommunity.com/app/2868840/discussions/0/802341528343330117/), [achievements](https://steamcommunity.com/app/2868840/discussions/0/662737213850924477/) and [leaderboards](https://steamcommunity.com/app/2868840/discussions/0/798966745989725135/) · [Steam guide on trainers](https://steamcommunity.com/sharedfiles/filedetails/?id=3756837676) · Nexus mods [340](https://www.nexusmods.com/slaythespire2/mods/340), [595](https://www.nexusmods.com/slaythespire2/mods/595), [66](https://www.nexusmods.com/slaythespire2/mods/66), [627](https://www.nexusmods.com/slaythespire2/mods/627), [47](https://www.nexusmods.com/slaythespire2/mods/47), [41](https://www.nexusmods.com/slaythespire2/mods/41) · [Spire Codex mod page](https://spire-codex.com/mod) · PCGamesN [2026-04-10](https://www.pcgamesn.com/slay-the-spire-2/patch-notes-neow-relics), [2026-04-17](https://www.pcgamesn.com/slay-the-spire-2/patch-notes-live-april-2026), [2026-06-19](https://www.pcgamesn.com/slay-the-spire-2/update-2-rng-rework-steam-workshop) · [gamedropdaily feed](https://gamedropdaily.com/updates/slay-the-spire-2/).

**This repository.** [DESIGN.md](../DESIGN.md) · [PLAN.md](../PLAN.md) · [SECURITY_REVIEW.md](../SECURITY_REVIEW.md) · [LANDSCAPE.md](LANDSCAPE.md) · [UPSTREAM.md](UPSTREAM.md).
