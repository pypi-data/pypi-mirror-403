**Loading state from Jira:**

Get current workflow state using CLI:

```bash
tdd-llm backend status
```

Returns JSON:
```json
{
  "backend": "jira",
  "current_epic": {
    "id": "PROJ-100",
    "name": "Epic name",
    "status": "in_progress",
    "tasks": [...]
  },
  "current_task": {
    "id": "PROJ-1234",
    "title": "...",
    "phase": "test"
  },
  "epics": [...]
}
```

If no active epic: `current_epic` and `current_task` will be null.

Local session state is cached in `.tdd-state.local.json` for phase tracking.

To get the next task to work on:
```bash
tdd-llm backend next-task {epic_id}
```
