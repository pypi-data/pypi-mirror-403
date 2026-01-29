# Messirve

A CLI tool that orchestrates Claude Code to execute development tasks autonomously in a loop. It takes a list of Jira-like tasks from a YAML file and executes them one-by-one using Claude Code, with comprehensive logging, git integration, and quality gates.

## Features

- **Sequential Task Execution**: Execute tasks in dependency order
- **YAML Task Files**: Define tasks using a simple, structured YAML format
- **Git Integration**: Multiple git strategies (commit-per-task, branch-per-task, etc.)
- **Hooks System**: Run commands before/after tasks and runs
- **Retry Logic**: Configurable retry attempts with delays
- **Comprehensive Logging**: Per-task and master logs in JSON and Markdown
- **Quality Gates**: Post-task hooks for testing and linting
- **Rich CLI**: Colored output with multiple verbosity levels

## Installation

```bash
pip install messirve
```

Or with pipx:

```bash
pipx install messirve
```

## Quick Start

1. **Initialize and onboard your project:**

   ```bash
   # Initialize messirve configuration
   messirve init

   # Onboard: detect tech stack, explore codebase with Claude Code
   messirve onboard
   ```

2. **Plan your tasks interactively:**

   ```bash
   # Start a planning session to generate tasks from goals
   messirve planning
   ```

   Or create a tasks file manually (`tasks.yaml`):

   ```yaml
   version: "1.0"
   tasks:
     - id: TASK-001
       title: "Add user authentication"
       description: |
         Implement JWT-based authentication for the API.
       context: |
         We're using FastAPI with SQLAlchemy.
       acceptance_criteria:
         - "POST /auth/login returns JWT token"
         - "Unit tests cover all auth endpoints"
   ```

3. **Run the tasks:**

   ```bash
   messirve run
   ```

## Typical Workflow

```bash
# 1. First time setup
messirve init              # Create .messirve/ config
messirve onboard           # Explore codebase, generate context

# 2. Plan your sprint/tasks
messirve planning          # Interactive: goals -> tasks

# 3. Execute tasks
messirve run               # Execute all tasks
messirve run --dry-run     # Preview what would run

# 4. Analyze code quality
messirve analyze --before main   # Check for regressions
```

## CLI Reference

### Project Onboarding

```bash
# Onboard to a project (recommended first step)
# This explores the codebase with Claude Code and generates context
messirve onboard

# Quick detection only (skip Claude Code exploration)
messirve onboard --skip-exploration

# Force regenerate context
messirve onboard --force

# Skip setup/verification commands
messirve onboard --skip-setup --skip-verify
```

### Task Planning

```bash
# Interactive planning session - generate tasks from high-level goals
messirve planning

# With pre-specified goals
messirve planning -g "Add user authentication" -g "Improve test coverage"

# Non-interactive mode (for CI/scripting)
messirve planning --goal "Add caching" --non-interactive -o tasks.yaml

# Specify output file
messirve planning -o my-sprint-tasks.yaml
```

### Running Tasks

```bash
# Run all tasks
messirve run

# Run tasks from specific file
messirve run --tasks path/to/tasks.yaml

# Run specific task(s)
messirve run --task TASK-001 --task TASK-002

# Dry run (show what would execute)
messirve run --dry-run

# Run with different git strategy
messirve run --git-strategy branch-per-task

# Run with different verbosity
messirve run --quiet          # Minimal output
messirve run -v               # Normal (default)
messirve run -vv              # Verbose
messirve run -vvv             # Debug

# Continue from failed task
messirve run --continue

# Run with code analysis
messirve run --analyze
```

### Task Management

```bash
# Create a new task interactively
messirve create-task

# Create task with inline values
messirve create-task --id TASK-003 --title "Add feature X"

# List tasks
messirve list-tasks
messirve list-tasks --tasks path/to/tasks.yaml

# Show task details
messirve show-task TASK-001

# Validate task file
messirve validate --tasks path/to/tasks.yaml
```

### Project Context

```bash
# Generate context from auto-detection (without Claude Code exploration)
messirve context generate

# Force regenerate
messirve context generate --force

# Show current context
messirve context show
messirve context show --format yaml

# Edit context file in your editor
messirve context edit

# Set specific context values
messirve context set description "My project description"
messirve context set business_description "Enterprise solution for..."
```

### Code Analysis

