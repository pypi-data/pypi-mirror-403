# dd-dm (Dungeon Master)

A CLI tool for managing shared engineering rules across projects. Define and compose rules into a project constitution, then keep them in sync with explicit, reviewable diffs.

## What it does

- Manages shared engineering rules ("constitutions") for projects
- Syncs rules between a templates repository and local projects
- Prevents convention drift between humans and AI agents
- Keeps prompts and context lean by centralizing rules

## Installation

### Local Development Setup

1. **Prerequisites**:
   - [asdf](https://asdf-vm.com/) for Python version management
   - [uv](https://github.com/astral-sh/uv) for package management

2. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd dd_dungeonmaster

   # Install Python version via asdf
   asdf install

   # Install dependencies
   uv sync --all-extras
   ```

3. **Run the CLI**:
   ```bash
   uv run dd-dm --help
   ```

4. **Run tests**:
   ```bash
   uv run pytest
   ```

5. **Run linter**:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

## Usage

```bash
# Initialize in a project (provide URL to your templates repo)
dd-dm init https://github.com/your-org/engineering-rules.git

# Add a module to your constitution
dd-dm add GIT_CONVENTIONAL_COMMITS

# Create a custom local module
dd-dm create my-team-rules

# Remove a module
dd-dm delete GIT_CONVENTIONAL_COMMITS

# Pull updates from templates repo
dd-dm pull

# Push local changes to templates repo
dd-dm push
```

## License

MIT
