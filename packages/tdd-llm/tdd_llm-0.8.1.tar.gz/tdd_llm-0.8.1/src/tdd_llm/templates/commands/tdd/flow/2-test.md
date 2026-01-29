# /tdd:flow:2-test

You are a paranoid QA Engineer. Your goal is to break future code. Write meaningful tests (RED phase).

## Instructions

### 1. Load context

Read in parallel:
- `.tdd-context.md` (current task context)
- `.tdd-epic-context.md` (epic context: interfaces, patterns)
- `docs/dev/standards.md` (formatting conventions)

Verify `.tdd-state.local.json`: `current.phase` must be "test".

### 2. Capture coverage baseline

Run coverage command from project standards. Add to `.tdd-context.md` after `## Conventions`:

```markdown
## Baseline
- Coverage: [X.X]%
- Tests: [N] tests
```

### 3. Determine test scope

**First, identify ALL classes impacted by the task:**
- Services / Business logic
- ViewModels / Presenters
- UI components (if testable)
- Data access / Repositories
- Any helper or utility classes

Each impacted class needs its own test coverage.

**Test Pyramid - Apply layers based on task:**

| Layer | Scope | Skip when |
|-------|-------|-----------|
| **Unit** | Single function/class in isolation | Never |
| **Integration** | Multiple components, real dependencies | No cross-component interaction |
| **Architecture** | Structure, dependencies, conventions | S tasks, no arch rules defined |
| **Performance** | Timeout, memory, scalability | S tasks, no perf requirements |

**Test Tracks - Apply to each layer:**

| Track | Minimum |
|-------|---------|
| **Happy Path** | 1 per behavior |
| **Edge Cases** | 1 per input parameter |
| **Error Handling** | 1 per error type |

**Ratio enforcement (STRICT):**
- Happy Path: **≤ 40%** of total tests
- Edge + Error: **≥ 50%** of total tests

### 4. Write unit tests

**Load from .tdd-context.md:**
- Test specs (section `Tests`)
- Conventions (section `Conventions`) - read mentioned examples for patterns

**Requirements:**
- Naming: `Action_Context_ExpectedResult`
- Structure: Arrange / Act / Assert
- Cover behaviors from specs, not implementation details

**Quality rules (STRICT):**

| Rule | Bad | Good |
|------|-----|------|
| No lazy assertions | `assert result is not None` | `assert result.value == 42` |
| Depth over breadth | 10 shallow tests | 3 deep tests |
| Test sad paths harder | Only valid inputs | null, empty, MAX_INT, negative |

**What to test beyond happy path:**
- Empty/None/null inputs
- Boundary values (0, -1, MAX_INT, empty string)
- Dependency failures (throws, timeout, garbage)
- Idempotency (call twice = same result?)
- Concurrency (if applicable)

**Mocking:** Use standard mocking library (unittest.mock, jest.fn, Moq). Prefer mocks over manual Fake classes unless state must persist across calls.

### 5. Write integration tests

**When required:** Task touches multiple components OR modifies data flow.

{{INTEGRATION_TEST_EXAMPLE}}

### 6. Write architecture tests (M, L tasks)

**When required:** Task is Medium or Large complexity, project has architectural rules.

{{ARCH_TEST_EXAMPLE}}

### 7. Write performance tests (critical paths)

**When required:** Task affects data processing, O(n²)+ algorithms, or I/O-bound operations.

{{PERF_TEST_EXAMPLE}}

### 8. Verify RED state

{{RED_STRATEGY}}

**Critical distinction:**
- **Syntax/Import error** (prevents test collection) → Create minimal stubs (empty classes/functions that throw)
- **Test FAILED** (assertion failed, NotImplementedError) → Correct RED state

{{ERROR_SUPPRESSION_WARNING}}

### 9. Completeness checklist

Before marking RED complete:

- [ ] **All impacted classes have tests**
- [ ] Every public method has ≥1 Happy Path test
- [ ] Every input parameter has ≥1 Edge Case test
- [ ] Every exception type has ≥1 Error Handling test
- [ ] Component interactions have Integration tests (if multi-component)
- [ ] Happy Path ≤ 40%, Edge + Error ≥ 50%
- [ ] Architecture tests exist (M, L only, if rules defined)

**If any box unchecked → add missing tests.**

### 10. Update .tdd-context.md

Add after `## Tests`:

```markdown
### RED Result
- Tests: [N] unit / [Y] integration / [Z] arch / [W] perf
- Ratio: [X]% happy / [Y]% edge+error
- Status: RED (all failing as expected)
```

### 11. Finalize

Create test files listed in `.tdd-context.md` section "Files > Create".

Determine next phase (check `skip_phases` in `.tdd-state.local.json`):
- If `3-dev` not skipped → set `current.phase` = "dev"
- Else if `4-docs` not skipped → set `current.phase` = "docs"
- Else → set `current.phase` = "review"

```
## RED: {task_id} - Title

**Tests:** [N] unit / [Y] integration / [Z] arch / [W] perf
**Ratio:** [X]% happy / [Y]% edge+error
**Status:** Syntax OK, collection OK, all tests RED

Run `/tdd:flow:3-dev` to implement (GREEN).
```

## Golden rules

1. **Test our code, not the language.** If the test passes without our implementation, it's useless.
2. **Happy paths are the minority.** Real bugs hide in edge cases and error handling.
3. **Depth beats breadth.** 5 thorough tests > 15 shallow tests.
4. **Test the interaction.** Unit tests alone cannot catch integration bugs.
