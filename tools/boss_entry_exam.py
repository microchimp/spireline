"""The per-decision human exam: what a human chose at a card reward or a rest site, and what the AI's run-level chooser would choose.

    python tools/boss_entry_exam.py validate --runs-root LAB/runs --gen 9 --n-runs 300
    python tools/boss_entry_exam.py exam --corpus runs-v0.107.1.jsonl.gz --runs-root LAB/runs --out exam.json
    python tools/boss_entry_exam.py agreement --candidate cand/run_value.npz --incumbent inc/run_value.npz --out agreement.json

The chooser is the nightly agent's own run-level value head (V_run, `run_value.npz` with the lookahead macro's W): every option's
afterstate is valued by expected floors and the best is taken, exactly as `LookaheadPolicy` picks at tau = 0. It runs offline, on numpy
alone, through the fork's `rl/run_train` package (read, never written); the emulator's native library is not loaded (a stub stands in
for `sts2_gym.native`, which only the live-state builders use).

A human record is turned into the state the chooser reads (a RunView): HP, max HP, gold, deck, relics and potions are rebuilt from the
record's rooms up to the decision; the act, its region and (when the run met it) its boss are known. The one thing the corpus lacks is
the act map and the position on it, which the chooser reads (a block of numbers on the paths ahead). The state is therefore valued under
`K` donor maps: the maps and positions of the AI's own self-play states on the same floor of the same region, and the values are
averaged. `validate` measures what this costs on the AI's own states (the donor-averaged choice against the choice with the true
map). Map and shop choices, and events, are not examined: a map choice needs the map, a shop choice the prices, an event the event ids.

Only the held-out fifth of the corpus (D38) is read, and only to score the AI against it; nothing is written for training, and the
report holds aggregates over cells of at least `MIN_CELL` decisions.

`agreement` is the exam as a check on a candidate head (the fork's V_run keep test, D47/D49): the same held-out decisions are scored
with the candidate and with the incumbent head under the same donor maps, and the output is the share of decisions where each head
takes the human's choice (a card reward: the same card or skip; a rest site: the same of heal and upgrade) with the paired
difference and its standard error. A fixed seeded subset of the fifth's runs is read (`--max-runs`), the decisions of the fifth are
cached once in a local file outside the repositories (`SPEC_CACHE`), and only counts and rates leave the tool.
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import hashlib
import json
import math
import random
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boss_entry as be  # noqa: E402

FORK = Path("D:/spireline/fork/sts2")
RUN_VALUE = Path("D:/spireline/referee/agent/gen9/candidate/run_value.npz")
W_WON = 53.0  # the lookahead macro's worth of a won run (the policy block of every gen 9 record)
REGION = {"ACT.OVERGROWTH": 1, "ACT.UNDERDOCKS": 2, "ACT.HIVE": 3, "ACT.GLORY": 4}
REGION_BOSSES = {1: (74, 82, 83), 2: (77, 79, 84), 3: (75, 76, 81), 4: (73, 78, 80)}  # run_train.vocab.BOSSES by region
BOSS_ID = {v: k for k, v in be.BOSSES.items()}
MAX_FLOOR = 33  # Acts 1 and 2
SPEC_CACHE = Path("D:/spireline/referee/backlog/boss-entry/exam-specs.jsonl.gz")  # the fifth's decisions, local only (never committed)
AGREE_SEED = 20261103  # the seeded subset of the fifth's runs `agreement` reads, and its donor draws; fixed so every check scores the same decisions
SPEC_CACHE_VERSION = 1


# ------------------------------------------------------------------------------------------------ human record -> decision specs


class Ids:
    """Slug -> emulator id for cards, relics and potions."""

    def __init__(self, cards: dict[str, int], relics: dict[str, int], potions: dict[str, int]) -> None:
        self.cards, self.relics, self.potions = cards, relics, potions

    @classmethod
    def load(cls, id_map: Path = be.DEFAULT_ID_MAP) -> Ids:
        im = json.loads(Path(id_map).read_text(encoding="utf-8"))
        return cls(*({be.slug(k): v for k, v in im[sec].items()} for sec in ("cards", "relics", "potions")))


def replay_potions(points: list[dict]) -> Counter:
    """The potions held after `points`, by slug: those picked or bought, less those used or discarded (a reconstruction)."""
    have: Counter = Counter()
    for pt in points:
        for ps in pt.get("player_stats") or []:
            for p in ps.get("potion_choices") or []:
                if p.get("was_picked"):
                    have[be._cid(p["choice"])] += 1
            for p in ps.get("bought_potions") or []:
                have[be._cid(p)] += 1
            for p in (ps.get("potion_used") or []) + (ps.get("potion_discarded") or []):
                if have[be._cid(p)] > 0:
                    have[be._cid(p)] -= 1
    return +have


def human_specs(r: dict, ids: Ids, cards: be.Cards) -> list[dict]:
    """The card-reward and rest-site decisions of one human run in Acts 1 and 2 as state-plus-choice specs (plain data, no fork types).
    A decision whose state holds a card, relic or potion the emulator has no id for is left out."""
    if not be.human_ok(r) or not cards.vanilla(r):
        return []
    acts = list(r.get("map_point_history") or [])
    flat = [pt for a in acts for pt in a]
    names = r.get("acts") or []
    relics = r["players"][0].get("relics") or []
    out: list[dict] = []
    base = 0
    for a, cur in enumerate(acts[:2]):
        region = REGION.get(names[a]) if a < len(names) else None
        boss = None
        if cur and cur[-1]["map_point_type"] == "boss":
            boss = BOSS_ID.get(be._cid(((cur[-1].get("rooms") or [{}])[0].get("model_id")) or ""))
        for i, pt in enumerate(cur):
            j = base + i
            t, s = pt["map_point_type"], be._stats(pt)
            if region is None or j + 1 > MAX_FLOOR or j < 1:
                continue
            kind = None
            if t == "rest_site" and (s.get("rest_site_choices") or [""])[0].upper() in ("HEAL", "SMITH"):
                kind = "rest"
            elif t not in ("shop", "ancient", "boss", "rest_site") and s.get("card_choices"):
                kind = "card_reward"
            elif t == "boss" and s.get("card_choices"):
                continue  # the boss reward comes after the fight the act is judged on
            if kind is None:
                continue
            deck = be.replay_deck(flat[:j])
            hp = s.get("current_hp", 0) - (s.get("hp_healed", 0) if kind == "rest" else 0)
            held = [x for x in relics if int(x.get("floor_added_to_deck", 0)) <= j]
            pots = replay_potions(flat[:j])
            try:
                spec = {"type": kind, "act": a, "floor": j + 1, "region": region, "boss": boss, "hp": hp, "max_hp": s.get("max_hp"),
                        "gold": s.get("current_gold"),
                        "deck": [[ids.cards[c], lv] for (c, lv), n in deck.items() for _ in range(n)],
                        "relics": sorted(ids.relics[be._cid(x["id"])] for x in held),
                        "potions": sorted(ids.potions[p] for p, n in pots.items() for _ in range(n)),
                        "slots": 2 + (2 if any(be._cid(x["id"]) == "POTION_BELT" for x in held) else 0)}
                if kind == "card_reward":
                    ch = s["card_choices"]
                    spec["offered"] = [ids.cards[be._cid(c["card"]["id"])] for c in ch]
                    spec["picked"] = next((k for k, c in enumerate(ch) if c.get("was_picked")), None)
                else:
                    c0 = s["rest_site_choices"][0].upper()
                    spec["chose"] = c0.lower()
                    up = (s.get("upgraded_cards") or [None])[0]
                    spec["smith_card"] = ids.cards.get(be._cid(up)) if up else None
            except KeyError:
                continue
            out.append(spec)
        base += len(cur)
    return out


# ------------------------------------------------------------------------------------------------ the chooser (fork, offline)


class Chooser:
    """V_run and the fork's feature code, loaded without the emulator's native library."""

    def __init__(self, fork: Path = FORK, weights: Path = RUN_VALUE, w_won: float = W_WON) -> None:
        for p in (fork / "src", fork, fork / "rl"):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        import sts2_gym  # noqa: PLC0415 -- the package loads its library lazily

        stub = types.ModuleType("sts2_gym.native")  # only the live-state builders read it
        sts2_gym.native = stub
        sys.modules["sts2_gym.native"] = stub
        import run_train  # noqa: PLC0415,F401

        pick = types.ModuleType("run_train.selfplay")  # policy imports the self-play module for a type only
        pick.Pick = type("Pick", (), {"__init__": lambda self, *a, **k: None})
        sys.modules["run_train.selfplay"] = pick
        from run_train import features, policy, shards, vocab  # noqa: PLC0415

        self.F, self.policy, self.shards, self.vocab = features, policy, shards, vocab
        self.model = dataclasses.replace(policy.load(weights), W=w_won)

    def view(self, spec: dict, boss: int, donor: tuple | None) -> Any:
        F = self.F
        nodes, pos = donor if donor else ((), (0, 0))
        return F.RunView(ascension=10, act_index=spec["act"], act_region=spec["region"], floor=spec["floor"], hp=spec["hp"],
                         max_hp=spec["max_hp"], gold=spec["gold"], deck=tuple(F.CardRef(c, bool(u)) for c, u in spec["deck"]),
                         relics=tuple(spec["relics"]), potions=tuple(spec["potions"]), max_potion_slots=spec["slots"],
                         map_nodes=nodes, position=pos, boss=boss)

    def decision(self, spec: dict, view: Any) -> tuple[Any, list[str]]:
        """The screen's options for a spec and a label per option."""
        F = self.F
        if spec["type"] == "card_reward":
            opts = [F.Option("card.take", i, card=F.CardRef(c, False)) for i, c in enumerate(spec["offered"])]
            opts.append(F.Option("card.skip", len(opts)))
            labels = [f"take:{c}" for c in spec["offered"]] + ["skip"]
        else:
            opts = [F.Option("rest.heal", 0)]
            labels = ["heal"]
            seen = set()
            for i, card in enumerate(view.deck):
                if card in seen or not self.vocab.card_upgradable(card.card_id, card.upgraded):
                    continue
                seen.add(card)
                opts.append(F.Option("rest.smith", 1, deck_index=i))
                labels.append(f"smith:{card.card_id}")
        return F.Decision(spec["type"], tuple(opts)), labels

    def values(self, spec: dict, donors: list[tuple] | None) -> tuple[list[float], list[str]]:
        """Mean V_W (expected floors) of each option over the donor maps (and over the region's bosses when the run never met its boss)."""
        bosses = [spec["boss"]] if spec.get("boss") else list(REGION_BOSSES[spec["region"]])
        total, n, labels = None, 0, []
        for boss in bosses:
            for donor in donors or [None]:
                view = self.view(spec, boss, donor)
                dec, labels = self.decision(spec, view)
                sc = {id(s.option): s.value for s in self.policy.score_options(dec, view, self.model)}
                vec = [sc[id(o)] for o in dec.options]
                total = vec if total is None else [a + b for a, b in zip(total, vec)]
                n += 1
        return [v / n for v in total], labels


