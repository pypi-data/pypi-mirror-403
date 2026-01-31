# ETL Generator — Main Interfaces

This document describes the main public interfaces of `pycharter.etl_generator`. Use these when building or extending ETL pipelines.

---

## Primary interface: run pipelines

### `ETLOrchestrator`

**Import:** `from pycharter.etl_generator import ETLOrchestrator`

The main entry point for running ETL. It runs: **Extract → Transform → Load** from contract artifacts and ETL configs (`extract.yaml`, `transform.yaml`, `load.yaml`).

- **Constructor:** `ETLOrchestrator(contract_dir=None, contract_file=None, contract_dict=None, contract_metadata=None, checkpoint_dir=None, progress_callback=None, verbose=True, max_memory_mb=None, config_context=None, extract_config=None, transform_config=None, load_config=None, extract_file=None, transform_file=None, load_file=None)`
- **Main methods:**
  - `run(**kwargs)` → `Dict` — Run the full pipeline (async). Pass `dry_run=True` to transform/load without writing. Input params (e.g. `symbol`, `start_date`) come from `extract.yaml`’s `input_params` and `**kwargs`.
  - `extract_stream(batch_size=None, max_records=None, **kwargs)` → `AsyncIterator[List[Dict]]` — Stream batches from extract only.
- **Config sources (priority):** direct dict args > file paths > files in `contract_dir`.

### `create_orchestrator(contract_dir=None, **kwargs) -> ETLOrchestrator`

**Import:** `from pycharter.etl_generator import create_orchestrator`

Factory helper that returns `ETLOrchestrator(contract_dir=contract_dir, **kwargs)`.

---

## Pipeline discovery

### `PipelineFactory`

**Import:** `from pycharter.etl_generator import PipelineFactory`

Discovers pipelines from a root directory: each subdir that contains `extract.yaml`, `transform.yaml`, and `load.yaml` is treated as one pipeline.

- **Constructor:** `PipelineFactory(config_root="configs", excluded_dirs=None, required_files=None)`
- **Methods:**
  - `get_pipeline_names() -> List[str]`
  - `get_contract_dir(pipeline_name: str) -> Optional[str]`
  - `create_orchestrator(pipeline_name, config_context=None, verbose=True, **orchestrator_kwargs) -> ETLOrchestrator`
  - `refresh()` — Rescan `config_root`

---

## Extract

### `extract_with_pagination_streaming(...) -> AsyncIterator[List[Dict]]`

**Import:** `from pycharter.etl_generator.extractors import extract_with_pagination_streaming`

Async generator that yields batches of records. Dispatches to the right extractor via `ExtractorFactory` using `source_type` (or auto-detection from `extract_config`).

- **Args:** `extract_config`, `params`, `headers`, `contract_dir=None`, `batch_size=1000`, `max_records=None`, `config_context=None`

### `ExtractorFactory` / `get_extractor(extract_config) -> BaseExtractor`

**Import:** `from pycharter.etl_generator.extractors import ExtractorFactory, get_extractor`

- `ExtractorFactory.get_extractor(extract_config)` — Returns an extractor instance for the given config.
- `get_extractor(extract_config)` — Same, module-level helper.
- **Auto-detection:** `base_url`/`api_endpoint` → http; `file_path` → file; `database` → database; `storage` → cloud_storage.

### Extractors (implementations of `BaseExtractor`)

**Import:** `from pycharter.etl_generator.extractors import HTTPExtractor, FileExtractor, DatabaseExtractor, CloudStorageExtractor, BaseExtractor`

- **BaseExtractor** — Abstract base. Subclasses implement `validate_config(extract_config)` and `extract_streaming(extract_config, params, headers, contract_dir, batch_size, max_records, config_context)`.
- **HTTPExtractor** — HTTP/API (single or paginated).
- **FileExtractor** — Local files (CSV, JSON, Parquet, etc., including glob).
- **DatabaseExtractor** — SQL over PostgreSQL, MySQL, SQLite, MSSQL, Oracle.
- **CloudStorageExtractor** — S3, GCS, Azure Blob.

