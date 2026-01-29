**Listing epics from local files:**

Read `docs/state.json` to get the list of epic IDs:
```json
{
  "epics": {
    "E1": { "status": "in_progress", "completed": [...] },
    "E2": { "status": "not_started", "completed": [] }
  }
}
```

For each epic, read its file from `docs/epics/e{n}-*.md` to get the name and description.
