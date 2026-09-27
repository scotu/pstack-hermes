---
name: setup-pstack
description: >-
  Configure how pstack's roles map onto this Hermes profile's models: the
  delegation model for subagents, and which roles run in-session, as subagents,
  or on another profile. Writes pstack-models.md in the profile home. Use for
  /setup-pstack, "configure pstack models", "pstack budget", or changing
  pstack's model choices.
---

# Setup pstack (Hermes)

Write `pstack-models.md` in this profile's home directory: `~/.hermes/profiles/<profile>/`, or `~/.hermes/` for the default profile. The `pstack-on-hermes` skill reads it whenever a pstack skill needs a role's model. Load `agent-plugin-pstack-7171b73f:pstack-on-hermes` with `skill_view` first if you have not.

## 1. Load the current state

- The profile's chat model: `hermes -p <profile> config get model`.
- Its subagent model: `hermes -p <profile> config get delegation.model` and `delegation.provider`. Empty means children use the chat model.
- The teammates and their models: `hermes profile list`. These are candidates for `profile:<name>` entries.
- If `pstack-models.md` exists, read it and treat its values as the current choices. Drop any line whose role is not in the table in step 4, and tell the user which lines you dropped.

## 2. Detect the models

A model is available only if the provider's model list shows it, and the providers' lists are cached in `provider_models_cache.json` in the profile home. Never write a model you have not confirmed. If the cache is empty or stale, ask the user to run `hermes model --refresh`, or to paste the model names they have.

## 3. Choose, then confirm

Use `clarify` for each choice:

- **Subagent model** (`delegation.model`): keep it, or pick a detected model. A model that differs from the chat model gives pstack's reviewers a second opinion. Also offer `unset` (children use the chat model).
- **Second-opinion profiles**: offer each teammate on a different model as a `profile:<name>` panel entry. Warn that these replies arrive asynchronously and cost that bot a turn.

Show the full role table with its values, and ask whether to accept it or change specific roles. Each role takes `parent`, `delegate`, or `profile:<name>`. A panel role takes a list, and its length sets the fan-out.

## 4. Write

Apply the subagent model first. Changing it is a config write, so say that before doing it:

```
hermes -p <profile> config set delegation.model <model>
hermes -p <profile> config set delegation.provider <provider>
```

Then overwrite `pstack-models.md` completely, so re-runs stay idempotent:

```
# pstack role → executor for this Hermes profile. Read by the pstack-on-hermes skill.
# parent = this session's chat model · delegate = delegate_task child (delegation.model) · profile:<name> = message_agent to that bot
# chat model: <model> · delegation.model: <model or "unset (= chat model)">
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
arena runners: parent, delegate, delegate
arena cross-judge pool: delegate
swarm workers: delegate
architect runners: parent, delegate, delegate
interrogate reviewers: delegate, delegate, delegate
```

These are the defaults. Replace them with whatever the user confirmed.

## 5. Confirm

Read the file back, and read `delegation.model` back with `config get`. Tell the user what changed. New sessions pick up the delegation model. Re-running this skill updates both.

## 6. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof: a `verify-*` skill or an existing harness. If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with create-verification-skill." On yes, load and follow `agent-plugin-pstack-7171b73f:create-verification-skill`. On no, move on without pushing.
