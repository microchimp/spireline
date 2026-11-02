"""The boss-entry instrument: what the AI (and the humans) bring to the Act 1 and Act 2 bosses, and the run-level choices behind it.

    python tools/boss_entry.py human    --corpus runs-v0.107.1.jsonl.gz --out human.jsonl.gz [--exam-ids ids.txt]
    python tools/boss_entry.py selfplay --runs-root LAB/runs --gens 5-9 --out selfplay.jsonl.gz
    python tools/boss_entry.py nights   --nightly LAB/nightly --out nights.jsonl.gz
    python tools/boss_entry.py report   --human human.jsonl.gz --selfplay selfplay.jsonl.gz --nights nights.jsonl.gz --out tables.md

Every reader turns one run into the same small summary (`a[0]` is Act 1, `a[1]` Act 2; None when the run never entered the act):

    r      the run entered that act's boss fight          k   the boss was killed (None: unknown)
    at     "boss" (state entering the boss fight), "death" (state entering the fight or room that ended the run before the boss),
           or None                                        hp, mhp, gold, pot, rel   HP, max HP, gold, potions, relics at `at`
    deck   cards at `at`, "NAME" or "NAME+" (upgraded)    boss   the boss's slug
    path   the rooms taken in the act before `at`, one letter each (M monster, E elite, R rest, S shop, T treasure, ? unknown)
    rests  [[HP fraction before, "heal" | "smith" | ...], ...]      offers   [[card taken or None, [cards offered]], ...]
    shop   {"v": visits, "c": cards bought, "r": relics bought, "x": removals}

Sources and what each holds (the report states what each lacks):
  - the human corpus (D13): every room's HP, max HP, gold, cards gained, upgraded, removed and transformed, relics, rest choices, card
    offers with the pick. The deck at boss entry is rebuilt by replaying the rooms (checked against the final deck: tests and report).
  - the lab's self-play shards (RunRecords, emulator, the nightly agent's own macro): the full run state at every decision and fight.
  - the nightly runs.jsonl rows (real arm and emulator arm): the path, the card picks and the rest choices only; no HP, deck or relics.

Human data is aggregates only: a cell over fewer than `MIN_CELL` runs is suppressed, no single human run is ever shown, and the
held-out fifth of D38 (`exam_bucket`) is read only to score the AI against it. Nothing here runs the game or the emulator.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

MIN_CELL = 20  # D13: a cell over fewer runs is suppressed
BOSS_FLOOR = (17, 33)  # the floors of the Act 1 and Act 2 bosses (rl/run_fields.ACT_BOSS_FLOORS)
NODE_LETTER = {1: "M", 2: "E", 3: "R", 4: "S", 5: "T", 6: "B", 7: "?", 8: "A"}  # the emulator's node types (run_train.vocab.NODE_*)
HUMAN_ROOM = {"monster": "M", "elite": "E", "rest_site": "R", "shop": "S", "treasure": "T", "unknown": "?"}
# The acts' bosses by emulator id (run_train.vocab.BOSSES); the corpus names the same bosses ENCOUNTER.<slug>.
BOSSES = {74: "CEREMONIAL_BEAST_BOSS", 82: "THE_KIN_BOSS", 83: "VANTOM_BOSS", 77: "LAGAVULIN_MATRIARCH_BOSS", 79: "SOUL_FYSH_BOSS",
          84: "WATERFALL_GIANT_BOSS", 75: "KAISER_CRAB_BOSS", 76: "KNOWLEDGE_DEMON_BOSS", 81: "THE_INSATIABLE_BOSS",
          73: "AEONGLASS_BOSS", 78: "QUEEN_BOSS", 80: "TEST_SUBJECT_BOSS"}
# Ironclad's starting deck at Ascension 10 (the character's ten cards and the Ascension curse); every run begins with it.
START_DECK = ("ASCENDERS_BANE",) + ("STRIKE_IRONCLAD",) * 5 + ("DEFEND_IRONCLAD",) * 4 + ("BASH",)
BASIC = frozenset({"STRIKE_IRONCLAD", "DEFEND_IRONCLAD", "ASCENDERS_BANE", "BASH"})
DEFAULT_EXPORT = Path("D:/spireline/referee/exports/v0.107.1.json")  # the game's card table (type, rarity per card)
DEFAULT_ID_MAP = Path("D:/spireline/fork/sts2/data/id_map.json")  # emulator ids -> card, relic names
DEFAULT_CORPUS = Path("D:/spireline/data/spire-codex/runs-v0.107.1.jsonl.gz")
EXAM_SALT = "spireline-d38-exam-fifth|"
EXAM_BUCKET = 0  # D38: one fifth of the corpus, by run id, is the exam for ever


def below_normal() -> None:
    """BelowNormal priority through the Windows priority class (no POSIX call)."""
    try:
        import ctypes  # noqa: PLC0415

        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except (AttributeError, OSError):
        pass


def slug(name: str) -> str:
    """PascalCase class name -> the game's UPPER_SNAKE id (`DoorsOfLight` -> `DOORS_OF_LIGHT`)."""
    text = re.sub(r"(?<=[A-Za-z0-9])(?=[A-Z])", "_", name.strip())
    return re.sub(r"[^A-Z0-9_]", "", re.sub(r"\s+", "_", text.upper()))


