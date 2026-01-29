**Get available status transitions:**
```bash
tdd-llm backend get-transitions {task_id}
```

Returns JSON array:
```json
[
  {"id": "21", "name": "Start Progress", "to_status": "In Progress"},
  {"id": "31", "name": "Done", "to_status": "Done"}
]
```

Use this before `update-status` to verify the transition is allowed.
