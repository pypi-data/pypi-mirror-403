**Archive context: Jira**

Add a completion summary to the Jira story. Extract from `.tdd-context.md`:

**Summary format:**
```
## Task Completed

### Objective
{One sentence from Objective section}

### Key Decisions
{2-4 bullet points from Design/Logic sections - architectural choices, patterns used, tradeoffs made}

### Changes
**Created:** {list of new files}
**Modified:** {list of modified files}

### Quality
- Coverage: {final %} ({delta from baseline})
- Tests: {count} passed

### Pull Request
{PR link from context or "Merged via PR #N"}
```

Add the summary as a Jira comment:
```bash
tdd-llm backend add-comment {task_id} "{formatted_summary}"
```

Then clean up the local context file:
```bash
rm .tdd-context.md
```

The summary keeps technical context with the story in Jira rather than creating documentation files in the repository.
