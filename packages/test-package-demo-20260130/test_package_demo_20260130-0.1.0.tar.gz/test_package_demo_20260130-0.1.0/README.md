# Test Package Demo

A simple Python package for demonstrating the package publishing process.

## Features

- `add(a, b)`: Adds two numbers
- `greet(name)`: Generates a greeting message

## Installation

```bash
pip install test-package-demo
```

## Usage

```python
from test_package import add, greet

# Add two numbers
result = add(1, 2)
print(result)  # Output: 3

# Generate a greeting
message = greet("World")
print(message)  # Output: Hello, World!
```

## Development

### Build the package

```bash
python -m build
```

### Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

## License

MIT License
