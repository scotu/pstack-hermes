#!/usr/bin/env python3
"""pstack split audit tick: monitor script for a Hermes cron job (pstack-economy, C-005).

Runs in the program dir. Reads owners.tsv (tab-separated, header row):
  owner  remote  repo  branch  pr  expected_minutes  started_at
and prints one stable line per owner, with no timestamps, so Hermes runs the watcher model only when
something changed:
  <owner> branch=<branch> head=<sha7|missing|unknown> expected=<n>m checks=<pass|pending|fail|none|unknown|nopr>
  bot_comments=<n|unknown|nopr> [STUCK]
Blank rows and rows starting with # are skipped. STUCK means both the owner and its last known head have been
idle longer than expected_minutes; an `unknown` head (a failed ls-remote) leaves that timer alone. bot_comments
counts comments, inline review comments and reviews whose author is a GitHub Bot account.
State (when each head was first seen) lives in .pstack-audit-state.json. PSTACK_AUDIT_NOW overrides the
clock for tests. Always exits 0: problems are reported as ERROR lines for the watcher to escalate.
"""
from __future__ import annotations

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
    """Bot-authored items across issue comments, inline review comments and reviews (where review bots post)."""
    total = 0
    for endpoint in (f"repos/{repo}/issues/{pr}/comments", f"repos/{repo}/pulls/{pr}/comments",
                     f"repos/{repo}/pulls/{pr}/reviews"):
        pages = gh_json("api", "--paginate", "--slurp", endpoint)
        if not isinstance(pages, list):
            return "unknown"
        items = [item for page in pages if isinstance(page, list) for item in page]
        total += sum(1 for item in items if isinstance(item, dict) and (item.get("user") or {}).get("type") == "Bot")
    return str(total)


def load_state() -> dict:
    try:
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
    except ValueError:
        return {}
    return state if isinstance(state, dict) else {}


def main() -> None:
    if not OWNERS.exists():
        print("ERROR owners.tsv not found")
        return
    rows = list(csv.reader(OWNERS.read_text().splitlines(), delimiter="\t"))
    now = int(os.environ.get("PSTACK_AUDIT_NOW") or time.time())
    state = load_state()
    lines = []
    for n, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row) or row[0].startswith("#"):
            continue
        if len(row) != COLUMNS:
            print(f"ERROR owners.tsv line {n}: expected {COLUMNS} columns")
            return
        owner, remote, repo, branch, pr, expected, started = row
        try:
            minutes, started_at = int(expected), int(started)
        except ValueError:
            print(f"ERROR owners.tsv line {n}: expected_minutes and started_at must be integers")
            return
        sha = head(remote, branch)
        seen = state.get(owner) if isinstance(state.get(owner), dict) else {}
        if sha != "unknown" and seen.get("sha") != sha:
            seen = {"sha": sha, "first_seen": now}
            state[owner] = seen
        limit = minutes * 60
        stuck = "first_seen" in seen and now - seen["first_seen"] > limit and now - started_at > limit
        if pr == "-":
            status = "checks=nopr bot_comments=nopr"
        else:
            status = f"checks={checks(repo, pr)} bot_comments={bot_comments(repo, pr)}"
        lines.append(f"{owner} branch={branch} head={sha} expected={minutes}m {status}" + (" STUCK" if stuck else ""))
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True))
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the watcher must see a stable line, never a crash
        print(f"ERROR internal {type(exc).__name__}")
