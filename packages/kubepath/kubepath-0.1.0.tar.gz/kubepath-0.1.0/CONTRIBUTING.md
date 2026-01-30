# Contributing to Kubepath

Thank you for your interest in contributing to Kubepath! This project aims to make learning Kubernetes accessible and fun for everyone. We welcome contributions of all kinds — from bug fixes and documentation improvements to new chapters and features.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Content Contributions](#content-contributions)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Code of Conduct](#code-of-conduct)

---

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/<your-username>/kubepath.git
   cd kubepath
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/nithin-nk/kubepath.git
   ```

---

## Development Setup

### Prerequisites

- Python 3.12+
- Docker Desktop (for running Kubernetes locally)
- kubectl
- minikube

### Install Dependencies

We use `uv` as our package manager:

```bash
# Install uv if you don't have it
pip install uv

# Install all dependencies
uv sync

# Verify the installation
uv run kubepath --help
```

### Running the Application

```bash
# Start the CLI
uv run kubepath

# List chapters
uv run kubepath list

# Start a specific chapter
uv run kubepath start 1
```

---

## Project Structure

```
kubepath/
├── kubepath/                 # Main application code
│   ├── cli.py               # Typer CLI commands and main entry point
│   ├── console.py           # Rich console configuration
│   ├── config.py            # Configuration management
│   ├── content/
│   │   ├── loader.py        # YAML chapter loading
│   │   └── renderer.py      # Rich content rendering
│   ├── k8s/
│   │   ├── detector.py      # Kubernetes environment detection
│   │   ├── client.py        # Kubernetes API wrapper
│   │   ├── validator.py     # Task validation
│   │   └── deployer.py      # Scenario deployment
│   ├── commands/
│   │   └── practice.py      # Command practice engine
│   ├── scenarios/
│   │   ├── engine.py        # Scenario execution
│   │   ├── hints.py         # Hint management
│   │   └── cleanup.py       # Resource cleanup
│   ├── quiz/
│   │   ├── engine.py        # Quiz orchestration
│   │   ├── multiple_choice.py
│   │   ├── command_challenge.py
│   │   ├── state_verification.py
│   │   └── yaml_exercise.py
│   ├── gamification/
│   │   ├── levels.py        # Level system
│   │   ├── streaks.py       # Streak tracking
│   │   └── sharing.py       # Social sharing
│   ├── scoring/
│   │   └── tracker.py       # Score calculation
│   ├── ai/
│   │   └── gemini.py        # Google Gemini integration
│   └── utils/
│       ├── progress.py      # Progress tracking
│       └── updater.py       # Auto-update functionality
├── content/
│   ├── chapters/            # Chapter YAML files (01-pods.yaml, etc.)
│   └── schema.md            # Content schema documentation
├── tests/
│   ├── unit/               # Fast, isolated unit tests
│   ├── integration/        # End-to-end integration tests
│   └── fixtures/           # Test data and fixtures
├── README.md
├── CONTRIBUTING.md          # This file
├── pyproject.toml          # Project configuration
└── CLAUDE.md               # AI assistant instructions
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create a new branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run only unit tests (faster)
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/ -v --cov=kubepath
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "Add: brief description of your changes"
```

**Commit message prefixes:**
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for enhancements
- `Docs:` for documentation changes
- `Test:` for test additions/changes
- `Refactor:` for code refactoring

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

---

## Testing

### Test Structure

- **Unit tests** (`tests/unit/`): Fast, isolated tests with mocked dependencies
- **Integration tests** (`tests/integration/`): Slower tests that may use real Kubernetes

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Specific module
uv run pytest tests/unit/test_loader.py -v

# With coverage report
uv run pytest tests/ -v --cov=kubepath --cov-report=html
```

### Coverage Requirements

- **Overall**: >= 80%
- **Core business logic**: >= 90%
  - `kubepath/scoring/tracker.py`
  - `kubepath/k8s/validator.py`
  - `kubepath/utils/progress.py`
  - `kubepath/quiz/*`

### Writing Tests

```python
# tests/unit/test_example.py
from unittest.mock import patch, MagicMock
import pytest

from kubepath.module import function_to_test

def test_function_returns_expected_value():
    """Test that function returns the expected value."""
    result = function_to_test("input")
    assert result == "expected_output"

def test_function_handles_error():
    """Test that function handles errors gracefully."""
    with pytest.raises(ValueError):
        function_to_test("invalid_input")
```

---

## Content Contributions

### Adding a New Chapter

Chapters are defined in YAML files in `content/chapters/`. Each chapter has 4 sections:

```yaml
chapter:
  number: 1
  title: "Chapter Title"
  description: "Brief description"

concepts:
  - title: "Concept 1"
    content: |
      Markdown content explaining the concept...

command_practice:
  - command: "kubectl get pods"
    description: "List all pods"
    expected_output_contains: "NAME"
    points: 10

scenarios:
  - id: "scenario-1"
    title: "Fix the broken deployment"
    description: "Debug and fix this deployment"
    manifest: |
      apiVersion: apps/v1
      kind: Deployment
      ...
    hints:
      - "Check the image name"
      - "Look for typos"
    validation:
      type: "resource_state"
      resource: "deployment/my-app"
      state: "Available"
    points: 20

quiz:
  questions:
    - type: "multiple_choice"
      question: "What command lists pods?"
      options:
        - "kubectl get pods"
        - "kubectl list pods"
        - "kubectl show pods"
      correct: 0
      points: 5
```

### Quiz Question Types

1. **multiple_choice**: Standard MCQ
2. **command_challenge**: User types a kubectl command
3. **state_verification**: User performs action, system verifies cluster state
4. **yaml_exercise**: User completes YAML with blanks

See `content/schema.md` for complete documentation.

---

## Code Style

### Python Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black default)

### Docstrings

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of what the function does.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is invalid.
    """
    pass
```

### Imports

Order imports as:
1. Standard library
2. Third-party packages
3. Local imports

```python
import os
from pathlib import Path

import typer
from rich.console import Console

from kubepath.config import settings
from kubepath.utils import load_progress
```

---

## Pull Request Process

### Before Submitting

- [ ] Tests pass: `uv run pytest tests/ -v`
- [ ] Code coverage >= 80%
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear

### PR Template

When creating a PR, include:

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Testing
- How was this tested?
- Any manual testing needed?

## Related Issues
Fixes #123
```

### Review Process

1. Maintainer reviews the PR
2. Address any feedback
3. Once approved, PR will be merged

---

## Reporting Issues

### Bug Reports

Please include:
- Python version (`python3 --version`)
- OS and version
- Kubepath version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

Please include:
- Clear description of the feature
- Use case / why it's useful
- Any implementation ideas

### Questions

For questions about usage, please check:
1. [README.md](README.md)
2. Existing issues
3. Open a new issue with the "question" label

---

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behaviors:**
- Trolling, insulting comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the maintainer. All complaints will be reviewed and investigated.

---

## Questions?

If you have any questions about contributing, feel free to:
- Open an issue with the "question" label
- Reach out to the maintainer

Thank you for contributing to Kubepath!
