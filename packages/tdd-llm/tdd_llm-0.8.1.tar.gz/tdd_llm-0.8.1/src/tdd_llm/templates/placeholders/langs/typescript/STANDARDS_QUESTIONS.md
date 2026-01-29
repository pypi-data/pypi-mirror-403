#### TypeScript-specific:

```
TypeScript-specific conventions:

1. Types: What rigor?
   - Strict (no any, no implicit any)
   - Pragmatic (any allowed as last resort)
   - Loose

2. Imports: What order?
   - Auto (prettier/eslint organizes)
   - Manual: external -> internal -> relative
   - No rule

3. Functions: What syntax to prefer?
   - Arrow functions everywhere
   - function for exports, arrow for callbacks
   - No preference

4. Null handling: What approach?
   - Strict null checks + optional chaining
   - Assertions (!) allowed
   - No null, undefined only
```