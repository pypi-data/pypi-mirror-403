"""
Spark-based validation backend for large datasets.

Supports:
- Local mode: Single machine, no cluster needed (default)
- Remote mode: Submit to external Spark service
- Cluster mode: Connect to Spark cluster (future)
"""

import json
import os
import pickle
from typing import Any, Dict, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    StringType,
    StructField,
    StructType,
)

from pycharter import build_contract_from_store, get_model_from_contract
from pycharter.metadata_store import MetadataStoreClient
from pycharter.runtime_validator.validator_core import ValidationResult, validate

from pycharter.worker.backends.base import ValidationBackend


class SparkValidationBackend(ValidationBackend):
    """
    Spark-compatible validation backend.

    Works in three modes:
    1. Local mode (default) - Single machine, no cluster needed
    2. Remote mode - Submit to external Spark service
    3. Cluster mode - Connect to Spark cluster (future)
    """

    def __init__(
        self,
        mode: str = "local",  # "local", "remote", "cluster"
        master: Optional[str] = None,  # "local[*]", "spark://host:port", "yarn", etc.
        app_name: str = "pycharter-validation",
    ):
        """
        Initialize Spark validation backend.

        Args:
            mode: Spark mode ("local", "remote", "cluster")
            master: Spark master URL (auto-detected if not provided)
            app_name: Spark application name
        """
        self.mode = mode
        self.master = master or self._get_default_master()
        self.app_name = app_name
        self.spark: Optional[SparkSession] = None

    def _get_default_master(self) -> str:
        """Get default Spark master based on mode."""
        if self.mode == "local":
            return "local[*]"  # Use all CPU cores locally
        elif self.mode == "remote":
            # For remote Spark service (e.g., Spark on Kubernetes)
            return os.getenv("SPARK_MASTER", "spark://localhost:7077")
        else:  # cluster
            return os.getenv("SPARK_MASTER", "yarn")

    def get_spark_session(self) -> SparkSession:
        """Get or create Spark session."""
        if self.spark is None:
            self.spark = (
                SparkSession.builder.appName(self.app_name)
                .master(self.master)
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                .getOrCreate()
            )
        return self.spark

    def validate(
        self,
        schema_id: str,
        data_source: str,  # S3 path, file path, database table, etc.
        store: MetadataStoreClient,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate data using Spark.

        This method:
        1. Loads contract from metadata store
        2. Reads data from source
        3. Validates using PyCharter validation logic
        4. Returns aggregated results

        Args:
            schema_id: Schema identifier
            data_source: Data source path or identifier
            store: Metadata store client
            options: Validation options

        Returns:
            Dictionary with validation results
        """
        spark = self.get_spark_session()
        options = options or {}

        # Load contract from metadata store
        contract = build_contract_from_store(store, schema_title=schema_id)
        model = get_model_from_contract(contract)

        # Serialize model for Spark UDF
        # Note: Pydantic models need to be pickled and broadcast
        model_pickle = pickle.dumps(model)
        model_broadcast = spark.sparkContext.broadcast(model_pickle)

        # Read data
        df = self._read_data(spark, data_source)

        # Define validation UDF
        @udf(
            returnType=StructType(
                [
                    StructField("is_valid", BooleanType()),
                    StructField("errors", ArrayType(StringType())),
                    StructField("data_json", StringType()),
                ]
            )
        )
        def validate_record(record_json: str) -> Dict[str, Any]:
            """Validate a single record using PyCharter."""
            import pickle

            # Unpickle model
            model = pickle.loads(model_broadcast.value)

            # Parse record
            record = json.loads(record_json)

            # Validate using PyCharter
            result = validate(model, record, strict=False)

            # Return result
            return {
                "is_valid": result.is_valid,
                "errors": result.errors or [],
                "data_json": json.dumps(result.data.model_dump())
                if result.data
                else None,
            }

        # Convert DataFrame to JSON strings for validation
        # Assuming data is already in a format we can work with
        # If data is in columns, we need to convert to JSON
        if "value" in df.columns:
            # Data is already in JSON format
            validation_df = df.withColumn(
                "validation_result", validate_record(col("value"))
            )
        else:
            # Convert row to JSON
            from pyspark.sql.functions import to_json, struct

            json_cols = [col(c) for c in df.columns]
            df_with_json = df.withColumn("value", to_json(struct(*json_cols)))
            validation_df = df_with_json.withColumn(
                "validation_result", validate_record(col("value"))
            )

        # Aggregate results
        results = validation_df.select(
            col("validation_result.is_valid").alias("is_valid"),
            col("validation_result.errors").alias("errors"),
        ).collect()

        # Calculate metrics
        total_count = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total_count - valid_count

        # Collect violations
        violations = []
        for result in results:
            if not result.is_valid and result.errors:
                violations.extend(result.errors)

        # Calculate quality score
        quality_score = valid_count / total_count if total_count > 0 else 0.0

        return {
            "total_count": total_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "violations": violations,
            "quality_score": quality_score,
            "data_source": data_source,
        }

    def _read_data(self, spark: SparkSession, data_source: str) -> DataFrame:
        """Read data from various sources."""
        if data_source.startswith("s3://") or data_source.startswith("s3a://"):
            # Read from S3
            return spark.read.parquet(data_source)
        elif data_source.startswith("hdfs://"):
            # Read from HDFS
            return spark.read.parquet(data_source)
        elif data_source.endswith(".parquet"):
            # Local parquet file
            return spark.read.parquet(data_source)
        elif data_source.endswith(".json"):
            # JSON file
            return spark.read.json(data_source)
        elif data_source.endswith(".csv"):
            # CSV file
            return spark.read.csv(data_source, header=True, inferSchema=True)
        else:
            # Assume it's a database table or try to infer format
            # For now, try JSON first
            try:
                return spark.read.json(data_source)
            except Exception:
                # Fallback to parquet
                return spark.read.parquet(data_source)

    def close(self):
        """Close Spark session."""
        if self.spark:
            self.spark.stop()
            self.spark = None

