---
name: pstack-on-hermes
description: >-
  Read first whenever you use any pstack skill (poteto-mode, how, why,
  interrogate, architect, arena, swarm, reflect, tdd, principle-*, ...) on
  Hermes. pstack's text was written for Cursor; this maps its tools, subagents,
  model roles, paths, and missing dependencies onto Hermes.
---

# pstack on Hermes

pstack's skills are upstream text written for Cursor, kept unedited so they stay easy to update. Follow them as written, but apply these substitutions without comment. When a substitution loses something (a missing plugin, one model where the skill wanted several), say so in one line in your report.

## Skills

- A pstack skill named with a slash (`/how`, `/why`, `/tdd`, `/unslop`) or in bold (the **how** skill) is a Hermes skill in this plugin. Load it with `skill_view` under its full name, `agent-plugin-pstack-7171b73f:<name>` (for example `agent-plugin-pstack-7171b73f:how`). Bare names do not resolve.
- Files a skill names relative to itself (`playbooks/bug-fix.md`, `references/rubric.md`) load with `skill_view("agent-plugin-pstack-7171b73f:<skill>", file_path="<relative path>")`. To run a script, find the skill's directory on disk: `plugins/pstack/skills/<skill>/` under the profile's Hermes home.
- When you delegate, give the child the full skill names it must load.
- Cursor's built-in `create-skill` becomes the Hermes skill format: `SKILL.md` with `name` and `description` frontmatter, where `name` matches its directory, placed under the profile's `skills/<category>/<name>/`. Use `skill_manage` or write the file.
- Cursor's built-in `babysit` doesn't exist. Use pstack's Babysit playbook, which is what poteto-mode wants anyway.

## Subagents

- `Task` with any `subagent_type` becomes `delegate_task`, one task per subagent. A child sees only its `goal` and `context`, so put the whole brief there: file paths, scope, the role's prompt file, and the expected output shape. Use `output_schema` when you will parse the result.
- `subagent_type: "poteto-agent"`: begin the child's `context` with the text of `references/poteto-agent.md` (`skill_view("agent-plugin-pstack-7171b73f:pstack-on-hermes", file_path="references/poteto-agent.md")`). Add: "load `agent-plugin-pstack-7171b73f:poteto-mode` and `agent-plugin-pstack-7171b73f:pstack-on-hermes` with skill_view first".
- The **Comment Sicko** agent: delegate with `references/comment-sicko.md` (same skill) as the child's `context`, plus the files or diff in scope.
- `readonly: true`: write "read-only: do not edit, create, or delete files" into the child's goal.
- `is_background` and resume-an-existing-agent: `delegate_task` children always run in the background. Use `delegate_task(action="list"|"steer")` to follow up on one instead of spawning a sibling.

## Models

Hermes has no per-call model. The chat model runs this session, and every `delegate_task` child runs on the profile's `delegation.model` (falling back to the chat model when unset). pstack's model slugs (`grok-4.7-*`, `claude-opus-*`, `gpt-5.6-*`) never apply here. Look up each role in `pstack-models.md` in the profile's home directory (`~/.hermes/profiles/<profile>/`, or `~/.hermes/` for the default profile). `setup-pstack` writes that file. A missing file or role means `delegate`.

- `parent`: do it yourself in this session. Cheap, or needs this conversation's context.
- `delegate`: a `delegate_task` child.
- `profile:<name>`: `message_agent` to that profile, which runs on its own model. This is the only way to get a different model family. It is asynchronous: send it, carry on with the other entries, and fold the reply in when its notification arrives. Never wait or poll.
- **Panel roles** (architect runners, interrogate reviewers, arena runners, the arena cross-judge pool) are lists: one run per entry. When every entry resolves to the same model, say that the panel's model diversity is reduced to prompt diversity. Arena's cross-judge picks an entry whose model differs from yours when one exists.

## Cursor features

- `AskQuestion` becomes `clarify`. poteto-mode's rule still holds: settle what an experiment can settle, and ask only real preference or irreversible calls.
- Cursor's `/loop` becomes Hermes `/loop` (a built-in with the same idea). Ending a wake with `LOOP_COMPLETE` on its own line stops it. For wakes that should outlive the session, use a cron job (`cronjob_manage`).
- **Cursor cloud agent** (one per PR in the shipping and autopilot playbooks) has no Hermes equivalent. Give each unit a local git worktree (`git worktree add`, or `delegation.worktree_isolation: true` in config) and a `delegate_task` child working in it. Pushing and opening PRs still go through `gh`.
- `~/.cursor/rules/pstack-models.mdc` becomes `pstack-models.md` (see Models).
- Agent transcripts (`~/.cursor/projects/<slug>/agent-transcripts/`) become this profile's sessions: `session_search`, or `hermes -p <profile> sessions export --format jsonl …`. The same privacy rule applies: this profile only, never another profile's sessions unless the user asks.
- `.cursor/skills/`, `~/.cursor/skills/`, `~/.cursor/plugins/` become the profile's `skills/` and `plugins/` directories under its Hermes home.
- `.cursor/worktrees/...` and `~/Library/Application Support/Cursor` paths in worktree-cleanup: skip whatever doesn't exist on this machine.

## Missing companion plugins

`cursor-team-kit` is not available on Hermes.

- `deslop` / `/deslop` becomes pstack's `unslop` skill over the diff.
- `control-ui` (browser, Electron, web UI) becomes Hermes browser tools, or `computer_use` for native apps.
- `control-cli` (CLIs, TUIs) becomes the `terminal` tool, driving the real binary.
- A named driver the project already has (a `verify-*` skill) wins over all of these.

## Scripts

`poteto-mode/scripts/` (`watch-pr`, `orch`, `check-plan.mjs`, `worktree-audit.sh`) live under `plugins/pstack/skills/poteto-mode/scripts/` in the profile's Hermes home. They need `bun`, `node`, and `gh` on PATH. Run `bun install` there once before the first use. `worktree-audit.sh` reads Cursor transcript paths and finds nothing on Hermes, so treat its "no transcript" signal as unknown, not as idle.
