# AppDevCommons

A collection of common utilities and functionalities for Python applications.

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/appdevcommons.git
cd appdevcommons

# Install in editable mode for development
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Using pip

```bash
pip install appdevcommons
```

## Development Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Format code:**
   ```bash
   black src/ tests/
   ```

5. **Lint code:**
   ```bash
   ruff check src/ tests/
   ```

6. **Type checking:**
   ```bash
   mypy src/
   ```

## Usage

```python
import appdevcommons

# Your code here
```

## Building and Distributing

To build the package:

```bash
# Clean previous builds (important to avoid uploading old versions)
rm -rf dist/ build/
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Build the package
python -m build
```

To upload to PyPI (after configuring credentials):

```bash
twine upload dist/*
```

## Project Structure

```
AppDevCommons/
├── src/
│   └── appdevcommons/
│       ├── __init__.py
│       └── ...  # Your modules here
├── tests/
│   ├── __init__.py
│   └── test_*.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── LICENSE
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
