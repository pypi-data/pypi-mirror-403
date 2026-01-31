"""
File-based loader for ETL orchestrator.

Writes transformed data to local files in JSON, CSV, Parquet, or JSONL format.
"""

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pycharter.utils.value_injector import resolve_values

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = ("json", "csv", "parquet", "jsonl")


def load_to_file(
    data: List[Dict[str, Any]],
    load_config: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Write transformed data to a local file.

    Load config (destination_type: file):
      file_path: Path to output file (required). Supports ${VAR} resolution.
      format: json | csv | parquet | jsonl (default: json)
      write_mode: overwrite | append (default: overwrite).
        append: for jsonl/csv, appends lines; for json, read-merge-write (array concat).

    Returns:
        Dict with keys: written, total, path, format
    """
    source_file = str(contract_dir / "load.yaml") if contract_dir else None
    file_path = load_config.get("file_path")
    if not file_path:
        raise ValueError(
            "File loader requires 'file_path' in load configuration. "
            "Example: file_path: ./output/data.json"
        )
    file_path = resolve_values(
        file_path, context=config_context, source_file=source_file
    )
    path = Path(file_path)

    fmt = (load_config.get("format") or "json").lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"File loader format must be one of {SUPPORTED_FORMATS}, got '{fmt}'"
        )
    write_mode = (load_config.get("write_mode") or "overwrite").lower()
    if write_mode not in ("overwrite", "append"):
        raise ValueError(
            "File loader write_mode must be 'overwrite' or 'append', "
            f"got '{write_mode}'"
        )

    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        _write_json(data, path, write_mode)
    elif fmt == "jsonl":
        _write_jsonl(data, path, write_mode)
    elif fmt == "csv":
        _write_csv(data, path, write_mode)
    elif fmt == "parquet":
        _write_parquet(data, path, write_mode)

    logger.info(f"File loader wrote {len(data)} records to {path} ({fmt})")
    return {"written": len(data), "total": len(data), "path": str(path), "format": fmt}


def _write_json(
    data: List[Dict[str, Any]], path: Path, write_mode: str
) -> None:
    if write_mode == "append" and path.exists():
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if isinstance(existing, list):
            data = existing + data
        else:
            data = [existing] + data
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _write_jsonl(
    data: List[Dict[str, Any]], path: Path, write_mode: str
) -> None:
    mode = "a" if write_mode == "append" and path.exists() else "w"
    with open(path, mode, encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record, default=str) + "\n")


def _write_csv(
    data: List[Dict[str, Any]], path: Path, write_mode: str
) -> None:
    if not data:
        return
    import csv

    mode = "a" if write_mode == "append" and path.exists() else "w"
    newfile = mode == "w"
    with open(path, mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if newfile:
            writer.writeheader()
        writer.writerows(data)


def _write_parquet(
    data: List[Dict[str, Any]], path: Path, write_mode: str
) -> None:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for Parquet file load. "
            "Install with: pip install pandas pyarrow"
        ) from e
    df = pd.DataFrame(data)
    if write_mode == "append" and path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_parquet(path, index=False)