class Donors:
    """Maps and positions of the AI's own self-play states, by region and floor."""

    def __init__(self, chooser: Chooser, runs_root: Path, gen: int, n_runs: int, seed: int = 7, per_key: int = 60,
                 skip_pool: int = 0) -> None:
        self.by: dict[tuple[int, int], list[tuple]] = defaultdict(list)
        self.runs: list[dict] = []
        rnd = random.Random(seed)
        files = [p for p, _g in be.shard_files(runs_root, {gen})]
        rnd.shuffle(files)
        for f in files:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    self.runs.append(rec)
                    cache: dict[int, tuple] = {}
                    for d in rec["decisions"] if len(self.runs) > skip_pool else []:
                        st = d["state"]
                        key = (st["act_region"], st["floor"])
                        if len(self.by[key]) >= per_key:
                            continue
                        if st["map"] not in cache:
                            cache[st["map"]] = chooser.shards._nodes_from_json(rec["maps"][st["map"]]["nodes"])
                        self.by[key].append((cache[st["map"]], (st["position"][0], st["position"][1])))
                    if len(self.runs) >= n_runs:
                        return

    def sample(self, region: int, floor: int, k: int, rnd: random.Random, exclude: Any = None) -> list[tuple]:
        pool = self.by.get((region, floor)) or []
        return rnd.sample(pool, min(k, len(pool))) if pool else []


