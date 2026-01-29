# /tdd:init:2-architecture

Define technical architecture based on project context.

## Instructions

### 1. Load context (if available)

Check and read if present:
- `{{AGENT_FILE}}` - Overview, stack, structure
- `docs/epics/*.md` - Understand planned features

**If `{{AGENT_FILE}}` doesn't exist**, ask basic questions:
```
Before defining architecture, I need some info:

1. Project name?
2. Description in 1-2 sentences?
3. Tech stack (language/framework)?
4. Project type (web, CLI, desktop, API, etc.)?
```

Extract or collect:
- Project name and description
- Chosen tech stack
- Project type (web, CLI, desktop, etc.)
- Main features (from epics or conversation)

### 2. Targeted questions based on context

**Don't ask generic questions.** Adapt based on detected project type.

#### If Web Frontend/Full-stack project:
```
For {name} architecture:

1. State management: How to manage app state?
   - Global store (Redux, Zustand, Pinia)
   - Context/Composition API
   - Server state only (React Query, SWR)
   - Minimal (local useState)

2. Routing: What approach?
   - File-based (Next.js, Nuxt)
   - Config-based (React Router, Vue Router)
   - Simple SPA (hash routing)

3. Styling: What CSS approach?
   - CSS Modules
   - Tailwind
   - CSS-in-JS (styled-components)
   - Plain CSS/SCSS

4. API calls: How to communicate with backend?
   - REST (fetch/axios)
   - GraphQL (Apollo, urql)
   - tRPC
   - No API (static)
```

#### If Backend/API project:
```
For {name} architecture:

1. API Pattern: What structure?
   - Classic REST (controllers/routes)
   - Clean Architecture (use cases, entities)
   - CQRS (separate commands/queries)
   - Minimal API / Functions

2. Database: What access?
   - ORM (Entity Framework, Prisma, SQLAlchemy)
   - Query builder (Knex, Dapper)
   - Raw SQL
   - Direct NoSQL driver

3. Auth: What strategy?
   - JWT tokens
   - Sessions
   - External OAuth/OIDC
   - No auth for now

4. Validation: Where to validate data?
   - DTOs with validation (FluentValidation, Zod)
   - In controllers
   - In domain layer
```

#### If CLI project:
```
For {name} architecture:

1. Argument parsing: What approach?
   - Library (System.CommandLine, yargs, click)
   - Simple manual
   - Subcommands git-style

2. Configuration: How to manage settings?
   - Config file (JSON, YAML, TOML)
   - Environment variables
   - Arguments only
   - Mix of all three

3. Output: How to display results?
   - JSON (machine-readable)
   - Formatted tables
   - Plain text
   - Interactive (prompts, progress bars)

4. Errors: How to handle them?
   - Exit codes + stderr
   - Exceptions with stack trace (debug)
   - User-friendly messages
```

### 3. Generate architecture

**For most projects:** Create `docs/dev/architecture.md` as single file.

**For large projects** (many modules, complex domains): Consider modular structure:
```
docs/dev/
├── architecture.md           # Overview + index of modules
└── architecture/
    ├── module-a.md           # Domain-specific architecture
    ├── module-b.md
    └── ...
```

The main `architecture.md` serves as entry point with links to module docs.

**Default template** for `docs/dev/architecture.md`:

```markdown
# {Project} - Architecture

{Short description}

## Stack

- **Runtime**: {detailed stack}
- **UI**: {if applicable}
- **Data**: {storage}
- **Testing**: {framework}

## Architecture

```
{ASCII diagram adapted to project}
{Show main components and their relationships}
```

## Components

### {Component 1}

| Aspect | Description |
|--------|-------------|
| Role | {description} |
| Responsibilities | {list} |

{Code example if relevant}

### {Component 2}

...

## Patterns

### {Main pattern chosen}

{Explanation and code example}

## Data Flow

{Main flow description}

## Project Structure

```
src/
├── {folder}/     # {description}
└── {folder}/     # {description}

tests/
└── {structure}
```

## Configuration

{Configuration pattern used}

## Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| {aspect} | {choice} | {justification} |
```

### 4. Update {{AGENT_FILE}}

Enrich Architecture section of `{{AGENT_FILE}}` with:
- Detailed project structure
- Main components
- Used patterns

### 5. Display summary

```
## Architecture defined: {project}

**Main components:**
- {component 1} - {role}
- {component 2} - {role}

**Patterns:**
- {pattern 1}
- {pattern 2}

**Files created/updated:**
- `docs/dev/architecture.md` (+ `docs/dev/architecture/` if modular)
- `{{AGENT_FILE}}` (Architecture section enriched)

**Next step:** `/tdd:init:3-standards`
```

## Notes

- Questions must be relevant to specific project
- Don't ask for choices already implicit in stack
- Propose sensible defaults
- Document must be actionable, not theoretical
- ASCII diagrams > no diagram > external tools
