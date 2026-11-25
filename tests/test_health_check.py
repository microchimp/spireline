"""tools/health_check.py on a made-up lab root: small synthetic files for every reader, one case for every colour rule, the scrub, the git step
with a fake `git`, and `--start-daemon` with a fake Popen. Nothing real is read, no process is started (an autouse fixture makes a real
`subprocess.run` an error), no network, no real repo.

The baseline root built by `make_root` is GREEN: a runner that reported two minutes ago, a practice loop (two processes, the venv pair), a judge job
running under a fresh `lab-train` line, a weekly real-game test that began 4.6 days ago, a clean runner.log (its one failure is three days old),
no alerts, plenty of disk. Each colour test changes one thing in it.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import health_check as hc  # noqa: E402

UTC = timezone.utc
NOW = datetime(2026, 11, 25, 10, 0, 0, tzinfo=UTC)
DAEMON_CMD = "D:\\spireline\\src\\sts2\\.venv\\Scripts\\python.exe " + " ".join(hc.DAEMON_ARGS).replace("/", "\\", 1)
RUNNER_CMD = '"D:\\spireline\\src\\sts2\\.venv\\Scripts\\pythonw.exe" tools\\lab\\runner.py --lab "D:\\spireline\\referee\\lab" --always-on'


def Z(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(autouse=True)
def no_real_processes(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("a test started a real process")
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)


# ---------------------------------------------------------------------------------------------------------- the made-up root
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def end_row(seed: str, floor: int, stand_in: int | None) -> dict:
    row = {"ev": "end", "seed": seed, "end": "death", "floor": floor}
    if stand_in is not None:
        row["stats"] = {"boss_fights": [{"act": 3, "floor": 48, "stand_in": stand_in}]}
    return row


def door_rows(passes: int, dies: int, lost: int, none: int = 2) -> list[dict]:
    """`passes` arrivals the player played and beat, `dies` it played and lost, `lost` where a stand-in played on, `none` that never arrived."""
    rows = [end_row(f"p{i}", 55, 0) for i in range(passes)] + [end_row(f"d{i}", 48, 0) for i in range(dies)]
    rows += [end_row(f"l{i}", 52, 2) for i in range(lost)] + [end_row(f"n{i}", 20, None) for i in range(none)]
    return rows


def write_block(root: Path, name: str, gen: int, rows: list[dict], finished: bool = True) -> None:
    g = root / "referee" / "lab" / "nightly" / name / f"g{gen}"
    write(g / "runs.jsonl", "".join(json.dumps(r) + "\n" for r in rows))
    (root / "referee" / "lab" / "nightly" / name / f"g{gen}-emu").mkdir(parents=True, exist_ok=True)
    if finished:
        write(g / "summary.json", "{}")


def make_root(tmp_path: Path, rows: list[dict] | None = None) -> hc.Env:
    root = tmp_path / "lab-root"
    lab = root / "referee" / "lab"
    write(lab / "status.txt", f"{Z(NOW - timedelta(seconds=120))} running job=20261125T0836-train step=train strategy=train "
          "since=2026-11-25T08:36:38Z tree=9432e74 jobs_done=1442 | train: 1 running\nsecond line\n")
    write(lab / "runner.log", "\n".join([
        "2026-11-22T06:03:13Z native/publish-native: rc=1 in 4.0s cpu=2.4s out=? (FAILED)",
        "2026-11-22T06:03:14Z job 20261122T0601-presort finished rc=1",
        "2026-11-25T07:04:13Z job 20261125T0704-presort: main moved to 9432e74",
        "2026-11-25T07:05:38Z corpus/corpus: skipped (inputs unchanged)",
        "2026-11-25T07:05:39Z job 20261125T0704-presort finished rc=0",
        "2026-11-25T08:36:38Z job 20261125T0836-train: ladder: train (priority 3)",
        "2026-11-25T08:36:39Z filler: 20261125T0836-selfplay stopped (a job needs its cores); the block was still running after 25 s, killed",
    ]) + "\n")
    (lab / "alerts").mkdir(parents=True, exist_ok=True)
    write_block(root, "2026-11-20T1904", 20, rows if rows is not None else door_rows(3, 3, 2))
    write(lab / "nightly" / "last-ok", "2026-11-21T01:40:25Z\r\n")
    write(root / "referee" / "QUIET.lock", f"lab-train {Z(NOW - timedelta(minutes=3))} pid=25404\n")
    write(root / "referee" / "gym-loop" / "loop.log", "\n".join([
        "2026-11-24T21:49:58Z promoted c0475 as v7 over v6 by rule v5 (route A3, stage 3): part h -0.44 points, part a3 +1.85; era 3 begins",
        "2026-11-25T00:00:26Z daily 2026-11-24: 31 segments, 13428 fights played; played 19.7 h (generate 14.0 h), waited 4.3 h (quiet:lab-train 2.1 h, yield 1.7 h), between steps or down 0.0 h; 8 gated",
        "2026-11-25T06:59:12Z run judge: v7 (gate c0475) carried by gen22/candidate-fight-v7: not promoted under keep rule v3 on 3400 pairs",
        "2026-11-25T08:33:47Z promoted c0476 as v8 over v7 by rule v5 (route F, stage 2): part h +0.90 points",
        f"{Z(NOW - timedelta(minutes=30))} wait start: quiet:lab-train",
    ]) + "\n")
    agent = root / "referee" / "agent"
    (agent / "gen21").mkdir(parents=True, exist_ok=True)
    (agent / "gen22").mkdir(parents=True, exist_ok=True)
    write(agent / "current.json", json.dumps({"generation": 21, "dir": "C:\\Users\\someone\\x\\gen21\\candidate-fight-v5", "promoted": "2026-11-22T09:44:43Z"}))
    head = "written\tcand_gen\tbase_gen\tseed_block\tseeds\tdecision\tcand_dir"
    write(agent / "promotions.tsv", "\n".join([head,
          "2026-11-22T09:44:43Z\t21\t20\tE21\t2000\tpromoted\tcandidate-fight-v5",
          "2026-11-25T06:59:07Z\t22\t21\tE22\t3400\trejected\tcandidate-fight-v7"]) + "\n")
    return hc.Env(root, tmp_path / "repo")


def procs_json(daemon: bool = True, runner: bool = True, extra_pids=(25404,)) -> dict:
    py = []
    if runner:
        py += [{"pid": 30664, "ppid": 2112, "name": "pythonw.exe", "cmd": RUNNER_CMD, "started": "2026-11-20T10:11:13Z"},
               {"pid": 25404, "ppid": 30664, "name": "pythonw.exe", "cmd": RUNNER_CMD.replace("D:\\spireline\\src\\sts2\\.venv\\Scripts\\", "C:\\x\\uv\\"), "started": "2026-11-20T10:11:13Z"}]
    if daemon:
        py += [{"pid": 30236, "ppid": 30500, "name": "python.exe", "cmd": DAEMON_CMD, "started": "2026-11-21T13:53:55Z"},
               {"pid": 10516, "ppid": 30236, "name": "python.exe", "cmd": "C:\\x\\uv\\python.exe " + " ".join(hc.DAEMON_ARGS), "started": "2026-11-21T13:53:55Z"}]
    py += [{"pid": 25024, "ppid": 10516, "name": "python.exe", "cmd": "D:\\x\\python.exe D:\\spireline\\fork\\wt-gym-loop-run\\rl\\gym_loop_train.py --root D:\\spireline\\referee\\gym-loop", "started": None}]
    return {"ok": True, "procs": py, "pids": {p["pid"] for p in py} | set(extra_pids), "why": ""}


def disk(free_gb: float = 1700):
    return lambda p: types.SimpleNamespace(total=int(2000 * 2**30), used=int((2000 - free_gb) * 2**30), free=int(free_gb * 2**30))


def run(env: hc.Env, now: datetime = NOW, procs=None, **kw) -> dict:
    procs = procs if procs is not None else procs_json()
    kw.setdefault("procs_fn", lambda: procs)
    kw.setdefault("schtasks_fn", lambda a: (0, "SUCCESS"))
    kw.setdefault("no_git", True)
    log = kw.pop("log", None) or hc.Log(env, now, echo=False)
    return hc.run_check(env, now=now, disk_fn=kw.pop("disk_fn", disk()), sleep=lambda s: None, log=log, **kw)


# --------------------------------------------------------------------------------------------------------------- the readers
def test_parse_processes_reads_our_object_and_a_bare_list_and_the_date_form():
    obj = {"pids": [1, 2, 3], "py": {"ProcessId": 3, "ParentProcessId": 1, "Name": "python.exe", "CommandLine": "x rl/gym_loop.py run",
                                     "Started": "2026-11-21T13:53:55Z"}}
    r = hc.parse_processes("\ufeff" + json.dumps(obj))
    assert r["ok"] and r["pids"] == {1, 2, 3} and r["procs"][0]["pid"] == 3 and r["procs"][0]["started"] == "2026-11-21T13:53:55Z"
    bare = [{"ProcessId": 7, "Name": "pythonw.exe", "CommandLine": "a", "CreationDate": "/Date(1795269235498)/"}]
    r = hc.parse_processes(json.dumps(bare))
    assert r["ok"] and r["pids"] == {7} and r["procs"][0]["started"] == "2026-11-21T13:53:55Z"
    assert hc.parse_processes("not json")["ok"] is False
    assert hc.parse_processes("")["ok"] is False


def test_list_processes_runs_powershell_readonly_and_parses_its_json(monkeypatch):
    seen = []

    def fake_run(cmd, **kw):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, json.dumps({"pids": [5], "py": []}), "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    r = hc.list_processes()
    assert r["ok"] and r["pids"] == {5}
    assert seen[0][:4] == ["powershell", "-NoProfile", "-NonInteractive", "-Command"]
    assert "Get-CimInstance Win32_Process" in seen[0][4] and "ConvertTo-Json" in seen[0][4]
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "boom"))
    assert hc.list_processes()["ok"] is False


def test_the_daemon_and_runner_are_found_by_their_command_lines_and_a_venv_pair_counts_as_alive(tmp_path):
    p = procs_json()
    d = hc.find_procs(p["procs"], hc.DAEMON_NEEDLE)
    assert sorted(x["pid"] for x in d) == [10516, 30236]  # the trainer child (gym_loop_train.py) is not the daemon
    assert sorted(x["pid"] for x in hc.find_procs(p["procs"], hc.RUNNER_NEEDLE)) == [25404, 30664]
    assert hc.find_procs(procs_json(daemon=False)["procs"], hc.DAEMON_NEEDLE) == []
    info = hc.daemon_info(make_root(tmp_path), p)
    assert info["alive"] and info["started"] == "2026-11-21T13:53:55Z" and info["pids"] == [10516, 30236]


def test_status_first_line_gives_age_mode_and_job_kind(tmp_path):
    env = make_root(tmp_path)
    s = hc.read_status(env, NOW)
    assert s["ok"] and s["age_s"] == 120 and s["mode"] == "running" and s["job_kind"] == "train" and s["tree"] == "9432e74"
    write(env.lab / "status.txt", "garbage\n")
    assert hc.read_status(env, NOW)["ok"] is False
    (env.lab / "status.txt").unlink()
    assert hc.read_status(env, NOW)["ok"] is False


def test_runner_log_counts_only_the_last_24_hours_and_the_failure_vocabulary(tmp_path):
    env = make_root(tmp_path)
    st = hc.read_status(env, NOW)
    rl = hc.read_runner_log(env, NOW, st)
    assert rl["ok"] and rl["failed_any"] is False and rl["tree"] == "9432e74" and rl["jobs_finished_24h"] == 1  # the 3-day-old failure is out
    with open(env.lab / "runner.log", "a", encoding="utf-8") as fh:
        fh.write("2026-11-25T08:00:00Z job 20261125T0700-score-real finished rc=1\n"
                 "2026-11-25T08:01:00Z score-real/score-real: rc=1 in 14401.2s cpu=9.0s out=? (FAILED)\n"
                 "2026-11-25T08:02:00Z score-real: not runnable (backing off after repeated failures until 2026-11-26T00:24:50Z)\n"
                 "2026-11-25T08:03:00Z score-real: not runnable (backing off after repeated failures until 2026-11-26T00:24:50Z)\n"
                 "2026-11-25T08:04:00Z ALERT timeout: train/train of 20261125T0700-train was killed at its 14400s limit (LAB/alerts/timeouts.txt)\n")
    rl = hc.read_runner_log(env, NOW, st)
    assert [j["rc"] for j in rl["failed_jobs"]] == [1] and rl["failed_steps"][0]["step"] == "score-real/score-real"
    assert rl["backoff_kinds"] == ["score-real"] and len(rl["limit_kills"]) == 1 and rl["failed_any"] is True


def test_quiet_lines_stuck_judge_and_stale_pid(tmp_path):
    env = make_root(tmp_path)
    st = hc.read_status(env, NOW)
    q = hc.read_quiet(env, NOW, {25404, 1}, st)
    assert q[0]["tag"] == "lab-train" and q[0]["pid_alive"] is True and not q[0]["stale"] and not q[0]["stuck"]
    write(env.quiet, f"lab-train {Z(NOW - timedelta(hours=30))} pid=25404\nw3-blocks {Z(NOW - timedelta(minutes=5))} pid=999\ngym-loop {Z(NOW)}\n")
    q = hc.read_quiet(env, NOW, {25404}, st)
    assert q[0]["stuck"] is False  # a train job is running in status.txt
    assert q[1]["stale"] is True and q[1]["stuck"] is False and q[2]["pid"] is None and q[2]["stale"] is False
    idle = dict(st, job="20261125T0900-presort", job_kind="presort")
    assert hc.read_quiet(env, NOW, {25404}, idle)[0]["stuck"] is True
    write(env.quiet, f"lab-nightly {Z(NOW - timedelta(hours=25))} pid=25404\n")
    assert hc.read_quiet(env, NOW, {25404}, st)[0]["stuck"] is True
    assert hc.read_quiet(env, NOW, None, st)[0]["pid_alive"] is None  # no process list: liveness unknown, not stale


def test_gym_log_daily_lines_and_fighter_promotions_not_judge_verdicts(tmp_path):
    env = make_root(tmp_path)
    g = hc.read_gym(env, NOW)
    assert g["ok"] and g["daily"][-1]["fights"] == 13428 and g["daily"][-1]["played_h"] == 19.7 and g["daily"][-1]["waited_h"] == 4.3
    assert g["promotions_total"] == 2 and g["newest_version"] == 8 and g["promoted"][-1]["over"] == 7  # 'not promoted under keep rule' is no promotion
    assert g["last_line_age_s"] == 1800
    (env.gym / "loop.log").unlink()
    assert hc.read_gym(env, NOW)["ok"] is False


def test_agent_folders_champion_and_judgement_rows(tmp_path):
    env = make_root(tmp_path)
    a = hc.read_agent(env)
    assert a["newest_generation"] == 22 and a["champion"] == {"generation": 21, "promoted": "2026-11-22T09:44:43Z", "folder": "candidate-fight-v5"}
    assert a["judgement_count"] == 2 and a["judgements"][-1]["decision"] == "rejected"


def test_blocks_newest_next_due_and_overdue(tmp_path):
    env = make_root(tmp_path)
    b = hc.read_blocks(env, NOW)
    assert b["ok"] and b["name"] == "2026-11-20T1904" and b["age_days"] == pytest.approx(4.62, abs=0.01) and b["generations"] == [20]
    assert b["next_due"] == "2026-11-27T19:03:00Z" and b["overdue"] is False and b["last_ok"] == "2026-11-21T01:40:25Z"
    late = hc.read_blocks(env, NOW + timedelta(days=3))
    assert late["next_due"] == "2026-11-27T19:03:00Z" and late["overdue"] is True
    assert hc.next_block_due(datetime(2026, 11, 27, 19, 4, tzinfo=UTC)).isoformat().startswith("2026-12-04T19:03")
    (env.lab / "nightly" / "active").mkdir()
    assert hc.read_blocks(env, NOW + timedelta(days=3))["overdue"] is False and hc.read_blocks(env, NOW)["active"] is True


@pytest.mark.parametrize("passes,dies,lost,verdict", [(3, 3, 2, "continue"), (1, 5, 2, "close"), (2, 4, 2, "one more block")])
def test_door_reading_and_the_january_rule(tmp_path, passes, dies, lost, verdict):
    env = make_root(tmp_path, door_rows(passes, dies, lost))
    d = hc.door_reading(env)
    assert d["ok"] and d["arrivals"] == passes + dies + lost and d["generation"] == 20
    assert (d["player_finished"]["k"], d["player_finished"]["n"]) == (passes, passes + dies)  # the stand-in's fights are not the player's
    assert (d["all"]["k"], d["all"]["n"]) == (passes, passes + dies + lost)  # every arrival in the base, still only the player's passes in the top
    assert d["lost_track"]["k"] == lost and d["january"] == verdict
    pf = d["player_finished"]
    assert pf["per100"] == round(100.0 * passes / (passes + dies), 1)
    p = passes / (passes + dies)
    assert pf["two_se"] == round(200.0 * (p * (1 - p) / pf["n"]) ** 0.5, 1)


def test_door_reading_skips_a_block_still_running_and_reports_no_block(tmp_path):
    env = make_root(tmp_path, door_rows(3, 3, 2))
    write_block(env.root, "2026-11-27T1903", 21, door_rows(0, 6, 0), finished=False)  # no summary.json yet: running
    assert hc.door_reading(env)["generation"] == 20
    assert hc.read_blocks(env, NOW + timedelta(days=2))["name"] == "2026-11-27T1903"  # the age rules still use the newest start
    empty = hc.Env(tmp_path / "nothing", tmp_path / "repo2")
    assert hc.door_reading(empty)["ok"] is False


# ---------------------------------------------------------------------------------------------------------------- the colours
def test_the_baseline_is_green_and_the_page_has_its_parts(tmp_path):
    env = make_root(tmp_path)
    res = run(env)
    assert res["colour"] == "GREEN"
    md = (env.repo / "status" / "latest.md").read_text(encoding="utf-8")
    assert md.splitlines()[0] == "# Spireline status: GREEN (2026-11-25 10:00Z)"
    for needle in ("the practice loop", "13,428 fights", "The weekly real-game test", "2026-11-27", "3 of the 6 fights it finished itself: 50.0 in 100, give or take",
                   "35 or more in 100 means continue and under 32 means stop", "## Since the last check", "## Repairs", "Nothing needed repair", "| figure | value |"):
        assert needle.lower() in md.lower(), needle
    doc = json.loads((env.repo / "status" / "latest.json").read_text(encoding="utf-8"))
    assert doc["colour"] == "GREEN" and doc["door"]["player_finished"]["k"] == 3 and doc["daemon"]["alive"] is True
    rows = list(csv.DictReader(open(env.repo / "status" / "history.csv", encoding="utf-8")))
    assert tuple(rows[0].keys()) == hc.HISTORY_COLUMNS
    assert rows[0]["date"] == "2026-11-25" and rows[0]["colour"] == "GREEN" and rows[0]["fights_last_day"] == "13428" and rows[0]["promotions_total"] == "2"
    assert rows[0]["newest_generation"] == "22" and rows[0]["last_block"] == "2026-11-20T1904" and rows[0]["door_rate_player_finished"] == "50.0"
    assert rows[0]["runner_alive"] == "yes" and rows[0]["daemon_alive"] == "yes" and rows[0]["disk_free_gb"] == "1700.0" and rows[0]["repairs"] == "none"
    assert (env.health / "state.json").is_file() and (env.logs / "health-2026-11-25.log").is_file()


def colour_of(env, **kw):
    res = run(env, **kw)
    return res["colour"], [r for r in res["figures"]["reasons"]]


def test_red_when_the_runner_status_is_older_than_two_hours(tmp_path):
    env = make_root(tmp_path)
    write(env.lab / "status.txt", f"{Z(NOW - timedelta(hours=2, minutes=1))} idle\n")
    c, why = colour_of(env)
    assert c == "RED" and any("lab runner has not reported" in r["text"] for r in why)
    write(env.lab / "status.txt", f"{Z(NOW - timedelta(hours=1, minutes=59))} idle\n")
    assert colour_of(env)[0] == "GREEN"


def test_red_when_the_daemon_is_absent_and_cannot_be_started(tmp_path):
    env = make_root(tmp_path)
    calls = []
    c, why = colour_of(env, procs=procs_json(daemon=False), schtasks_fn=lambda a: (calls.append(a) or (1, "ERROR: The system cannot find the file specified.")))
    assert c == "RED" and calls == [["/run", "/tn", "Spireline gym daemon"]] and any("practice loop is not running" in r["text"] for r in why)
    env2 = make_root(tmp_path / "b")  # the task ran but no process came
    c, _ = colour_of(env2, procs=procs_json(daemon=False))
    assert c == "RED"


def test_amber_when_the_daemon_was_restarted_by_this_check(tmp_path):
    env = make_root(tmp_path)
    seq = iter([procs_json(daemon=False), procs_json(daemon=True)])
    cur = {}

    def procs_fn():
        cur["p"] = next(seq, cur.get("p"))
        return cur["p"]
    calls = []
    res = run(env, procs_fn=procs_fn, schtasks_fn=lambda a: (calls.append(a) or (0, "SUCCESS: attempted to run")))
    assert res["colour"] == "AMBER" and calls == [["/run", "/tn", "Spireline gym daemon"]]
    assert res["figures"]["daemon"]["restarted"] is True and res["figures"]["daemon"]["restart_pid"] == 10516
    assert any("restart" in r["text"] for r in res["figures"]["reasons"]) and "started through the scheduled task" in res["markdown"]
    assert res["history"]["repairs"] == "daemon-restarted"


def test_amber_when_stopped_on_purpose_and_the_daemon_is_not_restarted(tmp_path):
    env = make_root(tmp_path)
    write(env.stop_file, "stop\n")
    calls = []
    res = run(env, procs=procs_json(daemon=False), schtasks_fn=lambda a: calls.append(a) or (0, ""))
    assert res["colour"] == "AMBER" and calls == []
    assert any("STOP" in r["text"] for r in res["figures"]["reasons"]) and "stopped on purpose" in res["markdown"]
    # the same with the file and a running daemon: still amber (stopped on purpose, the stop has not reached the daemon yet)
    assert run(env)["colour"] == "AMBER"


def test_halt_and_pause_files_make_it_amber_and_halt_blocks_a_restart(tmp_path):
    env = make_root(tmp_path)
    write(env.lab / "PAUSE", "now\n")
    assert run(env)["colour"] == "AMBER"
    (env.lab / "PAUSE").unlink()
    write(env.lab / "HALT", "now\n")
    calls = []
    res = run(env, procs=procs_json(daemon=False), schtasks_fn=lambda a: calls.append(a) or (0, ""))
    assert res["colour"] == "AMBER" and calls == []


def test_red_when_disk_is_under_100_gb(tmp_path):
    env = make_root(tmp_path)
    assert colour_of(env, disk_fn=disk(99.0))[0] == "RED"
    assert colour_of(env, disk_fn=disk(101.0))[0] == "GREEN"


def test_red_for_a_stuck_judge_line(tmp_path):
    env = make_root(tmp_path)
    write(env.quiet, f"lab-train {Z(NOW - timedelta(hours=25))} pid=25404\n")
    write(env.lab / "status.txt", f"{Z(NOW - timedelta(seconds=60))} running job=20261125T0900-presort step=presort tree=9432e74\n")
    c, why = colour_of(env)
    assert c == "RED" and any("judge job looks stuck" in r["text"] for r in why)


def test_block_age_amber_over_8_days_and_red_over_10(tmp_path):
    env = make_root(tmp_path)

    def at(days: float) -> dict:
        now = NOW + timedelta(days=days)  # keep the runner, the log and the lock file fresh as the clock moves
        write(env.lab / "status.txt", f"{Z(now - timedelta(seconds=60))} idle\n")
        write(env.gym / "loop.log", f"{Z(now - timedelta(minutes=10))} wait start: x\n")
        write(env.quiet, "")
        return run(env, now=now)

    assert at(3.3)["colour"] == "GREEN"  # 7.9 days since the block began
    res = at(4.0)  # 8.6 days
    assert res["colour"] == "AMBER" and any("a week is due" in r["text"] for r in res["figures"]["reasons"])
    res = at(6.0)  # 10.6 days
    assert res["colour"] == "RED" and any("weekly real-game test began" in r["text"] for r in res["figures"]["reasons"])


def test_red_for_a_new_alert_file_and_only_a_new_one(tmp_path):
    env = make_root(tmp_path)
    assert run(env)["colour"] == "GREEN"
    write(env.lab / "alerts" / "timeouts.txt", "something\n")
    os.utime(env.lab / "alerts" / "timeouts.txt", ((NOW + timedelta(minutes=5)).timestamp(),) * 2)  # the test's clock, not the machine's
    res = run(env, now=NOW + timedelta(minutes=10))
    assert res["colour"] == "RED" and any("new alert file appeared: timeouts.txt" in r["text"] for r in res["figures"]["reasons"])
    assert "New alert: timeouts.txt" in res["markdown"]
    res = run(env, now=NOW + timedelta(minutes=20))  # seen already: still open, not new
    assert res["colour"] == "GREEN" and "timeouts.txt" in res["markdown"]
    (env.lab / "alerts" / "timeouts.txt").unlink()
    assert "Alert cleared: timeouts.txt" in run(env, now=NOW + timedelta(minutes=30))["markdown"]


def test_a_first_ever_check_with_an_alert_standing_is_red(tmp_path):
    env = make_root(tmp_path)
    write(env.lab / "alerts" / "student.txt", "x\n")
    assert run(env)["colour"] == "RED"


def test_amber_for_a_failed_job_in_the_last_day(tmp_path):
    env = make_root(tmp_path)
    with open(env.lab / "runner.log", "a", encoding="utf-8") as fh:
        fh.write("2026-11-25T09:00:00Z job 20261125T0830-bench-env finished rc=1\n")
    c, why = colour_of(env)
    assert c == "AMBER" and any("trouble in the last day" in r["text"] for r in why)


def test_amber_for_a_stale_quiet_line(tmp_path):
    env = make_root(tmp_path)
    write(env.quiet, f"w3-blocks {Z(NOW - timedelta(hours=1))} pid=424242\n")
    c, why = colour_of(env)
    assert c == "AMBER" and any("stale line" in r["text"] for r in why)


def test_amber_for_an_unreadable_process_list_and_a_silent_log(tmp_path):
    env = make_root(tmp_path)
    res = run(env, procs={"ok": False, "procs": [], "pids": None, "why": "PowerShell returned 1"})
    assert res["colour"] == "AMBER" and "could not be checked" in res["markdown"]
    write(env.gym / "loop.log", f"{Z(NOW - timedelta(hours=37))} wait start: x\n")
    assert run(env)["colour"] == "AMBER"


def test_red_beats_amber_and_the_page_lists_both(tmp_path):
    env = make_root(tmp_path)
    write(env.stop_file, "stop\n")
    res = run(env, disk_fn=disk(50.0))
    assert res["colour"] == "RED"
    md = res["markdown"]
    assert md.startswith("# Spireline status: RED") and "- RED: only 50 GB" in md and "- AMBER: stopped on purpose" in md


def test_since_the_last_check_lists_promotions_generations_and_judgements(tmp_path):
    env = make_root(tmp_path)
    assert "first check" in run(env)["markdown"]
    with open(env.gym / "loop.log", "a", encoding="utf-8") as fh:
        fh.write(f"{Z(NOW + timedelta(hours=1))} promoted c0477 as v9 over v8 by rule v5 (route A3, stage 3): part h +1\n")
    (env.agent / "gen23").mkdir()
    with open(env.agent / "promotions.tsv", "a", encoding="utf-8") as fh:
        fh.write(f"{Z(NOW + timedelta(hours=2))}\t23\t22\tE23\t2000\tpromoted\tcandidate-fight-v9\n")
    write(env.agent / "current.json", json.dumps({"generation": 23, "dir": "x\\candidate-fight-v9", "promoted": Z(NOW)}))
    write_block(env.root, "2026-11-27T1903", 23, door_rows(1, 1, 0))
    later = NOW + timedelta(hours=3)
    write(env.lab / "status.txt", f"{Z(later - timedelta(seconds=30))} idle\n")
    res = run(env, now=later)
    md = res["markdown"]
    assert "promoted fighter v9 over v8" in md and "A new generation folder appeared: gen23" in md and "champion changed: generation 23" in md
    assert "judgement on candidate-fight-v9" in md and "A new weekly real-game test folder appeared: 2026-11-27T1903" in md
    assert "promoted fighter v8" not in md  # an old one is not "since the last check"
    assert res["history"]["promotions_total"] == 3


def test_a_second_check_the_same_day_replaces_the_days_history_row(tmp_path):
    env = make_root(tmp_path)
    run(env)
    run(env, now=NOW + timedelta(minutes=5), disk_fn=disk(50.0))
    rows = list(csv.DictReader(open(env.repo / "status" / "history.csv", encoding="utf-8")))
    assert [r["colour"] for r in rows] == ["RED"] and rows[0]["disk_free_gb"] == "50.0"
    run(env, now=NOW + timedelta(days=1))
    rows = list(csv.DictReader(open(env.repo / "status" / "history.csv", encoding="utf-8")))
    assert [r["date"] for r in rows] == ["2026-11-25", "2026-11-26"]


def test_dry_run_writes_nothing_and_restarts_nothing(tmp_path):
    env = make_root(tmp_path)
    calls = []
    res = run(env, dry_run=True, procs=procs_json(daemon=False), schtasks_fn=lambda a: calls.append(a) or (0, ""))
    assert res["colour"] == "RED" and calls == []
    assert not (env.repo / "status").exists() and not env.health.exists() and not env.logs.exists()


# ---------------------------------------------------------------------------------------------------------------------- scrub
def private_names() -> list[str]:
    names = [os.environ.get("USERNAME") or os.environ.get("USER"), os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME")]
    return [n for n in names if n and len(n) >= 3]


def test_no_home_path_user_name_or_host_name_reaches_any_output(tmp_path):
    env = make_root(tmp_path)
    names = private_names()
    home = "C:\\Users\\" + (names[0] if names else "someone")
    # a home path and the private names ride in through the places a message can come from: an alert file name, the task's error text
    write(env.lab / "alerts" / f"{names[0] if names else 'a'}-{names[-1] if names else 'b'}.txt", "x\n")
    res = run(env, procs=procs_json(daemon=False), schtasks_fn=lambda a: (1, f"ERROR: {home}\\AppData\\task.xml on {names[-1] if names else 'host'}"))
    texts = [(env.repo / "status" / "latest.md").read_text(encoding="utf-8"), (env.repo / "status" / "latest.json").read_text(encoding="utf-8"),
             (env.repo / "status" / "history.csv").read_text(encoding="utf-8"), (env.logs / "health-2026-11-25.log").read_text(encoding="utf-8"),
             res["markdown"]]
    assert "<home>" in texts[0] and "AppData" in texts[0]  # the path was there and is now only <home>
    for text in texts:
        assert "C:/Users" not in text and "C:\\Users" not in text and "C:\\\\Users" not in text
        for n in names:
            assert n.lower() not in text.lower()


def test_champion_folder_in_current_json_is_reduced_to_its_name(tmp_path):
    env = make_root(tmp_path)
    a = hc.read_agent(env)
    assert a["champion"]["folder"] == "candidate-fight-v5" and "Users" not in json.dumps(a)


# ----------------------------------------------------------------------------------------------------------------------- git
class FakeGit:
    def __init__(self, *, branch="main", behind=0, ahead=0, porcelain="", subjects="", fetch_rc=0, merge_rc=0, diff_rc=1, push_rc=0):
        self.calls: list[list[str]] = []
        self.cfg = dict(branch=branch, behind=behind, ahead=ahead, porcelain=porcelain, subjects=subjects, fetch_rc=fetch_rc, merge_rc=merge_rc,
                        diff_rc=diff_rc, push_rc=push_rc)

    def __call__(self, args):
        self.calls.append(list(args))
        c, a = self.cfg, args
        if a[0] == "fetch":
            return c["fetch_rc"], "" if c["fetch_rc"] == 0 else "fatal: unable to access"
        if a[:2] == ["rev-parse", "--abbrev-ref"]:
            return 0, c["branch"]
        if a[0] == "rev-list":
            return 0, f"{c['behind']}\t{c['ahead']}"
        if a[:2] == ["status", "--porcelain"]:
            return 0, c["porcelain"]
        if a[0] == "log":
            return 0, c["subjects"]
        if a[0] == "merge":
            return c["merge_rc"], "" if c["merge_rc"] == 0 else "not possible"
        if a[0] == "diff":
            return c["diff_rc"], ""
        if a[0] == "push":
            return c["push_rc"], "" if c["push_rc"] == 0 else "rejected"
        if a[:2] == ["rev-parse", "--short"]:
            return 0, "abc1234"
        return 0, ""

    @property
    def verbs(self) -> list[str]:
        return [c[0] for c in self.calls]


def test_git_step_adds_only_the_three_status_files_commits_and_pushes(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit()
    res = run(env, git=git, no_git=False)
    assert res["git"]["status"] == "pushed"
    assert git.calls[0] == ["fetch", "origin"]
    add = next(c for c in git.calls if c[0] == "add")
    assert add == ["add", "--", "status/latest.md", "status/latest.json", "status/history.csv"]
    commit = next(c for c in git.calls if c[0] == "commit")
    assert commit[:3] == ["commit", "-m", "status: 2026-11-25 GREEN"] and commit[3:] == ["--", "status/latest.md", "status/latest.json", "status/history.csv"]
    assert "Co-Authored-By" not in " ".join(commit)
    assert git.calls[-2] == ["push", "origin", "main"]
    flat = " ".join(" ".join(c) for c in git.calls)
    assert " -A" not in flat and "add ." not in flat and "--all" not in flat and "reset" not in flat and "--force" not in flat


@pytest.mark.parametrize("porcelain,why", [
    ("D  .github/ISSUE_TEMPLATE/simulator-access.yml\n", "staged"),
    (" M tests/test_morning_report.py\n", "modified"),
    ("R  old.py -> new.py\n", "staged"),
])
def test_git_step_skips_when_anything_is_staged_or_modified_outside_status(tmp_path, porcelain, why):
    env = make_root(tmp_path)
    git = FakeGit(porcelain=porcelain)
    res = run(env, git=git, no_git=False)
    assert res["git"]["status"] == "skipped" and "outside status/" in res["git"]["why"]
    assert not {"add", "commit", "push"} & set(git.verbs)
    md = (env.repo / "status" / "latest.md").read_text(encoding="utf-8")
    assert "Not published to GitHub" in md and "outside status/" in md
    assert "push-skipped" in res["history"]["repairs"]
    assert "outside status/" in (env.logs / "health-2026-11-25.log").read_text(encoding="utf-8")


def test_git_step_ignores_untracked_files_and_the_status_files_themselves(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit(porcelain="?? .claude/\n?? morning-summary-2026-10-16.md\n M status/latest.md\nA  status/history.csv\n")
    assert run(env, git=git, no_git=False)["git"]["status"] == "pushed"


def test_git_step_with_allow_dirty_commits_only_the_status_files(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit(porcelain="D  .github/x.yml\n M tests/t.py\n")
    res = run(env, git=git, no_git=False, allow_dirty=True)
    assert res["git"]["status"] == "pushed"
    commit = next(c for c in git.calls if c[0] == "commit")
    assert commit[3:] == ["--", *hc.STATUS_FILES]  # the pathspec form: other staged files are not in the commit
    assert any("left alone" in r for r in res["figures"]["repairs"])


def test_git_step_skips_when_not_on_main_or_fetch_fails_or_diverged(tmp_path):
    for kw, needle in (({"branch": "feature"}, "not main"), ({"fetch_rc": 128}, "git fetch failed"), ({"behind": 2, "ahead": 1}, "both moved")):
        env = make_root(tmp_path / needle.replace(" ", "_"))
        git = FakeGit(**kw)
        res = run(env, git=git, no_git=False)
        assert res["git"]["status"] == "skipped" and needle in res["git"]["why"]
        assert not {"add", "commit", "push"} & set(git.verbs)


def test_git_step_ahead_only_by_its_own_status_commits_still_pushes(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit(ahead=2, subjects="status: 2026-11-24 GREEN\nstatus: 2026-11-23 AMBER\n")
    assert run(env, git=git, no_git=False)["git"]["status"] == "pushed"
    env2 = make_root(tmp_path / "b")
    git2 = FakeGit(ahead=1, subjects="docs: something else\n")
    res = run(env2, git=git2, no_git=False)
    assert res["git"]["status"] == "skipped" and "not all status commits" in res["git"]["why"]


def test_git_step_behind_with_a_clean_tree_fast_forwards_and_a_dirty_tree_skips(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit(behind=3)
    res = run(env, git=git, no_git=False)
    assert res["git"]["status"] == "pushed" and ["merge", "--ff-only", "origin/main"] in git.calls
    assert any("brought forward" in r for r in res["figures"]["repairs"])
    env2 = make_root(tmp_path / "b")
    git2 = FakeGit(behind=3, porcelain=" M tests/t.py\n")
    res = run(env2, git=git2, no_git=False, allow_dirty=True)
    assert res["git"]["status"] == "skipped" and "cannot be brought forward" in res["git"]["why"] and "merge" not in git2.verbs


def test_git_push_failure_leaves_the_commit_and_the_next_check_says_so(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit(push_rc=1)
    res = run(env, git=git, no_git=False)
    assert res["git"]["status"] == "push-failed" and "reset" not in git.verbs
    nxt = FakeGit(ahead=1, subjects="status: 2026-11-25 GREEN\n")
    later = NOW + timedelta(days=1)
    write(env.lab / "status.txt", f"{Z(later - timedelta(seconds=30))} idle\n")
    write(env.gym / "loop.log", f"{Z(later - timedelta(minutes=10))} wait start: x\n")
    write(env.quiet, "")
    res = run(env, now=later, git=nxt, no_git=False)
    assert res["git"]["status"] == "pushed" and "The previous check could not publish" in res["markdown"]


def test_git_nothing_new_makes_no_commit(tmp_path):
    env = make_root(tmp_path)
    git = FakeGit(diff_rc=0)
    res = run(env, git=git, no_git=False)
    assert res["git"]["status"] == "unchanged" and "commit" not in git.verbs and "push" not in git.verbs


def test_make_git_keeps_the_first_porcelain_column_and_drops_stderr_warnings(monkeypatch):
    seen = []

    def fake_run(cmd, **kw):
        seen.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, " M tests/a.py\nD  b.yml\n", "warning: LF will be replaced by CRLF\n")
    monkeypatch.setattr(subprocess, "run", fake_run)
    rc, out = hc.make_git(Path("somewhere"))(["status", "--porcelain"])
    assert rc == 0 and out == " M tests/a.py\nD  b.yml" and hc.parse_porcelain(out) == (["b.yml"], ["tests/a.py"])
    assert seen[0][0][:3] == ["git", "-C", "somewhere"] and seen[0][1]["env"]["GIT_TERMINAL_PROMPT"] == "0"
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "fatal: nope\n"))
    assert hc.make_git(Path("somewhere"))(["fetch", "origin"]) == (1, "fatal: nope")


def test_parse_porcelain():
    staged, modified = hc.parse_porcelain("D  a.yml\n M b.py\nMM c.py\n?? d\n M status/latest.md\nR  e -> f\n")
    assert staged == ["a.yml", "c.py", "f"] and modified == ["b.py", "c.py"]


# ------------------------------------------------------------------------------------------------------------ the daemon starter
def test_daemon_args_are_one_constant_with_gate_procs_equal_to_procs():
    a = list(hc.DAEMON_ARGS)
    assert a[a.index("--procs") + 1] == a[a.index("--gate-procs") + 1] == "12"
    assert " ".join(a) == ("rl/gym_loop.py run --root D:/spireline/referee/gym-loop --max-epochs 8 --gate-every-min 120 "
                           "--teacher-store D:/spireline/referee/run-teacher --procs 12 --gate-procs 12 "
                           "--trainer-extra-rows-root D:/spireline/referee/run-cheap --trainer-extra-window 150000 --rule v5")
    assert hc.DAEMON_NEEDLE == "rl/gym_loop.py run --root d:/spireline/referee/gym-loop"
    assert hc.DAEMON_PYTHON == "D:/spireline/src/sts2/.venv/Scripts/python.exe" and hc.DAEMON_CWD == "D:/spireline/fork/wt-gym-loop-run"


class FakePopen:
    made: list = []

    def __init__(self, argv, **kw):
        self.argv, self.kw, self.pid, self.waited = argv, kw, 4321, False
        FakePopen.made.append(self)

    def wait(self):
        self.waited = True
        return 7


@pytest.fixture
def fake_popen():
    FakePopen.made = []
    return FakePopen


def starter_env(tmp_path) -> hc.Env:
    env = hc.Env(tmp_path / "root", tmp_path / "repo")
    return env


def test_start_daemon_starts_a_plain_child_with_the_brief_flags_and_logs_its_pid(tmp_path, fake_popen):
    env = starter_env(tmp_path)
    said = []
    rc = hc.start_daemon(env, wait=False, procs_fn=lambda: procs_json(daemon=False), popen=fake_popen, now=NOW, say=said.append)
    assert rc == 0 and len(fake_popen.made) == 1
    p = fake_popen.made[0]
    assert p.argv == ["D:/spireline/src/sts2/.venv/Scripts/python.exe", *hc.DAEMON_ARGS]
    assert p.kw["cwd"] == "D:/spireline/fork/wt-gym-loop-run".replace("/", os.sep) or p.kw["cwd"] == "D:/spireline/fork/wt-gym-loop-run" or p.kw["cwd"].endswith("wt-gym-loop-run")
    flags = p.kw["creationflags"]
    assert flags & hc.BELOW_NORMAL and flags & hc.NEW_GROUP
    assert not flags & 0x00000008  # DETACHED_PROCESS: the child stays attached so the scheduled task stays Running while it lives
    assert p.kw["stderr"] == subprocess.STDOUT and p.kw["stdin"] == subprocess.DEVNULL and p.kw["stdout"].name.endswith("daemon.out")
    assert env.daemon_out.exists()
    line = (env.health / "daemon-start.log").read_text(encoding="utf-8")
    assert "2026-11-25T10:00:00Z started pid=4321" in line
    assert p.waited is False  # --no-wait: the wrapper returns at once


def test_start_daemon_does_nothing_when_one_runs_or_stop_or_halt_exists(tmp_path, fake_popen):
    env = starter_env(tmp_path)
    said = []
    assert hc.start_daemon(env, procs_fn=lambda: procs_json(daemon=True), popen=fake_popen, say=said.append) == 0
    assert fake_popen.made == [] and "running already" in said[-1] and "10516" in said[-1]
    write(env.stop_file, "stop\n")
    assert hc.start_daemon(env, procs_fn=lambda: procs_json(daemon=False), popen=fake_popen, say=said.append) == 0
    assert fake_popen.made == [] and "STOP" in said[-1]
    env.stop_file.unlink()
    write(env.lab / "HALT", "x\n")
    assert hc.start_daemon(env, procs_fn=lambda: procs_json(daemon=False), popen=fake_popen, say=said.append) == 0
    assert fake_popen.made == [] and "HALT" in said[-1]


def test_start_daemon_never_starts_a_second_one_when_the_process_list_is_unreadable(tmp_path, fake_popen):
    env = starter_env(tmp_path)
    bad = {"ok": False, "procs": [], "pids": None, "why": "PowerShell returned 1"}
    assert hc.start_daemon(env, procs_fn=lambda: bad, popen=fake_popen, say=lambda s: None) == 3
    assert fake_popen.made == []


def test_start_daemon_selftest_starts_the_sleeper_even_beside_a_real_daemon(tmp_path, fake_popen):
    env = starter_env(tmp_path)
    write(env.stop_file, "stop\n")
    rc = hc.start_daemon(env, selftest=True, wait=False, procs_fn=lambda: procs_json(daemon=True), popen=fake_popen, now=NOW, say=lambda s: None)
    assert rc == 0 and len(fake_popen.made) == 1
    p = fake_popen.made[0]
    assert p.argv[1:] == ["-c", "import time; time.sleep(300)"] and "gym_loop" not in " ".join(p.argv)
    assert p.kw["stdout"].name.endswith("selftest.out") and not env.daemon_out.exists()
    assert (env.health / "selftest-start.log").exists() and not (env.health / "daemon-start.log").exists()


def test_start_daemon_waits_by_default_and_passes_on_the_childs_exit_code(tmp_path, fake_popen):
    # the self-test of 2026-11-25: a task whose action exits is Ready again at once, so the wrapper stays alive while the loop lives
    env = starter_env(tmp_path)
    rc = hc.start_daemon(env, procs_fn=lambda: procs_json(daemon=False), popen=fake_popen, say=lambda s: None)
    assert rc == 7 and fake_popen.made[0].waited is True
    assert "ended rc=7" in (env.health / "daemon-start.log").read_text(encoding="utf-8")


def test_ensure_daemon_does_nothing_when_a_practice_loop_runs(tmp_path):
    env = make_root(tmp_path)
    fig = hc.collect(env, NOW, procs_json(), disk(), lambda m: None)
    assert hc.ensure_daemon(env, fig, procs_fn=lambda: 1 / 0, schtasks_fn=lambda a: 1 / 0, sleep=lambda s: None, log=lambda m: None) == []


# ----------------------------------------------------------------------------------------------------------- the crash page and main
def test_a_crash_of_the_check_leaves_a_red_page(tmp_path, monkeypatch, capsys):
    env = make_root(tmp_path)

    def boom(*a, **k):
        raise RuntimeError("the lab fell over")
    monkeypatch.setattr(hc, "run_check", boom)
    rc = hc.main(["--root", str(env.root), "--repo", str(env.repo), "--no-git"])
    assert rc == 1
    md = (env.repo / "status" / "latest.md").read_text(encoding="utf-8")
    assert md.startswith("# Spireline status: RED (") and "RuntimeError: the lab fell over" in md


def test_the_modes_are_wired_in_main(tmp_path, monkeypatch):
    env = make_root(tmp_path)
    seen = {}
    monkeypatch.setattr(hc, "start_daemon", lambda e, **kw: seen.__setitem__("start", kw) or 0)
    assert hc.main(["--root", str(env.root), "--start-daemon", "--selftest"]) == 0
    assert seen["start"] == {"selftest": True, "wait": True}
    assert hc.main(["--root", str(env.root), "--start-daemon", "--no-wait"]) == 0
    assert seen["start"] == {"selftest": False, "wait": False}
    monkeypatch.setattr(hc, "run_check", lambda e, **kw: seen.__setitem__("check", kw) or {"markdown": "x", "colour": "GREEN"})
    assert hc.main(["--root", str(env.root), "--repo", str(env.repo), "--no-git", "--allow-dirty-tree", "--no-restart"]) == 0
    assert seen["check"]["allow_dirty"] is True and seen["check"]["no_git"] is True and seen["check"]["no_restart"] is True and seen["check"]["dry_run"] is False


def test_a_daily_summary_older_than_yesterday_is_said(tmp_path):
    env = make_root(tmp_path)
    assert "days old" not in run(env)["markdown"]  # the 11-24 summary read on 11-25
    later = NOW + timedelta(days=2)
    write(env.lab / "status.txt", f"{Z(later - timedelta(seconds=30))} idle\n")
    write(env.quiet, "")
    with open(env.gym / "loop.log", "a", encoding="utf-8") as fh:
        fh.write(f"{Z(later - timedelta(minutes=10))} wait start: x\n")
    assert "That summary is 3 days old" in run(env, now=later)["markdown"]