# ------------------------------------------------------------------------------------------------ scoring


def argmax(v: list[float]) -> int:
    return max(range(len(v)), key=lambda i: v[i])


def score_spec(ch: Chooser, spec: dict, donors: list[tuple]) -> dict | None:
    """What the chooser prefers at one human decision and how that differs from the human's choice."""
    if not donors:
        return None
    vals, labels = ch.values(spec, donors)
    top = argmax(vals)
    if spec["type"] == "card_reward":
        human = spec["picked"] if spec["picked"] is not None else len(labels) - 1
        rank = sorted(range(len(vals)), key=lambda i: -vals[i]).index(human)
        return {"top": top, "human": human, "rank": rank, "regret": vals[top] - vals[human],
                "ai_skip": labels[top] == "skip", "human_skip": human == len(labels) - 1,
                "ai_card": spec["offered"][top] if top < len(spec["offered"]) else None,
                "human_card": spec["offered"][human] if human < len(spec["offered"]) else None, "offered": spec["offered"]}
    ai_smith = labels[top].startswith("smith")
    human_smith = spec["chose"] == "smith"
    out = {"ai_smith": ai_smith, "human_smith": human_smith, "hp_frac": spec["hp"] / spec["max_hp"] if spec["max_hp"] else None,
           "heal_minus_best_smith": vals[0] - max(vals[1:]) if len(vals) > 1 else None}
    if human_smith and spec.get("smith_card") is not None:
        mine = [i for i, lab in enumerate(labels) if lab == f"smith:{spec['smith_card']}"]
        out["human_card_regret"] = (max(vals[1:]) - vals[mine[0]]) if mine and len(vals) > 1 else None
    return out


