# /tdd:flow:1-analyze

Technical analysis and design.
Act as a **Senior Architect** to prepare the ground before any code.

## Instructions

### 1. Load state

{{STATE_SOURCE}}

{{STATE_READ}}

If `current.phase` != `null` -> error, suggest the correct command.

### 2. Determine task

* Next incomplete task in `current.epic`
* If epic complete -> Validate with user and move to next

{{TASK_SOURCE}}

### 3. Evaluate complexity and type

**Determine task type from content/title:**
- `feature` - New functionality (default)
- `bugfix` - Fix existing behavior
- `refactor` - Restructure without behavior change
- `test` - Add/improve tests only
- `doc` - Documentation only
- `config` - Configuration, CI/CD, tooling
- `chore` - Maintenance, dependencies, cleanup

**Applicable phases by type:**

| Type | 2-test | 3-dev | 4-docs | 5-review |
|------|:------:|:-----:|:------:|:--------:|
| feature | yes | yes | yes | yes |
| bugfix | yes | yes | ? | yes |
| refactor | yes | yes | ? | yes |
| test | - | yes | ? | yes |
| doc | - | - | yes | yes |
| config | - | yes | ? | yes |
| chore | - | yes | ? | yes |

**Score complexity:**

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Files** | 1-2 | 3-5 | 6+ |
| **New interfaces** | 0 | 1-2 | 3+ or public API |
| **External deps** | None | Internal module, known lib | External API, DB, unknown lib |
| **Unknowns** | Mastered pattern | Known pattern, new context | Unknown territory, R&D |
| **Reversibility** | Trivial rollback | Migration possible | Breaking change, data migration |

**Examples:**
- **S (0-3):** Fix typo, add logging, modify constant, simple bug fix
- **M (4-6):** New CRUD endpoint, module refactor, add validation layer
- **L (7-10):** New auth system, DB migration, third-party API integration

**Complexity level:**
- **0-3 → S (Small)** - Fast track (skip to step 7)
- **4-6 → M (Medium)** - Standard flow
- **7-10 → L (Large)** - Full ceremony

Display:
```
Task: {task_id} - {title}
Epic: {epic_id}
Complexity: [S|M|L] (score: X/10)
Type: [feature|bugfix|refactor|test|doc|config|chore]
→ [Fast track|Standard flow|Full ceremony]
→ Phases: analyze [→ test] [→ dev] [→ docs] → review → done
```

### 4. Load/Create epic context

**If new epic** (first task): Create `.tdd-epic-context.md`:

```markdown
# {epic_id}: {Epic name} - Epic Context
- Last updated: {date}
## Architectural Decisions
*Will be enriched after each task*
## Defined Interfaces
*Will be enriched after each task*
```

**If epic in progress**: Read `.tdd-epic-context.md` for consistency.

### 5. Explore codebase [M, L only]

Launch exploration agent:

```
Code Scout for {task_id}. Report facts only, don't solve.
1. Read docs/dev/architecture.md (overview), docs/dev/standards.md
2. If docs/dev/architecture/ folder exists, load relevant modular docs:
   - List available files in docs/dev/architecture/
   - Based on task domain (UI, CLI, persistence, etc.), load only relevant module(s)
3. Read task description from backend
4. List impacted files (max 10 paths)
5. Find similar patterns (max 3 paths)
```

### 6. Deep analysis [L only]

Perform in-depth analysis covering:

**Data Design**
- Inputs: [types, nullability]
- Outputs: [types]
- Transformations: [if any]

**Logic Flow**
1. Step 1
2. If X then Y else Z
3. ...

**Risk Assessment**
- **Unknowns:** [libraries/APIs not mastered]
- **Technical Debt Risk:** [is simplest solution too dirty?]
- **Reversibility:** [easy to change later?]

**Architecture Questions**
- [Question 1 for user]
- [Question 2 for user]

**Engage discussion with user** to resolve questions before proceeding.

### 7. Decision synthesis

Present to user for confirmation:

---
**VALIDATION REQUIRED - {task_id}**

**Objective:** {One sentence}

**Scope**
- IN:
  - {bullet 1}
  - {bullet 2}
  - {bullet 3}
- OUT:
  - {bullet 1}
  - {bullet 2}

