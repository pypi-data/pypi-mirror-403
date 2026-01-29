**Updating state in local files:**

Update `docs/state.json`:

```json
{
  "epics": {
    "{epic_id}": {
      "status": "in_progress",
      "completed": [..., "{task_id}"]
    }
  }
}
```

If all epic tasks completed: set `status` = "completed".