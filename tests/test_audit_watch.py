"""pstack-audit-watch.py, the split audit tick's monitor script (C-005)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "pstack-economy" / "audit-watch" / "pstack-audit-watch.py"
HEADER = "owner\tremote\trepo\tbranch\tpr\texpected_minutes\tstarted_at\n"
GH_STUB = """#!/bin/sh
# Stub gh: `gh pr checks|view <n> ...` prints $GH_FIXTURES/<checks|view>-<n>.json and exits with the code in
# $GH_FIXTURES/<checks|view>-<n>.code (default 0); a missing fixture exits 1.
f="$GH_FIXTURES/$2-$3.json"
[ -f "$f" ] || exit 1
cat "$f"
c="$GH_FIXTURES/$2-$3.code"
[ -f "$c" ] && exit "$(cat "$c")"
exit 0
"""


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout.strip()


class AuditWatchTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.remote = base / "remote.git"
        git(base, "init", "-q", "--bare", str(self.remote))
        self.work = base / "work"
        git(base, "clone", "-q", str(self.remote), str(self.work))
        self.push("1")
        self.bin = base / "bin"
        self.bin.mkdir()
        (self.bin / "gh").write_text(GH_STUB)
        (self.bin / "gh").chmod(0o755)
        self.fx = base / "fx"
        self.fx.mkdir()
        self.fixture("checks", [{"bucket": "pass"}, {"bucket": "pending"}])
        self.fixture("view", {"comments": [{"author": {"login": "cursor[bot]"}}, {"author": {"login": "matteo"}}]})
        self.program = base / "program"
        self.program.mkdir()
        self.owners(f"owner-a\t{self.remote}\tme/demo\tfeat-a\t7\t40\t1000\n")

    def tearDown(self):
        self._tmp.cleanup()

    def push(self, content):
        (self.work / "f").write_text(content)
        git(self.work, "add", "f")
        git(self.work, "commit", "-qm", content)
        git(self.work, "push", "-q", "origin", "HEAD:refs/heads/feat-a")
        return git(self.work, "rev-parse", "--short=7", "HEAD")

    def fixture(self, kind, data, code=0):
        (self.fx / f"{kind}-7.json").write_text(json.dumps(data))
        (self.fx / f"{kind}-7.code").write_text(str(code))

    def owners(self, rows):
        (self.program / "owners.tsv").write_text(HEADER + rows)

    def watch(self, now):
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
               "GH_FIXTURES": str(self.fx), "PSTACK_AUDIT_NOW": str(now)}
        r = subprocess.run([sys.executable, str(SCRIPT)], cwd=self.program, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_line_format(self):
        head = git(self.work, "rev-parse", "--short=7", "HEAD")
        self.assertEqual(self.watch(1100),
                         f"owner-a branch=feat-a head={head} checks=pending bot_comments=1\n")

    def test_stable_output_without_changes(self):
        first, second = self.watch(1100), self.watch(1200)
        self.assertEqual(first, second)
        self.assertNotIn("1100", first)

    def test_new_push_changes_only_head(self):
        before = self.watch(1100)
        new = self.push("2")
        after = self.watch(1200)
        self.assertNotEqual(before, after)
        self.assertIn(f"head={new}", after)
        self.assertEqual(before.split("head=")[0], after.split("head=")[0])
        self.assertEqual(before.split(" checks=")[1], after.split(" checks=")[1])

    def test_stuck_after_expected_runtime(self):
        self.watch(1100)
        self.assertNotIn("STUCK", self.watch(1100 + 39 * 60))
        self.assertTrue(self.watch(1100 + 41 * 60).rstrip().endswith(" STUCK"))

    def test_stuck_clears_on_push(self):
        self.watch(1100)
        self.assertIn("STUCK", self.watch(1100 + 41 * 60))
        self.push("2")
        now = 1100 + 42 * 60
        self.assertNotIn("STUCK", self.watch(now))
        self.assertNotIn("STUCK", self.watch(now + 39 * 60))
        self.assertIn("STUCK", self.watch(now + 41 * 60))

    def test_checks_summary_reads_json_on_nonzero_exit(self):
        self.fixture("checks", [{"bucket": "pass"}, {"bucket": "fail"}], code=1)
        self.assertIn("checks=fail", self.watch(1100))
        self.fixture("checks", [{"bucket": "pending"}], code=8)
        self.assertIn("checks=pending", self.watch(1100))
        self.fixture("checks", [{"bucket": "pass"}, {"bucket": "skipping"}])
        self.assertIn("checks=pass", self.watch(1100))
        self.fixture("checks", [])
        self.assertIn("checks=none", self.watch(1100))

    def test_gh_failure_is_unknown(self):
        (self.fx / "checks-7.json").unlink()
        (self.fx / "view-7.json").unlink()
        self.assertIn("checks=unknown bot_comments=unknown", self.watch(1100))

    def test_no_pr_yet(self):
        self.owners(f"owner-a\t{self.remote}\tme/demo\tfeat-a\t-\t40\t1000\n")
        self.assertIn("checks=nopr bot_comments=nopr", self.watch(1100))

    def test_missing_branch(self):
        self.owners(f"owner-a\t{self.remote}\tme/demo\tnope\t7\t40\t1000\n")
        self.assertIn("head=missing", self.watch(1100))

    def test_missing_owners_file(self):
        (self.program / "owners.tsv").unlink()
        self.assertEqual(self.watch(1100), "ERROR owners.tsv not found\n")

    def test_malformed_row(self):
        self.owners("owner-a\tonly-two\n")
        self.assertEqual(self.watch(1100), "ERROR owners.tsv line 2: expected 7 columns\n")


if __name__ == "__main__":
    unittest.main()
