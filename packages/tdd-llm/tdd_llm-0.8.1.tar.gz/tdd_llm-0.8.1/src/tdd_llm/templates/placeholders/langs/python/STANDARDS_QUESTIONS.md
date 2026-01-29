#### Python-specific:

```
Python-specific conventions:

1. Type hints: What rigor?
   - Strict (mypy strict mode)
   - Standard (typed public API)
   - Minimal (no types)

2. Docstrings: What format?
   - Google style
   - NumPy style
   - Sphinx/reST
   - No docstrings

3. Imports: Organization?
   - isort automatic
   - Manual: stdlib -> third-party -> local
   - No rule

4. Classes: What approach?
   - Dataclasses for data
   - Pydantic for validation
   - Standard classes
```