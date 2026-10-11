"""Spireline's typed interfaces (design v1.1 §2.2) and the §1.4 output contract.

Invariants (design §2.2), restated because every implementation must keep them:

- Priors, values, features and search roots receive only an `InfoState`.
- The firewall is an allow-list; a payload field that is not listed is dropped and logged.
- Code owns legality and arithmetic; models return indices or probabilities.
- Every ledger row records which policy actually chose the action (`chosen_by`).
- Policies are pure functions `(state, kb, config) -> (action, scores, rationale)` with a
  logged config hash.

Decision 2026-10-10 (docs/DECISIONS.md D7): no LLM components anywhere. `Prior`
implementations are uniform, heuristic (B8 scores / deck fights) or a trained net only;
the design's haiku/jev priors, explainer and experiment E1 are out of scope.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Protocol, runtime_checkable

import numpy as np

from .infoset.schema import InfoState, det_seed

# --------------------------------------------------------------------------- enums & units

Track = Literal["D", "I"]  # D = Defect A10, Acts 1-3 (primary); I = Ironclad A10, captured cards only
ValueLevel = Literal["L0", "L1", "L2"]
Mode = Literal[
    "PLAY",
    "QUICK",
    "DEEP",
    "LABEL-bronze",
    "LABEL-A-silver",
    "LABEL-A-gold",
    "LABEL-B-silver",
    "LABEL-B-gold",
]


class Verdict(str, Enum):
    DECISIVE = "DECISIVE"
    CLOSE = "CLOSE"
    UNCERTAIN = "UNCERTAIN"
    UNSUPPORTED = "UNSUPPORTED"


L0_UNITS = "L0 points"  # 1 point = 0.01 of u_L0; never "pp of P(win)" (design §1.2)
U_LAMBDA_UNITS = "U_lambda units"
PP_WIN_UNITS = "pp P(win)"


def l1_units(act: int) -> str:
    return f"pp P(clear act {act})"


def units_ok(level: ValueLevel, units: str) -> bool:
    """The value ladder's unit rule (design §1.2): one currency per label, always printed."""
    if level == "L0":
        return units == L0_UNITS
    if level == "L1":
        return units.startswith("pp P(clear act ") and units.endswith(")")
    if level == "L2":
        return units in (U_LAMBDA_UNITS, PP_WIN_UNITS)
    return False


def l0_utility(dead: bool, hp_end: int, potions_held: int, max_hp: int) -> float:
    """u_L0 = 0 if dead, else 0.5 + 0.5 * min(1, (HP_end + 10 * potions_held) / maxHP) (design §1.2)."""
    if dead:
        return 0.0
    if max_hp <= 0:
        raise ValueError("max_hp must be positive")
    return 0.5 + 0.5 * min(1.0, (hp_end + 10 * potions_held) / max_hp)


# ε by mode and level (design §1.4 "Verdict" table). DRAFT until eval/prereg/phase1.yaml is frozen.
EPSILON: dict[str, tuple[ValueLevel, str, float]] = {
    "QUICK-combat": ("L0", "Q^tempo", 1.0),
    "DEEP-combat": ("L0", "Q^PLAY@16", 1.0),
    "LABEL-A-silver": ("L0", "Q^PLAY@60", 1.0),
    "LABEL-A-gold": ("L0", "Q^PLAY@300", 0.5),
    "QUICK-macro": ("L1", "V_run + paired deck fights", 2.0),
    "LABEL-B-gold": ("L1", "act rollouts", 2.0),
    "L2": ("L2", "P(win)", 1.0),
}


# --------------------------------------------------------------------------- actions & handles


@dataclass(frozen=True, slots=True)
class SemAction:
    """A semantic action, keyed so the same card means the same action in every world.

    Search children are keyed by this, not by a phase-local mask index (design §4.1):
    (DefId, upgraded, enchant, cost this turn, target creature id), plus the kind.
    Identical cards collapse into one action.
    """

    kind: Literal["play_card", "use_potion", "discard_potion", "end_turn", "select_card", "confirm", "skip", "macro"]
    def_id: str | None = None
    upgraded: int = 0
    enchant: str | None = None
    cost: int | None = None
    target: str | None = None  # entity_id; None for untargeted
    slot: int | None = None  # potion slot
    detail: str | None = None  # macro decisions: afterstate description


@dataclass(frozen=True, slots=True)
class Handle:
    """Opaque reference to an engine-owned state (emulator, referee or live)."""

    backend: Literal["emulator", "referee", "live"]
    ref: int


