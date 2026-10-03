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


if __name__ == "__main__":
    unittest.main()
