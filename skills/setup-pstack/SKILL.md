---
name: setup-pstack
description: >-
  Configure how pstack's roles map onto this Hermes profile's models: an
  inventory of every reachable model with its cost class and capability tier,
  the delegation model for subagents, the cron model for scheduled watchers,
  and which roles run in-session, as subagents, or on another profile. Writes
  pstack-models.md in the profile home. Use for /setup-pstack, "configure
  pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack (Hermes)

Write `pstack-models.md` in this profile's home directory: `~/.hermes/profiles/<profile>/`, or `~/.hermes/` for the default profile. The `pstack-on-hermes` and `pstack-economy` skills read it whenever a pstack skill needs a role's model or a model's cost. Load `agent-plugin-pstack-7171b73f:pstack-on-hermes` and `agent-plugin-pstack-7171b73f:pstack-economy` with `skill_view` first if you have not.

## 1. Load the current state

- The profile's chat model: `hermes -p <profile> config get model`.
- Its subagent model: `hermes -p <profile> config get delegation.model` and `delegation.provider`. Empty means children use the chat model.
- The teammates and their models: `hermes profile list`. These are candidates for `profile:<name>` entries.
- If `pstack-models.md` exists, read it, and treat its inventory and role values as the current choices. Drop any role line whose role is not in the table in step 5, and tell the user which lines you dropped.

## 2. Detect the models

A model is available only if the provider's model list shows it, and the providers' lists are cached in `provider_models_cache.json` in the profile home. Never write a model you have not confirmed. If the cache is empty or stale, ask the user to run `hermes model --refresh`, or to paste the model names they have. Include the teammates' models from step 1.

## 3. Propose the inventory

For each detected model, propose these values and mark them as proposals:

- **Cost class**, from the provider type:
  - a local or self-hosted base URL (Ollama, LM Studio, vLLM, llama.cpp) is `self-hosted`;
  - a plan login through OAuth (for example the Codex or ChatGPT plan, or a Claude subscription) is `subscription`;
  - an API key is `per-token`.

  When unsure, ask.
- **Tier**, from what you know of the model:
  - `frontier`: best reasoning and judgment;
  - `strong`: solid coding and review;
  - `light`: mechanical reading, searching and summarizing.
- **tools:** `yes` if the model handles tool calls reliably. For each `self-hosted` model, ask whether the user has found its tool calling reliable.

## 4. Choose, then confirm

Recommend the slots, then use `clarify` once to confirm the inventory and the slots together:

- **parent** (the chat model): the best `subscription` model.
- **delegate** (`delegation.model`): the cheapest model rated `strong` or better, preferring `self-hosted`, then `subscription`. Every subagent runs here, so this slot decides most of the spend. Also offer `unset` (children use the chat model).
- **cron**: the best `self-hosted` model with `tools: yes`, if any. It runs the split audit tick's watcher. Say plainly that self-hosted `light` models help only as the `cron` model or through a teammate profile, never as an inline subagent.
- **Second-opinion profiles:** offer each teammate on a different model as a `profile:<name>` panel entry. Warn that these replies arrive asynchronously and cost that bot a turn.

Then show the full role table with its values, and ask whether to accept it or change specific roles. Each role takes `parent`, `delegate`, or `profile:<name>`. A panel role takes a list. `pstack-economy` uses only the first entry of a duplicated-work panel (the first two for arena runners) unless the user approves going wide, so extra entries are the go-wide width.

## 5. Write

Apply the subagent model first. Changing it is a config write, so say that before doing it:

```
hermes -p <profile> config set delegation.model <model>
hermes -p <profile> config set delegation.provider <provider>
```

Then overwrite `pstack-models.md` completely, so re-runs stay idempotent:

```
# Models this profile can reach (re-run setup-pstack when they change)
# model | provider | cost class | tier | tools | executor
<model> | <provider> | <self-hosted|subscription|per-token> | <frontier|strong|light> | <yes|no> | <parent|delegate|profile:<name>|cron|(not assigned)>

# pstack role → executor for this Hermes profile. Read by the pstack-on-hermes and pstack-economy skills.
# parent = this session's chat model · delegate = delegate_task child (delegation.model) · profile:<name> = message_agent to that bot
# chat model: <model> · delegation.model: <model or "unset (= chat model)"> · cron model: <model or "none">
feature, refactoring: delegate
bug-fix: delegate
perf-issue: delegate
hillclimb: delegate
judgment and prose: parent
hardest tasks: parent
how explorer: delegate
how explainer: parent
why investigators: delegate
why synthesizer: parent
reflect tooling: delegate
reflect judgment, divergent, synthesizer: parent
arena runners: parent, delegate
arena cross-judge pool: parent
swarm workers: delegate
architect runners: parent
interrogate reviewers: delegate
```

These are the defaults. Replace them with whatever the user confirmed. Mark at most one model `cron`.

## 6. Confirm

Read the file back, and read `delegation.model` back with `config get`. Tell the user what changed. New sessions pick up the delegation model. Re-running this skill updates both.

## 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof: a `verify-*` skill or an existing harness. If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with create-verification-skill." On yes, load and follow `agent-plugin-pstack-7171b73f:create-verification-skill`. On no, move on without pushing.