@dataclass(frozen=True, slots=True)
class AiParticle:
    """One sample of monster AI state and current moves, drawn from the belief, never the payload.

    `per_monster` maps entity_id -> (current move id, AI fields). `assumed` marks a
    deterministic history-only reconstruction after no particle survived (ai_state_assumed,
    design §3.2); such positions are excluded from gold labels.
    """

    per_monster: tuple[tuple[str, str, tuple[tuple[str, object], ...]], ...]
    assumed: bool = False


@dataclass(frozen=True, slots=True)
class StepResult:
    handle: Handle
    terminal: bool
    revealed_information: bool  # True when the step crossed an information boundary
    utility: float | None = None  # u_L at a terminal, in the level's own units
    fidelity_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PriorOut:
    logits: np.ndarray  # one per legal action, same order
    source: str
    latency_s: float = 0.0


@dataclass(frozen=True, slots=True)
class Budget:
    """Search budget. Fixed simulation counts for anything that must be deterministic (§7.4)."""

    mode: Mode
    sims: int | None = None
    worlds_per_survivor: int | None = None
    target_half_width: float | None = None  # in the label's units
    max_core_s: float | None = None
    deterministic: bool = True

    def __post_init__(self) -> None:
        if self.deterministic and self.max_core_s is not None and self.sims is None and self.worlds_per_survivor is None:
            raise ValueError("a deterministic budget needs a fixed sims or worlds count, not only a time limit")


# --------------------------------------------------------------------------- the §1.4 contract


@dataclass(frozen=True, slots=True)
class OptionRow:
    a: str
    q: float | None
    cs95: tuple[float, float] | None
    n_worlds: int
    pruned_at: str | None = None


@dataclass(frozen=True, slots=True)
class Stability:
    pi_ref_60_vs_300: str | None = None  # "same_argmax" | "different_argmax" | None (not run)
    second_family_B8: str | None = None


@dataclass(frozen=True)
class Decision:
    """Every decision, live or offline, in the design §1.4 output contract."""

    decision_id: str
    game_build: int
    engine_sha: str
    oracle_cfg: str
    info_state_hash: str
    track: Track
    mode: Mode
    value_level: ValueLevel
    value_units: str
    options: tuple[OptionRow, ...]
    best: str | None
    p_best: float | None
    gap: float | None
    gap_cs95: tuple[float, float] | None
    ci_method: str
    epsilon: float
    verdict: Verdict
    regret_ucb95_if_follow: float | None
    regret_bound_scope: Literal["survivors_only"] = "survivors_only"
    screen_recall_dev: float | None = None
    pi_ref: str = ""
    horizon: str = ""
    stability: Stability = field(default_factory=Stability)
    continuation_sensitive: bool = False
    currency_sensitive: bool = False
    vpi_clairvoyant: float | None = None  # diagnostic only, never a label
    ai_state: str = ""  # e.g. "particles(k=64)" or "ai_state_assumed"
    fidelity_flags: tuple[str, ...] = ()
    prior: tuple[tuple[str, str], ...] = (("source", "none"),)
    wall_s: float = 0.0
    usd: float = 0.0  # cloud-burst compute attributable to this decision; 0.0 locally
    chosen_by: str | None = None  # ledger: which policy actually chose (design §2.2)

    def __post_init__(self) -> None:
        if not units_ok(self.value_level, self.value_units):
            raise ValueError(f"units {self.value_units!r} are not valid for level {self.value_level}")
        if self.verdict is Verdict.UNSUPPORTED and not self.fidelity_flags:
            raise ValueError("UNSUPPORTED needs at least one fidelity flag saying why")
        if self.mode == "LABEL-A-gold" and self.ai_state == "ai_state_assumed":
            raise ValueError("gold labels require ai_state != ai_state_assumed (design §1.4)")
        for o in self.options:
            if (o.q is None) != (o.n_worlds == 0):
                raise ValueError(f"option {o.a!r}: q is set iff n_worlds > 0")

    def to_contract(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "game_build": self.game_build,
            "engine_sha": self.engine_sha,
            "oracle_cfg": self.oracle_cfg,
            "info_state_hash": self.info_state_hash,
            "track": self.track,
            "mode": self.mode,
            "value_level": self.value_level,
            "value_units": self.value_units,
            "options": [
                {"a": o.a, "q": o.q, "cs95": list(o.cs95) if o.cs95 else None, "n_worlds": o.n_worlds}
                | ({"pruned_at": o.pruned_at} if o.pruned_at else {})
                for o in self.options
            ],
            "best": self.best,
            "p_best": self.p_best,
            "gap": self.gap,
            "gap_cs95": list(self.gap_cs95) if self.gap_cs95 else None,
            "ci_method": self.ci_method,
            "epsilon": self.epsilon,
            "verdict": self.verdict.value,
            "regret_ucb95_if_follow": self.regret_ucb95_if_follow,
            "regret_bound_scope": self.regret_bound_scope,
            "screen_recall_dev": self.screen_recall_dev,
            "pi_ref": self.pi_ref,
            "horizon": self.horizon,
            "stability": {"pi_ref_60_vs_300": self.stability.pi_ref_60_vs_300,
                          "second_family_B8": self.stability.second_family_B8},
            "continuation_sensitive": self.continuation_sensitive,
            "currency_sensitive": self.currency_sensitive,
            "vpi_clairvoyant": self.vpi_clairvoyant,
            "ai_state": self.ai_state,
            "fidelity_flags": list(self.fidelity_flags),
            "prior": dict(self.prior),
            "wall_s": self.wall_s,
            "usd": self.usd,
            "chosen_by": self.chosen_by,
        }


