# /tdd:flow:4-docs

Document the completed task.

## Instructions

### 1. Load context

Read `.tdd-context.md` (lightweight).

Verify `.tdd-state.local.json`: `current.phase` must be "docs".

### 2. Update CHANGELOG.md

**Add entry** under appropriate section (Added/Changed/Fixed):

- Format: `- [Module]: description of change`
- Be **specific** (mention classes/methods)
- Write from user/developer perspective

**Example:**
```markdown
### Added
- GDTF import: extract color wheels with CIE xyY values and gobo images
- `FixtureType.Wheels` collection for accessing fixture wheel definitions
```

### 3. Verify code documentation

**Read created/modified files** (from `.tdd-context.md > Files`).

**If public APIs:**
- Verify all public types/methods have documentation (docstrings, JSDoc, XML docs)
- Follow existing format in the project (check similar files)
- Add those that are missing

### 4. Update user documentation

**IMPORTANT:** New features and behavior changes MUST have user documentation. Don't skip this.

**Read `{{AGENT_FILE}}` section "Documentation Structure"** for project doc locations.

**If section not found in `{{AGENT_FILE}}`:** Discover doc structure and add it:
```bash
# Find doc directories
find . -type d -name "doc*" -o -name "wiki" -o -name "help" 2>/dev/null | head -10
```

**For each documentation type below, explicitly verify and update:**

| Type | MUST update if... | Action |
|------|-------------------|--------|
| **User docs** (`docs/user/`, `help/`) | New feature, UI change, behavior change | Add/update usage guide |
| **Dev docs** (`docs/dev/`, `docs/api/`) | API changes, new patterns | Update API docs |
| **Architecture docs** (`docs/dev/architecture/`) | Architectural changes, new modules | Update relevant module doc or `architecture.md` |
| **API specs** (`openapi.yaml`, `swagger.json`) | Endpoint changes | Update spec file |
| **Project context** (`README.md`, `{{AGENT_FILE}}`) | Important patterns, setup changes | Update relevant sections |

**Architecture documentation structure:**
- If `docs/dev/architecture/` folder exists with modular docs, update the relevant module file
- If only `docs/dev/architecture.md` exists, update that single file
- For new architectural components, consider if a new module doc is warranted
- **If creating a new module doc:** Add a reference to it in `docs/dev/architecture.md` (index/overview file)

**For new features specifically:**
1. Find the appropriate user doc file (or create one if needed)
2. Document: what it does, how to use it, example usage
3. If CLI command: add to command reference

### 5. Validate existing examples

**If task modified public APIs:**
- Search docs for code examples using changed functions/classes
- Verify examples still work after changes
- Update outdated examples

### 6. Evaluate if ADR needed

**Read `.tdd-context.md > Decisions`.**

**Create ADR if:**
- Choice between multiple valid approaches
- Decision impacts multiple modules
- Significant trade-off (performance vs simplicity)

**Don't create if:**
- Standard implementation without alternative
- Decision local to one file

**If ADR needed:**
- Find existing ADRs location (usually `docs/dev/decisions/` or `docs/adr/`)
- Use project's ADR template if exists
- Numbering: next available number

### 7. Update .tdd-context.md

Add final section:

```markdown
## Documentation
- CHANGELOG updated ([Added/Changed/Fixed])
- Code docs: Complete
- User docs: [file] / N/A (reason)
- ADR: [NNN-title] / Not needed
```

### 8. Update phase

Set `current.phase` = "review" in `.tdd-state.local.json`.

### 9. Report

```
## Documentation: {task_id} - Title

### Updated
- `CHANGELOG.md` - Section [Added/Changed/Fixed]
- Code docs: [N] added / Already complete
- User docs: [file updated] / N/A (reason: [bug fix only / internal refactor / no user-visible change])
- [list any other docs updated]

### Created
- `docs/decisions/[NNN-title].md` / No ADR needed

Run `/tdd:flow:5-review` for review and PR creation.
```

**Note:** If user docs show "N/A", you MUST provide a valid reason. "New feature" or "behavior change" are NOT valid reasons to skip user docs.

## CHANGELOG best practices

**Good:**
```markdown
### Added
- GDTF import: extract color wheels with CIE xyY values and gobo images
- `FixtureType.Wheels` collection for accessing fixture wheel definitions

### Changed
- `GdtfImporter.Import()` now extracts channel functions with DMX ranges
```

**Bad:**
```markdown
### Added
- Added wheels
- New feature
```
