# Installation

## Requirements

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Install from PyPI

```bash
pip install lcra
```

Or using `uv`:

```bash
uv pip install lcra
```

## Install as a CLI Tool

To install as a standalone CLI tool (recommended for command-line usage):

```bash
uv tool install lcra
```

This installs the `lcra` command globally without affecting your project's dependencies.

## Install from Source

1. Clone the repository:

```bash
git clone https://github.com/lancereinsmith/lcra.git
cd lcra
```

1. Install dependencies:

Using `uv`:

```bash
uv sync
```

Using `pip`:

```bash
pip install -e .
```

## Development Installation

For development, install with dev dependencies:

```bash
uv sync --group dev
```

Or:

```bash
pip install -e ".[dev]"
```

## Verify Installation

Check that the CLI is available:

```bash
lcra --help
```

Or test the Python import:

```python
from scraper import LCRAFloodDataScraper
```

