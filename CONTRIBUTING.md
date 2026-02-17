# Contributing to SkyModderAI

Thank you for your interest in contributing to SkyModderAI! We appreciate your time and effort in making this project better. This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Development Workflow](#development-workflow)
  - [Creating a New Branch](#creating-a-new-branch)
  - [Making Changes](#making-changes)
  - [Testing](#testing)
  - [Submitting a Pull Request](#submitting-a-pull-request)
- [Code Style and Guidelines](#code-style-and-guidelines)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- **Python 3.9+** (3.11+ recommended)
- Git
- pip (Python package manager)

### Setting Up the Development Environment

#### Linux / macOS / WSL

```bash
# Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

#### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### Creating a New Branch

1. Make sure your local `main` branch is up to date:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/description-of-fix
   ```

### Making Changes

1. Make your changes to the codebase.
2. Run the tests to ensure everything works as expected:
   ```bash
   pytest
   ```
3. Run linters and formatters:
   ```bash
   black .
   ruff check . --fix
   ```

### Testing

We use `pytest` for testing. To run the test suite:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=.
```

### Submitting a Pull Request

1. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "feat: add new feature"
   ```

2. Push your changes to your fork:
   ```bash
   git push origin your-branch-name
   ```

3. Open a pull request against the `main` branch.
4. Fill out the pull request template with details about your changes.
5. Wait for the CI to run and address any issues that arise.

## Code Style and Guidelines

- We use [Black](https://github.com/psf/black) for code formatting.
- We use [Ruff](https://github.com/charliermarsh/ruff) for linting.
- We use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for documentation.
- Keep functions small and focused on a single responsibility.
- Write tests for new features and bug fixes.
- Update the documentation when adding new features or changing existing behavior.

## Continuous Integration (CI)

Our CI pipeline automatically runs on every push and pull request. The CI includes:

### CI Jobs

| Job | Description |
|-----|-------------|
| **Lint** | Ruff linting and import sorting |
| **Test** | pytest on Python 3.9, 3.10, 3.11, 3.12 |
| **Test Games** | Parser initialization for all 8 supported games |
| **Performance** | Load order analysis performance budget (<5s for 500 mods) |
| **Docker** | Docker image build and smoke test |
| **Security** | Dependency vulnerability scanning (safety, pip-audit) |
| **Integration** | End-to-end API tests |

### Passing CI

Before submitting a PR, ensure:
- [ ] All tests pass locally: `pytest`
- [ ] Linting passes: `ruff check .`
- [ ] Your code works on Python 3.9+
- [ ] You've added tests for new features

### Coverage

We track code coverage with Codecov. Aim for >70% coverage on new code.

```bash
# Run tests with coverage report
pytest --cov=. --cov-report=term-missing
```

## Reporting Issues

If you find a bug or have a suggestion, please open an issue on GitHub. Be sure to include:

- A clear description of the issue
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your operating system and Python version

## Feature Requests

We welcome feature requests! Please open an issue and use the "Feature Request" template to describe your idea.

## License

By contributing to SkyModderAI, you agree that your contributions will be licensed under the [MIT License](LICENSE).

| Task | Linux/macOS | Windows |
|------|-------------|---------|
| Run app | `./run.sh` or `make run` | `run.bat` or `run.ps1` |
| Run tests | `make test` or `./venv/bin/pytest` | `venv\Scripts\pytest` |
| Download LOOT data | `make loot` or `make loot GAME=fallout4` | `venv\Scripts\python loot_parser.py skyrimse` |
| Clean | `make clean` | Delete `venv`, `__pycache__` |

## Environment

Copy `.env.example` to `.env` and fill in values for Stripe, email, etc. See README for full config.

## Testing Pro Locally

Add to `.env`:
```
SKYMODDERAI_DEV_PRO=1
```
Any logged-in user gets full Pro features (no payment).

## Code Style

- Ruff for linting: `ruff check .`
- Pytest for tests: `pytest tests/ -v`

## Submitting Changes

1. Fork the repo
2. Create a branch
3. Make your changes
4. Run tests
5. Open a PR
