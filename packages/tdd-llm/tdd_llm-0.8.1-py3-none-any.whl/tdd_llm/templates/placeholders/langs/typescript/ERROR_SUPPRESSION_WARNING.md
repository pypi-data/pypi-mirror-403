**NEVER suppress errors to make tests compile:**
- No `// @ts-ignore`
- No `// @ts-expect-error`
- No `// eslint-disable`
- No `as any` casts to bypass type errors

These suppressions are easily forgotten and hide real problems. Let tests fail naturally with thrown `Error`.
