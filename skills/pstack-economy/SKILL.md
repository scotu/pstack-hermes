---
name: pstack-economy
description: >-
  Spending rules for pstack on this profile. Lean by default: cut duplicated
  agent work (races, same-prompt panels, repeated lanes, polling loops), keep
  divided work, ask before going wide, and route each role to the cheapest
  executor that meets its tier. Apply before any pstack fan-out, loop, or
  role-model choice.
---

# pstack economy

Upstream pstack assumes model calls are cheap. On this profile they are not. Apply these rules whenever a pstack skill would spawn more than one agent, arm a loop, or pick a model for a role. They override the widths that pstack's skills state. They never weaken a check. They only limit how many copies of the same check run.

## Duplicated and divided work

- **Divided work:** several agents each do a different piece. Examples are swarm coverage slices, `how` explorers on distinct angles, `why` investigators per evidence category, `reflect`'s three lenses, and poteto-mode delegates. Run it as the skill says, with subagents as needed.
- **Duplicated work:** several agents do the same piece. Examples are races, best-of, several candidates for one artifact, several reviewers with one prompt, repeated verification lanes, and periodic re-checks. Run the lean width below.
- **Free-executor exemption.** Duplicated work may run on a `self-hosted` executor (see Routing) when its output stays advisory and you read only a short report. Advisory means it never merges, dispatches, stands down, or decides.

For a duplicated-work panel role in `pstack-models.md` (architect runners, arena runners, arena cross-judge pool, interrogate reviewers), use only the first entry, or the first two for arena runners, unless the user approved going wide. Profiles set up before this skill may list three entries; that is the go-wide width, not the default.

## Lean widths

| Pattern | Lean default | Go wide (upstream) |
|---|---|---|
| swarm, coverage slices | one worker per slice, no cap | — |
| swarm, races and best-of | no race, one worker per arm | upstream races |
| architect | one design by the parent that names the alternatives it rejected and why, with no runners | 2 to 3 runners |
| arena | 2 candidates on different executors or model families, judged by the parent against the rubric, with no separate cross-judge | 3 candidates plus a cross-judge |
| interrogate | 1 reviewer on an executor whose model differs from the author's, plus optionally one free advisory reviewer on a `self-hosted` executor | one reviewer per configured model |
| reflect, why, how, poteto-mode subagents | as upstream (divided work) | — |
| live verification | one lane per distinct check, with no repeats | ten lanes |
| autopilot audit tick | the split audit tick when `pstack-models.md` has a `cron` model, otherwise none (audit when owners report back or when asked) | full hourly `/loop 1h` tick on the root |
| second-opinion profiles (`message_agent`) | only when the user asks | as configured |

Event-driven waits (a `/loop` that watches CI or a merge) stay as upstream. They wait for something to happen; they don't repeat work.

## Going wide

Before any step wider than lean, post one message that names:
- the pattern;
- the width you want and the lean width it replaces;
- the executors involved, with their models and cost classes from `pstack-models.md`;
- a rough relative cost, for example "about 3x one pass; 2 runs are subscription, 1 is per-token".

Then wait for an explicit yes. "Go wide", "spare no expense", or a named width for the current task ("arena with 3") approves that task only. Approval never carries over to later tasks or sessions. When nobody is watching (autopilot, figure-it-out, the user stepped away), stay lean, and list in your report the steps you would have widened.

## Routing

`pstack-models.md` starts with an inventory: model, provider, cost class (`self-hosted`, `subscription`, `per-token`), tier (`frontier`, `strong`, `light`), `tools` (yes or no), and executor (`parent`, `delegate`, `profile:<name>`, `cron`). If the inventory is missing, treat `parent` and `delegate` as unknown cost, say so once, and suggest running `agent-plugin-pstack-7171b73f:setup-pstack`.

- **Which work needs which tier:**
  - `light`: exploration and grep sweeps, running tests and reporting results, reading transcripts or logs.
  - `strong`: code-writing delegates, reviewers, investigators.
  - `frontier`: judgment, synthesis, the hardest tasks, final picks and verdicts.
