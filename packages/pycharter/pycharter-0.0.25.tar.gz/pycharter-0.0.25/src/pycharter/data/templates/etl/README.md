# ETL Config Templates

Templates for ETL pipeline configuration. Supports two formats:

1. **Single-file format**: `pipeline.yaml` with extract, transform, load sections
2. **Multi-file format**: Separate `extract.yaml`, `transform.yaml`, `load.yaml` files

## Quick Start

### Single-File Format (Recommended)

```yaml
# pipelines/users/pipeline.yaml
name: users_pipeline
version: "1.0.0"

extract:
  type: http  # Required: http | file | database | cloud_storage
  url: https://api.example.com/users

transform:
  - rename:
      userId: user_id
  - convert:
      user_id: int
  - add:
      full_name: "${first_name} ${last_name}"
      loaded_at: now()

load:
  type: postgres  # Required: postgres | sqlite | file | cloud_storage
  table: users
  database:
    url: ${DATABASE_URL}
```

```python
from pycharter import Pipeline
import asyncio

async def main():
    pipeline = Pipeline.from_config("pipelines/users/pipeline.yaml")
    result = await pipeline.run()
    print(f"Loaded {result.rows_loaded} rows")

asyncio.run(main())
```

### Multi-File Format

```bash
mkdir -p pipelines/users
cp pycharter/data/templates/etl/extract_http_simple.yaml pipelines/users/extract.yaml
cp pycharter/data/templates/etl/transform_simple.yaml pipelines/users/transform.yaml
cp pycharter/data/templates/etl/load_postgresql.yaml pipelines/users/load.yaml
```

```python
pipeline = Pipeline.from_config("pipelines/users/")
```

## Type Field (Required)

All extract and load configs require an explicit `type` field:

**Extract types:**
- `http` - HTTP/API extraction
- `file` - Local file extraction (CSV, JSON, Parquet, etc.)
- `database` - SQL database extraction
- `cloud_storage` - Cloud storage (S3, GCS, Azure)

**Load types:**
- `postgres` / `postgresql` - PostgreSQL
- `sqlite` - SQLite
- `file` - Local file (JSON, CSV, Parquet)
- `cloud_storage` - Cloud storage (S3, GCS, Azure)

## Extract Templates

| Template | Type | Description |
|----------|------|-------------|
| `extract_http_simple.yaml` | http | Single HTTP request (no pagination) |
| `extract_http_paginated.yaml` | http | HTTP with pagination (page/offset/cursor) |
| `extract_http_path_params.yaml` | http | HTTP with `{param}` path substitution |
| `extract_file_csv.yaml` | file | CSV file extraction |
| `extract_file_json.yaml` | file | JSON file extraction |
| `extract_file_parquet.yaml` | file | Parquet file extraction |
| `extract_file_glob.yaml` | file | Multiple files via glob pattern |
| `extract_database.yaml` | database | SQL database extraction |
| `extract_database_ssh.yaml` | database | Database via SSH tunnel |
| `extract_cloud_s3.yaml` | cloud_storage | AWS S3 extraction |
| `extract_cloud_gcs.yaml` | cloud_storage | Google Cloud Storage |
| `extract_cloud_azure.yaml` | cloud_storage | Azure Blob Storage |

## Transform Templates

| Template | Description |
|----------|-------------|
| `transform_simple.yaml` | rename, convert, defaults, add, select, drop |
| `transform_custom_function.yaml` | Call Python function |
| `transform_jsonata.yaml` | JSONata expressions |
| `transform_combined.yaml` | Simple + JSONata + custom |

### Transform Formats

**List format (ordered)** - Transforms applied in specified order:

```yaml
transform:
  - rename: {old_field: new_field}
  - convert: {field: int}
  - add:
      full_name: "${first_name} ${last_name}"
      timestamp: now()
  - select: [id, name, email]
```

**Dict format (legacy)** - Fixed order: rename → convert → defaults → add → select → drop

```yaml
transform:
  rename:
    old_field: new_field
  convert:
    field: int
```

### Expression Syntax

In `add` fields, you can use expressions:

- `${field_name}` - Reference field value
- `${field_name:-default}` - Field with default if missing
- `now()` - Current timestamp (ISO format)
- `uuid()` - Generate UUID
- `concat(${a}, " ", ${b})` - Concatenate values
- `lower(${field})` / `upper(${field})` - Case conversion

## Load Templates

| Template | Type | Description |
|----------|------|-------------|
| `load_postgresql.yaml` | postgres | PostgreSQL (upsert, insert, etc.) |
| `load_sqlite.yaml` | sqlite | SQLite database |
| `load_file.yaml` | file | JSON, CSV, Parquet file |
| `load_upsert.yaml` | postgres | Upsert by primary key |
| `load_insert.yaml` | postgres | Insert only |
| `load_truncate_and_load.yaml` | postgres | Truncate then insert |
| `load_with_dlq.yaml` | postgres | With dead letter queue |
| `load_with_ssh_tunnel.yaml` | postgres | Via SSH tunnel |
| `load_cloud_s3.yaml` | cloud_storage | AWS S3 |
| `load_cloud_gcs.yaml` | cloud_storage | Google Cloud Storage |
| `load_cloud_azure.yaml` | cloud_storage | Azure Blob Storage |

## Complete Pipeline Template

See `pipeline_http_to_db.yaml` for a complete single-file pipeline example.

## Variable Substitution

Configs support `${VAR}` syntax for flexible configuration:

```yaml
path: ${DATA_DIR}/input.json                  # From variables
params:
  api_key: ${API_KEY:?API_KEY is required}    # Required - error if missing
  limit: ${BATCH_LIMIT:-100}                  # With default value
database:
  url: ${DATABASE_URL}                        # From environment
```

Provide values via the `variables` parameter (recommended) or environment variables:

```python
# Recommended: explicit variables - no assumptions about structure
pipeline = Pipeline.from_config_files(
    extract="my_extract.yaml",
    load="my_load.yaml",
    variables={
        "DATA_DIR": "./data",
        "OUTPUT_DIR": "./output",
        "API_KEY": "xxx",
        "DATABASE_URL": "postgresql://..."
    }
)

# Or with from_config() for directory-based loading
pipeline = Pipeline.from_config(
    "pipelines/users",
    variables={"API_KEY": "xxx"}
)
```

## Programmatic API

Instead of config files, use the Pipeline API directly:

```python
from pycharter import (
    Pipeline, HTTPExtractor, PostgresLoader,
    Rename, Select, Filter, Convert, AddField
)

pipeline = (
    Pipeline(HTTPExtractor(url="https://api.example.com/users"))
    | Rename({"userName": "user_name"})
    | AddField("full_name", "${first_name} ${last_name}")  # Expression support!
    | Select(["id", "user_name", "email", "full_name"])
    | Convert({"id": int})
    | Filter(lambda r: r.get("email"))
    | PostgresLoader(
        connection_string="postgresql://localhost/db",
        table="users",
        write_method="upsert",
        primary_key="id"
    )
)

result = await pipeline.run()
```

## Examples

See `examples/etl_config_example/` for working examples with config files.
