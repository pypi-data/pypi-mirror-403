**Listing stories from Jira:**

```bash
tdd-llm backend list-stories {epic_id}
```

Optional: filter by status:
```bash
tdd-llm backend list-stories PROJ-100 --status not_started
```

Returns JSON array:
```json
[
  {
    "id": "PROJ-1234",
    "epic_id": "PROJ-100",
    "title": "Story title",
    "description": "...",
    "status": "not_started",
    "acceptance_criteria": "...",
    "phase": null
  }
]
```