def cmd_validate(a: argparse.Namespace) -> int:
    """The donor-averaged chooser against the chooser with the true map, on the AI's own states (records not in the donor pool)."""
    be.below_normal()
    ch = Chooser()
    donors = Donors(ch, Path(a.runs_root), a.gen, a.n_runs + a.donor_runs, skip_pool=a.n_runs)
    pool_runs = donors.runs
    rnd = random.Random(11)
    agree = {"card_reward": [0, 0, 0], "rest": [0, 0, 0]}
    for rec in pool_runs[:a.n_runs]:
        for d in rec["decisions"]:
            if d["type"] not in agree:
                continue
            dec = ch.shards.entry_decision(d)
            view = ch.shards.state_view(rec, d)
            full = {id(s.option): s.value for s in ch.policy.score_options(dec, view, ch.model)}
            vf = [full[id(o)] for o in dec.options]
            dn = donors.sample(view.act_region, view.floor, a.k, rnd)
            if not dn:
                continue
            acc = None
            for nodes, pos in dn:
                v2 = dataclasses.replace(view, map_nodes=nodes, position=pos)
                sc = {id(s.option): s.value for s in ch.policy.score_options(dec, v2, ch.model)}
                vec = [sc[id(o)] for o in dec.options]
                acc = vec if acc is None else [x + y for x, y in zip(acc, vec)]
            blind = {id(s.option): s.value for s in ch.policy.score_options(dec, dataclasses.replace(view, map_nodes=(), position=(0, 0)), ch.model)}
            vb = [blind[id(o)] for o in dec.options]
            kind = (lambda i: dec.options[i].kind) if d["type"] == "rest" else (lambda i: i)
            r = agree[d["type"]]
            r[0] += kind(argmax(acc)) == kind(argmax(vf))
            r[1] += kind(argmax(vb)) == kind(argmax(vf))
            r[2] += 1
    out = {k: {"donor_average": v[0] / v[2], "no_map": v[1] / v[2], "decisions": v[2]} for k, v in agree.items() if v[2]}
    print(json.dumps(out))
    return 0


def cmd_exam(a: argparse.Namespace) -> int:
    be.below_normal()
    cards = be.Cards.load()
    ids = Ids.load()
    ch = Chooser()
    donors = Donors(ch, Path(a.runs_root), a.gen, a.donor_runs)
    rnd = random.Random(5)
    rows: list[dict] = []
    done = skipped = 0
    with be.opener(Path(a.corpus)) as fh:
        for line in fh:
            if '"ascension":10' not in line or "CHARACTER.IRONCLAD" not in line:
                continue
            r = json.loads(line)
            rid = r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}"
            if not be.human_ok(r) or not be.is_exam(rid) or not cards.vanilla(r):
                continue  # the exam fifth only (vanilla runs, as the tables count them)
            for spec in human_specs(r, ids, cards):
                res = score_spec(ch, spec, donors.sample(spec["region"], spec["floor"], a.k, rnd))
                if res is None:
                    skipped += 1
                    continue
                res.update(type=spec["type"], act=spec["act"], floor=spec["floor"])
                rows.append(res)
            done += 1
            if a.limit and done >= a.limit:
                break
    Path(a.out).write_text(json.dumps({"runs": done, "skipped": skipped, "rows": rows}, separators=(",", ":")), encoding="utf-8")
    print(f"exam: {done} exam-fifth runs, {len(rows)} decisions scored, {skipped} without donor maps", file=sys.stderr)
    return 0


