# PyCharter API

REST API wrapper for PyCharter services using FastAPI.

## Overview

The PyCharter API is located at the root level of the repository (`api/`) and provides HTTP endpoints for all core PyCharter services:
- **Contract Parsing**: Parse data contract files into components
- **Contract Building**: Reconstruct contracts from metadata store
- **Metadata Storage**: Store and retrieve schemas, metadata, and rules
- **Schema Generation**: Generate Pydantic models from JSON Schemas
- **Schema Conversion**: Convert Pydantic models to JSON Schemas
- **Runtime Validation**: Validate data against schemas
- **Quality Assurance**: Run quality checks, query metrics and violations

## Installation

Install PyCharter with API dependencies:

```bash
pip install pycharter[api]
```

## Running the API Server

### Using the CLI command:

```bash
pycharter api
```

### Using uvicorn directly:

```bash
uvicorn api.main:app --reload
```

### Using Python:

```python
from api.main import main
main()
```

## Configuration

The API requires a database connection for most endpoints. Configure it using environment variables:

### Database URL Configuration

The API uses `PYCHARTER_DATABASE_URL` environment variable to connect to the database. You can set it in several ways:

#### Method 1: Export in Shell (Recommended)

```bash
# Set the environment variable
export PYCHARTER_DATABASE_URL="postgresql://user:password@localhost:5432/pycharter"

# Then run the API
pycharter api
```

#### Method 2: Inline with Command

```bash
# Set and run in one line
PYCHARTER_DATABASE_URL="postgresql://user:password@localhost:5432/pycharter" pycharter api
```

#### Method 3: Add to Shell Profile (Persistent)

Add to your `~/.bashrc`, `~/.zshrc`, or `~/.profile`:

```bash
export PYCHARTER_DATABASE_URL="postgresql://user:password@localhost:5432/pycharter"
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

#### Method 4: Using a .env File

Create a `.env` file in your project root:

```bash
PYCHARTER_DATABASE_URL=postgresql://user:password@localhost:5432/pycharter
```

Then load it before running (requires `python-dotenv`):
```bash
export $(cat .env | xargs)
pycharter api
```

Or use `dotenv-cli`:
```bash
pip install dotenv-cli
dotenv run pycharter api
```

### Alternative Environment Variable

PyCharter also supports Airflow-style configuration:

```bash
export PYCHARTER__DATABASE__SQL_ALCHEMY_CONN="postgresql://user:password@localhost:5432/pycharter"
```

### Metadata Store Configuration

The API can be configured to use different metadata store backends:

```bash
# Metadata store type (in_memory, postgres, mongodb, redis)
export PYCHARTER_API_STORE_TYPE=postgres

