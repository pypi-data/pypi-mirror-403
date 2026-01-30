# AI Context Core

The central nervous system for your AI-assisted coding workflow.

## Features
- **Project Analysis**: Deep AST analysis for Python projects.
- **Context Management**: Keeps `.ai-context` files updated.
- **Profiles**: 
    - `python-generic`: Standard Python support.
    - `qgis-plugin`: Specialized rules for QGIS plugin development.
- **Workflow Automation**: Standardized scripts for session management.
- **Advanced Analysis**:
    - **Entry Point Detection**: Supports QGIS plugins, Click CLIs, Flask, and FastAPI apps.
    - **Anti-Pattern Detection**: Identifies God Objects, Spaghetti Code, Magic Numbers, and Dead Code.
    - **Security Audit**: Scans for vulnerabilities like SQL Injection, `eval/exec`, and insecure assertions.

## Installation

### Globally (as a tool)

```bash
uv tool install .
```

### In a Virtual Environment

This is the recommended way to install and use `ai-context-core`.

1. **Create and activate the environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install the package**:
   ```bash
   uv pip install .
   ```

   The `ai-ctx` command will be available within the virtual environment.

### For Development

If you want to contribute to the project, you need to install it in editable mode with the development dependencies.

1. **Create and activate the environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install the package with development dependencies**:
   ```bash
   uv sync --all-extras
   ```

   This will install the project in editable mode and all the dependencies, including the ones for testing and documentation.

### Using in Another Project

If you want to use `ai-ctx` within the context of **another project's** virtual environment:

#### Option A: One-off execution (No installation required)
You can run it directly using the path to this repository:
```bash
uv run --with /path/to/ai-context-core ai-ctx analyze
```

#### Option B: Install in an existing environment
Activate your project's environment and run:
```bash
uv pip install /path/to/ai-context-core
```

#### Option C: Add as a development dependency
If the other project also uses `uv`:
```bash
uv add --dev --path /path/to/ai-context-core
```

```

## Docker Support

The project includes Docker support for reproducible development, testing, and CI/CD.

### Quick Start with Docker

```bash
# Build all images
make docker-build

# Run tests in Docker
make docker-test

# Interactive development shell
make docker-shell

# Run linter
make docker-lint
```

### Docker Images

- **Development** (`ai-ctx:dev`) - Full environment with dev dependencies
- **Test** (`ai-ctx:test`) - Runs test suite with coverage
- **Production** (`ai-ctx:prod`) - Minimal runtime image

### Manual Docker Commands

```bash
# Build specific stage
docker build --target test -t ai-ctx:test .

# Run tests
docker run --rm ai-ctx:test

# Run CLI from production image
docker run --rm ai-ctx:prod analyze

# Interactive shell
docker run --rm -it ai-ctx:dev /bin/bash
```

## Usage

```bash
# Initialize in a new project
ai-ctx init --profile qgis-plugin

# Update context manually
ai-ctx analyze
```

