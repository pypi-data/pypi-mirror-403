Create minimal stubs (`throw new Error()`) so type-check passes. Run `npx tsc --noEmit` then `npm test`.

| Status | Meaning | Action |
|--------|---------|--------|
| `FAIL` (Error thrown) | Stub throws | Correct RED |
| Type error TS2307 | Module missing | Add stub file |
