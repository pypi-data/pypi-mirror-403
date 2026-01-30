# Contributing to ML-EcoLyzer

Thank you for your interest in contributing to ML-EcoLyzer! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ml-ecolyzer.git
   cd ml-ecolyzer
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/JomaMinoza/ml-ecolyzer.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or conda for package management
- Git

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install in development mode with all dependencies:
   ```bash
   pip install -e ".[dev,docs]"
   ```

3. Install pre-commit hooks (optional but recommended):
   ```bash
   pre-commit install
   ```

### Optional Framework Dependencies

Depending on what you're working on, you may need additional dependencies:

```bash
# For HuggingFace support
pip install -e ".[huggingface]"

# For PyTorch support
pip install -e ".[pytorch]"

# For full installation
pip install -e ".[all]"
```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. Make your changes following our [code style](#code-style) guidelines

3. Add or update tests as needed

4. Update documentation if you're adding new features

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mlecolyzer --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run tests with specific markers
pytest -m "not slow"          # Skip slow tests
pytest -m "not gpu"           # Skip GPU tests
pytest -m sklearn             # Only sklearn tests
```

### Test Markers

- `slow`: Long-running tests
- `integration`: Integration tests
- `gpu`: Tests requiring GPU
- `huggingface`: Tests requiring HuggingFace
- `sklearn`: Tests requiring scikit-learn
- `pytorch`: Tests requiring PyTorch

### Writing Tests

- Place tests in the `tests/` directory
- Follow the naming convention `test_*.py`
- Use pytest fixtures from `conftest.py`
- Mark tests appropriately with pytest markers

Example:
```python
import pytest
from mlecolyzer.core.config import ModelConfig

def test_model_config_creation():
    config = ModelConfig(name="gpt2", task="text")
    assert config.name == "gpt2"
    assert config.framework == "huggingface"

@pytest.mark.slow
def test_model_loading():
    # Long-running test
    pass

@pytest.mark.gpu
def test_gpu_monitoring():
    # Test requiring GPU
    pass
```

## Code Style

We use the following tools to maintain code quality:

### Formatting

- **Black** for code formatting (line length: 88)
- **isort** for import sorting

```bash
# Format code
black mlecolyzer tests
isort mlecolyzer tests
```

### Linting

- **Flake8** for style checking
- **MyPy** for type checking

```bash
# Run linters
flake8 mlecolyzer tests
mypy mlecolyzer
```

### Guidelines

1. **Type hints**: Use type hints for function signatures
2. **Docstrings**: Use Google-style docstrings for public functions/classes
3. **Imports**: Group imports (stdlib, third-party, local)
4. **Comments**: Write clear, concise comments for complex logic

Example docstring:
```python
def calculate_ess(parameters: int, co2_grams: float) -> float:
    """
    Calculate Environmental Sustainability Score (ESS).

    Args:
        parameters: Number of model parameters in millions
        co2_grams: CO2 emissions in grams

    Returns:
        ESS score (parameters per gram of CO2)

    Raises:
        ValueError: If co2_grams is zero or negative
    """
    if co2_grams <= 0:
        raise ValueError("CO2 emissions must be positive")
    return parameters / co2_grams
```

## Submitting Changes

### Pull Request Process

1. Ensure all tests pass locally
2. Update documentation if needed
3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Create a Pull Request on GitHub

### PR Guidelines

- Use a clear, descriptive title
- Reference any related issues (e.g., "Fixes #123")
- Provide a summary of changes
- Include test results or screenshots if applicable

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Test addition

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Updated documentation

## Related Issues
Fixes #(issue number)
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Environment**: Python version, OS, installed packages
2. **Steps to reproduce**: Minimal code example
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full traceback if applicable

### Feature Requests

For feature requests, please describe:

1. **Use case**: Why this feature would be useful
2. **Proposed solution**: How you envision it working
3. **Alternatives**: Other solutions you've considered

## Project Structure

```
ml-ecolyzer/
├── mlecolyzer/
│   ├── core/           # Core functionality (runner, config)
│   ├── monitoring/     # Hardware and environmental monitoring
│   ├── models/         # Model loading utilities
│   ├── datasets/       # Dataset loading utilities
│   ├── metrics/        # Accuracy and environmental metrics
│   ├── utils/          # Helper functions
│   ├── cli/            # Command-line interface
│   └── data/           # Reference data (CSV files)
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Example scripts
```

## Questions?

- Open a [Discussion](https://github.com/JomaMinoza/ml-ecolyzer/discussions) on GitHub
- Check existing [Issues](https://github.com/JomaMinoza/ml-ecolyzer/issues)

Thank you for contributing to sustainable ML!
