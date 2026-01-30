# LCRA Flood Status API

A Python library and CLI tool for extracting real-time flood status, lake levels, river conditions, and floodgate operations from the Lower Colorado River Authority (LCRA) Hydromet system.

## Features

- **Real-time Data**: Fetches up-to-date information from LCRA's official APIs
- **Structured Models**: Uses Pydantic for data validation and serialization
- **Multiple Endpoints**: Access lake levels, river conditions, floodgate operations, and complete flood reports
- **Async & Fast**: Built with FastAPI and httpx for high performance
- **CLI Tool**: Command-line interface for quick data extraction
- **REST API**: FastAPI-based service with interactive documentation
- **Type Safe**: Full type hints and Pydantic models

## Quick Start

### Installation

```bash
pip install lcra
```

Or using `uv`:

```bash
uv pip install lcra
```

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
lcra serve --host 0.0.0.0 --port 8080
```

Then visit `http://localhost:8080/docs` for interactive API documentation.

## Data Sources

This library accesses data from the [LCRA Hydromet system](https://hydromet.lcra.org/), which provides:

- **Lake Levels**: Current elevations at major dams (Buchanan, Inks, LBJ, Marble Falls, Travis, Austin, Bastrop)
- **River Conditions**: Stage, flow, and flood status at various gauge locations
- **Floodgate Operations**: Current and forecasted floodgate operations
- **Narrative Summaries**: Text summaries of current flood conditions

## Project Structure

```text
lcra/
├── src/
│   ├── api/         # FastAPI application
│   ├── scraper/     # LCRA data scraper
│   └── lcra/        # Data models and CLI
├── tests/           # Test suite
└── docs/            # Documentation
```

## License

MIT License - see LICENSE file for details.

## Credits

- [LCRA Hydromet](https://hydromet.lcra.org/) for providing public data
- Built with [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), and [httpx](https://www.python-httpx.org/)

