# Contributing to TruthLens

Thank you for your interest in contributing to TruthLens! We welcome contributions from developers, researchers, and enthusiasts.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please read and follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 15+
- Git

### Setup

1. Fork the repository
2. Clone your fork
3. Follow the [Development Setup Guide](DEVELOPMENT.md)

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/feature-name`
- `fix/bug-description`
- `docs/documentation-update`
- `refactor/code-improvement`

### Commit Messages

Follow conventional commits:
- `feat: add new feature`
- `fix: fix bug`
- `docs: update documentation`
- `style: format code`
- `refactor: refactor code`
- `test: add tests`
- `chore: maintenance`

Example:
```
feat: add batch image analysis mode

- Implement batch upload UI
- Add queue management
- Update API to handle multiple images
```

### Pull Request Process

1. Update documentation
2. Add/update tests
3. Run pre-commit hooks
4. Push to your fork
5. Create pull request
6. Wait for review

## Coding Standards

### Python

- Follow PEP 8
- Use Black for formatting
- Use isort for import sorting
- Add docstrings to functions
- Type hints where appropriate

### JavaScript/React

- Follow ESLint rules
- Use functional components
- Use hooks instead of classes
- Add PropTypes or TypeScript
- Comment complex logic

### General

- Keep functions small and focused
- Use meaningful variable names
- Avoid magic numbers
- Write self-documenting code
- Add comments for non-obvious logic

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
npm test -- --coverage
```

### Test Requirements

- New features must have tests
- Bug fixes must include regression tests
- Maintain ≥85% backend coverage
- Maintain ≥80% frontend coverage

## Submitting Changes

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Coverage meets requirements
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

### Pull Request Template

Use the PR template when creating pull requests.

### Review Process

1. Automated checks must pass
2. At least one maintainer approval
3. All feedback addressed
4. Squash and merge to main

## Reporting Issues

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Screenshots if applicable

### Feature Requests

Include:
- Description of the feature
- Use case
- Proposed implementation
- Alternatives considered

### Security Issues

Do not report security issues publicly. Email security@truthlens.app instead.

## Questions

- Check existing documentation
- Search existing issues
- Ask in GitHub Discussions
- Contact maintainers

## Recognition

Contributors will be acknowledged in the project documentation.

Thank you for contributing to TruthLens!
