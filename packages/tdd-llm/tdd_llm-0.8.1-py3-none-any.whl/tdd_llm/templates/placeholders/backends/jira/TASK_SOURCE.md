**Task source: Jira**

Fetch task details using CLI:

```bash
tdd-llm backend get-task {task_id}
```

Returns JSON:
```json
{
  "id": "PROJ-1234",
  "epic_id": "PROJ-100",
  "title": "Task title",
  "description": "Full description...",
  "status": "not_started",
  "acceptance_criteria": "AC text or null",
  "phase": "test"
}
```

Task identification:
- epic_id: Jira epic key (e.g., `PROJ-100`)
- task_id: Jira story key (e.g., `PROJ-1234`)

Fields are mapped from Jira:
- `summary` → title
- `description` → description
- `status` → mapped from Jira workflow status
- `acceptanceCriteria` or custom field → acceptance_criteria
- TDD labels (`tdd:test`, etc.) → phase
