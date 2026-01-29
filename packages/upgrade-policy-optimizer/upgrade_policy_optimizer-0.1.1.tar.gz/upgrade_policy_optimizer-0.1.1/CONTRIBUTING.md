# Contributing to upgrade-policy-optimizer

Thank you for considering contributing to this project!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/eonof/upgrade-policy-optimizer
cd upgrade-policy-optimizer
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
pip install -e .
```

## Running Tests

Run the test suite with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=upo --cov-report=html
```

## Code Quality

This project uses several tools to maintain code quality:

### Formatting with Black

```bash
black src/ tests/ examples/
```

### Linting with Ruff

```bash
ruff check src/ tests/ examples/
```

### Type Checking with MyPy

```bash
mypy src/
```

## Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for all public APIs (Google style)
- Keep functions focused and modular
- Add tests for new features
- Aim for >90% test coverage

## Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: int, param2: str) -> bool:
    """Short description of what the function does.
    
    Longer description if needed, explaining behavior,
    edge cases, or providing examples.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: When and why this is raised.
        
    Example:
        >>> example_function(42, "test")
        True
    """
    pass
```

## Adding New Features

1. Create a new branch for your feature
2. Implement the feature with tests
3. Ensure all tests pass and code is formatted
4. Update documentation as needed
5. Submit a pull request

## Testing Guidelines

- Write tests for all new functionality
- Include both positive and negative test cases
- Test edge cases and boundary conditions
- Use descriptive test names that explain what is being tested

Example test structure:

```python
def test_feature_expected_behavior() -> None:
    """Test that feature works correctly under normal conditions."""
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = feature_function(setup_data)
    
    # Assert
    assert result == expected_value
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings for all new public APIs
- Include examples in docstrings where helpful
- Update examples/ if adding new capabilities

## Pull Request Process

1. Update tests and documentation
2. Ensure all tests pass locally
3. Format code with Black
4. Check types with MyPy
5. Lint with Ruff
6. Write a clear PR description explaining the changes
7. Link any related issues

## Questions?

Feel free to open an issue for questions or discussions about potential contributions!
