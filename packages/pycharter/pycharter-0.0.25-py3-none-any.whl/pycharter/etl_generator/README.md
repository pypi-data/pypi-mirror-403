# ETL Orchestrator - User Guide

This document describes the ETL Orchestrator features, including simple transformations, JSONata support, and custom functions.

## Transformation Capabilities

The ETL orchestrator supports **three levels of transformation complexity**, applied in order:

1. **Simple Operations** (declarative, easy to use) - NEW! ✅
2. **JSONata** (powerful query language for complex transformations)
3. **Custom Functions** (Python functions for advanced logic)

### Simple Operations (Recommended for Most Use Cases)

Simple, declarative operations that handle 90% of transformation needs:

```yaml
# transform.yaml
transform:
  rename:
    oldName: new_name
    camelCase: snake_case
  convert:
    price: float
    quantity: integer
  defaults:
    status: "pending"
  add:
    full_name: "${first_name} ${last_name}"
    created_at: "now()"
  select:
    - field1
    - field2
  drop:
    - internal_id
```

**See [TRANSFORMATION_GUIDE.md](TRANSFORMATION_GUIDE.md) for complete documentation.**

### JSONata (Advanced)

Full JSONata support for complex transformations:

```yaml
jsonata:
  expression: |
    $.{
      "ticker": symbol,
      "avg_price": $average(prices),
      "total_volume": $sum(volumes)
    }
  mode: "batch"  # or "record"
```

### Custom Functions

Import and run external Python modules/functions:

```yaml
custom_function:
  module: "myproject.transforms"
  function: "optimize_data"
  mode: "batch"
  kwargs:
    method: "min_volatility"
```

**All three can be used together!** Simple operations → JSONata → Custom functions.

## Enhanced Features

## Features Overview

### Phase 1: Core Streaming Infrastructure ✅
- **Streaming/Incremental ETL**: Process data in batches (Extract-Batch → Transform-Batch → Load-Batch)
- **Generator-based Extraction**: Async generators for memory-efficient data extraction
- **Memory Management**: Automatic memory monitoring and limits

### Phase 2: Observability & Configuration ✅
- **Configurable Processing Modes**: Choose between `full`, `streaming`, or `hybrid` modes
- **Progress Tracking**: Real-time progress reporting with callbacks
- **Error Recovery**: Retry strategies and error threshold management

### Phase 3: Advanced Features ✅
- **Checkpoint/Resume**: Save and resume long-running jobs
- **Multiple Runs Support**: Process multiple parameter sets efficiently with rate limiting

## Usage Examples

### Basic Usage (Backward Compatible)

```python
from pycharter.etl_generator import ETLOrchestrator

# Default behavior (full mode) - backward compatible
orchestrator = ETLOrchestrator(contract_dir="data/examples/my_contract")
result = await orchestrator.run()
```

### Streaming Mode (Memory Efficient)

Configure in `extract.yaml`:
```yaml
processing_mode: streaming
batch_size: 1000
```

Or use programmatically:
```python
orchestrator = ETLOrchestrator(contract_dir="data/examples/my_contract")
result = await orchestrator.run_streaming(batch_size=1000)
```

### Progress Tracking

```python
from pycharter.etl_generator import ETLOrchestrator, ETLProgress

def log_progress(progress: ETLProgress):
    print(f"{progress}")

orchestrator = ETLOrchestrator(
    contract_dir="data/examples/my_contract",
    progress_callback=log_progress,
    verbose=True
)
result = await orchestrator.run()
```

### Checkpoint/Resume

```python
orchestrator = ETLOrchestrator(
    contract_dir="data/examples/my_contract",
    checkpoint_dir="./checkpoints"
)

# Run with checkpoint
result = await orchestrator.run(checkpoint_id="my_job_001")

# Resume from checkpoint
result = await orchestrator.run(
    checkpoint_id="my_job_001",
    resume=True
)
```

### Memory Management

```python
orchestrator = ETLOrchestrator(
    contract_dir="data/examples/my_contract",
    max_memory_mb=2048  # Limit to 2GB
)
result = await orchestrator.run()
```

### Multiple Runs Processing

Run the same ETL pipeline multiple times with different parameters efficiently:

```python
orchestrator = ETLOrchestrator(contract_dir="data/examples/my_contract")

# Simple case: vary a single parameter (e.g., symbols)
results = await orchestrator.run_multiple(
    param_name='symbol',
    param_values=["AAPL", "MSFT", "GOOGL", "TSLA"],
    batch_size=5,
    delay_between_runs=1.0
)

for result in results:
    params = result['params']
    print(f"{params}: {result['success']} - {result.get('records', 0)} records")

# Complex case: vary multiple parameters
results = await orchestrator.run_multiple(
    param_sets=[
        {'symbol': 'AAPL', 'date': '2024-01-01'},
        {'symbol': 'MSFT', 'date': '2024-01-02'},
        {'symbol': 'GOOGL', 'date': '2024-01-03'},
    ],
    batch_size=3,
    delay_between_runs=0.5
)
```

### Error Recovery

```python
result = await orchestrator.run_streaming(
    batch_size=1000,
    max_retries=3,
    error_threshold=0.1  # Abort if >10% of batches fail
)
```

## Configuration Options

### extract.yaml

```yaml
# Processing mode: 'full', 'streaming', or 'hybrid'
processing_mode: streaming

# Batch size for processing
batch_size: 1000

# Memory limit (optional)
max_memory_mb: 2048

# Checkpoint configuration (optional)
checkpoint:
  enabled: true
  interval: 100  # Checkpoint every N batches
```

## Processing Modes

### Full Mode (Default)
- **Behavior**: Extract all → Transform all → Load all
- **Use Case**: Small to medium datasets, backward compatible
- **Memory**: All data in memory at once

### Streaming Mode
- **Behavior**: Extract-Batch → Transform-Batch → Load-Batch (incremental)
- **Use Case**: Large datasets, memory-constrained environments
- **Memory**: Constant memory usage (batch size)

### Hybrid Mode
- **Behavior**: Extract in chunks, transform/load in batches
- **Use Case**: Fast extraction but slow transformation/loading
- **Memory**: Moderate memory usage

## Architecture

### New Modules

- **`progress.py`**: Progress tracking and observability
- **`checkpoint.py`**: Checkpoint/resume functionality
- **`extractors/`**: Modular extraction (HTTP, file, database, cloud) with streaming entry point `extract_with_pagination_streaming`
- **`orchestrator.py`**: Enhanced with all new features

### Backward Compatibility

All new features are **100% backward compatible**. Existing code continues to work without changes. New features are opt-in via:
- Configuration in `extract.yaml`
- Optional constructor parameters
- New method calls (`run_streaming()`, `run_multiple()`, etc.)

## Performance Considerations

### Memory Usage
- **Full Mode**: O(n) where n = total records
- **Streaming Mode**: O(b) where b = batch size
- **Hybrid Mode**: O(c) where c = chunk size

### Throughput
- **Full Mode**: Fastest for small datasets (single pass)
- **Streaming Mode**: Slower but handles unlimited size
- **Hybrid Mode**: Balanced approach

## Best Practices

1. **Use streaming mode** for datasets > 100K records
2. **Enable checkpoints** for jobs expected to run > 1 hour
3. **Set memory limits** to prevent OOM crashes
4. **Use progress callbacks** for monitoring long-running jobs
5. **Configure error thresholds** based on data quality expectations