def f1(v: float | None, nd: int = 1) -> str:
    return "." if v is None else f"{v:.{nd}f}"


def pct(v: float | None, nd: int = 1) -> str:
    return "." if v is None else f"{100 * v:.{nd}f}%"


def opener(path: Path, mode: str = "rt"):
    return gzip.open(path, mode, encoding="utf-8") if str(path).endswith(".gz") else open(path, mode, encoding="utf-8")


def read_jsonl(path: Path) -> Iterator[dict]:
    with opener(Path(path)) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with opener(Path(path), "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            n += 1
    return n


# ------------------------------------------------------------------------------------------------ card tables


class Cards:
    """Card type per slug (from the game's card table) and the emulator id -> slug map."""

    def __init__(self, types: dict[str, str], ids: dict[int, str] | None = None, relics: set[str] | None = None) -> None:
        self.types = types
        self.ids = ids or {}
        self.relics = relics or set()

    @classmethod
    def load(cls, export: Path = DEFAULT_EXPORT, id_map: Path = DEFAULT_ID_MAP) -> Cards:
        types: dict[str, str] = {}
        doc = json.loads(Path(export).read_text(encoding="utf-8"))["results"][0]
        for pool in doc["card_pools"].values():
            for c in pool["all"]:
                types.setdefault(c["id"], c["type"])
        ids, relics = None, None
        if Path(id_map).is_file():
            im = json.loads(Path(id_map).read_text(encoding="utf-8"))
            ids = {v: slug(k) for k, v in im["cards"].items()}
            relics = {slug(k) for k in im.get("relics", {})}
        return cls(types, ids, relics)

    def vanilla(self, r: dict) -> bool:
        """Every card and relic of the run's final deck and relics is in the emulator's id map (D13's vanilla filter, on the final holdings)."""
        pl = r["players"][0]
        if self.types and any(_cid(c["id"]) not in self.types for c in pl.get("deck") or []):
            return False
        return not self.relics or all(_cid(x["id"]) in self.relics for x in pl.get("relics") or [])

    def kind(self, name: str) -> str:
        """attack, skill, power or other (curses, statuses, quests)."""
        t = self.types.get(name.rstrip("+"), "")
        return {"Attack": "attack", "Skill": "skill", "Power": "power"}.get(t, "other")

    def name(self, card_id: int, upgraded: bool = False) -> str:
        return self.ids.get(int(card_id), f"?{int(card_id)}") + ("+" if upgraded else "")


# ------------------------------------------------------------------------------------------------ the exam fifth (D38)


def exam_bucket(run_id: str) -> int:
    """The fifth of the corpus a run belongs to, by its run id: a fixed hash, so the split never moves."""
    return int(hashlib.sha256((EXAM_SALT + str(run_id)).encode()).hexdigest()[:8], 16) % 5


def is_exam(run_id: str) -> bool:
    return exam_bucket(run_id) == EXAM_BUCKET


# ------------------------------------------------------------------------------------------------ the human corpus


def human_ok(r: dict) -> bool:
    """Ironclad, Ascension 10, standard, one player, finished (not abandoned), no modifiers."""
    pl = r.get("players") or []
    return (r.get("ascension") == 10 and r.get("game_mode") == "standard" and not r.get("was_abandoned") and not r.get("modifiers")
            and len(pl) == 1 and pl[0].get("character") == "CHARACTER.IRONCLAD")


def _cid(x: Any) -> str:
    return str(x).split(".", 1)[-1]


def replay_deck(points: list[dict]) -> Counter:
    """The deck after `points` (rooms in order), as {(card, upgrade level): copies}: the starting deck, then each room's
    removals, transformations, gains, upgrades and downgrades."""
    deck: Counter = Counter()
    for c in START_DECK:
        deck[(c, 0)] += 1

    def take(name: str, level: int) -> None:
        if deck[(name, level)] > 0:
            deck[(name, level)] -= 1
            return
        for key in list(deck):  # the record names no such level: take any copy of the card
            if key[0] == name and deck[key] > 0:
                deck[key] -= 1
                return

    for pt in points:
        for ps in pt.get("player_stats") or []:
            for c in ps.get("cards_removed") or []:
                take(_cid(c["id"]), int(c.get("current_upgrade_level", 0)))
            for t in ps.get("cards_transformed") or []:
                o, f = t["original_card"], t["final_card"]
                take(_cid(o["id"]), int(o.get("current_upgrade_level", 0)))
                deck[(_cid(f["id"]), int(f.get("current_upgrade_level", 0)))] += 1
            for c in ps.get("cards_gained") or []:
                deck[(_cid(c["id"]), int(c.get("current_upgrade_level", 0)))] += 1
            for cid in ps.get("upgraded_cards") or []:
                if deck[(_cid(cid), 0)] > 0:
                    deck[(_cid(cid), 0)] -= 1
                    deck[(_cid(cid), 1)] += 1
            for cid in ps.get("downgraded_cards") or []:
                if deck[(_cid(cid), 1)] > 0:
                    deck[(_cid(cid), 1)] -= 1
                    deck[(_cid(cid), 0)] += 1
    return +deck


def deck_list(deck: Counter) -> list[str]:
    return sorted(f"{c}{'+' if lv else ''}" for (c, lv), n in deck.items() for _ in range(n))


def final_deck(r: dict) -> Counter:
    """The run's last deck as the record lists it (for checking `replay_deck`)."""
    return Counter((_cid(c["id"]), int(c.get("current_upgrade_level", 0))) for c in r["players"][0].get("deck") or [])


def _stats(pt: dict) -> dict:
    ps = pt.get("player_stats") or [{}]
    return ps[0]


def human_potions(points: list[dict]) -> int:
    """Potions held after `points`: picked and bought, less used and discarded (a reconstruction; the record has no belt)."""
    n = 0
    for pt in points:
        for ps in pt.get("player_stats") or []:
            n += sum(1 for p in ps.get("potion_choices") or [] if p.get("was_picked")) + len(ps.get("bought_potions") or [])
            n -= len(ps.get("potion_used") or []) + len(ps.get("potion_discarded") or [])
            n = max(n, 0)
    return min(n, 3)


def human_summary(r: dict, cards: Cards | None = None) -> dict | None:
    """One human run as a summary, or None when it is not an Ironclad A10 standard single-player finished run (and, with `cards`,
    vanilla: every final card and relic is in the emulator's id map)."""
    if not human_ok(r) or (cards is not None and not cards.vanilla(r)):
        return None
    acts = list(r.get("map_point_history") or [])
    flat = [pt for a in acts for pt in a]
    win = bool(r.get("win"))
    ended_by = ((r.get("killed_by_encounter") or "NONE.NONE") != "NONE.NONE"
                or (r.get("killed_by_event") or "NONE.NONE") != "NONE.NONE")
    relics = r["players"][0].get("relics") or []
    out: dict = {"src": "h", "id": r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}", "floor": len(flat), "won": win,
                 "end": "win" if win else ("death" if ended_by else "none"), "a": [None, None]}
    out["ex"] = int(is_exam(out["id"]))
    tk = sk = hl = sm = 0
    for pt in flat:
        if pt["map_point_type"] not in ("shop", "ancient"):
            ch = _stats(pt).get("card_choices")
            if ch:
                if any(c.get("was_picked") for c in ch):
                    tk += 1
                else:
                    sk += 1
        if pt["map_point_type"] == "rest_site":
            for c in _stats(pt).get("rest_site_choices") or []:
                hl += c.upper() == "HEAL"
                sm += c.upper() == "SMITH"
    out["tot"] = {"taken": tk, "skipped": sk, "heal": hl, "smith": sm}
    base = 0
    for a in (0, 1):
        cur = acts[a] if a < len(acts) else []
        if not cur:
            continue
        reached = cur[-1]["map_point_type"] == "boss"
        later = len(acts) > a + 1 and bool(acts[a + 1])
        last_act = len(acts) == a + 1
        d: dict = {"r": int(reached), "k": None, "at": None}
        j = base + len(cur) - 1  # the index, in the whole run, of the boss room or of the room that ended the run
        if reached:
            d["k"] = int(later) if (later or ended_by or win) else None
            d["boss"] = _cid(((cur[-1].get("rooms") or [{}])[0].get("model_id")) or "")
            d["at"] = "boss"
            pre = cur[:-1]
        elif last_act and not win:
            d["at"] = "death" if j >= 1 else None
            pre = cur[:-1]
        else:
            pre = cur
        if d["at"] and j >= 1:
            prev = _stats(flat[j - 1])
            d["hp"], d["mhp"], d["gold"] = prev.get("current_hp"), prev.get("max_hp"), prev.get("current_gold")
            d["deck"] = deck_list(replay_deck(flat[:j]))
            d["rel"] = sum(1 for x in relics if int(x.get("floor_added_to_deck", 0)) <= j)
            d["pot"] = human_potions(flat[:j])
        elif d["at"]:
            d["at"] = None
        path, rests, offers, shop = [], [], [], {"v": 0, "c": 0, "r": 0, "x": 0}
        pots = [0, 0]
        for pt in pre:
            t, s = pt["map_point_type"], _stats(pt)
            if t in HUMAN_ROOM:
                path.append(HUMAN_ROOM[t])
            if t not in ("shop", "ancient"):
                for pc in s.get("potion_choices") or []:
                    pots[0 if pc.get("was_picked") else 1] += 1
            if t == "rest_site":
                for c in s.get("rest_site_choices") or []:
                    mhp = s.get("max_hp") or 0
                    before = (s.get("current_hp", 0) - s.get("hp_healed", 0)) / mhp if mhp else None
                    rests.append([None if before is None else round(before, 3), c.lower()])
            if t == "shop":
                shop["v"] += 1
                shop["c"] += len(s.get("cards_gained") or [])
                shop["r"] += len(s.get("bought_relics") or [])
                shop["x"] += len(s.get("cards_removed") or [])
            elif t != "ancient" and s.get("card_choices"):
                ch = s["card_choices"]
                took = next((_cid(c["card"]["id"]) for c in ch if c.get("was_picked")), None)
                offers.append([took, [_cid(c["card"]["id"]) for c in ch]])
        d.update(path="".join(path), rests=rests, offers=offers, shop=shop, pots=pots)
        out["a"][a] = d
        base += len(cur)
    return out


