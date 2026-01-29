# Contributing to Voight

Thank you for your interest in contributing to Voight! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/voight.git
   cd voight
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run tests:
   ```bash
   uv run pytest tests/ -v
   ```

4. Run the CLI:
   ```bash
   uv run voight --help
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_integration.py -v

# Run with coverage
uv run pytest tests/ --cov=agent_evals --cov-report=html
```

### Code Style

We follow standard Python conventions:

- Use type hints for function signatures
- Write docstrings for public functions and classes
- Keep functions focused and reasonably sized
- Prefer descriptive variable names

### Project Structure

```
voight/
├── src/agent_evals/       # Main package
│   ├── __init__.py        # Public API exports
│   ├── cli.py             # CLI implementation
│   ├── core.py            # Core interfaces (EvalResult, protocols)
│   ├── decorators.py      # @scenario decorator
│   ├── generators.py      # Input generators
│   ├── judges.py          # Evaluation judges
│   └── sandbox.py         # File system sandbox
├── tests/                 # Test suite
├── recipes/               # Example recipes
└── docs/                  # Documentation
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(generators): add FuzzGenerator for random input generation`
- `fix(sandbox): ensure directory restoration on exception`
- `docs(readme): add quickstart guide`

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request with a clear description

## Adding New Features

### Adding a New Judge

1. Create the judge class in `src/agent_evals/judges.py`
2. Implement the `evaluate()` method returning `EvalResult`
3. Export it in `src/agent_evals/__init__.py`
4. Add tests in `tests/test_intelligence.py`
5. Add a recipe in `recipes/`

### Adding a New Generator

1. Create the generator class in `src/agent_evals/generators.py`
2. Implement the `generate()` method returning `list[str]`
3. Export it in `src/agent_evals/__init__.py`
4. Add tests in `tests/test_intelligence.py`

## Testing Guidelines

- Write tests for all new functionality
- Include both positive and negative test cases
- Test edge cases and error handling
- Use descriptive test names that explain the scenario

## Questions?

- Open a [GitHub Issue](https://github.com/your-org/voight/issues) for bugs or feature requests
- Start a [Discussion](https://github.com/your-org/voight/discussions) for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
