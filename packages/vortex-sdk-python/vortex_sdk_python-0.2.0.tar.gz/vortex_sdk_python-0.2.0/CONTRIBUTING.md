# Contributing to Vortex SDK Python

Thank you for your interest in contributing to the Vortex SDK Python wrapper! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details**: OS, Python version, Node.js version
- **Code samples** or test cases that demonstrate the issue
- **Error messages** and stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** explaining why this enhancement would be useful
- **Proposed implementation** if you have ideas
- **Alternatives considered**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** if you're adding functionality
4. **Update documentation** if needed
5. **Ensure tests pass**
6. **Create a pull request**

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vortex-python-sdk.git
cd vortex-python-sdk

# Install npm dependencies
npm install

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vortex_sdk --cov-report=html

# Run specific test file
pytest tests/test_sdk.py

# Run with verbose output
pytest -v
```

### Code Style

We follow Python best practices:

- **PEP 8** for code style
- **Type hints** for all function signatures
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **mypy** for type checking

```bash
# Format code
black src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/

# Type check
mypy src/
```

### Documentation

- Update docstrings for any modified functions/classes
- Follow [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings
- Update `README.md` if adding user-facing features
- Add examples for new functionality

## Project Structure

```
vortex-python-sdk/
├── src/vortex_sdk/          # Main package code
│   ├── __init__.py          # Package exports
│   ├── sdk.py               # Main SDK class
│   ├── bridge.py            # Node.js bridge
│   ├── types.py             # Type definitions
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Test files
├── examples/                # Usage examples
├── docs/                    # Documentation
└── package.json             # npm dependencies
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for new token
fix: resolve import error with global packages
docs: update installation instructions
test: add tests for async methods
chore: update dependencies
```

## Release Process

For maintainers:

1. Update version in `setup.py`, `pyproject.toml`, and `__init__.py`
2. Update `CHANGELOG.md` with changes
3. Create PR with version bump
4. After merge, tag the release: `git tag v0.1.0`
5. Push tag: `git push origin v0.1.0`
6. GitHub Actions will publish to PyPI automatically

## Questions?

- Open a [GitHub Discussion](https://github.com/pendulum-chain/vortex-python-sdk/discussions)
- Join our [Discord](https://discord.gg/pendulum) (if applicable)
- Email: info@pendulumchain.tech

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
