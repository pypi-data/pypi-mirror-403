# Contributing to Veritas Framework

Thank you for your interest in contributing to Veritas! This document provides guidelines for contributions.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior.

## Philosophy

Veritas is built on a fundamental principle: **Trust is character, not permission.**

When contributing, keep these principles in mind:

1. **Verification Before Claim** - All features must be tested
2. **Loud Failure** - Error handling must be explicit
3. **Honest Uncertainty** - Document limitations clearly
4. **Paper Trail** - All decisions should be traceable
5. **Diligent Execution** - No shortcuts in implementation

## Ways to Contribute

| Contribution Type | Description | Labels |
|-------------------|-------------|--------|
| **Bug Reports** | Report issues you encounter | `bug` |
| **Feature Requests** | Suggest new capabilities | `enhancement` |
| **Documentation** | Improve docs, add examples | `documentation`, `good first issue` |
| **Code** | Fix bugs, add features | varies |
| **Tests** | Improve test coverage | `testing`, `good first issue` |
| **Integrations** | Add adapters for frameworks | `integration` |

### Good First Issues

Look for issues labeled `good first issue`. These are great for newcomers:

- Adding docstrings to functions
- Writing unit tests for existing code
- Improving error messages
- Adding examples to documentation
- Creating integration adapters

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/veritas-framework.git
   cd veritas-framework
   ```

3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Run tests to ensure everything works:
   ```bash
   pytest
   ```

## Development Workflow

### Creating a Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### Making Changes

1. Write tests first (TDD encouraged)
2. Implement your changes
3. Run the test suite: `pytest`
4. Run the linter: `ruff check .`
5. Run type checking: `mypy veritas/`

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(gates): add max_age_hours requirement option

Allows gates to require evidence newer than a specified age.
This prevents stale evidence from passing gates.

Closes #123
```

### Pull Requests

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Create PR with clear description

## Code Standards

### Style

- Follow PEP 8
- Use type hints for all public APIs
- Maximum line length: 100 characters
- Use `ruff` for formatting

### Documentation

- All public classes and functions need docstrings
- Use Google-style docstrings
- Include examples in docstrings when helpful

### Testing

- Aim for >80% test coverage
- Write both unit and integration tests
- Use pytest fixtures for common setup
- Test edge cases and error conditions

## Architecture Guidelines

When adding new features:

1. **Core vs Layers** - Core defines types and behaviors; Layers enforce them
2. **Evidence-Centric** - Every claim should be backed by evidence
3. **Composable** - Components should work independently and together
4. **Configurable** - Behaviors should be adjustable via configuration

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
