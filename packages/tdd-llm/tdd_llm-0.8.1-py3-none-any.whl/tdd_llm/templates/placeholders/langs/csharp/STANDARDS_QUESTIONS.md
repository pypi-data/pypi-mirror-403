#### C#-specific:

```
C#-specific conventions:

1. Nullability: How to handle?
   - Strict (nullable enabled, no ! except exceptions)
   - Pragmatic (! allowed when obvious)
   - Disabled

2. Records vs Classes: What rule?
   - Records for data, Classes for services
   - Records everywhere except mutable state
   - Classes everywhere

3. Async: Naming convention?
   - Async suffix mandatory
   - Async suffix except when obvious (GetUser vs GetUserAsync)
   - No suffix

4. Collections: Initialization?
   - Collection expressions (= [])
   - new List<T>()
   - Array.Empty<T>() for immutable
```