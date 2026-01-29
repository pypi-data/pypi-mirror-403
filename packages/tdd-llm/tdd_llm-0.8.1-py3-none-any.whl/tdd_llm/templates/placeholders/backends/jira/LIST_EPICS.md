**Listing epics from Jira:**

```bash
tdd-llm backend list-epics
```

Optional: filter by status:
```bash
tdd-llm backend list-epics --status in_progress
```

Returns JSON array:
```json
[
  {
    "id": "PROJ-100",
    "name": "Epic name",
    "description": "...",
    "status": "in_progress",
    "tasks": [...]
  }
]
```
