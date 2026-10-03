# pstack customizations

This file lists the personal changes made on top of the Hermes port of upstream pstack. It exists only on the `main` branch.

- `upstream` holds the exact build output from agent-plugin-factory. Never edit it by hand.
- `main` is `upstream` plus the changes listed here. Hermes installs this branch.
- `git diff upstream main --` shows the full set of changes. The `--` is needed because macOS sees the `UPSTREAM` file and the `upstream` branch as the same name.
- Upstream is brought in by `python3 -m factory sync pstack` (scotu/agent-plugin-factory) with a merge. Never rebase or rewrite `main`, because `hermes plugins update` only fast-forwards.

Each change has one entry. The commits that implement or fix it start with its ID, for example `C-001: …`. When resolving a merge conflict, re-apply the **Intent**. Don't try to preserve the old wording.

Status is `active` or `retired`. Retire an entry when upstream covers it or it is no longer wanted, and keep it in the file as history.

Entry format:

```
## C-NNN — <skill>: <short title>  [active]
Intent: what must be true afterwards, written so it survives upstream rewording.
Why: the reason for the change.
Touches: skills/<name>/SKILL.md, ...
Check: how to confirm it still holds.
```

<!-- entries below, newest last -->

## C-001 — pstack-economy: lean-by-default spending policy  [active]
Intent: a pstack-economy skill defines lean widths for duplicated agent work (divided work untouched), per-task go-wide approval with a cost statement, tier routing over the setup-pstack inventory with the per-token rule, and the split audit tick procedure.
Why: upstream assumes cheap LLM calls; this profile pays through subscription quotas, self-hosted and per-token models.
Spec: https://github.com/scotu/agent-plugin-factory/blob/main/docs/specs/2026-10-04-pstack-economy-design.md
Touches: skills/pstack-economy/SKILL.md, tests/test_skills.py
Check: python3 -m unittest tests.test_skills passes

## C-002 — pstack-on-hermes: route every fan-out through pstack-economy  [active]
Intent: pstack-on-hermes, which every pstack skill loads first, tells the agent to load and apply pstack-economy before any fan-out, loop, or role-model choice.
Why: one hook makes the economy policy reach all 47 skills without editing each.
Spec: https://github.com/scotu/agent-plugin-factory/blob/main/docs/specs/2026-10-04-pstack-economy-design.md
Touches: skills/pstack-on-hermes/SKILL.md
Check: python3 -m unittest tests.test_skills.OnHermesHookTest passes

## C-003 — setup-pstack: model inventory and lean panel defaults  [active]
Intent: setup-pstack proposes and confirms an inventory of every reachable model (cost class, tier, tools, executor), recommends parent/delegate/cron slots by cost, and writes lean defaults for duplicated-work panels (architect runners: parent; arena runners: parent, delegate; arena cross-judge pool: parent; interrogate reviewers: delegate).
Why: routing by cost needs to know each model's cost class and capability, and old 3-entry panel defaults made duplicated work the norm.
Spec: https://github.com/scotu/agent-plugin-factory/blob/main/docs/specs/2026-10-04-pstack-economy-design.md
Touches: skills/setup-pstack/SKILL.md
Check: python3 -m unittest tests.test_skills.SetupInventoryTest passes

## C-004 — poteto-mode: one live lane per distinct check  [active]
Intent: multi-phase plans run one live-verification lane per distinct check (no repeats) and state "(N lanes)"; ten lanes only when going wide. check-plan.mjs accepts both phrasings and requires lanes numbered exactly 1..N.
Why: ten lanes repeat about five distinct checks; the repeats spend quota without adding coverage.
Spec: https://github.com/scotu/agent-plugin-factory/blob/main/docs/specs/2026-10-04-pstack-economy-design.md
Touches: skills/poteto-mode/scripts/check-plan.mjs, skills/poteto-mode/playbooks/multi-phase-plan.md
Check: python3 -m unittest tests.test_check_plan passes; grep -c "Ten lanes" skills/poteto-mode/playbooks/multi-phase-plan.md prints 1

## C-005 — poteto-mode: split audit tick instead of an hourly root loop  [active]
Intent: programs arm a split audit tick (free self-hosted cron watcher pstack-audit-<program> running pstack-audit-watch.py, escalating to the root, which does the judgment) when pstack-models.md has a cron model; otherwise no tick (audit on report-back); the hourly /loop 1h root tick only when going wide. check-plan.mjs accepts /loop 1h or pstack-audit- as the program marker.
Why: an hourly tick on a paid model re-audits unchanged state; mechanical liveness checks are free on a self-hosted model, and judgment is needed only when something changed.
Spec: https://github.com/scotu/agent-plugin-factory/blob/main/docs/specs/2026-10-04-pstack-economy-design.md
Touches: skills/poteto-mode/playbooks/multi-phase-plan.md, skills/poteto-mode/playbooks/autopilot-full.md, skills/poteto-mode/playbooks/autopilot-stack.md, skills/poteto-mode/scripts/check-plan.mjs, skills/pstack-economy/audit-watch/
Check: python3 -m unittest tests.test_check_plan tests.test_audit_watch tests.test_skills.SplitTickPlaybooksTest passes
