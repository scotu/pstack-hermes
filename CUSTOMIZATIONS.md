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
