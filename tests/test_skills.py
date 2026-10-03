"""Text checks for the economy customizations (C-001, C-002, C-003, C-005)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"


def skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def frontmatter_name(text: str) -> str:
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    return re.search(r"^name:\s*(\S+)", m.group(1), re.M).group(1) if m else ""


class SkillNamesTest(unittest.TestCase):
    def test_every_skill_name_matches_its_folder(self):
        for md in sorted(SKILLS.glob("*/SKILL.md")):
            self.assertEqual(frontmatter_name(md.read_text()), md.parent.name, md)


class EconomySkillTest(unittest.TestCase):
    def test_sections(self):
        text = skill("pstack-economy")
        for heading in ("## Duplicated and divided work", "## Lean widths", "## Going wide",
                        "## Routing", "## Split audit tick"):
            self.assertIn(heading, text)

    def test_economy_states_first_entry_rule(self):
        self.assertIn("use only the first entry", skill("pstack-economy"))

    def test_economy_states_per_token_rule(self):
        text = skill("pstack-economy")
        self.assertIn("per-token", text)
        self.assertIn("only executor at the tier", text)

    def test_economy_points_at_watcher_files(self):
        text = skill("pstack-economy")
        self.assertIn("audit-watch/pstack-audit-watch.py", text)
        self.assertIn("audit-watch/watcher-prompt.md", text)
        self.assertIn("pstack-audit-<program>", text)


class OnHermesHookTest(unittest.TestCase):
    def test_on_hermes_points_at_economy(self):
        text = skill("pstack-on-hermes")
        self.assertIn("agent-plugin-pstack-7171b73f:pstack-economy", text)
        subagents = text.split("## Subagents", 1)[1]
        self.assertIn("pstack-economy", subagents.split("\n- ", 2)[1])


class SetupInventoryTest(unittest.TestCase):
    def test_inventory_and_lean_defaults(self):
        text = skill("setup-pstack")
        for needle in ("cost class", "self-hosted", "subscription", "per-token", "frontier", "strong", "light",
                       "tools", "cron", "# Models this profile can reach"):
            self.assertIn(needle, text)
        for line in ("architect runners: parent\n", "arena runners: parent, delegate\n",
                     "arena cross-judge pool: parent\n", "interrogate reviewers: delegate\n"):
            self.assertIn(line, text)
        self.assertNotIn("interrogate reviewers: delegate, delegate, delegate", text)


class SplitTickPlaybooksTest(unittest.TestCase):
    PLAYBOOKS = ROOT / "skills" / "poteto-mode" / "playbooks"

    def test_every_loop_1h_sentence_names_the_conditions(self):
        for name in ("multi-phase-plan.md", "autopilot-full.md", "autopilot-stack.md"):
            text = (self.PLAYBOOKS / name).read_text()
            self.assertIn("pstack-audit-", text, name)
            for line in text.splitlines():
                if "`/loop 1h`" in line:
                    self.assertIn("going wide", line, f"{name}: {line[:80]}")

    def test_no_cron_fallback_is_not_contradicted(self):
        for name in ("autopilot-full.md", "autopilot-stack.md"):
            text = (self.PLAYBOOKS / name).read_text()
            self.assertNotIn("otherwise use the split tick", text, name)
            self.assertNotIn("in place of the split tick", text, name)


class ReviewFixesTest(unittest.TestCase):
    def test_script_goes_to_the_profile_scripts_dir_and_is_checked(self):
        text = skill("pstack-economy")
        self.assertIn("~/.hermes/profiles/<profile>/scripts/", text)
        self.assertIn("cron run", text)
        self.assertNotIn("into `~/.hermes/scripts/`.", text)

    def test_escalations_name_the_program(self):
        prompt = (SKILLS / "pstack-economy" / "audit-watch" / "watcher-prompt.md").read_text()
        self.assertIn("<program>", prompt)
        self.assertIn("<program dir>", prompt)
        text = skill("pstack-economy")
        self.assertIn("plan.txt", text)
        self.assertIn("sed", text)

    def test_on_hermes_panel_rule_defers_to_economy(self):
        text = skill("pstack-on-hermes")
        self.assertIn("pstack-economy decides how many entries run", text)


if __name__ == "__main__":
    unittest.main()