# ------------------------------------------------------------------------------------------------ self-play RunRecords


def _chosen(d: dict) -> str | None:
    ch, opts = d.get("chosen"), d.get("options") or []
    return opts[ch]["kind"] if isinstance(ch, int) and 0 <= ch < len(opts) else None


def ai_summary(rec: dict, cards: Cards) -> dict:
    """One RunRecord (the lab's self-play shards) as a summary."""
    decisions, fights, oc = rec.get("decisions") or [], rec.get("fights") or [], rec.get("outcome") or {}
    won, died = bool(oc.get("won")), bool(oc.get("died"))
    out: dict = {"src": "s", "id": rec.get("seed"), "gen": rec.get("generation"), "floor": oc.get("final_floor"), "won": won,
                 "end": "win" if won else ("death" if died else "none"), "a": [None, None]}
    tk = sk = hl = sm = 0
    for d in decisions:
        k = _chosen(d)
        tk += d["type"] == "card_reward" and k == "card.take"
        sk += d["type"] == "card_reward" and k == "card.skip"
        hl += d["type"] == "rest" and k == "rest.heal"
        sm += d["type"] == "rest" and k == "rest.smith"
    out["tot"] = {"taken": tk, "skipped": sk, "heal": hl, "smith": sm}
    for a in (0, 1):
        ds = [d for d in decisions if d["state"]["act_index"] == a]
        if not ds:
            continue
        boss = next((f for f in fights if f["node_type"] == 6 and f["state"]["act_index"] == a), None)
        dd: dict = {"r": int(boss is not None), "k": None, "at": None}
        snap = None
        if boss is not None:
            dd["k"] = int(bool(boss["won"]))
            dd["at"], snap = "boss", boss["state"]
            dd["boss"] = BOSSES.get(boss["state"].get("boss"), str(boss["state"].get("boss")))
        elif died and not oc.get("truncated"):
            last = fights[-1] if fights else None
            if last is not None and last["state"]["act_index"] == a and not last["won"]:
                dd["at"], snap = "death", last["state"]
            elif ds[-1]["state"]["act_index"] == a and (not last or last["state"]["act_index"] <= a):
                dd["at"], snap = "death", ds[-1]["state"]  # the run ended outside a fight (an event)
        if snap is not None:
            dd.update(hp=snap["hp"], mhp=snap["max_hp"], gold=snap["gold"], pot=len(snap.get("potions") or []),
                      rel=len(snap.get("relics") or []), deck=sorted(cards.name(c[0], bool(c[1])) for c in snap["deck"]))
        pre = [d for d in ds if d["state"]["floor"] < BOSS_FLOOR[a]]
        path, rests, offers, shop = [], [], [], {"v": 0, "c": 0, "r": 0, "x": 0}
        shop_floors: set[int] = set()
        pots, elites = [0, 0], [0, 0]  # potion rewards [taken, left]; map choices [with an elite on offer, took an elite]
        for d in pre:
            k, st = _chosen(d), d["state"]
            if d["type"] == "map":
                node = d["options"][d["chosen"]].get("node") if k else None
                letter = NODE_LETTER.get(node[2], "x") if node else "x"
                if letter not in ("B", "A"):
                    path.append(letter)
                if any((o.get("node") or [0, 0, 0])[2] == 2 for o in d["options"]):
                    elites[0] += 1
                    elites[1] += letter == "E"
            elif d["type"] == "rewards":
                if k == "reward.potion":
                    pots[0] += 1
                elif k == "reward.proceed":
                    pots[1] += sum(1 for o in d["options"] if o["kind"] == "reward.potion")
            elif d["type"] == "rest" and k:
                mhp = st["max_hp"]
                rests.append([round(st["hp"] / mhp, 3) if mhp else None, k.split(".", 1)[1]])
            elif d["type"] == "card_reward":
                opts = d["options"]
                took = None
                if k == "card.take":
                    c = opts[d["chosen"]]["card"]
                    took = cards.name(c[0], bool(c[1]))
                offers.append([took, [cards.name(o["card"][0], bool(o["card"][1])) for o in opts if o["kind"] == "card.take"]])
            elif d["type"] == "shop":
                if st["floor"] not in shop_floors:
                    shop_floors.add(st["floor"])
                    shop["v"] += 1
                shop["c"] += k == "shop.card"
                shop["r"] += k == "shop.relic"
                shop["x"] += k == "shop.remove"
        dd.update(path="".join(path), rests=rests, offers=offers, shop=shop, pots=pots, elites=elites)
        out["a"][a] = dd
    return out


