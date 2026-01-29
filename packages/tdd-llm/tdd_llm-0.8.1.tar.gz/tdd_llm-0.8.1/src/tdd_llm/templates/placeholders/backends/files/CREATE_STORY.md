**Creating story in local files:**

```bash
tdd-llm backend create-story "{epic_id}" "{title}" "{description}"
```

With acceptance criteria:
```bash
tdd-llm backend create-story "{epic_id}" "{title}" "{description}" --ac "{acceptance_criteria}"
```

Optional: specify task ID:
```bash
tdd-llm backend create-story E1 "Title" "Description" --id T5
```

This will:
- Add a `## T{N}: {title}` section to the epic markdown file
- Return JSON with the created task details
