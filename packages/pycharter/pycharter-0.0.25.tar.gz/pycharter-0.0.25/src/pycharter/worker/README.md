# PyCharter Worker

Async validation processing component using Spark.

## Overview

The `worker` component provides asynchronous validation processing for large datasets using Spark. It runs as a separate service that consumes validation jobs from a message queue and processes them efficiently.

## Features

- **Non-blocking**: API returns immediately with job_id
- **Spark-compatible**: Works with local Spark (no cluster) or remote cluster
- **Scalable**: Handles large datasets efficiently
- **Optional**: Install separately: `pip install pycharter[worker]`
- **Separate process**: Runs independently: `pycharter worker start`

## Installation

```bash
pip install pycharter[worker]
```

This installs:
- `pyspark>=3.5.0` - Spark support
- `redis>=5.0.0` - Message queue

## Usage

### 1. Start Redis (if not already running)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install and run locally
redis-server
```

### 2. Start the Worker

```bash
# Local Spark mode (default, no cluster needed)
pycharter worker start

# With custom Redis URL
pycharter worker start --redis-url redis://localhost:6379

# With database URL
pycharter worker start --db-url postgresql://user:pass@localhost/pycharter

# Remote Spark mode (future)
pycharter worker start --mode remote --spark-master spark://host:7077
```

### 3. Submit Jobs via API

```bash
# Submit validation job
curl -X POST http://localhost:8000/api/v1/validation/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "schema_id": "user_schema_v1",
    "data_source": "s3://bucket/data/users.parquet",
    "options": {
      "include_profiling": true
    }
  }'

# Check job status
curl http://localhost:8000/api/v1/validation/jobs/{job_id}
```

## Architecture

```
API Service → Redis Queue → Worker (Spark) → Database
```

1. **API Service**: Receives validation requests, enqueues jobs
2. **Redis Queue**: Stores jobs and status
3. **Worker**: Consumes jobs, validates using Spark, persists results
4. **Database**: Stores quality metrics and violations

## Spark Modes

### Local Mode (Default)

No cluster needed. Uses all CPU cores on the machine:

```bash
pycharter worker start --mode local
```

### Remote Mode

Submit to external Spark service:

```bash
pycharter worker start --mode remote --spark-master spark://host:7077
```

### Cluster Mode (Future)

Connect to Spark cluster:

```bash
pycharter worker start --mode cluster --spark-master yarn
```

## Configuration

### Environment Variables

- `PYCHARTER_DATABASE_URL`: Database connection URL (used if not provided via CLI)
- `SPARK_MASTER`: Spark master URL (used if not provided via CLI)
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)

### CLI Options

- `--mode`: Spark mode (`local`, `remote`, `cluster`)
- `--redis-url`: Redis connection URL
- `--db-url`: Database connection URL
- `--spark-master`: Spark master URL

## Integration with API

The API service automatically detects if the worker component is installed and enables async job submission endpoints:

- `POST /api/v1/validation/jobs` - Submit async validation job
- `GET /api/v1/validation/jobs/{job_id}` - Get job status

If the worker is not installed, these endpoints return a 503 error with installation instructions.

## Data Sources

The worker supports various data sources:

- **S3**: `s3://bucket/path/to/data.parquet`
- **HDFS**: `hdfs://namenode:port/path/to/data.parquet`
- **Local files**: `/path/to/data.parquet`, `/path/to/data.json`, `/path/to/data.csv`
- **Database tables**: Table name (requires JDBC configuration)

## Result Storage

Validation results are stored in the database:

- **Quality Metrics**: Stored in `quality_metrics` table
- **Violations**: Stored in `quality_violations` table (if enabled)
- **Job Status**: Stored in Redis with TTL

## Troubleshooting

### Worker not starting

1. Check Redis is running: `redis-cli ping`
2. Check Spark is installed: `python -c "import pyspark"`
3. Check database connection: `pycharter db current`

### Jobs not processing

1. Check worker logs for errors
2. Verify Redis queue has jobs: `redis-cli LLEN validation-jobs`
3. Check Spark session is created successfully

### Performance issues

1. Use local Spark mode for small-medium datasets
2. Use cluster mode for very large datasets (TB+)
3. Adjust Spark configuration for your workload

## Development

For development, you can run the worker in the same way:

```bash
# From project root
pycharter worker start --redis-url redis://localhost:6379
```

## Future Enhancements

- Support for other message queues (RabbitMQ, Kafka)
- Support for other compute backends (Dask, Ray)
- Real-time progress updates via WebSocket
- Result streaming for large result sets
- Automatic backend selection based on data size

