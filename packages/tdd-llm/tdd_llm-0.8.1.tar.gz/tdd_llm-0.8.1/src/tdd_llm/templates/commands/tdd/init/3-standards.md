# /tdd:init:3-standards

Define code conventions based on project stack.

## Instructions

### 1. Load context (if available)

Check and read if present:
- `{{AGENT_FILE}}` - Tech stack, structure
- `docs/dev/architecture.md` - Chosen patterns

**If `{{AGENT_FILE}}` doesn't exist**, ask basic questions:
```
Before defining standards, I need some info:

1. What language/stack?
2. What test framework?
```

Identify or collect:
- Main language
- Framework (if applicable)
- Test framework

### 2. Targeted questions based on stack

**Adapt questions to detected language.** Only ask relevant questions.

#### Common questions (all languages):

```
Some questions about {project} conventions:

1. Code documentation: What level?
   - Exhaustive (document everything)
   - Standard (public API + complex logic)
   - Minimal (obvious signatures = no doc)

2. Comment/doc language?
   - English
   - French
   - Other

3. Commit messages: What format?
   - Conventional Commits (feat:, fix:, chore:)
   - Epic/Task prefix (E1: T2 - description)
   - Free but descriptive
```

{{STANDARDS_QUESTIONS}}

#### Test questions (all languages):

```
Test conventions:

1. Test file organization?
   - Mirror of src/ (tests/Module/ClassTests)
   - By feature (tests/features/)
   - Co-located with code (*.test.ts next to source)

2. Test naming?
   - Method_Scenario_Expected (Save_ValidData_ReturnsTrue)
   - should_expected_when_scenario
   - Free description ("saves valid data")

3. Internal test structure?
   - Arrange/Act/Assert (AAA)
   - Given/When/Then
   - No imposed structure
```

### 3. Generate standards document

Create `docs/dev/standards.md` adapted to stack:

```markdown
# Development Standards

## TDD Approach

The project follows Test-Driven Development:

1. **RED**: Write tests first (must fail)
2. **GREEN**: Implement minimal code to pass tests
3. **REFACTOR**: Improve code while keeping tests green

### Test Conventions

- Organization: {chosen structure}
- Naming: `{chosen convention}`
- Structure: {AAA/GWT/free}

### Coverage

- Each public behavior must have a test
- Test edge cases (null, empty, limits)
- No code without corresponding test

## {Language} Conventions

### Files and Naming

- Files: {convention}
- Types/Classes: {convention}
- Functions/Methods: {convention}
- Variables: {convention}
- Constants: {convention}

### Code Organization

{Stack-specific conventions}

### {Language-specific aspect}

{Conventions based on answers}

## Documentation

- Level: {choice}
- Language: {choice}

{{DOC_EXAMPLE}}

## Git Conventions

### Commits

```
{chosen format with example}
```

### Branches

- Feature: `feature/{description}`
- Fix: `fix/{description}`
- Epic: `e{n}-t{m}` (task branches)
```

### 4. Update {{AGENT_FILE}}

Add a "Conventions" section in `{{AGENT_FILE}}` with key points:
- Naming rules
- Required patterns
- What to avoid

### 5. Display summary

```
## Standards defined: {project}

**Language:** {language}

**Tests:**
- Structure: {organization}
- Naming: {convention}

**Code:**
- Documentation: {level}
- {Key aspect 1}: {choice}
- {Key aspect 2}: {choice}

**Git:**
- Commits: {format}

**Files created/updated:**
- `docs/dev/standards.md`
- `{{AGENT_FILE}}` (Conventions section)

**Next step:** `/tdd:init:4-readme`
```

## Notes

- Don't repeat standard language conventions (obvious stuff)
- Focus on choices that vary between projects
- Keep document concise and actionable
- Examples must be consistent with actual stack
