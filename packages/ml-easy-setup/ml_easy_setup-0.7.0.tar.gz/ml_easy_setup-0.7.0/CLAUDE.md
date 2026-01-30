# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ML Easy Setup is a Python CLI tool for automatically configuring machine learning and deep learning environments. It solves common pain points around dependency conflicts, CUDA version matching, and environment setup. The project also includes an SDK for simplified PyTorch model building and training.

**Key Design Philosophy**: Convention over configuration - intelligent defaults with minimal user input required.

## Development Commands

### Building & Distribution
```bash
# Build the package
python -m build

# Install locally in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev,sdk]"
```

### Testing & Code Quality
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=ml_easy_setup

# Type checking
mypy src/

# Linting
ruff check src/
black --check src/

# Auto-format
black src/
ruff check --fix src/
```

### CLI Testing
```bash
# Test CLI entry point
mlsetup --help
mlsetup list-templates
mlsetup detect

# Create a test project
mlsetup create test-project --template minimal --cuda cpu
```

## Architecture

### Core Components

**CLI Layer** (`src/ml_easy_setup/cli.py`)
- Click-based command interface with Rich formatting
- Commands: `create`, `list-templates`, `detect`, `add`, `health`
- Entry points: `mlsetup` and `ml-easy-setup`

**Template System** (`src/ml_easy_setup/core/template.py`)
- 13 pre-configured environment templates (minimal, pytorch, tensorflow, nlp, cv, rl, model-builder, algorithm-validator, data-science, gradient-boosting, mlops, timeseries, graph, full)
- Templates are defined as `BUILTIN_TEMPLATES` dict with dependencies, dev_dependencies, core_packages
- CUDA version mapping for PyTorch/TensorFlow variants
- Supports loading from external YAML files or using built-in defaults

**Environment Manager** (`src/ml_easy_setup/core/env_manager.py`)
- Creates project structure (src/, tests/, data/, notebooks/, outputs/)
- Prefers `uv` for faster package installation, falls back to standard `venv`
- Generates requirements.txt, requirements-dev.txt, .gitignore
- Creates example code based on template type

**Hardware Detection** (`src/ml_easy_setup/core/detector.py`)
- Detects CUDA via `nvcc --version` or `nvidia-smi`
- GPU detection (NVIDIA or Apple Silicon MPS)
- System info (OS, architecture, Python version)
- UV package manager detection

**Health Checker** (`src/ml_easy_setup/core/health.py`)
- Checks venv status, dependency conflicts, GPU/CUDA, compatibility, disk space
- Scores each category 0-1, aggregates to overall status (healthy/warning/critical)
- Supports both `uv pip check` and `pip check` for dependency validation
- Provides specific suggestions for common issues (numpy conflicts, PyTorch CUDA mismatches, platform incompatibilities)

**SDK Layer** (`src/ml_easy_setup/sdk/`)
- **SimpleModel**: Build neural networks via layer size lists: `SimpleModel([784, 128, 10])`
- **AutoTrainer**: Automated training loop with default configs
- **Device utilities**: Auto-detect CPU/CUDA/MPS with `get_device()`
- Design goal: One-line model building and training for common ML tasks

### Template Type System

Templates have a `type` field that determines CUDA behavior:
- `"pytorch"`: Applies PyTorch CUDA package substitutions
- `"tensorflow"`: Applies TensorFlow CUDA package substitutions
- `"minimal"`: No CUDA-specific packages (CPU-only)

### Project Structure Convention

Projects created by ML Easy Setup follow this structure:
```
project/
├── .venv/              # Virtual environment
├── src/                # Source code
├── tests/              # Tests
├── data/               # Data directory (gitignored except .gitkeep)
├── notebooks/          # Jupyter notebooks
├── outputs/            # Output files (gitignored)
├── requirements.txt    # Core dependencies
└── requirements-dev.txt # Dev dependencies
```

## Key Implementation Details

### Version Management
- Version defined in `pyproject.toml` (currently 0.5.0)
- CLI has hardcoded version in `cli.py` line 20 (should be kept in sync or made dynamic)
- SDK has separate version in `sdk/__init__.py` (0.1.0)

### UV Fallback Pattern
The codebase checks for UV availability and falls back to venv:
```python
def _check_uv_available(self) -> bool:
    try:
        result = subprocess.run(["uv", "--version"], ...])
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
```

### CUDA Detection Strategy
1. Try `nvcc --version` and parse for version number
2. Fall back to `nvidia-smi` and parse "CUDA Version" from output
3. If neither works, returns None (CPU-only mode)

### Health Check Scoring
Each category returns 0.0-1.0 score:
- `venv`: Checks virtual environment existence and pip availability
- `dependencies`: Runs `uv pip check` or `pip check`
- `gpu`: Checks nvidia-smi and PyTorch CUDA availability
- `compatibility`: Python version >= 3.10, common package versions
- `disk`: Requires >1GB free (critical) or >5GB (warning)

## Common Patterns

### Adding a New Template
1. Add entry to `BUILTIN_TEMPLATES` in `template.py`
2. Include `type`, `description`, `core_packages`, `dependencies`, `dev_dependencies`
3. Run `pytest tests/test_template.py` to verify

### Adding CLI Commands
1. Add `@main.command()` decorated function in `cli.py`
2. Use Click parameters/types for arguments
3. Use Rich for console output (console.print, Panel, Table)
4. Add test in `tests/test_cli.py`

### Error Handling Pattern
```python
try:
    # operation
    console.print("[green]✓ Success[/green]")
except Exception as e:
    console.print(f"[red]✗ Failed:[/red] {e}")
    raise click.ClickException(str(e))
```

## Platform-Specific Notes

- **Apple Silicon**: Automatically detected as "Apple Silicon (MPS)" GPU
- **Windows**: Uses `.venv/Scripts/pip.exe` instead of `.venv/bin/pip`
- **Python Version**: Requires >=3.10, warns on >=3.13 (compatibility issues)

## Dependencies

Core runtime: `click>=8.1.0`, `pyyaml>=6.0`, `rich>=13.0.0`, `packaging>=23.0`

Dev tools: `pytest`, `pytest-cov`, `black`, `ruff`, `mypy`
SDK (optional): `torch>=2.0.0`, `tqdm>=4.65.0`
