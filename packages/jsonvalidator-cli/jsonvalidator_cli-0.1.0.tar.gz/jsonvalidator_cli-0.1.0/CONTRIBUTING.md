# Contributing to JSON Validator CLI

Thank you for your interest in contributing to JSON Validator CLI! We welcome contributions from everyone.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- A GitHub account

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/jsonvalidator.git
   cd jsonvalidator
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

5. **Create a branch for your feature:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=jsonvalidator --cov-report=html
```

### Code Style

We use `flake8` for linting. Please ensure your code passes linting:

```bash
flake8 jsonvalidator tests
```

**Coding standards:**
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small

### Testing Your Changes

Before submitting a PR, make sure:

1. All tests pass
2. Code is properly formatted
3. New features have tests
4. Documentation is updated if needed

**Example: Testing manually**
```bash
# Test validation
python -m jsonvalidator.cli validate examples/valid.json

# Test schema validation
python -m jsonvalidator.cli validate examples/user.json --schema examples/schema.json
```

## Submitting Changes

### Pull Request Process

1. **Update documentation** if you're adding features
2. **Add tests** for new functionality
3. **Update CHANGELOG.md** with your changes
4. **Commit your changes** with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "Add feature: description of what you added"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference any related issues

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests when relevant

**Examples:**
- `Fix validation error for nested objects`
- `Add support for YAML schema files (#42)`
- `Update documentation for schema validation`

## What to Contribute

### Good First Issues

Look for issues labeled `good first issue` - these are great for newcomers.

### Ideas for Contributions

- **Bug fixes** - Found a bug? Fix it!
- **New features** - YAML support, batch validation, etc.
- **Documentation** - Improve README, add examples
- **Tests** - Increase test coverage
- **Performance** - Optimize existing code

## Code Review Process

- Maintainers will review your PR within 2-3 days
- You may be asked to make changes
- Once approved, a maintainer will merge your PR

## Community Guidelines

- Be respectful and welcoming
- Provide constructive feedback
- Help others learn and grow
- Follow our Code of Conduct

## Questions?

- Open an issue for questions
- Tag your issue with `question` label
- We're here to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
