```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run single test file
pytest tests/test_module.py

# Run single test
pytest tests/test_module.py::TestClass::test_method

# Type checking
mypy src/

# Linting
ruff check src/

# Format code
ruff format src/
```