#!/usr/bin/env python3
"""Where a rollout step's time goes: the ctypes call, Python bookkeeping, or the engine itself.

Replays combat_mcts.rollout (combat_mcts.py:472-500) on determinized forks of one opening and
times each part of every step separately. Read-only; imports the emulator from STS2_EMU like
sts2bench.py. One core, run it on an idle machine:

    STS2_EMU=<emu> <emu>/.venv/Scripts/python.exe step_probe.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=406)
    ap.add_argument("--encounter", type=int, default=29)
    ap.add_argument("--calls", type=int, default=200_000, help="empty ctypes calls to time")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    base = Path(os.environ["STS2_EMU"]).resolve()
    for sub in ("src", "rl"):
        sys.path.insert(0, str(base / sub))
    import numpy as np  # noqa: PLC0415
    import combat_mcts as cm  # noqa: PLC0415
    from sts2_gym import native  # noqa: PLC0415

    lib = native._lib  # noqa: SLF001
    pc = time.perf_counter

    # 1. Bare ctypes cost: a no-argument native call that returns a constant.
    f = lib.Sts2_ObsSize
    t0 = pc()
    for _ in range(a.calls):
        f()
    empty_call_us = 1e6 * (pc() - t0) / a.calls

    # Python loop + perf_counter overhead, subtracted from nothing; reported for scale.
    t0 = pc()
    for _ in range(a.calls):
        pass
    loop_us = 1e6 * (pc() - t0) / a.calls

    extra = cm.sample_extra_cards(a.seed, 2, 8, "Ironclad")
    relics = cm.sample_relics(a.seed, 0, 5, "Ironclad")
    root = cm.Combat.opening(a.seed, a.encounter, 8, 0, extra, relics)
    rng = np.random.default_rng(1)

    parts = {k: 0.0 for k in ("clone", "valid_actions_call", "legal_list", "weights", "choice_weighted",
                              "choice_uniform", "step_wrapper", "step_raw", "destroy")}
    steps = 0
    raw_step = lib.Sts2_Step
    try:
        for k in range(a.rollouts):
            t = pc()
            sim = root.fork(1_000_000 + k)
            parts["clone"] += pc() - t
            for _ in range(cm.STEP_CAP):
                if sim.done:
                    break
                t = pc()
                mask = native.valid_actions(sim.handle, cm.MAX_ACTIONS)
                t1 = pc()
                legal = [i for i in range(cm.MAX_ACTIONS) if mask[i]]
                t2 = pc()
                parts["valid_actions_call"] += t1 - t
                parts["legal_list"] += t2 - t1
                if not legal:
                    break
                if len(legal) > 1:
                    t = pc()
                    w = cm.rollout_weights(sim, legal)
                    t1 = pc()
                    action = int(rng.choice(legal, p=w))
                    t2 = pc()
                    int(rng.choice(legal))  # timed for comparison only; result unused
                    t3 = pc()
                    parts["weights"] += t1 - t
                    parts["choice_weighted"] += t2 - t1
                    parts["choice_uniform"] += t3 - t2
                else:
                    action = legal[0]
                # Alternate the wrapper and the raw call so both see the same mix of states.
                if steps % 2 == 0:
                    t = pc()
                    sim.step(action)
                    parts["step_wrapper"] += pc() - t
                else:
                    t = pc()
                    sim.done = bool(raw_step(sim.handle, action, sim.obs, sim.reward))
                    parts["step_raw"] += pc() - t
                steps += 1
            t = pc()
            sim.close()
            parts["destroy"] += pc() - t
    finally:
        root.close()

    half = steps / 2
    per_step = {
        "valid_actions_call_us": 1e6 * parts["valid_actions_call"] / steps,
        "legal_list_us": 1e6 * parts["legal_list"] / steps,
        "weights_us": 1e6 * parts["weights"] / steps,
        "choice_weighted_us": 1e6 * parts["choice_weighted"] / steps,
        "choice_uniform_us": 1e6 * parts["choice_uniform"] / steps,
        "step_wrapper_us": 1e6 * parts["step_wrapper"] / half,
        "step_raw_us": 1e6 * parts["step_raw"] / half,
    }
    tempo_step = (per_step["valid_actions_call_us"] + per_step["legal_list_us"] + per_step["weights_us"]
                  + per_step["choice_weighted_us"] + per_step["step_wrapper_us"])
    out = {
        "kind": "step_probe",
        "machine": {"platform": platform.platform(), "processor": platform.processor(),
                    "python": sys.version.split()[0]},
        "settings": vars(a) | {"json": None},
        "empty_ctypes_call_us": empty_call_us,
        "empty_python_loop_us": loop_us,
        "rollouts": a.rollouts,
        "steps": steps,
        "steps_per_rollout": steps / a.rollouts,
        "clone_us": 1e6 * parts["clone"] / a.rollouts,
        "destroy_us": 1e6 * parts["destroy"] / a.rollouts,
        "per_step": per_step,
        "tempo_rollout_step_us_sum": tempo_step,
        "engine_share_of_tempo_step": per_step["step_raw_us"] / tempo_step if tempo_step else None,
    }
    for k, v in out.items():
        if k not in ("machine", "settings"):
            print(f"{k}: {json.dumps(v, default=str) if isinstance(v, dict) else v}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