```bash
# Analyze current directory
messirve analyze

# Analyze specific paths
messirve analyze src/ tests/

# Compare against a git ref (e.g., detect regressions)
messirve analyze --before main

# Output to file
messirve analyze --output report.json --format json
messirve analyze --output report.md --format markdown

# Fail CI if regression detected
messirve analyze --before main --fail-on-regression

# Disable specific analysis
messirve analyze --no-complexity
messirve analyze --no-quality
```

### Configuration

```bash
# Initialize messirve in current project
messirve init

# Show current configuration
messirve config show

# Set configuration value
messirve config set defaults.max_retries 5

# Add a rule
messirve config add-rule "Use async/await for I/O operations"

# Add a boundary
messirve config add-boundary "*.secret" --type never_modify
```

### Logs and Reports

```bash
# Show execution history
messirve logs

# Show specific run
messirve logs --run 2024-01-20-143052

# Show specific task log
messirve logs --task TASK-001 --run 2024-01-20-143052

# Export report
messirve report --format json --output report.json
messirve report --format markdown --output report.md
```

### Templates

```bash
# List available task templates
messirve list-templates

# Show template details
messirve show-template api-endpoint

# Generate tasks from template
messirve generate api-endpoint --output tasks.yaml

# List available task flavors
messirve list-flavors
```

## Task File Format

```yaml
version: "1.0"

tasks:
  - id: TASK-001
    title: "Add user authentication"
    description: |
      Implement JWT-based authentication for the API.
      This includes login, logout, and token refresh endpoints.
    context: |
      We're using FastAPI with SQLAlchemy.
      The User model already exists in models/user.py.
    acceptance_criteria:
      - "POST /auth/login returns JWT token on valid credentials"
      - "POST /auth/logout invalidates the token"
      - "Unit tests cover all auth endpoints"
    depends_on: []
    hooks:
      pre_task:
        - "ruff check src/"
      post_task:
        - "pytest tests/auth/"

  - id: TASK-002
    title: "Create user dashboard endpoint"
    description: |
      Create a GET /dashboard endpoint that returns user stats.
    context: |
      Requires authentication from TASK-001.
    acceptance_criteria:
      - "GET /dashboard returns user profile data"
      - "Requires valid JWT token"
    depends_on:
      - TASK-001
```

### Task Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique task identifier |
| `title` | string | Yes | Short task title |
| `description` | string | Yes | Detailed task description |
| `context` | string | Yes | Project context, existing code references |
| `acceptance_criteria` | list[string] | Yes | List of criteria to verify completion |
| `depends_on` | list[string] | No | List of task IDs that must complete first |
| `hooks.pre_task` | list[string] | No | Commands to run before this task |
| `hooks.post_task` | list[string] | No | Commands to run after this task |

## Configuration File

Configuration is stored in `.messirve/config.yaml`:

```yaml
version: "1.0"

defaults:
  max_retries: 3
  retry_delay_seconds: 5
  verbosity: normal
  git_strategy: branch-per-task
  base_branch: main
  create_pr: false
  claude_code_permissions: skip

hooks:
  pre_run:
    - "echo 'Starting messirve execution'"
  post_run:
    - "echo 'Execution complete'"
  pre_task:
    - "ruff check src/ --fix"
  post_task:
    - "pytest tests/ -x -q"

rules:
  - "Use type hints for all functions"
  - "Follow PEP 8 conventions"
  - "Write docstrings for public functions"

boundaries:
  never_modify:
    - "poetry.lock"
    - ".env"
  read_only:
    - "pyproject.toml"
```

## Git Strategies

| Strategy | Description |
|----------|-------------|
| `none` | No git operations (user manages git) |
| `commit-per-task` | Auto-commit after each task on current branch |
| `branch-per-task` | Create new branch per task (`messirve/{task-id}-{slug}`) |
| `single-branch` | All work on one branch (`messirve/run-{timestamp}`) |

## Logging

Messirve creates comprehensive logs in `.messirve/logs/`:

```
.messirve/logs/
├── master.json                    # Master log with all runs
└── runs/
    └── 2024-01-20-143052/        # Run ID
        ├── run.json               # Run metadata & summary
        ├── TASK-001.json          # Task log (JSON)
        ├── TASK-001.md            # Task log (Markdown)
        └── ...
```

## Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run pytest`
5. Run linting: `poetry run ruff check src/ tests/`
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.
