"""check-plan.mjs behavior for the lean lane count (C-004) and the split audit tick marker (C-005)."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "poteto-mode" / "scripts" / "check-plan.mjs"
RULE = ("Tests alone are not sufficient verification. "
        "A PR is verified only when its unit, live, and perf boxes are all checked.")
TEN = "Ten lanes on `gpt-6.1-sol` at the PR head, per the boot recipe."
LEAN3 = "One lane per distinct check on `gpt-6.1-sol` at the PR head (3 lanes), per the boot recipe."
LOOP = "- [ ] Arm the audit tick as `/loop 1h` with the tick prompt."
SPLIT = "- [ ] Arm the split audit tick as cron job `pstack-audit-demo`."


def lanes(numbers):
    return "\n".join(f"- [ ] Lane {i}. Scenario {i}. Save `lane{i}.png`. Pass when it renders." for i in numbers)


def plan(live_line, n_lanes, marker=LOOP):
    numbers = range(1, n_lanes + 1) if isinstance(n_lanes, int) else n_lanes
    return f"""# Demo program

A short intro.

## How to read this

One box is one unit of work. Each box names the evidence. Check a box only when its evidence exists. The steps follow playbooks/ in pstack. {RULE}

## Program checklist

### Arm the program

- [ ] Read `git show origin/main:pstack/skills/swarm/SKILL.md` first.
{marker}
- [ ] Post a status message when something changes.

### Spawn owners

- [ ] Spawn one owner.

### PR mechanics

- [ ] Open the PR ready.

### Verdict and merge

- [ ] Merge on a clean verdict.

### Boot recipe

- [ ] Boot the app.

## PR 1. Demo change

**Depends on.** Nothing.

**Files.**

- [ ] `src/a.ts` changes.

**Build.**

- [ ] Build it.

**You see.**

- [ ] The demo works.

**Verify, unit.** {RULE}

- [ ] Run `npm test`.

**Verify, live.** {RULE} {live_line}

{lanes(numbers)}

**Verify, perf.** {RULE}

- [ ] Metric. Load time.
- [ ] Probe. Interleaved runs.
- [ ] Baseline. Trunk first.
- [ ] Rule. Fail above two seconds.

**Review gate.** None. PR 1 is not review-gated.

**Merge.**

- [ ] Squash-merge.

## Close the program

- [ ] Retro.

## Appendix A. Prototype evidence

Nothing yet.
"""


def check(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "plan.md"
        path.write_text(text)
        r = subprocess.run(["node", str(SCRIPT), str(path)], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


class LaneCountTest(unittest.TestCase):
    def test_ten_lanes_still_pass(self):
        code, out = check(plan(TEN, 10))
        self.assertEqual(code, 0, out)

    def test_lean_lane_count_passes(self):
        code, out = check(plan(LEAN3, 3))
        self.assertEqual(code, 0, out)

    def test_lean_count_mismatch_fails(self):
        for numbers in (4, [1, 2, 4]):
            code, out = check(plan(LEAN3, numbers))
            self.assertEqual(code, 1, out)
            self.assertIn("lanes are", out)

    def test_lean_without_count_fails(self):
        code, out = check(plan("One lane per distinct check on `gpt-6.1-sol` at the PR head.", 3))
        self.assertEqual(code, 1, out)

    def test_no_lane_line_fails(self):
        code, out = check(plan("Some lanes run.", 3))
        self.assertEqual(code, 1, out)
        self.assertIn("Verify, live lacks", out)

    def test_ten_lanes_with_three_fails(self):
        code, out = check(plan(TEN, 3))
        self.assertEqual(code, 1, out)


if __name__ == "__main__":
    unittest.main()