# ------------------------------------------------------------------------------------------------ agreement (the keep test's human leg)


def paired(a: list[float], b: list[float]) -> dict:
    """Rate `a` (the candidate) and rate `b` (the incumbent) over the same decisions, and their paired difference with its standard error."""
    n = len(a)
    if n == 0:
        return {"n": 0, "candidate": None, "incumbent": None, "diff": None, "se": None}
    d = [x - y for x, y in zip(a, b)]
    mean = sum(d) / n
    se = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1) / n) if n > 1 else None
    return {"n": n, "candidate": sum(a) / n, "incumbent": sum(b) / n, "diff": mean, "se": se}


def run_id(r: dict) -> str:
    return r.get("run_hash") or f"{r.get('seed')}:{r.get('start_time')}"


def exam_specs(corpus: Path, ids_file: Path | None, cache: Path = SPEC_CACHE, rebuild: bool = False, cards: be.Cards | None = None,
               idm: Ids | None = None) -> dict[str, list[dict]]:
    """The held-out fifth's card-reward and rest-site decisions by run id. Read from the cache when it matches the corpus file and the id
    list; otherwise the corpus is scanned once (several minutes) and the cache written. The cache is a local file, not part of any repo."""
    ids = set(Path(ids_file).read_text(encoding="utf-8").split()) if ids_file else None
    meta = {"version": SPEC_CACHE_VERSION, "corpus_bytes": Path(corpus).stat().st_size,
            "ids_sha": hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest() if ids is not None else None}
    if cache.is_file() and not rebuild:
        with gzip.open(cache, "rt", encoding="utf-8") as fh:
            head = json.loads(fh.readline())
            if head.get("meta") == meta:
                return {row["rid"]: row["specs"] for row in map(json.loads, fh)}
    cards, idm = cards or be.Cards.load(), idm or Ids.load()
    out: dict[str, list[dict]] = {}
    with be.opener(Path(corpus)) as fh:
        for line in fh:
            if '"ascension":10' not in line or "CHARACTER.IRONCLAD" not in line:
                continue
            r = json.loads(line)
            rid = run_id(r)
            if not be.human_ok(r) or not cards.vanilla(r) or not (rid in ids if ids is not None else be.is_exam(rid)):
                continue
            specs = human_specs(r, idm, cards)
            if specs:
                out[rid] = specs
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(cache.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps({"meta": meta}) + "\n")
        for rid in sorted(out):
            fh.write(json.dumps({"rid": rid, "specs": out[rid]}, separators=(",", ":")) + "\n")
    tmp.replace(cache)
    return out


def agree_flag(res: dict, kind: str) -> float:
    """1.0 when the head's choice is the human's: the same pick (a card or skip) at a card reward, the same of heal and upgrade at a rest."""
    return float(res["top"] == res["human"]) if kind == "card_reward" else float(res["ai_smith"] == res["human_smith"])


def agreement_doc(heads: list[list[tuple[str, dict | None]]], labels: list[str]) -> dict:
    """The measures of every head but the last (the incumbent) against the last, from per-decision (kind, score) lists, one list per
    head over the same decisions; a decision any head could not score (None) is left out of all."""
    n = len(heads[0])
    keep = [j for j in range(n) if all(h[j][1] is not None for h in heads)]
    flags = [{k: [agree_flag(h[j][1], k) for j in keep if h[j][0] == k] for k in ("card_reward", "rest")} for h in heads]
    extra = [{"skip": [float(h[j][1]["ai_skip"]) for j in keep if h[j][0] == "card_reward"],
              "upgrade": [float(h[j][1]["ai_smith"]) for j in keep if h[j][0] == "rest"]} for h in heads]
    last = len(heads) - 1
    cands = [{"label": labels[i], "measures": {k: paired(flags[i][k], flags[last][k]) for k in ("card_reward", "rest")},
              "skip_share": paired(extra[i]["skip"], extra[last]["skip"]),
              "upgrade_share": paired(extra[i]["upgrade"], extra[last]["upgrade"])} for i in range(last)]
    return {"scored": len(keep), "skipped_without_donor_maps": n - len(keep), "candidates": cands,
            "incumbent": {"agreement": {k: (sum(v) / len(v) if v else None) for k, v in flags[last].items()}}}


