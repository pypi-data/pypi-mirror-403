**NEVER suppress errors to make tests compile:**
- No `#pragma warning disable`
- No `[SuppressMessage]` attributes
- No `#nullable disable`

These suppressions are easily forgotten and hide real problems. Let tests fail naturally with `NotImplementedException`.