def shard_files(runs_root: Path, gens: set[int]) -> Iterator[tuple[Path, int]]:
    """The run shards (r*.jsonl.gz) of every self-play job of the given generations."""
    for job in sorted(Path(runs_root).glob("*selfplay*")):
        meta = job / "shards" / "shards.json"
        if not meta.is_file():
            continue
        try:
            g = int(json.loads(meta.read_text(encoding="utf-8")).get("generation", -1))
        except (ValueError, OSError):
            continue
        if g in gens:
            for p in sorted((job / "shards").glob("r*.jsonl.gz")):
                yield p, g


# ------------------------------------------------------------------------------------------------ the nightly runs.jsonl rows


def split_nodes(nodes: str) -> list[str]:
    """The map letters of a row, cut at each boss ('B'): [act 1 rooms, act 2 rooms, ...], the boss letters themselves dropped."""
    parts, cur = [], []
    for ch in nodes or "":
        if ch == "B":
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def night_summary(row: dict) -> dict | None:
    """One nightly row (the real arm or the emulator arm) as a summary; None for a crash row (counted as a loss elsewhere)."""
    if row.get("crash"):
        return None
    acts_b = {int(a): float(f) for a, f in row.get("boss_damage_acts") or []}
    floor = int(row.get("floor") or 0)
    out: dict = {"src": "n", "id": row.get("seed"), "floor": floor, "won": bool(row.get("win")), "end": row.get("end"), "a": [None, None]}
    cards, rests, nodes = row.get("cards") or [], row.get("rests") or [], split_nodes(row.get("nodes") or "")
    tk = sum(1 for _f, c in cards if c != "skip")
    out["tot"] = {"taken": tk, "skipped": len(cards) - tk, "heal": sum(1 for _f, k in rests if k == "heal"),
                  "smith": sum(1 for _f, k in rests if k == "smith")}
    for a in (0, 1):
        if a == 1 and floor <= BOSS_FLOOR[0]:
            break
        lo, hi = (1, BOSS_FLOOR[0]) if a == 0 else (BOSS_FLOOR[0] + 1, BOSS_FLOOR[1])
        dd: dict = {"r": int(a in acts_b), "k": None, "at": None}
        if a in acts_b:
            dd["k"] = int(acts_b[a] >= 1.0)
        dd["path"] = nodes[a] if a < len(nodes) else ""
        dd["rests"] = [[None, k] for f, k in rests if lo <= f < hi]
        dd["offers"] = [[None if c == "skip" else c, None] for f, c in cards if lo <= f < hi]
        out["a"][a] = dd
    return out


