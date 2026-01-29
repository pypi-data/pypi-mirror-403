**Add labels:**
```bash
tdd-llm backend update-labels {task_id} --add bug --add urgent
```

**Remove labels:**
```bash
tdd-llm backend update-labels {task_id} --remove wontfix
```

**Add and remove:**
```bash
tdd-llm backend update-labels {task_id} --add reviewed --remove needs-review
```

Note: TDD phases use `set-phase`, not labels.
