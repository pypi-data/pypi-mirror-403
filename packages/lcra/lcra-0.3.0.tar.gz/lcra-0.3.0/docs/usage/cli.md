# CLI Usage

The LCRA CLI provides a simple command-line interface for extracting flood status data.

## Basic Commands

### Get Flood Operations Report

Extract the complete flood operations report:

```bash
lcra get --report
```

### Get Lake Levels

Extract current lake levels:

```bash
lcra get --lake-levels
```

### Get River Conditions

Extract current river conditions:

```bash
lcra get --river-conditions
```

### Get Floodgate Operations

Extract floodgate operations data:

```bash
lcra get --floodgate-operations
```

## Saving Output

### Auto-named File (Timestamped)

Save output to a file with an auto-generated timestamp:

```bash
lcra get --report --save
```

This creates a file like `reports/report_2025-01-15T10-30-45.json`.

### Custom Filename

Save with a custom filename:

```bash
lcra get --report --saveas my_report
```

This creates `reports/my_report.json`.

## Starting the API Server

Start the FastAPI server:

```bash
lcra serve --host 0.0.0.0 --port 8080
```

Options:

- `--host`: Host to bind to (default: `0.0.0.0`)
- `--port`: Port to bind to (default: `8080`)

Once started, visit:

- API docs: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## Command Reference

### `lcra get`

Extract LCRA flood status data.

**Options:**

- `--report`: Extract the full flood operations report
- `--lake-levels`: Extract current lake levels
- `--river-conditions`: Extract current river conditions
- `--floodgate-operations`: Extract floodgate operations
- `--save`: Save result as JSON with auto-generated timestamp filename
- `--saveas <filename>`: Store result as JSON in `reports/<filename>.json`

**Examples:**

```bash
# Print report to stdout
lcra get --report

# Save report with timestamp
lcra get --report --save

# Save with custom name
lcra get --lake-levels --saveas lake_data

# Multiple data types (uses first match)
lcra get --report --lake-levels
```

### `lcra serve`

Serve the LCRA Flood Status API.

**Options:**

- `--host <host>`: Host to serve on (default: `0.0.0.0`)
- `--port <port>`: Port to serve on (default: `8080`)

**Examples:**

```bash
# Default host and port
lcra serve

# Custom port
lcra serve --port 9000

# Custom host and port
lcra serve --host 127.0.0.1 --port 8080
```

