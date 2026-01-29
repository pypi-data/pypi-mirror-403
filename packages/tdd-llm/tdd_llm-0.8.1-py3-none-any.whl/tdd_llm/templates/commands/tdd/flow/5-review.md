# /tdd:flow:5-review

Code review and quality validation.

## Instructions

### 1. Load context

Read `.tdd-context.md` and `.tdd-epic-context.md`.
Verify `.tdd-state.local.json`: `current.phase` must be "review".

Extract complexity (S/M/L) from `.tdd-context.md` header.

### 2. Build and tests

Run build and tests. Fix any failures before continuing.

### 3. Verify coverage

Run coverage (command from `docs/dev/standards.md`).

{{COVERAGE_THRESHOLDS}}

If not met, add missing tests first.

### 4. Code review

Review changes against `main` branch using `git diff main...HEAD`.

#### 4.1 Gather context (Haiku agents in parallel)

Launch 2 Haiku agents:

**Agent A - Project rules:**
Find all relevant guidance files:
- Root CLAUDE.md (if exists)
- CLAUDE.md in directories touched by the diff
- `docs/dev/architecture.md` (overview)
- If `docs/dev/architecture/` folder exists, load module docs relevant to changed files
Return list of file paths and their key rules/patterns.

**Agent B - Change summary:**
View the diff and return:
- Files modified/created/deleted
- Nature of changes (new feature, bugfix, refactor, etc.)
- Key code patterns used

#### 4.2 Parallel review (depth based on complexity)

Launch review agents based on task complexity:

**Small (S) - 2 Sonnet agents:**
1. **Project rules compliance** - Check changes against CLAUDE.md and architecture docs
2. **Bug scan** - Shallow scan for obvious bugs in the diff

**Medium (M) - 3 Sonnet agents:**
1. **Project rules compliance** - Check changes against CLAUDE.md and architecture docs
2. **Bug scan** - Shallow scan for obvious bugs in the diff
3. **Task completion** - Read `.tdd-context.md` and verify ALL requirements in Scope/Tests/Design sections are implemented

**Large (L) - 5 Sonnet agents:**
1. **Project rules compliance** - Check changes against CLAUDE.md and architecture docs
2. **Bug scan** - Shallow scan for obvious bugs in the diff
3. **Task completion** - Read `.tdd-context.md` and verify ALL requirements in Scope/Tests/Design sections are implemented
4. **Git history** - Read git blame/history of modified files for context-aware review
5. **Code comments** - Check compliance with guidance in code comments of modified files

Each agent returns issues with format:
```
- [SEVERITY] Description
  File: path/to/file.py:L42
  Reason: {CLAUDE.md rule | architecture violation | bug pattern | missing requirement | historical context | comment guidance}
```

#### 4.3 Severity levels

- **critical**: Security vulnerability, data loss risk, breaking change, core functionality broken
- **major**: Bug that will occur in practice, missing required feature, CLAUDE.md violation (explicit rule)
- **minor**: Code style issue, potential edge case, minor optimization, non-explicit CLAUDE.md preference

#### 4.4 False positives to ignore

- Pre-existing issues (not introduced by this change)
- Issues a linter/typechecker/compiler would catch
- General quality issues unless required in CLAUDE.md
- Issues silenced by lint ignore comments
- Intentional functionality changes related to the task
- Changes on lines not modified in the diff

### 5. Process review results

#### 5.1 Consolidate issues

Merge duplicate issues from different agents. Present summary:

```
## Code Review Results

### Critical (X)
- [ ] Issue description - file:line

### Major (X)
- [ ] Issue description - file:line

### Minor (X)
- [ ] Issue description - file:line
```

#### 5.2 Fix all issues

**Fix ALL issues (critical, major, and minor)** unless one of these exceptions applies:

1. **False positive**: The issue doesn't actually apply to this code
2. **Major refactor required**: Fixing would require significant architectural changes beyond the scope of this task

For any issue NOT fixed, you MUST provide justification:
```
SKIPPED: [Issue description]
Reason: [false positive | major refactor required]
Justification: [Explain why this is a false positive OR why fixing requires major refactor]
```

**Critical issues**: MUST be resolved. If you believe it's a false positive, ask user for confirmation before skipping.

If a fix is ambiguous (multiple valid approaches), ask user which approach to take.

### 6. Commit and Push

Commit all changes (including review fixes): `{task_id}: {short description}`
Push to origin on current branch.

### 7. Create PR

Create PR with `gh pr create`:
- Title: `{task_id}: {task title}`
- Summary: objective from `.tdd-context.md`
- Changes: list of created/modified files
- Test plan: build, tests, coverage status
- Review fixes applied (if any)

### 8. Update .tdd-context.md

Add after `## Baseline`:
- Final coverage (line %, delta from baseline)
- PR number
- Review issues fixed (count by severity)

### 9. Finalize

Set `current.phase` = "done" in `.tdd-state.local.json`.

```
## REVIEW: {task_id} - Title

**Build:** OK
**Tests:** [N]/[N] passed
**Coverage:** [X.X]% (baseline: [Y.Y]%)
**Review:** [X] critical, [X] major, [X] minor fixed
**PR:** #{N}

Run `/tdd:flow:6-done` to finalize.
```