# ------------------------------------------------------------------------------------------------ aggregation


COHORTS = ("entered", "boss", "killed", "lost", "before")
COHORT_TEXT = {"entered": "entered the act", "boss": "reached the boss", "killed": "killed the boss", "lost": "died at the boss",
               "before": "died before the boss"}


def in_cohort(a: dict | None, name: str) -> bool:
    if a is None:
        return False
    return {"entered": True, "boss": bool(a.get("r")), "killed": bool(a.get("r")) and a.get("k") == 1,
            "lost": bool(a.get("r")) and a.get("k") == 0, "before": not a.get("r") and a.get("at") == "death"}[name]


HP_BINS = ("<40%", "40-60%", "60-80%", ">=80%")


def hp_bin(f: float | None) -> str | None:
    if f is None:
        return None
    return "<40%" if f < 0.4 else "40-60%" if f < 0.6 else "60-80%" if f < 0.8 else ">=80%"


def cell(runs: list[dict], act: int, cohort: str, cards: Cards) -> dict:
    """The figures of one table cell: `runs` are summaries, filtered to the cohort here. Means are over the runs that carry the field."""
    sel = [r["a"][act] for r in runs if in_cohort(r["a"][act], cohort)]
    n = len(sel)
    out: dict = {"n": n}
    if not n:
        return out
    snaps = [a for a in sel if a.get("deck") is not None]
    out["n_snap"] = len(snaps)
    if snaps:
        def mean(f) -> float:
            return sum(f(a) for a in snaps) / len(snaps)

        out["hp"] = mean(lambda a: a["hp"])
        out["mhp"] = mean(lambda a: a["mhp"])
        out["hp_frac"] = mean(lambda a: a["hp"] / a["mhp"] if a["mhp"] else 0.0)
        out["gold"] = mean(lambda a: a["gold"])
        out["relics"] = mean(lambda a: a["rel"])
        out["potions"] = mean(lambda a: a.get("pot", 0))
        out["deck"] = mean(lambda a: len(a["deck"]))
        out["upgraded"] = mean(lambda a: sum(c.endswith("+") for c in a["deck"]))
        for kind in ("attack", "skill", "power", "other"):
            out[kind] = mean(lambda a, kind=kind: sum(cards.kind(c) == kind for c in a["deck"]))
        out["basic"] = mean(lambda a: sum(c.rstrip("+") in ("STRIKE_IRONCLAD", "DEFEND_IRONCLAD") for c in a["deck"]))
        pres: Counter = Counter()
        for a in snaps:
            for c in set(x.rstrip("+") for x in a["deck"]):
                if c not in BASIC:
                    pres[c] += 1
        out["top_cards"] = [[c, round(v / len(snaps), 3)] for c, v in pres.most_common(12)]
    paths: Counter = Counter()
    for a in sel:
        paths.update(a.get("path") or "")
    out["path"] = {k: paths[k] / n for k in "MERST?"}
    rc: Counter = Counter()
    for a in sel:
        for _hp, k in a.get("rests") or []:
            rc[k] += 1
    out["rest_heal"], out["rest_smith"] = rc["heal"] / n, rc["smith"] / n
    out["rest_other"] = (sum(rc.values()) - rc["heal"] - rc["smith"]) / n
    tk = sum(1 for a in sel for took, _o in a.get("offers") or [] if took)
    sk = sum(1 for a in sel for took, _o in a.get("offers") or [] if not took)
    out["taken"], out["skipped"] = tk / n, sk / n
    out["skip_rate"] = sk / (tk + sk) if tk + sk else None
    pots = [a["pots"] for a in sel if a.get("pots")]
    if pots:
        out["pot_taken"], out["pot_left"] = sum(x[0] for x in pots) / len(pots), sum(x[1] for x in pots) / len(pots)
    el = [a["elites"] for a in sel if a.get("elites")]
    if el and sum(x[0] for x in el):
        out["elite_take_rate"] = sum(x[1] for x in el) / sum(x[0] for x in el)
        out["elite_offers"] = sum(x[0] for x in el) / len(el)
    sh = [a["shop"] for a in sel if a.get("shop")]
    if sh:
        out["shop_visits"] = sum(s["v"] for s in sh) / len(sh)
        out["shop_cards"] = sum(s["c"] for s in sh) / len(sh)
        out["shop_relics"] = sum(s["r"] for s in sh) / len(sh)
        out["shop_removals"] = sum(s["x"] for s in sh) / len(sh)
    return out


