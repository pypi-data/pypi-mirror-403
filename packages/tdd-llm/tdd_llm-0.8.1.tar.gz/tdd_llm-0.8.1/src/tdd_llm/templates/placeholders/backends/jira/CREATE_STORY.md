**Creating story in Jira:**

```bash
tdd-llm backend create-story "{epic_id}" "{title}" "{description}"
```

With acceptance criteria:
```bash
tdd-llm backend create-story "{epic_id}" "{title}" "{description}" --ac "{acceptance_criteria}"
```

This will:
- Create a Story issue linked to the Epic in Jira
- Return JSON with the created task details including Jira key

Returns:
```json
{
  "id": "PROJ-1234",
  "epic_id": "PROJ-100",
  "title": "Story title",
  "description": "...",
  "status": "not_started",
  "acceptance_criteria": "...",
  "phase": null
}
```
