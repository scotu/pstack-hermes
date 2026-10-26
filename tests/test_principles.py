"""Whole-tree guards for the Principles in CUSTOMIZATIONS.md: every skill file, including ones upstream adds later."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
ON_HERMES = (SKILLS / "pstack-on-hermes" / "SKILL.md").read_text()
# The policy files themselves name the go-wide forms on purpose.
POLICY = {SKILLS / "pstack-economy", SKILLS / "pstack-on-hermes", SKILLS / "setup-pstack"}
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def docs():
    for md in sorted(SKILLS.rglob("*.md")):
        if not any(md.is_relative_to(p) for p in POLICY):
            yield md, md.read_text()


def lines_with(pattern: str):
    rx = re.compile(pattern)
    for md, text in docs():
        for n, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                yield f"{md.relative_to(ROOT)}:{n}", line


class Guard(unittest.TestCase):
    def assertNone(self, problems):
        self.assertFalse(problems, "\n" + "\n".join(problems))


class EconomyPrincipleTest(Guard):
    """P-1: duplicated work and recurring ticks run lean unless the operator approves going wide."""

    def test_hourly_root_tick_only_when_going_wide(self):
        self.assertNone([w for w, line in lines_with(r"/loop 1h") if not re.search(r"(?i)going wide", line)])

    def test_ten_lanes_only_when_going_wide(self):
        self.assertNone([w for w, line in lines_with(r"(?i)\bten (live )?lanes\b")
                         if not re.search(r"(?i)going wide", line)])


class HermesPrincipleTest(Guard):
    """P-2: everything a skill points at exists on Hermes or has a mapping in pstack-on-hermes."""

    def test_relative_links_resolve(self):
        # URLs and template placeholders such as (url) are not file links.
        self.assertNone([f"{md.relative_to(ROOT)}: {target}" for md, text in docs() for target in LINK.findall(text)
                         if not re.match(r"^[a-z]+:", target) and re.search(r"[./]", target)
                         and not (md.parent / target).exists()])

    def test_named_skills_exist_or_are_mapped(self):
        skills = {p.name for p in SKILLS.iterdir() if p.is_dir()}
        self.assertNone([f"{md.relative_to(ROOT)}: {name}" for md, text in docs()
                         for name in re.findall(r"\*\*([a-z0-9][a-z0-9-]+)\*\* skill", text)
                         + re.findall(r"`/([a-z0-9][a-z0-9-]+)`", text)
                         if name not in skills and not re.search(rf"`/?{re.escape(name)}`", ON_HERMES)])

    def test_companion_plugins_are_mapped(self):
        self.assertNone([f"{md.relative_to(ROOT)}: {plugin}" for md, text in docs()
                         for plugin in re.findall(r"from the `([\w-]+)` plugin", text) if f"`{plugin}`" not in ON_HERMES])

    # Cursor-only concepts upstream has used, and the text in pstack-on-hermes that maps each.
    CURSORISMS = {
        r"reasoning level": "**Reasoning level and speed.**",
        r"agent'?s store": "**The agent's store**",
        r'environment: "cloud"|cloud_base_branch|cloud VM': "or cloud VM",
        r"\bmcps/": "`mcps/`",
        r"`(cursor-grok|composer)-": "`composer-*`",
    }

    def test_cursorisms_are_mapped(self):
        self.assertNone([f"{md.relative_to(ROOT)}: {pattern}" for pattern, mapping in self.CURSORISMS.items()
                         if mapping not in ON_HERMES for md, text in docs() if re.search(pattern, text)])

    def test_subagent_types_are_mapped(self):
        refs = SKILLS / "pstack-on-hermes" / "references"
        self.assertNone([f"{md.relative_to(ROOT)}: {kind}" for md, text in docs()
                         for kind in re.findall(r'subagent_type[^a-z"]*"([a-z-]+)"', text)
                         if not (refs / f"{kind}.md").exists()])


if __name__ == "__main__":
    unittest.main()
