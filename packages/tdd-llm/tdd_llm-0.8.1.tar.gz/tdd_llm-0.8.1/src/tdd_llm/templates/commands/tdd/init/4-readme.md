# /tdd:init:4-readme

Generate final README.md by synthesizing all project documentation.

## Instructions

### 1. Load available context

Check and read if present:
- `{{AGENT_FILE}}` - Overview, stack, commands
- `docs/dev/architecture.md` - Technical architecture
- `docs/dev/standards.md` - Conventions
- `docs/epics/*.md` - Planned features
- `docs/state.json` - Current state

**If none of these files exist**, ask essential questions:
```
To generate the README, I need some info:

1. Project name?
2. Description in 1-2 sentences?
3. Tech stack?
4. Build command?
5. Test command?
6. Run command?
```

### 2. Optional questions

If information is missing, ask:

```
To complete the README:

1. Project license?
   - MIT
   - Apache 2.0
   - GPL
   - Proprietary / No license
   - Other

2. Is the project public or private?
   - Public (complete README for external contributors)
   - Private (internal README, less installation details)

3. Badges to include?
   - Build status
   - Coverage
   - Version/Release
   - License
   - None for now
```

### 3. Generate README.md

Create `README.md` at root:

```markdown
# {Project name}

{Description in 1-2 sentences - extracted from {{AGENT_FILE}}}

## Features

{List of main features - extracted from epics}

- {Feature 1 from E1}
- {Feature 2 from E2}
- ...

## Getting Started

### Prerequisites

- {Runtime} {version}
- {Other dependencies}

### Installation

```bash
{Installation commands based on stack}
```

### Running

```bash
{Command to run project}
```

## Development

### Setup

```bash
# Clone the repository
git clone {url if known}
cd {project-name}

# Install dependencies
{install command}

# Run tests
{test command}
```

### Project Structure

```
{Simplified project structure}
```

### Testing

```bash
# Run all tests
{test command}

# Run specific test
{single test command}
```

## Documentation

- [Architecture](docs/dev/architecture.md) - Technical architecture
- [Standards](docs/dev/standards.md) - Code conventions
- [Epics](docs/epics/) - Feature roadmap

## Roadmap

{Summary of planned epics}

| Epic | Description | Status |
|------|-------------|--------|
| E0 | Foundation | {status} |
| E1 | {Name} | {status} |
| ... | ... | ... |

## Contributing

{If public project}

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

{Chosen license or "Proprietary"}
```

### 4. Adapt based on project type

**For a library/SDK:**
Add "Usage" section with code examples.

**For a CLI:**
Add "Commands" section with available commands.

**For a web app:**
Add deployment info if relevant.

### 5. Display final summary

```
## Initialization complete: {project}

**Files created:**
- `README.md` - Main documentation

**Full init structure:**
```
{project}/
├── README.md
├── {{AGENT_FILE}}
├── CHANGELOG.md
└── docs/
    ├── state.json
    ├── dev/
    │   ├── architecture.md
    │   └── standards.md
    └── epics/
        ├── e0-foundation.md
        └── e1-{feature}.md
```

**Project is ready for development!**

Run `/tdd:flow:1-analyze` to start the first task.
```

## Notes

- README should be standalone (understandable without reading other docs)
- Keep README concise - details in dedicated docs
- Adapt tone: formal for public, casual for internal
- Optional sections can be omitted if not relevant
- Update README when features are implemented
