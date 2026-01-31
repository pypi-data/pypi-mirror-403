"""
Cloud storage loader for ETL orchestrator.

Writes transformed data to AWS S3, Google Cloud Storage, or Azure Blob Storage.
"""

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pycharter.utils.value_injector import resolve_values

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = ("json", "csv", "parquet", "jsonl")

try:
    import boto3
    from botocore.exceptions import ClientError

    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    boto3 = None
    ClientError = None

try:
    from google.cloud import storage as gcs_storage

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    gcs_storage = None

try:
    from azure.storage.blob import BlobServiceClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    BlobServiceClient = None


def load_to_cloud_storage(
    data: List[Dict[str, Any]],
    load_config: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Write transformed data to cloud storage (S3, GCS, or Azure Blob).

    Load config (destination_type: cloud_storage):
      storage:
        provider: s3 | gcs | azure
        bucket: bucket name (S3/GCS). For Azure use container.
        container: container name (Azure only; use instead of bucket for Azure)
        path: object key/path (e.g. output/data.json)
        credentials: optional provider-specific credentials
      format: json | csv | parquet | jsonl (default: json)

    Returns:
        Dict with keys: written, total, path, format, provider
    """
    storage = load_config.get("storage", {})
    if not storage:
        raise ValueError(
            "Cloud storage loader requires 'storage' in load configuration "
            "with provider, bucket/container, and path."
        )
    source_file = str(contract_dir / "load.yaml") if contract_dir else None
    provider = resolve_values(
        storage.get("provider", ""), context=config_context, source_file=source_file
    )
    provider = (provider or "").lower()
    if provider not in ("s3", "gcs", "azure"):
        raise ValueError(
            f"Cloud storage provider must be 's3', 'gcs', or 'azure', got '{provider}'"
        )

    bucket = resolve_values(
        storage.get("bucket"), context=config_context, source_file=source_file
    )
    container = resolve_values(
        storage.get("container"), context=config_context, source_file=source_file
    )
    path = resolve_values(
        storage.get("path"), context=config_context, source_file=source_file
    )
    if not path:
        raise ValueError("Cloud storage loader requires 'storage.path'")
    # Azure uses container; S3/GCS use bucket
    if provider == "azure":
        if not container:
            container = bucket  # allow bucket as alias
        if not container:
            raise ValueError(
                "Azure cloud storage loader requires 'storage.container' or 'storage.bucket'"
            )
    else:
        if not bucket:
            raise ValueError(
                f"{provider.upper()} loader requires 'storage.bucket'"
            )

    fmt = (load_config.get("format") or "json").lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Cloud storage format must be one of {SUPPORTED_FORMATS}, got '{fmt}'"
        )

    payload, content_type = _serialize_data(data, fmt)

    if provider == "s3":
        _upload_s3(bucket, path, payload, content_type, storage.get("credentials"))
    elif provider == "gcs":
        _upload_gcs(bucket, path, payload, content_type, storage.get("credentials"))
    else:
        _upload_azure(
            container, path, payload, content_type, storage.get("credentials")
        )

    logger.info(
        f"Cloud storage loader wrote {len(data)} records to {provider}:{bucket or container}/{path}"
    )
    return {
        "written": len(data),
        "total": len(data),
        "path": path,
        "format": fmt,
        "provider": provider,
    }


def _serialize_data(
    data: List[Dict[str, Any]], fmt: str
) -> Tuple[bytes, str]:
    """Return (bytes, content_type)."""
    if fmt == "json":
        buf = io.BytesIO()
        json.dump(data, buf, indent=2, default=str)
        return buf.getvalue(), "application/json"
    if fmt == "jsonl":
        lines = [json.dumps(r, default=str) + "\n" for r in data]
        return "".join(lines).encode("utf-8"), "application/x-ndjson"
    if fmt == "csv":
        import csv

        buf = io.StringIO()
        if data:
            w = csv.DictWriter(buf, fieldnames=data[0].keys())
            w.writeheader()
            w.writerows(data)
        return buf.getvalue().encode("utf-8"), "text/csv"
    if fmt == "parquet":
        import pandas as pd

        df = pd.DataFrame(data)
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        return buf.getvalue(), "application/octet-stream"
    raise ValueError(f"Unsupported format: {fmt}")


def _upload_s3(
    bucket: str,
    key: str,
    body: bytes,
    content_type: str,
    credentials: Optional[Dict[str, Any]],
) -> None:
    if not S3_AVAILABLE:
        raise ImportError(
            "boto3 is required for S3 load. "
            "Install with: pip install boto3 or pip install pycharter[etl]"
        )
    kwargs = {}
    if credentials and isinstance(credentials, dict):
        kwargs["aws_access_key_id"] = credentials.get("aws_access_key_id")
        kwargs["aws_secret_access_key"] = credentials.get("aws_secret_access_key")
        kwargs["region_name"] = credentials.get("region", "us-east-1")
    client = boto3.client("s3", **{k: v for k, v in kwargs.items() if v})
    client.put_object(
        Bucket=bucket, Key=key, Body=body, ContentType=content_type
    )


def _upload_gcs(
    bucket_name: str,
    path: str,
    body: bytes,
    content_type: str,
    credentials: Optional[Any],
) -> None:
    if not GCS_AVAILABLE:
        raise ImportError(
            "google-cloud-storage is required for GCS load. "
            "Install with: pip install google-cloud-storage"
        )
    if credentials:
        if isinstance(credentials, str):
            client = gcs_storage.Client.from_service_account_json(credentials)
        elif isinstance(credentials, dict):
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as tmp:
                json.dump(credentials, tmp)
                tmp_path = tmp.name
            try:
                client = gcs_storage.Client.from_service_account_json(tmp_path)
            finally:
                Path(tmp_path).unlink()
        else:
            client = gcs_storage.Client()
    else:
        client = gcs_storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(path)
    if isinstance(body, bytes) and content_type not in (
        "text/csv",
        "application/json",
        "application/x-ndjson",
    ):
        blob.upload_from_file(io.BytesIO(body), content_type=content_type)
    else:
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        blob.upload_from_string(text, content_type=content_type)


def _upload_azure(
    container_name: str,
    path: str,
    body: bytes,
    content_type: str,
    credentials: Optional[Dict[str, Any]],
) -> None:
    if not AZURE_AVAILABLE:
        raise ImportError(
            "azure-storage-blob is required for Azure load. "
            "Install with: pip install azure-storage-blob"
        )
    import os

    if credentials:
        conn_str = credentials.get("connection_string")
        account_name = credentials.get("account_name")
        account_key = credentials.get("account_key")
        if conn_str:
            client = BlobServiceClient.from_connection_string(conn_str)
        elif account_name and account_key:
            url = f"https://{account_name}.blob.core.windows.net"
            client = BlobServiceClient(url, credential=account_key)
        else:
            raise ValueError(
                "Azure credentials must include 'connection_string' or "
                "('account_name', 'account_key')"
            )
    else:
        conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
        if not conn_str:
            raise ValueError(
                "Azure load requires credentials or AZURE_STORAGE_CONNECTION_STRING"
            )
        client = BlobServiceClient.from_connection_string(conn_str)
    container = client.get_container_client(container_name)
    blob_client = container.get_blob_client(path)
    from azure.storage.blob import ContentSettings

    blob_client.upload_blob(
        body, overwrite=True, content_settings=ContentSettings(content_type=content_type)
    )