def rest_by_hp(runs: list[dict], act: int) -> dict:
    """The rest sites of an act by the HP fraction on arrival: {bin: [sites, share that upgraded]}."""
    cnt: dict[str, list[int]] = {b: [0, 0] for b in HP_BINS}
    for r in runs:
        for hp, k in ((r["a"][act] or {}).get("rests") or []):
            b = hp_bin(hp)
            if b and k in ("heal", "smith"):
                cnt[b][0] += 1
                cnt[b][1] += k == "smith"
    return {b: [c[0], (c[1] / c[0]) if c[0] else None] for b, c in cnt.items()}


def pick_rates(runs: list[dict], act: int) -> dict[str, list[int]]:
    """Per card, [times offered, times taken] over the card rewards before the act's boss."""
    out: dict[str, list[int]] = {}
    for r in runs:
        for took, offered in ((r["a"][act] or {}).get("offers") or []):
            for c in offered or []:
                c = c.rstrip("+")
                o = out.setdefault(c, [0, 0])
                o[0] += 1
                o[1] += (took or "").rstrip("+") == c
    return out


def boss_table(runs: list[dict], act: int) -> dict[str, dict]:
    """Per boss: runs that met it, the share killed, mean HP fraction on entry."""
    out: dict[str, dict] = {}
    for r in runs:
        a = r["a"][act]
        if a and a.get("r") and a.get("boss"):
            o = out.setdefault(a["boss"], {"n": 0, "known": 0, "killed": 0, "hp": []})
            o["n"] += 1
            o["known"] += a.get("k") is not None
            o["killed"] += a.get("k") == 1
            if a.get("hp") is not None and a.get("mhp"):
                o["hp"].append(a["hp"] / a["mhp"])
    return {b: {"n": o["n"], "kill_rate": (o["killed"] / o["known"]) if o["known"] else None,
                "hp_frac": (sum(o["hp"]) / len(o["hp"])) if o["hp"] else None} for b, o in out.items()}


def headline(runs: list[dict]) -> dict:
    """The run-level numbers every source shares: floors, boss reach and kill shares, whole-run picks and rests."""
    n = len(runs)
    out: dict = {"n": n}
    if not n:
        return out
    out["floor"] = sum(r["floor"] for r in runs) / n
    for a, tag in ((0, "a1"), (1, "a2")):
        reached = sum(1 for r in runs if r["a"][a] and r["a"][a].get("r"))
        killed = sum(1 for r in runs if r["a"][a] and r["a"][a].get("r") and r["a"][a].get("k") == 1)
        known = sum(1 for r in runs if r["a"][a] and r["a"][a].get("r") and r["a"][a].get("k") is not None)
        out[f"{tag}_reached"], out[f"{tag}_killed_share"] = reached / n, killed / n
        out[f"{tag}_kill_rate"] = killed / known if known else None
    out["a2_entered"] = sum(1 for r in runs if r["a"][1]) / n
    out["won"] = sum(1 for r in runs if r["won"]) / n
    tot: Counter = Counter()
    for r in runs:
        tot.update(r["tot"])
    out["taken_per_run"] = tot["taken"] / n
    out["skip_rate"] = tot["skipped"] / (tot["taken"] + tot["skipped"]) if tot["taken"] + tot["skipped"] else None
    out["smith_share"] = tot["smith"] / (tot["smith"] + tot["heal"]) if tot["smith"] + tot["heal"] else None
    return out


