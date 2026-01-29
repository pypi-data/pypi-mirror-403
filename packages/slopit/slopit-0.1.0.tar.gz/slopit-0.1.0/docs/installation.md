# Installation

slopit requires Python 3.13 or later.

## Using pip

Install from PyPI:

```bash
pip install slopit
```

## Using uv

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Install slopit with:

```bash
uv add slopit
```

Or create a new project with slopit:

```bash
uv init my-analysis
cd my-analysis
uv add slopit
```

## Optional Dependencies

### LLM Detection

For LLM-based content analysis (experimental), install with the `llm` extra:

```bash
pip install slopit[llm]
```

This adds PyTorch and Hugging Face Transformers for model-based detection.

### Server Mode

For running slopit as a web service:

```bash
pip install slopit[server]
```

This adds FastAPI and Uvicorn for HTTP API endpoints.

### Development

For contributing to slopit:

```bash
pip install slopit[dev]
```

This adds testing, linting, and documentation tools.

## Development Setup

Clone the repository and install in development mode:

```bash
git clone https://github.com/aaronstevenwhite/slopit.git
cd slopit/python

# Using uv (recommended)
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Using uv
uv run pytest

# Or directly
pytest
```

### Type Checking

slopit uses strict type checking with pyright:

```bash
# Using uv
uv run pyright

# Or directly
pyright
```

### Linting and Formatting

slopit uses ruff for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Fix issues automatically
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Verifying Installation

Verify that slopit is installed correctly:

```python
import slopit
print(slopit.__version__)
```

Or using the CLI:

```bash
slopit --version
```

## Python Version Requirements

slopit requires Python 3.13+ because it uses:

- The `type` statement for type aliases (PEP 695)
- Modern union syntax (`X | Y` instead of `Union[X, Y]`)
- Built-in generic types (`list[str]` instead of `List[str]`)

If you need to support older Python versions, please open an issue on GitHub.

## Dependencies

Core dependencies (installed automatically):

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >= 2.0 | Numerical computations |
| pandas | >= 2.2 | Data manipulation |
| scikit-learn | >= 1.5 | Machine learning utilities |
| sentence-transformers | >= 3.0 | Text embeddings |
| spacy | >= 3.8 | NLP processing |
| pydantic | >= 2.10 | Data validation |
| rich | >= 13.0 | Terminal output |
| click | >= 8.1 | CLI framework |
