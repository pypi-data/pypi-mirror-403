**Creating epic in local files:**

```bash
tdd-llm backend create-epic "{name}" "{description}"
```

Optional: specify ID:
```bash
tdd-llm backend create-epic "{name}" "{description}" --id E5
```

This will:
- Create `docs/epics/e{n}-{slug}.md` with the epic content
- Add the epic to `docs/state.json`
- Return JSON with the created epic details
