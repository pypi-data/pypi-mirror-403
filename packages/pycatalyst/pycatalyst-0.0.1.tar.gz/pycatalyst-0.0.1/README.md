# pycatalyst

A modern Python package template. Replace this with your package description.

## Installation

```bash
pip install pycatalyst
```

From source (editable):

```bash
git clone https://github.com/your-org/pycatalyst
cd pycatalyst
pip install -e ".[dev]"
```

## Quick Start

```python
import pycatalyst

print(pycatalyst.__version__)
```

## Development

- **Lint & format:** `ruff check . && ruff format .`
- **Type check:** `mypy src/`
- **Tests:** `pytest`
- **Coverage:** `pytest --cov=pycatalyst --cov-report=term-missing`

## Publishing

1. Bump version in `pyproject.toml` and `CHANGELOG.md`.
2. Create a release tag: `git tag v0.1.0 && git push origin v0.1.0`.
3. The GitHub Action uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/); configure the publisher on PyPI for this repo, then the workflow will publish on tag push.

## License

MIT
