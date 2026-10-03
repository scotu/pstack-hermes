#!/usr/bin/env python3
"""pstack split audit tick: monitor script for a Hermes cron job (pstack-economy, C-005).

Runs in the program dir. Reads owners.tsv (tab-separated, header row):
  owner  remote  repo  branch  pr  expected_minutes  started_at
and prints one stable line per owner, with no timestamps, so Hermes runs the watcher model only when
something changed:
  <owner> branch=<branch> head=<sha7|missing|unknown> checks=<pass|pending|fail|none|unknown|nopr>
  bot_comments=<n|unknown|nopr> [STUCK]
STUCK means both the owner and its current head have been idle longer than expected_minutes.
State (when each head was first seen) lives in .pstack-audit-state.json. PSTACK_AUDIT_NOW overrides the
clock for tests. Always exits 0: problems are reported as ERROR lines for the watcher to escalate.
"""
import csv
import json
import os
import subprocess
import time
from pathlib import Path

OWNERS = Path("owners.tsv")
STATE = Path(".pstack-audit-state.json")
COLUMNS = 7


def run(*cmd: str) -> tuple[int, str] | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.returncode, r.stdout


def head(remote: str, branch: str) -> str:
    result = run("git", "ls-remote", remote, f"refs/heads/{branch}")
    if result is None or result[0] != 0:
        return "unknown"
    return result[1].split()[0][:7] if result[1].strip() else "missing"


def gh_json(*args: str):
    """gh output as JSON. `gh pr checks` exits non-zero while checks pend or fail but still prints JSON."""
    result = run("gh", *args)
    if result is None:
        return None
    try:
        return json.loads(result[1])
    except ValueError:
        return None


def checks(repo: str, pr: str) -> str:
    data = gh_json("pr", "checks", pr, "-R", repo, "--json", "bucket")
    if not isinstance(data, list):
        return "unknown"
    buckets = {c.get("bucket") for c in data}
    if not buckets:
        return "none"
    if buckets & {"fail", "cancel"}:
        return "fail"
    if "pending" in buckets:
        return "pending"
    return "pass"


def bot_comments(repo: str, pr: str) -> str:
    data = gh_json("pr", "view", pr, "-R", repo, "--json", "comments")
    if not isinstance(data, dict):
        return "unknown"
    logins = [str((c.get("author") or {}).get("login", "")).lower() for c in data.get("comments", [])]
    return str(sum(1 for login in logins if login.endswith("[bot]") or login.endswith("bot")))


def main() -> None:
    if not OWNERS.exists():
        print("ERROR owners.tsv not found")
        return
    rows = list(csv.reader(OWNERS.read_text().splitlines(), delimiter="\t"))
    now = int(os.environ.get("PSTACK_AUDIT_NOW") or time.time())
    try:
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
    except ValueError:
        state = {}
    lines = []
    for n, row in enumerate(rows[1:], start=2):
        if len(row) != COLUMNS:
            print(f"ERROR owners.tsv line {n}: expected {COLUMNS} columns")
            return
        owner, remote, repo, branch, pr, expected, started = row
        sha = head(remote, branch)
        seen = state.get(owner, {})
        if seen.get("sha") != sha:
            seen = {"sha": sha, "first_seen": now}
            state[owner] = seen
        limit = int(expected) * 60
        stuck = now - seen["first_seen"] > limit and now - int(started) > limit
        if pr == "-":
            status = "checks=nopr bot_comments=nopr"
        else:
            status = f"checks={checks(repo, pr)} bot_comments={bot_comments(repo, pr)}"
        lines.append(f"{owner} branch={branch} head={sha} {status}" + (" STUCK" if stuck else ""))
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
