# Simforge

Simforge client for provider-based API calls.

## Monorepo Structure

This package is part of the Harvest monorepo. While the TypeScript/JavaScript packages use a **pnpm workspace** for shared dependencies, this Python package uses Poetry for its dependency management.

**Note:** The pnpm workspace includes:

- `simforge-web` - Next.js web application
- `simforge-typescript-sdk` - TypeScript SDK
- `simforge-vscode` - VS Code extension
- `frontend` - Legacy frontend

From the root directory, you can run TypeScript tests and validation across all packages with `pnpm test` or `pnpm validate`.

## Installation

### Basic Installation

```bash
pip install simforge-py
```

### With OpenAI Tracing Support

If you want to use the OpenAI Agents SDK tracing integration:

```bash
pip install simforge-py[openai-tracing]
```

### Local Development

For local development:

```bash
cd simforge-python-sdk
poetry install --with dev
```

After installation, you can use developer tasks. For the best experience, add Poetry's venv to your PATH:

```bash
# Add to your ~/.zshrc or ~/.bashrc
export PATH="$(poetry env info --path)/bin:$PATH"

# Then you can use 'dev' directly (no ./run or poetry run needed!)
dev list
dev test
```

See [Development Tasks](#development-tasks) below for all available commands.

Or install as an editable package from the parent directory:

```bash
poetry add --editable ../simforge-python-sdk
```

## Usage

### Basic Usage

```python
from simforge import Simforge

client = Simforge(
    api_key="sf_your_api_key_here",
    service_url="https://simforge.goharvest.ai",  # Optional, defaults to production
    env_vars={"OPENAI_API_KEY": "sk-your-openai-key"},  # Optional, for local BAML execution
    execute_locally=True  # Optional, defaults to True
)

result = client.call("method_name", arg1="value1", arg2="value2")
```

### OpenAI Agents SDK Tracing

If you have the `openai-agents` package installed (via `pip install simforge-py[openai-tracing]`), you can use the tracing processor:

```python
from simforge import Simforge
from agents import set_trace_processors

simforge = Simforge(api_key="sf_your_api_key_here")
processor = simforge.get_openai_tracing_processor()

# Register the processor with OpenAI Agents SDK
set_trace_processors([processor])

# Now all your agent traces will be sent to Simforge
```

**Note:** If you try to use `get_openai_tracing_processor()` without installing the `openai-tracing` extra, you'll get a helpful error message telling you to install it.

## Configuration

- `api_key`: **Required** - Your Simforge API key (generate from your Simforge dashboard)
- `service_url`: Optional - The Simforge service URL (defaults to `https://simforge.goharvest.ai`)
- `env_vars`: Optional - Environment variables for LLM providers (e.g., `{"OPENAI_API_KEY": "..."}`)
- `execute_locally`: Optional - Whether to execute BAML locally (defaults to `True`)

## Development Tasks

This project uses a Python-based developer tasks module (`dev/`) instead of Makefiles for better cross-platform support and more robust CLI capabilities.

### Using Developer Tasks

After running `poetry install --with dev`, you can use developer tasks:

#### Quick Setup (One-time)

```bash
# Install dependencies (creates the 'dev' script in the venv)
poetry install --with dev

# Run this script to add to PATH for current session and get command to make it permanent
./setup-dev-path.sh

# Copy-paste the command it outputs, then reload your shell config:
source ~/.zshrc  # or ~/.bashrc
```

The `setup-dev-path.sh` script will:

- Add the venv bin to PATH for your current session
- Detect your shell (zsh/bash) and output a command you can copy-paste to make it permanent
- Skip if already configured

#### Using Developer Commands

Once PATH is set up, use commands directly - just like `make <target>`:

```bash
dev list              # List all available commands
dev test              # Run tests
dev test --verbose    # Run tests with verbose output
dev lint              # Lint code
dev format            # Format code
dev build             # Build package
dev publish patch      # Publish with version bump
```

**How it works**: When you define `[tool.poetry.scripts]` in `pyproject.toml`, Poetry creates executable scripts in the venv's `bin/` directory. Adding that `bin/` to PATH makes those scripts available as commands.

**Key advantage**: Just like Makefiles, it's super clear - `dev <command>` is as obvious as `make <target>`!

### Module Structure

Each command is in its own file in the `dev/` module:

- `dev/test.py` - Test commands
- `dev/lint.py` - Linting
- `dev/build.py` - Building
- `dev/publish.py` - Publishing
- etc.

This makes it easy to find and modify individual commands.

## Publishing

This package uses `bump-my-version` for version management. To publish a new version:

```bash
# Use the dev command
dev publish patch          # Bump patch (0.3.0 -> 0.3.1)
dev publish minor          # Bump minor (0.3.0 -> 0.4.0)
dev publish major          # Bump major (0.3.0 -> 1.0.0)
dev publish version=1.2.3  # Custom version

# Or just bump version without publishing
dev bump patch
dev bump minor
```

The publish process will:

1. Run all tests
2. Bump the version in `pyproject.toml`
3. Commit and tag the changes
4. Build the package
5. Prompt for confirmation before publishing to PyPI

**Note:** Publishing requires:

- A clean git working directory (no uncommitted changes)
- Poetry installed and configured
- PyPI credentials configured (via `poetry config pypi-token.pypi <token>`)