def classify_verdict(
    gap: float,
    gap_cs: tuple[float, float],
    epsilon: float,
    *,
    budget_exhausted: bool,
    unsupported: bool = False,
) -> Verdict | None:
    """Design §1.4 verdict rules on the paired top-2 gap (best minus runner-up).

    UNSUPPORTED overrides everything. DECISIVE: LCB > 0 and point gap >= ε. CLOSE: the CS
    lies inside [-ε, +ε]. Otherwise UNCERTAIN once the budget is spent, else None (keep racing).
    """
    if epsilon <= 0 or not math.isfinite(epsilon):
        raise ValueError("epsilon must be positive and finite")
    lo, hi = gap_cs
    if lo > hi:
        raise ValueError("gap_cs must be (lower, upper)")
    if unsupported:
        return Verdict.UNSUPPORTED
    if lo > 0 and gap >= epsilon:
        return Verdict.DECISIVE
    if -epsilon <= lo and hi <= epsilon:
        return Verdict.CLOSE
    return Verdict.UNCERTAIN if budget_exhausted else None


def regret_ucb(lcb_best: float, ucb_others: list[float]) -> float:
    """regret_ucb95 = max(0, max_{b≠â} UCB(b) − LCB(â)); callers pass Bonferroni-corrected bounds."""
    if not ucb_others:
        return 0.0
    return max(0.0, max(ucb_others) - lcb_best)


# --------------------------------------------------------------------------- protocols


@runtime_checkable
class Engine(Protocol):
    """Emulator; the referee and the live game implement subsets."""

    def from_info_state(self, I: InfoState, hidden_seed: int, ai: AiParticle) -> Handle: ...
    def clone(self, h: Handle, resample_hidden: bool, det_seed: int) -> Handle: ...
    def legal(self, h: Handle) -> list[SemAction]: ...
    def step(self, h: Handle, a: SemAction) -> StepResult: ...
    def info_state(self, h: Handle) -> InfoState: ...  # firewall-filtered, hashable
    def afterstate(self, h: Handle, a: SemAction) -> InfoState | None: ...


@runtime_checkable
class AiBelief(Protocol):
    """infoset/ai_belief.py: likelihood-weighted particles over AI state and current moves."""

    def sample(self, I: InfoState, k: int, seed: int) -> list[tuple[AiParticle, float]]: ...


@runtime_checkable
class Prior(Protocol):
    """uniform | heuristic | net. Swappable and logged. No LLM priors (D7)."""

    name: str
    version: str

    def __call__(self, I: InfoState, legal: list[SemAction]) -> PriorOut: ...


@runtime_checkable
class RunValue(Protocol):
    level: ValueLevel
    units: str

    def value(self, X: InfoState) -> float: ...  # in the level's own units
    def dist(self, X: InfoState) -> np.ndarray | None: ...  # 18- or 53-class floor/won


@runtime_checkable
class Searcher(Protocol):
    def decide(self, I: InfoState, budget: Budget, prior: Prior, value: RunValue) -> Decision: ...


__all__ = [
    "Track",
    "ValueLevel",
    "Mode",
    "Verdict",
    "L0_UNITS",
    "U_LAMBDA_UNITS",
    "PP_WIN_UNITS",
    "l1_units",
    "units_ok",
    "l0_utility",
    "EPSILON",
    "SemAction",
    "Handle",
    "AiParticle",
    "StepResult",
    "PriorOut",
    "Budget",
    "OptionRow",
    "Stability",
    "Decision",
    "classify_verdict",
    "regret_ucb",
    "Engine",
    "AiBelief",
    "Prior",
    "RunValue",
    "Searcher",
    "InfoState",
    "det_seed",
]
