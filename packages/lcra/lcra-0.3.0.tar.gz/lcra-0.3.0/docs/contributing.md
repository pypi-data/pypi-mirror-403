# Contributing

Thank you for your interest in contributing to the LCRA Flood Status API!

## Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/lancereinsmith/lcra.git
cd lcra
```

1. Install development dependencies:

```bash
uv sync --group dev
```

1. Run tests:

```bash
pytest
```

1. Run linting:

```bash
ruff check .
black --check .
mypy .
```

## Code Style

- Follow PEP 8
- Use type hints
- Format with Black (line length 100)
- Lint with Ruff
- Type check with mypy

## Testing

- Write tests for new features
- Ensure all tests pass: `pytest`
- Aim for good test coverage

## Pull Requests

1. Create a feature branch
2. Make your changes
3. Add tests
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

## Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:

- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Python version and environment details