# Connection string for database-backed stores
export PYCHARTER_API_CONNECTION_STRING=postgresql://user:pass@localhost:5432/pycharter
```

**Note**: If `PYCHARTER_DATABASE_URL` is set, it will be used for both the database connection and metadata store (for PostgreSQL).

## API Endpoints

### Contract Endpoints

#### `POST /api/v1/contracts/parse`
Parse a data contract dictionary into components.

**Request Body:**
```json
{
  "contract": {
    "schema": {...},
    "metadata": {...},
    "ownership": {...},
    "governance_rules": {...}
  }
}
```

**Response:**
```json
{
  "schema": {...},
  "metadata": {...},
  "ownership": {...},
  "governance_rules": {...},
  "coercion_rules": {...},
  "validation_rules": {...},
  "versions": {...}
}
```

#### `POST /api/v1/contracts/build`
Build a complete contract from metadata store.

**Request Body:**
```json
{
  "schema_id": "user_schema",
  "version": "1.0.0",
  "include_metadata": true,
  "include_ownership": true,
  "include_governance": true
}
```

#### `GET /api/v1/contracts`
List all data contracts stored in the database.

#### `GET /api/v1/contracts/{contract_id}`
Get a specific data contract by ID.

### Metadata Endpoints

#### `GET /api/v1/metadata/schemas`
List all schemas stored in the metadata store.

#### `GET /api/v1/metadata/schemas/{schema_id}`
Get a schema by ID (optional version parameter).

#### `GET /api/v1/metadata/schemas/{schema_id}/complete`
Get complete schema with coercion and validation rules merged.

#### `POST /api/v1/metadata/schemas`
Store a schema in the metadata store.

#### `GET /api/v1/metadata/metadata/{schema_id}`
Get metadata for a schema (optional version parameter).

#### `POST /api/v1/metadata/metadata`
Store metadata for a schema.

#### `GET /api/v1/metadata/coercion-rules/{schema_id}`
Get coercion rules for a schema (optional version parameter).

#### `POST /api/v1/metadata/coercion-rules`
Store coercion rules for a schema.

#### `GET /api/v1/metadata/validation-rules/{schema_id}`
Get validation rules for a schema (optional version parameter).

#### `POST /api/v1/metadata/validation-rules`
Store validation rules for a schema.

### Quality Assurance Endpoints

#### `GET /api/v1/quality/metrics`
List quality metrics (optional filtering by schema_id, pagination).

#### `GET /api/v1/quality/metrics/{metric_id}`
Get a specific quality metric by ID.

#### `GET /api/v1/quality/reports/{schema_id}`
Get quality reports for a schema/data feed (optional data_source filter).

#### `POST /api/v1/quality/check`
Run a quality check against a data contract.

#### `POST /api/v1/quality/violations`
Query data quality violations.

### Schema Endpoints

#### `POST /api/v1/schemas/generate`
Generate Pydantic model from JSON Schema.

#### `POST /api/v1/schemas/convert`
Convert Pydantic model to JSON Schema.

### Validation Endpoints

#### `POST /api/v1/validation/validate`
Validate a single record against a schema.

#### `POST /api/v1/validation/validate-batch`
Validate a batch of records against a schema.

## API Documentation

Once the API server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Example Usage

### Using curl:

```bash
# List all contracts
curl http://localhost:8000/api/v1/contracts

# Get a specific contract
curl http://localhost:8000/api/v1/contracts/{contract_id}

# List all schemas
curl http://localhost:8000/api/v1/metadata/schemas

# Get a schema
curl http://localhost:8000/api/v1/metadata/schemas/{schema_id}

# Get quality metrics
curl http://localhost:8000/api/v1/quality/metrics

# Get quality report for a schema
curl http://localhost:8000/api/v1/quality/reports/{schema_id}
```

### Using Python requests:

```python
import requests

# List contracts
response = requests.get("http://localhost:8000/api/v1/contracts")
contracts = response.json()

# Get quality metrics
response = requests.get("http://localhost:8000/api/v1/quality/metrics")
metrics = response.json()
```

## Troubleshooting

### Database Connection Issues

If you see errors about database URL not being configured:

1. **Check environment variable is set:**
   ```bash
   echo $PYCHARTER_DATABASE_URL
   ```

2. **Verify database is accessible:**
   ```bash
   psql $PYCHARTER_DATABASE_URL -c "SELECT 1;"
   ```

3. **Ensure database is initialized:**
   ```bash
   pycharter db init $PYCHARTER_DATABASE_URL
   ```

### API Not Starting

If the API fails to start:

1. **Check if uvicorn is installed:**
   ```bash
   pip install pycharter[api]
   ```

2. **Check for port conflicts:**
   ```bash
   # Use a different port
   pycharter api --port 8001
   ```

3. **Check logs for errors:**
   The API will print error messages to stderr if there are configuration issues.

## Production Deployment

For production, consider:

1. **Use a process manager** (systemd, supervisor, etc.)
2. **Set environment variables** in your deployment configuration
3. **Use a reverse proxy** (nginx, traefik) in front of the API
4. **Enable HTTPS** for secure connections
5. **Configure CORS** appropriately in `api/main.py`
6. **Use a production ASGI server** like Gunicorn with Uvicorn workers:

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```
