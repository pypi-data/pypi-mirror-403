**Listing stories from local files:**

Read the epic file `docs/epics/e{n}-*.md` and parse task sections:
- `## T1: Title` - Task header
- Content until next `## T{N}:` or `## Completion`

Or use CLI:
```bash
tdd-llm backend list-stories E1
```

Optional: filter by status:
```bash
tdd-llm backend list-stories E1 --status not_started
```