**Files impacted**
- Create: `path/file.py` - {responsibility}
- Modify: `path/file.py` - {what changes}

**Design** (M, L only)
```
# Key signatures only
def function_name(param: Type) -> ReturnType: ...
class ClassName:
    def method(self) -> Type: ...
```

**Test cases**
1. `test_happy_path` - {scenario}
2. `test_edge_case` - {scenario}
3. `test_error_handling` - {scenario}

**Risks** (if any)
- {Risk description}

---
> Reply "ok" to proceed, or specify changes.

**On rejection:** Return to relevant step (3, 5, or 6).
**On approval:** Proceed to branch creation.

### 8. Create task branch

```bash
git checkout main && git pull origin main
```

{{BRANCH_FORMAT}}

### 9. Update state

```json
{ "current": { "epic": "{epic_id}", "task": "{task_id}", "phase": "analyze" } }
```

### 10. Create .tdd-context.md

**Delete existing file first.** Use the appropriate template based on complexity.

#### Template S (Small)

```markdown
# {task_id} - {Title}
Epic: {epic_id}
Complexity: S | Type: {type} | Started: {date}
Phases: analyze [→ test] [→ dev] [→ docs] → review → done

## Objective
{One sentence}

## Scope
- IN: {2-3 bullets}
- OUT: {1-2 bullets}

## Files
- Modify: `path/file` - {why}
- Create: `path/file` - {why}

## Tests (if applicable)
1. `test_name` - {scenario}
2. `test_name` - {scenario}
```

#### Template M (Medium)

```markdown
# {task_id} - {Title}
Epic: {epic_id}
Complexity: M | Type: {type} | Started: {date}
Phases: analyze [→ test] [→ dev] [→ docs] → review → done

## Objective
{One sentence}

## Scope
- IN: {bullets}
- OUT: {bullets}

## Design
### Signatures
{Key types/interfaces only - no implementation details}

### Logic
1. {Step}
2. {Step}

## Files
- Modify: `path` - {why}
- Create: `path` - {why}

## Tests (if applicable)
1. `test_happy` - {scenario}
2. `test_edge` - {scenario}
3. `test_error` - {scenario}

## Risks
- {If any, otherwise omit section}
```

#### Template L (Large)

```markdown
# {task_id} - {Title}
Epic: {epic_id}
Complexity: L | Type: {type} | Started: {date}
Phases: analyze [→ test] [→ dev] [→ docs] → review → done

## Objective
{One sentence}

## Analysis
### Data Design
- Inputs: {types, nullability}
- Outputs: {types}
- Transformations: {if any}

### Risk Assessment
- **Unknowns:** {libraries/APIs not mastered}
- **Technical Debt Risk:** {is simplest solution acceptable?}
- **Reversibility:** {easy to change later?}

## Scope
- IN: {bullets}
- OUT: {bullets}

## Design
### Signatures
{Key types/interfaces}

### Architecture
- Pattern: {name}
- Error handling: {strategy}

### Logic
1. {Step}
2. {Step}

## Files
### Create
- `path` - {responsibility}

### Modify
- `path` - {changes}

## Tests (if applicable)
1. `test_name` - {scenario}
2. ...

## Risks
- {Risk 1}
- {Risk 2}
```

### 11. Finalize

Determine next phase based on type and `skip_phases` in `.tdd-state.local.json`:

1. Get applicable phases for task type (from table above)
2. Remove phases listed in `skip_phases` (if any)
3. Set `current.phase` to first remaining phase after `analyze`

**Phase transition logic:**
- If `2-test` applicable and not skipped → set to `test`
- Else if `3-dev` applicable and not skipped → set to `dev`
- Else if `4-docs` applicable and not skipped → set to `docs`
- Else → set to `review`

```
## Ready: {task_id} - {Title}
Epic: {epic_id}
Complexity: [S|M|L] | Type: {type} | Context: .tdd-context.md
Phases: analyze [→ test] [→ dev] [→ docs] → review → done

Next: Run `/tdd:flow:2-test` to write tests (RED).
      Or `/tdd:flow:3-dev` if test phase skipped.
      Or `/tdd:flow:4-docs` if doc-only task.
```
