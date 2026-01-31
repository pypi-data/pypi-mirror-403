# Async and Execution Model

This document describes how PyCharter's ETL pipeline uses async execution, where the event loop runs, and how to run pipelines from scripts and long-running applications.

## Pipeline execution is async

The `Pipeline.run()` method is **async** and returns a coroutine. Extractors yield batches asynchronously, and loaders perform I/O asynchronously. You must run the pipeline within an event loop.

## Running a pipeline

### From a script (one-off run)

Use `asyncio.run()` to run the pipeline. This creates an event loop, runs the pipeline, and closes the loop when done.

```python
import asyncio
from pycharter import Pipeline

async def main():
    pipeline = Pipeline.from_config_dir("pipelines/users/")
    result = await pipeline.run()
    print(f"Loaded {result.rows_loaded} rows")

if __name__ == "__main__":
    asyncio.run(main())
```

**Important:** Call `asyncio.run(main())` only once per process. Do not nest `asyncio.run()` calls.

### From an async application (FastAPI, Celery async, etc.)

If you are already inside an async context (e.g. a FastAPI route or an async Celery task), **await** the pipeline directly. Do not use `asyncio.run()` — it would create a new event loop and can conflict with the existing one.

```python
from fastapi import APIRouter
from pycharter import Pipeline

router = APIRouter()

@router.post("/run-etl")
async def run_etl():
    pipeline = Pipeline.from_config_dir("pipelines/users/")
    result = await pipeline.run()
    return {"rows_loaded": result.rows_loaded}
```

### Where the event loop runs

| Context                    | Event loop                    | How to run the pipeline      |
|---------------------------|-------------------------------|------------------------------|
| Script (e.g. `python run.py`) | Created by `asyncio.run()`     | `asyncio.run(main())`        |
| Jupyter / IPython         | Built-in loop                 | `await pipeline.run()`       |
| FastAPI / Starlette       | Uvicorn’s loop                | `await pipeline.run()`       |
| Async Celery task         | Worker’s loop                 | `await pipeline.run()`       |
| Sync code (no loop)       | None                          | Use `asyncio.run(main())`    |

## Error handling and error mode

`Pipeline.run()` accepts an optional `error_context` (from `pycharter.shared.errors`). The default error context’s mode controls whether failures **raise** or are **collected**:

- **STRICT (default for many paths):** Extraction or load failures raise exceptions. Use when you want fail-fast behavior.
- **LENIENT:** Failures are logged and appended to `result.errors`; the pipeline continues where possible.
- **COLLECT:** Same as lenient but errors are also collected on the context for later inspection.

```python
from pycharter import Pipeline
from pycharter.shared.errors import get_error_context, set_error_mode, ErrorMode

# Optional: set global mode (e.g. lenient for a script)
set_error_mode(ErrorMode.LENIENT)

pipeline = Pipeline.from_config_dir("pipelines/users/")
result = await pipeline.run()

if not result.success:
    for err in result.errors:
        print(err)
```

You can also pass a specific `ErrorContext` into `run()` instead of using the global default:

```python
from pycharter.shared.errors import ErrorContext, ErrorMode

ctx = ErrorContext(mode=ErrorMode.LENIENT)
result = await pipeline.run(error_context=ctx)
```

## No async context manager (yet)

The pipeline does not provide an `async with` context manager. Connections (e.g. DB, HTTP) are managed inside the extractor and loader. For cleanup, instantiate and run the pipeline in a scope where you control resource lifetime, or wrap the run in your own try/finally or async context manager.