Custom extractors: `ExtractorFactory.register_extractor(source_type, extractor_class)`.

---

## Transform

### `apply_transforms(data, transform_config, **kwargs) -> List[Dict]`

**Import:** `from pycharter.etl_generator.transformers import apply_transforms`

Runs the transform pipeline on a list of records. Order: **simple_ops → jsonata → custom_function**. Each step is skipped if not present in config.

- **Args:** `data: List[Dict]`, `transform_config: Dict`, plus any `**kwargs` passed to custom functions.
- **Config shape:** Supports canonical `transform: { rename, convert, defaults, add, select, drop }` and/or top-level `jsonata`, `custom_function`. See `transformers.config.normalize_transform_config` and `pycharter/data/templates/etl/`.

---

## Load

### `load_to_file(data, load_config, ...) -> Dict`

**Import:** `from pycharter.etl_generator.loaders import load_to_file`

Writes records to a local file. Used when `load_config` has `destination_type: file` (or implies it via `file_path`).

- **Args:** `data`, `load_config`, `contract_dir=None`, `config_context=None`
- **Returns:** `{ "written": n, "total": n }` (and related metadata).

### `load_to_cloud_storage(data, load_config, ...) -> Dict`

**Import:** `from pycharter.etl_generator.loaders import load_to_cloud_storage`

Writes to S3, GCS, or Azure Blob. Used when `destination_type: cloud_storage` or config has `storage`.

- **Args:** `data`, `load_config`, `contract_dir=None`, `config_context=None`
- **Returns:** `{ "written": n, "total": n }` (and related metadata).

Database loading is handled inside the orchestrator via `pycharter.etl_generator.database.load_data` when `destination_type` is omitted or `database` (and `load_config` has `database`, `target_table`, `schema_name`, etc.).

---

## Config generation

### `generate_etl_config(...)` / `generate_etl_config_from_contract(...)` / `generate_etl_config_from_store(...)`

**Import:** `from pycharter.etl_generator import generate_etl_config, generate_etl_config_from_contract, generate_etl_config_from_store`

Helpers to produce ETL config dicts (extract/transform/load) from contracts or from the metadata store. See docstrings and `config_generator.py` for parameters.

---

## Utilities (progress, checkpoint, DLQ)

- **Progress:** `ETLProgress`, `ProgressTracker` — `from pycharter.etl_generator import ETLProgress, ProgressTracker`
- **Checkpoint/resume:** `CheckpointManager`, `CheckpointState` — `from pycharter.etl_generator import CheckpointManager, CheckpointState`
- **Dead letter:** `DeadLetterQueue`, `DeadLetterRecord`, `DLQReason` — `from pycharter.etl_generator import DeadLetterQueue, DeadLetterRecord, DLQReason`

---

## Quick reference: import map

| Use case                 | Import |
|--------------------------|--------|
| Run ETL                  | `from pycharter.etl_generator import ETLOrchestrator, create_orchestrator` |
| Discover pipelines       | `from pycharter.etl_generator import PipelineFactory` |
| Extract (streaming)      | `from pycharter.etl_generator.extractors import extract_with_pagination_streaming, ExtractorFactory, get_extractor` |
| Transform                | `from pycharter.etl_generator.transformers import apply_transforms` |
| Load to file/cloud       | `from pycharter.etl_generator.loaders import load_to_file, load_to_cloud_storage` |
| Config generation        | `from pycharter.etl_generator import generate_etl_config, generate_etl_config_from_contract, generate_etl_config_from_store` |
| Progress / checkpoint/DLQ| `from pycharter.etl_generator import ETLProgress, ProgressTracker, CheckpointManager, CheckpointState, DeadLetterQueue, DeadLetterRecord, DLQReason` |
