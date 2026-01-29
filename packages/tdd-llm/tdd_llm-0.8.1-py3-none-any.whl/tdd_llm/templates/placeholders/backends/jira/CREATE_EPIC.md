**Creating epic in Jira:**

```bash
tdd-llm backend create-epic "{name}" "{description}"
```

This will:
- Create an Epic issue in the configured Jira project
- Return JSON with the created epic details including Jira key

Returns:
```json
{
  "id": "PROJ-100",
  "name": "Epic name",
  "description": "...",
  "status": "not_started",
  "tasks": []
}
```
