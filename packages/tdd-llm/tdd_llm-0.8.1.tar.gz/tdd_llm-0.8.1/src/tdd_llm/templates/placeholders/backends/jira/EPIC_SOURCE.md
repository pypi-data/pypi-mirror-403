**Epic source: Jira**

Fetch epic and all its tasks using CLI:

```bash
tdd-llm backend get-epic {epic_id}
```

Returns JSON:
```json
{
  "id": "PROJ-100",
  "name": "Epic name",
  "description": "Epic description/objective",
  "status": "in_progress",
  "tasks": [
    {
      "id": "PROJ-1234",
      "epic_id": "PROJ-100",
      "title": "Task title",
      "description": "...",
      "status": "completed",
      "acceptance_criteria": "...",
      "phase": null
    }
  ]
}
```

Fields are mapped from Jira:
- Epic `summary` → name
- Epic `description` → description
- Epic workflow status → status
- Child issues (Stories/Tasks) → tasks array