# ------------------------------------------------------------------------------------------------ a small logistic fit


FEATURES = ("hp_frac", "mhp", "upgraded", "relics", "potions", "attacks", "skills", "powers", "gold")


def features(a: dict, cards: Cards) -> list[float]:
    """What the run brought to the boss, as the kill model reads it."""
    d = a["deck"]
    kinds = Counter(cards.kind(c) for c in d)
    return [a["hp"] / a["mhp"] if a["mhp"] else 0.0, float(a["mhp"]), float(sum(c.endswith("+") for c in d)), float(a["rel"]),
            float(a.get("pot", 0)), float(kinds["attack"]), float(kinds["skill"]), float(kinds["power"]), float(a["gold"])]


def card_vocab(rows: list[dict], k: int = 60) -> list[str]:
    """The `k` non-basic cards held most often in `rows`' decks."""
    pres: Counter = Counter()
    for a in rows:
        pres.update(c for c in set(x.rstrip("+") for x in a["deck"]) if c not in BASIC)
    return [c for c, _ in pres.most_common(k)]


def card_featurizer(cards: Cards, vocab: list[str]):
    """The nine features plus the copies held of each card in `vocab`."""

    def fx(a: dict) -> list[float]:
        have = Counter(x.rstrip("+") for x in a["deck"])
        return features(a, cards) + [float(have[c]) for c in vocab]

    return fx


