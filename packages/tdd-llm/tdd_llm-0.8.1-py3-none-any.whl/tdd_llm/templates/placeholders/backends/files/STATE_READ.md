**Loading state from local files:**

If `docs/state.json` doesn't exist -> display:
```
Project not initialized. Run `/tdd:init:1-project` first.
```

If `.tdd-state.local.json` doesn't exist -> create with current epic (first `in_progress` or `not_started`).