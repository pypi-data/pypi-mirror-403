# /tdd:init:1-project

Exploratory conversation to understand the project, define epics and initialize TDD structure.

## Instructions

### 1. Check if project already exists

Check if `docs/state.json` exists:
- If yes -> ask confirmation before reinitializing
- If no -> continue

### 2. Discovery conversation

The goal is to understand the project through natural conversation. Ask open questions and dig deeper based on answers.

**Start with:**
```
Tell me about your project. What are you trying to build?
```

**Dig deeper based on answer.** Follow-up question examples:

| If user mentions... | Follow-up questions |
|---------------------|---------------------|
| Website / Web app | Frontend only or full-stack? Which framework? SSR/SPA? Auth required? |
| API / Backend | REST or GraphQL? What main entities? Database? |
| CLI | What commands? Interactive or batch? Config file? |
| Desktop | Which platform? Native or web-based UI? |
| File import/export | What formats? File size? Streaming needed? |
| Database | SQL or NoSQL? What entities? Relations? |
| Real-time | WebSocket? Polling? What frequency? |
| Hardware / IoT | What protocols? Latency critical? |

**Essential questions to cover (adapt to context):**

1. **Purpose**: What problem does it solve? For whom?
2. **Key features**: The 3-5 main features?
3. **Preferred stack**: Language/framework already chosen or open?
4. **Constraints**: Performance, platform, external integrations?
5. **MVP**: What's essential vs nice-to-have?

### 3. Synthesize and propose epics

Once project is well understood, propose epic breakdown:

```
## Summary

**Project:** {name} - {short description}
**Stack:** {language/framework}
**Type:** {web/cli/desktop/etc.}

## Proposed Epics

| Epic | Name | Description | Estimated tasks |
|------|------|-------------|-----------------|
| E0 | Foundation | {setup, base models} | ~{n} |
| E1 | {Feature 1} | {description} | ~{n} |
| E2 | {Feature 2} | {description} | ~{n} |
| ... | ... | ... | ... |

**Order:** E0 -> E1 -> E2 -> ...

Does this work for you? Want to adjust anything?
```

### 4. Detail epics

For each validated epic, ask for details or propose them:

```
For epic "{Name}", here are the tasks I propose:

| # | Task | Description |
|---|------|-------------|
| T1 | {title} | {description} |
| T2 | {title} | {description} |
| ... | ... | ... |

Any adjustments?
```

### 5. Create structure

Once everything is validated, create:

**Folder structure:**
```bash
mkdir -p docs/dev/api
mkdir -p docs/dev/decisions
mkdir -p docs/epics
mkdir -p docs/user/guides
mkdir -p docs/user/reference
```

**`docs/state.json`:**
```json
{
  "current": {
    "epic": "E0",
    "task": null,
    "phase": null
  },
  "epics": {
    "E0": { "status": "not_started", "completed": [] },
    "E1": { "status": "not_started", "completed": [] }
  }
}
```

**`docs/epics/e{n}-{name}.md`** for each epic:
```markdown
# E{N}: {Name}

{Description}

## Objective

- {Objective 1}
- {Objective 2}

## Tasks

| # | Task | Description |
|---|------|-------------|
| T1 | {Title} | {Description} |
| T2 | {Title} | {Description} |

## T1: {Title}

{Detailed description}

**To create:**
- {file/component}

## T2: {Title}

{Detailed description}

## Completion criteria

- [ ] Build OK
- [ ] Tests OK
- [ ] {Functional criterion}
```

**Base `{{AGENT_FILE}}`:**
```markdown
# {{AGENT_FILE}}

This file provides guidance to the AI agent when working with this repository.

## Project Overview

{Name} - {Complete description based on conversation}

## Build & Test Commands

{{BUILD_COMMANDS}}

## Architecture

### Technology Stack
- **Runtime:** {stack}
- **Testing:** {test framework}

### Project Structure
```
{structure based on project type}
```

## Development Flow (TDD)

```
/tdd:flow:1-analyze -> /tdd:flow:2-test (RED) -> /tdd:flow:3-dev (GREEN) -> /tdd:flow:4-docs -> /tdd:flow:5-review -> /tdd:flow:6-done
```

## Epic Sequence

{E0} -> {E1} -> {E2} -> ...

See `docs/epics/` for details and `docs/state.json` for progress.

## Documentation Structure

| Type | Path | Purpose |
|------|------|---------|
| Dev docs | `docs/dev/` | Architecture, API reference, decisions (ADR) |
| User docs | `docs/user/` | Guides and reference for end users |
| Changelog | `CHANGELOG.md` | Version history |
```

**`CHANGELOG.md`:**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial project setup
```

### 6. Display summary

```
## Project initialized: {name}

**Stack:** {stack}
**Epics:** {n} epics, {m} total tasks

**Files created:**
- `docs/state.json`
- `docs/epics/e0-foundation.md`
- `docs/epics/e1-{name}.md`
- ...
- `{{AGENT_FILE}}`
- `CHANGELOG.md`

**Next steps:**
1. `/tdd:init:2-architecture` - Define technical architecture
2. `/tdd:init:3-standards` - Define code conventions
3. `/tdd:init:4-readme` - Generate README

Or skip directly to dev: `/tdd:flow:1-analyze`
```

## Notes

- Conversation should be natural, not an interrogation
- Adapt questions to context (don't ask "SQL or NoSQL" for simple CLI)
- Propose choices when user hesitates
- Epics can be adjusted later
- Prefer simplicity: fewer well-defined epics > many vague epics
