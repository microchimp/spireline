#!/usr/bin/env python3
"""List what changed upstream since we last looked, so useful fixes can be read and picked.

Spireline's simulator is its own fork of r33hab/sts2 (docs/DECISIONS.md D16). Upstream and
related projects keep changing; this reports new branches and commits per repo against the
heads recorded in `scripts/upstream_watch.json`. It reads the public GitHub API only, writes
nothing but that file (with --update), and never fetches or runs code. A change found here is
taken only after its diff is read (security review §7.1).

    python scripts/upstream_watch.py            # report
    python scripts/upstream_watch.py --update   # report, then record the heads seen

Unauthenticated calls are limited to 60 an hour; set GITHUB_TOKEN to raise that.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

STATE = Path(__file__).with_name("upstream_watch.json")
REPOS = {
    "r33hab/sts2": "the emulator this fork starts from (b745217)",
    "r33hab/STS2MCP": "the live-game mod fork Spireline pins (5a63f92)",
    "evangambit/sts2": "the emulator's previous home",
    "Zamiell/slay-the-spire-2-emulator": "the original emulator",
    "Gennadiyev/STS2MCP": "the original mod",
    "favet/divine-sts2": "runs the game's own code headless (referee approach)",
    "wuhao21/sts2-cli": "patched game code on stub Godot (referee approach)",
    "zhiyue/sts2-rl-agent": "Python simulator checked against the decompiled source",
}


def api(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json",
                                                                      "User-Agent": "spireline-upstream-watch"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def branches(repo: str) -> dict[str, str]:
    out, page = {}, 1
    while True:
        rows = api(f"/repos/{repo}/branches?per_page=100&page={page}")
        out.update({r["name"]: r["commit"]["sha"] for r in rows})
        if len(rows) < 100:
            return out
        page += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--update", action="store_true", help="record the heads seen")
    ap.add_argument("--max-commits", type=int, default=15, help="commit subjects shown per branch")
    args = ap.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    new_state, changed = {}, 0
    for repo, why in REPOS.items():
        try:
            heads = branches(repo)
        except urllib.error.HTTPError as exc:
            print(f"{repo}: HTTP {exc.code} ({why})")
            new_state[repo] = state.get(repo, {})
            continue
        except urllib.error.URLError as exc:
            print(f"{repo}: unreachable: {exc.reason}")
            new_state[repo] = state.get(repo, {})
            continue
        new_state[repo] = heads
        old = state.get(repo)
        if old is None:
            print(f"{repo}: first look, {len(heads)} branches recorded ({why})")
            continue
        for name, sha in sorted(heads.items()):
            if old.get(name) == sha:
                continue
            changed += 1
            if name not in old:
                print(f"{repo} [{name}]: NEW branch at {sha[:9]}")
                continue
            try:
                cmp = api(f"/repos/{repo}/compare/{old[name]}...{sha}")
            except urllib.error.HTTPError as exc:
                print(f"{repo} [{name}]: moved {old[name][:9]} -> {sha[:9]} (compare failed: HTTP {exc.code})")
                continue
            print(f"{repo} [{name}]: {old[name][:9]} -> {sha[:9]}, {cmp.get('ahead_by')} ahead, "
                  f"{cmp.get('behind_by')} behind, {len(cmp.get('files', []))} files")
            for c in cmp.get("commits", [])[-args.max_commits:]:
                print(f"    {c['sha'][:9]} {c['commit']['message'].splitlines()[0][:100]}")
        for name in sorted(set(old) - set(heads)):
            changed += 1
            print(f"{repo} [{name}]: branch DELETED (was {old[name][:9]})")
    if not changed and state:
        print("no changes since the last --update")
    if args.update:
        STATE.write_text(json.dumps(new_state, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"recorded heads in {STATE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
