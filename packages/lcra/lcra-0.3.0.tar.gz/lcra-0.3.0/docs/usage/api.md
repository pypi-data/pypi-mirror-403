# API Usage

The LCRA Flood Status API is a FastAPI-based REST service that provides programmatic access to LCRA Hydromet data.

## Starting the Server

```bash
lcra serve
```

The server will start on `http://localhost:8080` by default.

## Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

## Endpoints

### Root

**GET** `/`

Returns API information and available endpoints.

**Response:**

```json
{
  "message": "LCRA Flood Status Data Extractor API",
  "version": "1.0.0",
  "endpoints": {
    "complete_report": "/flood-report",
    "lake_levels": "/lake-levels",
    "river_conditions": "/river-conditions",
    "floodgate_operations": "/floodgate-operations",
    "docs": "/docs"
  }
}
```

### Health Check

**GET** `/health`

Check API health and LCRA API connectivity.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:45",
  "lcra_accessible": true
}
```

### Flood Report

**GET** `/flood-report`

Get complete flood operations report with all available data.

**Response:** `FloodOperationsReport` object

**Example:**

```bash
curl http://localhost:8080/flood-report
```

### Lake Levels

**GET** `/lake-levels`

Get current lake levels at all dams.

**Response:** Array of `LakeLevel` objects

**Example:**

```bash
curl http://localhost:8080/lake-levels
```

### River Conditions

**GET** `/river-conditions`

Get current river conditions at gauge locations.

**Response:** Array of `RiverCondition` objects

**Example:**

```bash
curl http://localhost:8080/river-conditions
```

### Floodgate Operations

**GET** `/floodgate-operations`

Get current floodgate operations data.

**Response:** Array of `FloodgateOperation` objects

**Example:**

```bash
curl http://localhost:8080/floodgate-operations
```

## Python Client Example

```python
import httpx

async with httpx.AsyncClient() as client:
    # Get flood report
    response = await client.get("http://localhost:8080/flood-report")
    report = response.json()

    # Get lake levels
    response = await client.get("http://localhost:8080/lake-levels")
    lake_levels = response.json()
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful request
- `503 Service Unavailable`: LCRA API is unreachable
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with error information:

```json
{
  "detail": "Failed to fetch data from LCRA API: ..."
}
```