def logistic_fit(x: list[list[float]], y: list[int], steps: int = 60, ridge: float = 1e-3) -> list[float]:
    """Newton fit of a logistic regression with an intercept on standardised columns (L2 penalty `ridge` on the standardised weights);
    returns [intercept, w...] in the original units. Plain IRLS: enough for a few dozen columns and some thousand rows."""
    import numpy as np  # noqa: PLC0415

    X, Y = np.asarray(x, float), np.asarray(y, float)
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = np.hstack([np.ones((len(X), 1)), (X - mu) / sd])
    pen = ridge * np.eye(Z.shape[1])
    pen[0, 0] = 0.0
    w = np.zeros(Z.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ (p - Y) + pen @ w
        h = (Z * (p * (1 - p))[:, None]).T @ Z + pen + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(h, g)
        w -= step
        if float(np.abs(step).max()) < 1e-9:
            break
    slope = w[1:] / sd
    return [float(w[0] - (slope * mu).sum()), *[float(s) for s in slope]]


def predict(coef: list[float], x: list[float]) -> float:
    z = coef[0] + sum(c * v for c, v in zip(coef[1:], x))
    return 1 / (1 + math.exp(-max(min(z, 30), -30)))


def visits(runs: list[dict], act: int) -> list[dict]:
    """The boss visits of an act that carry a state and a known result."""
    return [r["a"][act] for r in runs if r["a"][act] and r["a"][act].get("r") and r["a"][act].get("k") is not None
            and r["a"][act].get("deck") is not None]


def kill_model(rows: list[dict], cards: Cards, min_rows: int = 200, fx=None, ridge: float = 1e-3) -> list[float] | None:
    """A logistic model of the boss kill on what the run brought, fitted on boss visits `rows` (None when there are too few)."""
    if len(rows) < min_rows:
        return None
    fx = fx or (lambda a: features(a, cards))
    return logistic_fit([fx(a) for a in rows], [int(a["k"]) for a in rows], ridge=ridge)


def mean_kill(coef: list[float], rows: list[dict], cards: Cards, shift: list[float] | None = None, fx=None) -> float:
    fx = fx or (lambda a: features(a, cards))
    xs = [fx(a) for a in rows]
    if shift:
        xs = [[v + d for v, d in zip(x, shift)] for x in xs]
    return sum(predict(coef, x) for x in xs) / len(xs)


def mean_vector(rows: list[dict], cards: Cards) -> list[float]:
    xs = [features(a, cards) for a in rows]
    return [sum(c) / len(xs) for c in zip(*xs)]


def shift_effects(coef: list[float], rows: list[dict], target: list[float], cards: Cards) -> dict[str, float]:
    """For `rows` (boss visits) the change in the mean modelled kill share when each feature's mean moves to `target`'s, the others
    held (names in FEATURES), and when all move together ('all')."""
    cur = mean_vector(rows, cards)
    base = mean_kill(coef, rows, cards)
    out = {}
    for i, name in enumerate(FEATURES):
        sh = [0.0] * len(FEATURES)
        sh[i] = target[i] - cur[i]
        out[name] = mean_kill(coef, rows, cards, sh) - base
    out["all"] = mean_kill(coef, rows, cards, [t - c for t, c in zip(target, cur)]) - base
    return out


def auc(scores: list[float], labels: list[int]) -> float:
    """Area under the ROC curve (rank form)."""
    n_pos = sum(1 for y in labels if y)
    n_neg = len(labels) - n_pos
    if not n_pos or not n_neg:
        return float("nan")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    rank = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        for t in range(i, j + 1):
            rank[order[t]] = (i + j) / 2 + 1
        i = j + 1
    rp = sum(rank[i] for i, y in enumerate(labels) if y)
    return (rp - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


# ------------------------------------------------------------------------------------------------ commands


def cmd_human(a: argparse.Namespace) -> int:
    below_normal()
    cards = Cards.load(Path(a.export), Path(a.id_map))
    n = seen = 0
    ids: list[str] = []

    def rows() -> Iterator[dict]:
        nonlocal n, seen
        with opener(Path(a.corpus)) as fh:
            for line in fh:
                if '"ascension":10' not in line or "CHARACTER.IRONCLAD" not in line:
                    continue
                seen += 1
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                s = human_summary(r, cards)
                if s is None:
                    continue
                n += 1
                if s["ex"]:
                    ids.append(s["id"])
                yield s
                if a.limit and n >= a.limit:
                    return

    cnt = write_jsonl(Path(a.out), rows())
    if a.exam_ids:
        Path(a.exam_ids).write_text("\n".join(sorted(ids)) + "\n", encoding="utf-8")
    print(f"human: {cnt} runs kept of {seen} Ironclad A10 lines; exam fifth {len(ids)}", file=sys.stderr)
    return 0


def check_replay(r: dict) -> tuple[bool, bool]:
    """Whether the replayed deck equals the run's final deck in cards (ignoring upgrades) and in the total of upgrades."""
    rep, fin = replay_deck([pt for a in r.get("map_point_history") or [] for pt in a]), final_deck(r)

    def by_card(d: Counter) -> Counter:
        out: Counter = Counter()
        for (name, _lv), n in d.items():
            out[name] += n
        return out

    return by_card(rep) == by_card(fin), sum(lv * n for (_c, lv), n in rep.items()) == sum(lv * n for (_c, lv), n in fin.items())


def cmd_check(a: argparse.Namespace) -> int:
    """How well the replayed deck matches the final deck, over the first `--limit` kept human runs (the evidence for the entry decks)."""
    cards = Cards.load(Path(a.export), Path(a.id_map))
    n = same = same_up = 0
    with opener(Path(a.corpus)) as fh:
        for line in fh:
            if '"ascension":10' not in line or "CHARACTER.IRONCLAD" not in line:
                continue
            r = json.loads(line)
            if not human_ok(r) or not cards.vanilla(r):
                continue
            ok_ids, ok_up = check_replay(r)
            n += 1
            same += ok_ids
            same_up += ok_up
            if n >= a.limit:
                break
    print(json.dumps({"runs": n, "same_cards": same, "same_upgrade_total": same_up}))
    return 0


def parse_gens(text: str) -> set[int]:
    out: set[int] = set()
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out.update(range(int(lo), int(hi or lo) + 1))
    return out


def cmd_selfplay(a: argparse.Namespace) -> int:
    below_normal()
    cards = Cards.load(Path(a.export), Path(a.id_map))

    def rows() -> Iterator[dict]:
        for path, _g in shard_files(Path(a.runs_root), parse_gens(a.gens)):
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        yield ai_summary(json.loads(line), cards)
                    except (KeyError, ValueError, IndexError, TypeError) as e:
                        print(f"skip a record in {path.name}: {type(e).__name__}", file=sys.stderr)

    print(f"selfplay: {write_jsonl(Path(a.out), rows())} runs", file=sys.stderr)
    return 0


def cmd_nights(a: argparse.Namespace) -> int:
    out: list[dict] = []
    for run_dir in sorted(Path(a.nightly).glob("20*/*")):
        p = run_dir / "runs.jsonl"
        if not p.is_file():
            continue
        night, arm = run_dir.parent.name, run_dir.name
        for row in read_jsonl(p):
            if "seed" not in row or "floor" not in row:
                continue
            s = night_summary(row)
            if s:
                s["night"], s["arm"] = night, arm
                out.append(s)
    print(f"nights: {write_jsonl(Path(a.out), out)} runs", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("human")
    h.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    h.add_argument("--out", required=True)
    h.add_argument("--exam-ids")
    h.add_argument("--limit", type=int, default=0)
    h.add_argument("--export", default=str(DEFAULT_EXPORT))
    h.add_argument("--id-map", default=str(DEFAULT_ID_MAP))
    h.set_defaults(fn=cmd_human)
    s = sub.add_parser("selfplay")
    s.add_argument("--runs-root", default="D:/spireline/referee/LAB/runs")
    s.add_argument("--gens", default="9")
    s.add_argument("--out", required=True)
    s.add_argument("--export", default=str(DEFAULT_EXPORT))
    s.add_argument("--id-map", default=str(DEFAULT_ID_MAP))
    s.set_defaults(fn=cmd_selfplay)
    c = sub.add_parser("check")
    c.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    c.add_argument("--limit", type=int, default=3000)
    c.add_argument("--export", default=str(DEFAULT_EXPORT))
    c.add_argument("--id-map", default=str(DEFAULT_ID_MAP))
    c.set_defaults(fn=cmd_check)
    n = sub.add_parser("nights")
    n.add_argument("--nightly", default="D:/spireline/referee/LAB/nightly")
    n.add_argument("--out", required=True)
    n.set_defaults(fn=cmd_nights)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