def cmd_agreement(a: argparse.Namespace) -> int:
    be.below_normal()
    cands = [Path(p) for p in a.candidate]
    inc = Path(a.incumbent)
    chs = [Chooser(Path(a.fork), p, a.w) for p in cands + [inc]]
    specs = exam_specs(Path(a.corpus), Path(a.exam_ids) if a.exam_ids else None, Path(a.cache), a.rebuild_cache)
    rids = sorted(specs)
    if a.max_runs and a.max_runs < len(rids):
        rids = sorted(random.Random(AGREE_SEED).sample(rids, a.max_runs))
    donors = Donors(chs[0], Path(a.runs_root), a.gen, a.donor_runs)
    rnd = random.Random(AGREE_SEED)
    heads: list[list[tuple[str, dict | None]]] = [[] for _ in chs]
    for rid in rids:
        for spec in specs[rid]:
            dn = donors.sample(spec["region"], spec["floor"], a.k, rnd)
            for h, ch in zip(heads, chs):
                h.append((spec["type"], score_spec(ch, spec, dn)))
    doc = agreement_doc(heads, [f"candidate-{i}" for i in range(len(cands))])
    for c, p in zip(doc["candidates"], cands):
        c["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    doc.update(kind="human-agreement", runs=len(rids), max_runs=a.max_runs, seed=AGREE_SEED,
               donors={"gen": a.gen, "runs": a.donor_runs, "k": a.k}, measures=doc["candidates"][0]["measures"],
               note="aggregates over the held-out fifth (D38); no single run or decision is kept")
    doc["incumbent"]["sha256"] = hashlib.sha256(inc.read_bytes()).hexdigest()
    Path(a.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"agreement: {len(rids)} exam-fifth runs, {doc['scored']} decisions, {doc['skipped_without_donor_maps']} without donor maps", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("validate", cmd_validate), ("exam", cmd_exam)):
        p = sub.add_parser(name)
        p.add_argument("--runs-root", default="D:/spireline/referee/LAB/runs")
        p.add_argument("--gen", type=int, default=9)
        p.add_argument("--k", type=int, default=4, help="donor maps averaged per decision")
        p.add_argument("--donor-runs", type=int, default=1200)
        p.set_defaults(fn=fn)
        if name == "validate":
            p.add_argument("--n-runs", type=int, default=300)
        else:
            p.add_argument("--corpus", default=str(be.DEFAULT_CORPUS))
            p.add_argument("--out", required=True)
            p.add_argument("--limit", type=int, default=0)
    ag = sub.add_parser("agreement", help="a candidate head's and the incumbent's agreement with the human choice on the held-out fifth")
    ag.add_argument("--candidate", action="append", required=True, help="a candidate's run_value.npz (repeat for several)")
    ag.add_argument("--incumbent", required=True, help="the incumbent's run_value.npz")
    ag.add_argument("--runs-root", default="D:/spireline/referee/LAB/runs")
    ag.add_argument("--gen", type=int, default=9, help="the self-play generation the donor maps come from")
    ag.add_argument("--k", type=int, default=4, help="donor maps averaged per decision")
    ag.add_argument("--donor-runs", type=int, default=1200)
    ag.add_argument("--corpus", default=str(be.DEFAULT_CORPUS))
    ag.add_argument("--exam-ids", default=None, help="the fifth's run ids (default: the hash rule)")
    ag.add_argument("--max-runs", type=int, default=1000, help="a fixed seeded subset of the fifth's runs (0: all of them)")
    ag.add_argument("--cache", default=str(SPEC_CACHE))
    ag.add_argument("--rebuild-cache", action="store_true")
    ag.add_argument("--fork", default=str(FORK), help="the fork tree whose rl/run_train scores the heads")
    ag.add_argument("--w", type=float, default=W_WON)
    ag.add_argument("--out", required=True)
    ag.set_defaults(fn=cmd_agreement)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
