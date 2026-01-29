**NEVER suppress errors to make tests compile:**
- No `# type: ignore`
- No `# noqa`
- No `# pylint: disable`

These suppressions are easily forgotten and hide real problems. Let tests fail naturally with `NotImplementedError`.
