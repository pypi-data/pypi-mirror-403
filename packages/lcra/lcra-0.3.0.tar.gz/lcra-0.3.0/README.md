# LCRA Flood Status API

A Python library and CLI tool for extracting real-time flood status, lake levels, river conditions, and floodgate operations from the Lower Colorado River Authority (LCRA) Hydromet system.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project provides both a command-line interface and a RESTful API to access current flood status, lake levels, river conditions, and floodgate operations for the Lower Colorado River basin in Texas. It fetches data directly from LCRA's public APIs, structures it with Pydantic models, and exposes it via a modern, documented FastAPI interface.

## Features

- **Real-time Data**: Fetches up-to-date information from LCRA's official APIs
- **Structured Models**: Uses Pydantic for data validation and serialization
- **Multiple Endpoints**: Access lake levels, river conditions, floodgate operations, and complete flood reports
- **CLI Tool**: Command-line interface for quick data extraction
- **REST API**: FastAPI-based service with interactive documentation
- **Async & Fast**: Built with FastAPI and httpx for high performance
- **Type Safe**: Full type hints and Pydantic models
- **Well Tested**: Comprehensive test suite with pytest

## Installation

### From PyPI

```bash
pip install lcra
```

Or using `uv`:

```bash
uv pip install lcra
```

### From Source

```bash
git clone https://github.com/lancereinsmith/lcra.git
cd lcra
uv sync  # or: pip install -e .
```

## Requirements

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

---

## Quick Start

### CLI Usage

Extract flood operations report:

```bash
lcra get --report
```

Get lake levels:

```bash
lcra get --lake-levels
```

Save to file:

```bash
lcra get --report --save
```

### API Server

Start the API server:

```bash
lcra serve
```

Then visit `http://localhost:8080/docs` for interactive API documentation.

## Usage

### Command Line Interface

The CLI provides several commands for extracting LCRA data:

#### Get Data

```bash
# Full flood operations report
lcra get --report

# Lake levels only
lcra get --lake-levels

# River conditions only
lcra get --river-conditions

# Floodgate operations only
lcra get --floodgate-operations
```

#### Save Output

```bash
# Auto-named timestamped file
lcra get --report --save
# Creates: reports/report_2025-01-15T10-30-45.json

# Custom filename
lcra get --report --saveas my_report
# Creates: reports/my_report.json
```

#### Start API Server

```bash
# Default (localhost:8080)
lcra serve

# Custom host and port
lcra serve --host 0.0.0.0 --port 9000
```

### Python API

```python
from scraper import LCRAFloodDataScraper
from lcra import FloodOperationsReport

async with LCRAFloodDataScraper() as scraper:
    # Get complete report
    report: FloodOperationsReport = await scraper.scrape_all_data()

    # Get specific data
    lake_levels = await scraper.scrape_lake_levels()
    river_conditions = await scraper.scrape_river_conditions()
    floodgate_operations = await scraper.scrape_floodgate_operations()
```

---

## REST API Endpoints

| Endpoint                  | Method | Description                                 |
|--------------------------|--------|---------------------------------------------|
| `/`                      | GET    | API root info                               |
| `/health`                | GET    | Health check (LCRA API connectivity)        |
| `/flood-report`          | GET    | Complete flood operations report            |
| `/lake-levels`           | GET    | Current lake levels at dams                 |
| `/river-conditions`      | GET    | Current river conditions                    |
| `/floodgate-operations`  | GET    | Current floodgate operations                |
| `/docs`                  | GET    | Swagger UI (interactive API docs)           |
| `/redoc`                 | GET    | ReDoc (alternative API docs)                |

### Example API Usage

```bash
# Get complete flood report
curl http://localhost:8080/flood-report

# Get lake levels
curl http://localhost:8080/lake-levels

# Health check
curl http://localhost:8080/health
```

Visit `http://localhost:8080/docs` for interactive API documentation.

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/lancereinsmith/lcra.git
cd lcra

# Install with dev dependencies
uv sync --group dev
```

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

### Building Documentation

```bash
mkdocs serve  # Local development
mkdocs build  # Build static site
```

## Project Structure

```text
lcra/
├── src/
│   ├── api/             # FastAPI application
│   │   └── __init__.py
│   ├── scraper/         # LCRA data scraper
│   │   └── __init__.py
│   └── lcra/            # Data models and CLI
│       ├── __init__.py
│       └── cli.py       # CLI entrypoint
├── tests/               # Test suite
├── docs/                # Documentation
├── pyproject.toml       # Project configuration
└── README.md            # This file
```

## Data Sources

This library accesses data from the [LCRA Hydromet system](https://hydromet.lcra.org/), which provides:

- **Lake Levels**: Current elevations at major dams (Buchanan, Inks, LBJ, Marble Falls, Travis, Austin, Bastrop)
- **River Conditions**: Stage, flow, and flood status at various gauge locations
- **Floodgate Operations**: Current and forecasted floodgate operations
- **Narrative Summaries**: Text summaries of current flood conditions

## Troubleshooting

- **No Data Returned**: Ensure the LCRA website and APIs are accessible from your network. The `/health` endpoint will indicate if the upstream API is reachable.
- **Dependency Issues**: Make sure you have run `uv sync` and are using Python 3.10 or higher.
- **Port Conflicts**: If port 8080 is in use, specify another port with `--port <number>`.
- **Import Errors**: Ensure the package is installed: `pip install lcra` or `uv pip install lcra`

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## Documentation

Full documentation is available at: <https://lancereinsmith.github.io/lcra/>

Or build locally:

```bash
mkdocs serve
```

## License

MIT License - see LICENSE file for details.

## Credits

- [LCRA Hydromet](https://hydromet.lcra.org/) for providing public data
- Built with [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), and [httpx](https://www.python-httpx.org/)
- Documentation powered by [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
