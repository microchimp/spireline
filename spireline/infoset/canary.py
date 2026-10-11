"""Canary tokens for leak test L6 (design §7.6).

`plant_canaries` copies a raw STS2MCP payload and writes a unique token into every hidden
or conditionally hidden field it contains:

- every `seed`, wherever it occurs (McpMod.StateBuilder.cs:535-539);
- `player.draw_pile_ordered[].id/.uid` and the uids of the other `*_ordered` lists
  (McpMod.StateBuilder.cs:1760-1769, 2258-2275);
- per enemy and ally: `move_id`, `move_follow_up_id`, the last `state_log` entry (the
  pending move), every `ai_fields` value, `combat_id`, `revive.in_turns`
  (McpMod.StateExtras.cs:212-240; McpMod.StateBuilder.cs:2507-2571, 2669-2686);
- powers hidden from the HUD (`hidden_in_ui`, McpMod.StateBuilder.cs:4265-4266): id and amount;
- relic raw `saved` / `fields` values (McpMod.StateExtras.cs:375-441);
- `vs_targets[].values` and `vs_targets[].combat_id` (McpMod.StateBuilder.cs:2042-2078);
- pile card uids and `run.start_time`.

`audit` then searches everything a FirewallResult exposes (InfoState JSON, drop log, flags,
meta, repr) plus any extra text (captured log lines) for each token. A token found there is
a leak unless its path was deliberately admitted by the policy.

`plant_control_canary` writes a token into an admitted field (an intent label) so a test
can prove the audit detects a token that does pass: the positive control for this suite.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

CANARY_PREFIX = "SPLCANARY"


@dataclass(frozen=True, slots=True)
class Canary:
    token: str
    path: str  # concrete path, list indices included, e.g. "battle.enemies[0].move_id"


@dataclass(frozen=True, slots=True)
class Leak:
    canary: Canary
    where: str


def _token(salt: str, path: str) -> str:
    h = hashlib.blake2b(f"{salt}|{path}".encode(), digest_size=6).hexdigest()
    return f"{CANARY_PREFIX}-{h}"


class _Planter:
    def __init__(self, salt: str) -> None:
        self.salt = salt
        self.canaries: list[Canary] = []

    def put(self, obj: dict | list, key: Any, path: str) -> None:
        tok = _token(self.salt, path)
        obj[key] = tok
        self.canaries.append(Canary(tok, path))

    def seeds(self, obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for k in list(obj):
                p = f"{path}.{k}" if path else k
                if k == "seed" and obj[k] is not None:
                    self.put(obj, k, p)
                else:
                    self.seeds(obj[k], p)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self.seeds(v, f"{path}[{i}]")

    def powers(self, lst: Any, path: str) -> None:
        if not isinstance(lst, list):
            return
        for i, pw in enumerate(lst):
            if isinstance(pw, dict) and pw.get("hidden_in_ui") is True:
                for k in ("id", "amount"):
                    if k in pw:
                        self.put(pw, k, f"{path}[{i}].{k}")

    def creature(self, c: Any, path: str) -> None:
        if not isinstance(c, dict):
            return
        for k in ("move_id", "move_follow_up_id", "combat_id"):
            if k in c and c[k] is not None:
                self.put(c, k, f"{path}.{k}")
        log = c.get("state_log")
        if isinstance(log, list) and log:
            self.put(log, len(log) - 1, f"{path}.state_log[{len(log) - 1}]")
        ai = c.get("ai_fields")
        if isinstance(ai, dict):
            for k in list(ai):
                self.put(ai, k, f"{path}.ai_fields.{k}")
        rv = c.get("revive")
        if isinstance(rv, dict) and "in_turns" in rv:
            self.put(rv, "in_turns", f"{path}.revive.in_turns")
        self.powers(c.get("status"), f"{path}.status")

    def player(self, p: Any) -> None:
        if not isinstance(p, dict):
            return
        for lst_key in ("draw_pile_ordered", "hand_ordered", "discard_pile_ordered", "exhaust_pile_ordered"):
            lst = p.get(lst_key)
            if isinstance(lst, list):
                for i, e in enumerate(lst):
                    if not isinstance(e, dict):
                        continue
                    keys = ("id", "uid") if lst_key == "draw_pile_ordered" else ("uid",)
                    for k in keys:
                        if k in e:
                            self.put(e, k, f"player.{lst_key}[{i}].{k}")
        for pile in ("draw_pile", "discard_pile", "exhaust_pile", "play_pile"):
            lst = p.get(pile)
            if isinstance(lst, list):
                for i, e in enumerate(lst):
                    if isinstance(e, dict) and "uid" in e:
                        self.put(e, "uid", f"player.{pile}[{i}].uid")
        for i, card in enumerate(p.get("hand") or []):
            if not isinstance(card, dict):
                continue
            for j, vt in enumerate(card.get("vs_targets") or []):
                if not isinstance(vt, dict):
                    continue
                if "combat_id" in vt:
                    self.put(vt, "combat_id", f"player.hand[{i}].vs_targets[{j}].combat_id")
                vals = vt.get("values")
                if isinstance(vals, dict):
                    for k in list(vals):
                        self.put(vals, k, f"player.hand[{i}].vs_targets[{j}].values.{k}")
        for i, rel in enumerate(p.get("relics") or []):
            if not isinstance(rel, dict):
                continue
            for blk in ("saved", "fields"):
                d = rel.get(blk)
                if isinstance(d, dict):
                    for k in list(d):
                        self.put(d, k, f"player.relics[{i}].{blk}.{k}")
        self.powers(p.get("status"), "player.status")


def plant_canaries(payload: dict[str, Any], salt: str = "spireline") -> tuple[dict[str, Any], list[Canary]]:
    """Deep-copy `payload` and plant one unique token per hidden field. Returns (copy, canaries)."""
    planted = copy.deepcopy(payload)
    pl = _Planter(salt)
    pl.seeds(planted, "")
    run = planted.get("run")
    if isinstance(run, dict) and "start_time" in run:
        pl.put(run, "start_time", "run.start_time")
    pl.player(planted.get("player"))
    battle = planted.get("battle")
    if isinstance(battle, dict):
        for side in ("enemies", "allies"):
            for i, c in enumerate(battle.get(side) or []):
                pl.creature(c, f"battle.{side}[{i}]")
    return planted, pl.canaries


def plant_control_canary(payload: dict[str, Any], salt: str = "control") -> tuple[dict[str, Any], Canary]:
    """Plant one token in an admitted, displayed field (the first enemy's first intent label)."""
    planted = copy.deepcopy(payload)
    intent = planted["battle"]["enemies"][0]["intents"][0]
    path = "battle.enemies[0].intents[0].label"
    tok = _token(salt, path)
    intent["label"] = tok
    return planted, Canary(tok, path)


def audit(
    result: Any,
    canaries: Iterable[Canary],
    *,
    extra_texts: Iterable[str] = (),
    admitted_paths: Iterable[str] = (),
) -> list[Leak]:
    """Return every canary found in what `result` exposes (or in `extra_texts`), minus admitted ones."""
    haystacks = [("firewall_result", result.audit_text())]
    haystacks += [(f"extra[{i}]", t) for i, t in enumerate(extra_texts)]
    ok = set(admitted_paths)
    leaks = []
    for c in canaries:
        if c.path in ok:
            continue
        for where, text in haystacks:
            if c.token in text:
                leaks.append(Leak(c, where))
    return leaks


def assert_no_leaks(result: Any, canaries: Iterable[Canary], **kw: Any) -> None:
    leaks = audit(result, canaries, **kw)
    if leaks:
        lines = "\n".join(f"  {lk.canary.path} -> {lk.where}" for lk in leaks)
        raise AssertionError(f"{len(leaks)} canary leak(s):\n{lines}")


__all__ = ["CANARY_PREFIX", "Canary", "Leak", "plant_canaries", "plant_control_canary", "audit", "assert_no_leaks"]