- Route each role to the cheapest executor whose model meets its tier. At equal tier, prefer `self-hosted`, then `subscription`, then `per-token`.
- **Per-token rule:** never pick a `per-token` executor unless it is the only executor at the tier the role needs. When a role would land on one, say so before spending.
- A `profile:<name>` executor is used only where the role table names it, never implicitly. It is asynchronous and costs that bot a turn.
- `self-hosted` executors, including the `cron` model, may take duplicated or scheduled work under the free-executor exemption.

## Split audit tick

Use this in place of the hourly `/loop 1h` tick when a program arms its audit tick and `pstack-models.md` has a `cron` model with `tools: yes`. The watcher does the mechanical checks for free. You do the judgment. Below, the profile home is `~/.hermes/profiles/<profile>/`, or `~/.hermes/` for the default profile.

1. **Program dir.** Create `<profile home>/pstack-programs/<program>/`, outside any repo checkout. Write `plan.txt` there: the plan path, the execution playbook, and the session to report to.
2. **`owners.tsv`.** Write it in the program dir, tab-separated, with this header: `owner remote repo branch pr expected_minutes started_at`.
   - `remote` is the git URL, and `repo` is `owner/name` for `gh`.
   - `pr` is the PR number, or `-` before the PR exists.
   - `expected_minutes` and `started_at` (epoch seconds) are integers.
   - Blank rows and `#` rows are ignored.
   - Update it whenever an owner spawns, opens its PR, or finishes.
3. **Install the script and prompt.** Hermes runs a profile's cron scripts from that profile's own `scripts/` folder: `~/.hermes/profiles/<profile>/scripts/`, or `~/.hermes/scripts/` for the default profile.
   - Copy `audit-watch/pstack-audit-watch.py` there from this skill's folder (`plugins/pstack/skills/pstack-economy/` under the profile home).
   - Fill the prompt: `sed -e "s|<program dir>|$DIR|g" -e "s|<program>|$NAME|g" audit-watch/watcher-prompt.md > "$DIR/watcher-prompt.md"`.
   - Hermes strips `GH_TOKEN` and `GITHUB_TOKEN` from cron scripts, so `gh` must be logged in through its keyring (`gh auth status`).
4. **Arm the watcher.** The cron job is named `pstack-audit-<program>`:
   ```
   hermes -p <profile> cron create 15m "$(cat <program dir>/watcher-prompt.md)" \
     --name pstack-audit-<program> --monitor-script pstack-audit-watch.py \
     --workdir <program dir> --model <cron model> --provider <its provider> --pin \
     --deliver bot-chat:<profile> --failure-deliver local
   ```
   The script runs every 15 minutes. The watcher model runs only when the script's output changes, and replies `[SILENT]` unless something needs you.
5. **Check that it works.** Failures are delivered locally, so a broken watcher is otherwise invisible.
   - Run `hermes -p <profile> cron run pstack-audit-<program>` once.
   - Confirm with `hermes -p <profile> cron list` (or `cron runs`) that the run succeeded and the monitor script produced owner lines, not "monitor source failed".
   - If it failed, fix it (script path, `gh` login, `owners.tsv`), or remove the job and fall back to auditing on report-back. Never leave a broken watcher armed.
6. **On an escalation.** A watcher message names the program, its program dir, and the owners concerned. Read `<program dir>/plan.txt` and `owners.tsv`, then run the judgment half of the playbook's audit tick for those owners only:
   - re-read the playbook from trunk;
   - fix drift;
   - stand down and replace stuck owners;
   - handle failed checks and bot comments.
7. **Teardown.** When no delegated work is left, run `hermes -p <profile> cron remove pstack-audit-<program>`, then delete the program dir and its copied script.

Without a `cron` model, arm no tick. Audit when an owner reports back and when the user asks. Arm the hourly `/loop 1h` tick only when the user approves going wide.
