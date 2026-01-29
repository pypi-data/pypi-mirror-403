**Search with JQL:**
```bash
tdd-llm backend search "project = PROJ AND status = 'In Progress'" --max 20
```

**Common queries:**
- All in epic: `parent = PROJ-100`
- My issues: `assignee = currentUser()`
- Recent: `project = PROJ AND created >= -7d`
- By label: `labels IN (bug, urgent)`
