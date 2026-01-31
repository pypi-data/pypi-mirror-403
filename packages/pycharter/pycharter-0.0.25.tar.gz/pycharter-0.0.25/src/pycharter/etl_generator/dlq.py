"""
Dead Letter Queue (DLQ) for ETL pipelines.

Captures and stores failed records that cannot be processed during ETL operations.
This allows for later analysis, debugging, and potential retry of failed records.
"""

import hashlib
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DLQReason(Enum):
    """Reasons for DLQ placement."""

    EXTRACTION_ERROR = "extraction_error"
    TRANSFORMATION_ERROR = "transformation_error"
    VALIDATION_ERROR = "validation_error"
    LOAD_ERROR = "load_error"
    CONNECTION_ERROR = "connection_error"
    SCHEMA_MISMATCH = "schema_mismatch"
    UNKNOWN = "unknown"


class DeadLetterRecord:
    """Represents a record in the dead letter queue."""

    def __init__(
        self,
        pipeline_name: str,
        record_data: Dict[str, Any],
        reason: DLQReason,
        error_message: str,
        error_type: str,
        stage: str,  # 'extract', 'transform', 'load'
        metadata: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
    ):
        """
        Initialize a dead letter record.

        Args:
            pipeline_name: Name of the pipeline that failed
            record_data: The actual record data that failed
            reason: Reason for DLQ placement
            error_message: Error message
            error_type: Type of error (exception class name)
            stage: ETL stage where failure occurred
            metadata: Additional metadata (batch_num, run_id, etc.)
            record_id: Optional record identifier (if None, will be generated)
        """
        self.pipeline_name = pipeline_name
        self.record_data = record_data
        self.reason = reason
        self.error_message = error_message
        self.error_type = error_type
        self.stage = stage
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.retry_count = 0
        self.status = "pending"  # pending, retrying, resolved, ignored

        # Generate ID if not provided
        self.id = record_id or self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for DLQ record."""
        # Create a hash from pipeline, reason, and record data
        data_str = json.dumps(self.record_data, sort_keys=True, default=str)
        hash_input = f"{self.pipeline_name}:{self.reason.value}:{self.stage}:{data_str}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "pipeline_name": self.pipeline_name,
            "record_data": self.record_data,
            "reason": self.reason.value,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stage": self.stage,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "status": self.status,
        }


class DeadLetterQueue:
    """
    Dead Letter Queue for failed ETL records.

    Supports multiple storage backends:
    - database: Store in PostgreSQL/other database
    - file: Store as JSON files
    - memory: In-memory only (for testing)
    """

    def __init__(
        self,
        db_session: Optional[Any] = None,
        storage_backend: str = "database",
        storage_path: Optional[str] = None,
        enabled: bool = True,
        schema_name: Optional[str] = None,
    ):
        """
        Initialize Dead Letter Queue.

        Args:
            db_session: Database session for database backend
            storage_backend: Backend type ("database", "file", "memory")
            storage_path: Path for file backend
            enabled: Whether DLQ is enabled
            schema_name: Database schema name for DLQ table (default: None, uses model's schema)
        """
        self.db_session = db_session
        self.storage_backend = storage_backend
        self.storage_path = Path(storage_path) if storage_path else None
        self.enabled = enabled
        self.schema_name = schema_name
        self._in_memory_queue: List[DeadLetterRecord] = []

        if storage_backend == "file" and not storage_path:
            raise ValueError("storage_path is required for file backend")

        if storage_backend == "file" and self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    async def add_record(
        self,
        pipeline_name: str,
        record_data: Dict[str, Any],
        reason: DLQReason,
        error_message: str,
        error_type: str,
        stage: str,
        metadata: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
    ) -> Optional[DeadLetterRecord]:
        """
        Add a failed record to the DLQ.

        Args:
            pipeline_name: Name of the pipeline
            record_data: The failed record data
            reason: Reason for failure
            error_message: Error message
            error_type: Error type
            stage: ETL stage
            metadata: Additional metadata
            record_id: Optional record identifier

        Returns:
            DeadLetterRecord if added, None if DLQ is disabled
        """
        if not self.enabled:
            return None

        try:
            dlq_record = DeadLetterRecord(
                pipeline_name=pipeline_name,
                record_data=record_data,
                reason=reason,
                error_message=error_message,
                error_type=error_type,
                stage=stage,
                metadata=metadata,
                record_id=record_id,
            )

            if self.storage_backend == "database" and self.db_session:
                await self._persist_to_database(dlq_record)
            elif self.storage_backend == "file" and self.storage_path:
                await self._persist_to_file(dlq_record)
            else:
                self._in_memory_queue.append(dlq_record)

            logger.debug(
                f"Added record to DLQ: {dlq_record.id} (pipeline={pipeline_name}, reason={reason.value}, stage={stage})"
            )
            return dlq_record
        except Exception as e:
            logger.error(f"Failed to add record to DLQ: {e}", exc_info=True)
            # Don't fail the pipeline if DLQ write fails
            return None

    async def add_batch(
        self,
        pipeline_name: str,
        batch: List[Dict[str, Any]],
        reason: DLQReason,
        error_message: str,
        error_type: str,
        stage: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DeadLetterRecord]:
        """
        Add multiple failed records to the DLQ.

        Args:
            pipeline_name: Name of the pipeline
            batch: List of failed records
            reason: Reason for failure
            error_message: Error message
            error_type: Error type
            stage: ETL stage
            metadata: Additional metadata

        Returns:
            List of DeadLetterRecord objects
        """
        if not self.enabled or not batch:
            return []

        records = []
        for i, record_data in enumerate(batch):
            record_metadata = {**(metadata or {}), "batch_index": i}
            dlq_record = await self.add_record(
                pipeline_name=pipeline_name,
                record_data=record_data,
                reason=reason,
                error_message=error_message,
                error_type=error_type,
                stage=stage,
                metadata=record_metadata,
            )
            if dlq_record:
                records.append(dlq_record)

        logger.info(
            f"Added {len(records)} records to DLQ for pipeline {pipeline_name} "
            f"(reason={reason.value}, stage={stage})"
        )
        return records

    async def _persist_to_database(self, record: DeadLetterRecord) -> None:
        """Persist record to database using configurable schema."""
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError
        from sqlalchemy.ext.asyncio import AsyncSession
        import json

        # Handle both async and sync sessions
        is_async = isinstance(self.db_session, AsyncSession)
        
        # Determine schema name - use provided schema or default to model's schema
        schema = self.schema_name if self.schema_name is not None else "pycharter"
        table_name = f'"{schema}"."dead_letter_queue"' if schema else '"dead_letter_queue"'

        try:
            if is_async:
                # Async session - use raw SQL for schema flexibility
                # Check if record exists
                check_sql = text(
                    f'SELECT id, retry_count FROM {table_name} WHERE id = :id'
                )
                result = await self.db_session.execute(check_sql, {"id": record.id})
                existing = result.fetchone()

                if existing:
                    # Update retry count and status
                    update_sql = text(
                        f"""
                        UPDATE {table_name}
                        SET retry_count = retry_count + 1,
                            status = :status,
                            error_message = :error_message,
                            updated_at = NOW()
                        WHERE id = :id
                        """
                    )
                    await self.db_session.execute(
                        update_sql,
                        {
                            "id": record.id,
                            "status": "pending",
                            "error_message": record.error_message,
                        }
                    )
                else:
                    # Create new record
                    insert_sql = text(
                        f"""
                        INSERT INTO {table_name} (
                            id, pipeline_name, record_data, reason, error_message,
                            error_type, stage, additional_metadata, retry_count,
                            status, timestamp, created_at, updated_at
                        ) VALUES (
                            :id, :pipeline_name, :record_data::jsonb, :reason,
                            :error_message, :error_type, :stage, :additional_metadata::jsonb,
                            :retry_count, :status, :timestamp, NOW(), NOW()
                        )
                        """
                    )
                    await self.db_session.execute(
                        insert_sql,
                        {
                            "id": record.id,
                            "pipeline_name": record.pipeline_name,
                            "record_data": json.dumps(record.record_data),
                            "reason": record.reason.value,
                            "error_message": record.error_message,
                            "error_type": record.error_type,
                            "stage": record.stage,
                            "additional_metadata": json.dumps(record.metadata) if record.metadata else None,
                            "retry_count": record.retry_count,
                            "status": record.status,
                            "timestamp": record.timestamp,
                        }
                    )

                await self.db_session.commit()
            else:
                # Sync session - use raw SQL for schema flexibility
                check_sql = text(
                    f'SELECT id, retry_count FROM {table_name} WHERE id = :id'
                )
                result = self.db_session.execute(check_sql, {"id": record.id})
                existing = result.fetchone()

                if existing:
                    # Update retry count and status
                    update_sql = text(
                        f"""
                        UPDATE {table_name}
                        SET retry_count = retry_count + 1,
                            status = :status,
                            error_message = :error_message,
                            updated_at = NOW()
                        WHERE id = :id
                        """
                    )
                    self.db_session.execute(
                        update_sql,
                        {
                            "id": record.id,
                            "status": "pending",
                            "error_message": record.error_message,
                        }
                    )
                else:
                    # Create new record
                    insert_sql = text(
                        f"""
                        INSERT INTO {table_name} (
                            id, pipeline_name, record_data, reason, error_message,
                            error_type, stage, additional_metadata, retry_count,
                            status, timestamp, created_at, updated_at
                        ) VALUES (
                            :id, :pipeline_name, :record_data::jsonb, :reason,
                            :error_message, :error_type, :stage, :additional_metadata::jsonb,
                            :retry_count, :status, :timestamp, NOW(), NOW()
                        )
                        """
                    )
                    self.db_session.execute(
                        insert_sql,
                        {
                            "id": record.id,
                            "pipeline_name": record.pipeline_name,
                            "record_data": json.dumps(record.record_data),
                            "reason": record.reason.value,
                            "error_message": record.error_message,
                            "error_type": record.error_type,
                            "stage": record.stage,
                            "additional_metadata": json.dumps(record.metadata) if record.metadata else None,
                            "retry_count": record.retry_count,
                            "status": record.status,
                            "timestamp": record.timestamp,
                        }
                    )

                self.db_session.commit()
        except ProgrammingError as e:
            # Check if it's a table doesn't exist error
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'undefinedtable' in error_str or 'relation' in error_str:
                # Rollback immediately to clear the failed transaction state
                try:
                    if is_async:
                        await self.db_session.rollback()
                    else:
                        self.db_session.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                logger.warning(
                    f"DLQ table does not exist - skipping DLQ persistence. "
                    f"Create the table to enable DLQ functionality."
                )
                return  # Don't raise - allow pipeline to continue
            # For other ProgrammingErrors, rollback and log
            try:
                if is_async:
                    await self.db_session.rollback()
                else:
                    self.db_session.rollback()
            except Exception:
                pass  # Ignore rollback errors
            logger.error(f"Failed to persist DLQ record to database: {e}", exc_info=True)
            # Don't raise - allow pipeline to continue even if DLQ fails
        except Exception as e:
            # For any other errors, rollback and log
            try:
                if is_async:
                    await self.db_session.rollback()
                else:
                    self.db_session.rollback()
            except Exception:
                pass  # Ignore rollback errors
            logger.error(f"Failed to persist DLQ record to database: {e}", exc_info=True)
            # Don't raise - allow pipeline to continue even if DLQ fails

    async def _persist_to_file(self, record: DeadLetterRecord) -> None:
        """Persist record to file."""
        try:
            # Create filename with timestamp and ID
            timestamp_str = record.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{record.pipeline_name}_{timestamp_str}_{record.id}.json"
            filepath = self.storage_path / filename

            with open(filepath, "w") as f:
                json.dump(record.to_dict(), f, indent=2, default=str)

            logger.debug(f"Persisted DLQ record to file: {filepath}")
        except Exception as e:
            logger.error(f"Failed to persist DLQ record to file: {e}", exc_info=True)
            raise

    def get_records(
        self,
        pipeline_name: Optional[str] = None,
        reason: Optional[DLQReason] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[DeadLetterRecord]:
        """
        Query DLQ records.

        Args:
            pipeline_name: Filter by pipeline name
            reason: Filter by reason
            stage: Filter by stage
            status: Filter by status
            limit: Maximum number of records to return

        Returns:
            List of DeadLetterRecord objects
        """
        if self.storage_backend == "database" and self.db_session:
            return self._query_from_database(pipeline_name, reason, stage, status, limit)
        elif self.storage_backend == "file" and self.storage_path:
            return self._query_from_file(pipeline_name, reason, stage, status, limit)
        else:
            return self._query_from_memory(pipeline_name, reason, stage, status, limit)

    def _query_from_database(
        self,
        pipeline_name: Optional[str],
        reason: Optional[DLQReason],
        stage: Optional[str],
        status: Optional[str],
        limit: int,
    ) -> List[DeadLetterRecord]:
        """Query records from database using configurable schema."""
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError
        from sqlalchemy.ext.asyncio import AsyncSession
        import json

        # Handle both async and sync sessions
        is_async = isinstance(self.db_session, AsyncSession)
        
        # Determine schema name
        schema = self.schema_name if self.schema_name is not None else "pycharter"
        table_name = f'"{schema}"."dead_letter_queue"' if schema else '"dead_letter_queue"'

        try:
            if is_async:
                # Async session - return empty list for now (would need async method)
                # This is a limitation - get_records should be async if using async session
                logger.debug("get_records() called with async session - returning empty list. Use async method instead.")
                return []
            else:
                # Sync session - use raw SQL for schema flexibility
                conditions = []
                params = {}
                
                if pipeline_name:
                    conditions.append("pipeline_name = :pipeline_name")
                    params["pipeline_name"] = pipeline_name
                if reason:
                    conditions.append("reason = :reason")
                    params["reason"] = reason.value
                if stage:
                    conditions.append("stage = :stage")
                    params["stage"] = stage
                if status:
                    conditions.append("status = :status")
                    params["status"] = status
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                params["limit"] = limit
                
                query_sql = text(
                    f"""
                    SELECT id, pipeline_name, record_data, reason, error_message,
                           error_type, stage, additional_metadata, retry_count,
                           status, timestamp
                    FROM {table_name}
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT :limit
                    """
                )
                
                result = self.db_session.execute(query_sql, params)
                rows = result.fetchall()
                
                records = []
                for row in rows:
                    records.append(
                        DeadLetterRecord(
                            pipeline_name=row.pipeline_name,
                            record_data=row.record_data if isinstance(row.record_data, dict) else json.loads(row.record_data),
                            reason=DLQReason(row.reason),
                            error_message=row.error_message,
                            error_type=row.error_type,
                            stage=row.stage,
                            metadata=row.additional_metadata if isinstance(row.additional_metadata, dict) else (json.loads(row.additional_metadata) if row.additional_metadata else {}),
                            record_id=row.id,
                        )
                    )
                    records[-1].retry_count = row.retry_count
                    records[-1].status = row.status
                    records[-1].timestamp = row.timestamp
                
                return records
        except ProgrammingError as e:
            # If table doesn't exist, return empty list
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'undefinedtable' in error_str or 'relation' in error_str:
                logger.debug(f"DLQ table does not exist - returning empty list")
            else:
                logger.warning(f"Failed to query DLQ records: {e}")
            return []
        except Exception as e:
            logger.warning(f"Failed to query DLQ records: {e}")
            return []

    def _query_from_file(
        self,
        pipeline_name: Optional[str],
        reason: Optional[DLQReason],
        stage: Optional[str],
        status: Optional[str],
        limit: int,
    ) -> List[DeadLetterRecord]:
        """Query records from file storage."""
        records = []
        for filepath in sorted(self.storage_path.glob("*.json"), reverse=True):
            if len(records) >= limit:
                break

            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                # Apply filters
                if pipeline_name and data.get("pipeline_name") != pipeline_name:
                    continue
                if reason and data.get("reason") != reason.value:
                    continue
                if stage and data.get("stage") != stage:
                    continue
                if status and data.get("status") != status:
                    continue

                record = DeadLetterRecord(
                    pipeline_name=data["pipeline_name"],
                    record_data=data["record_data"],
                    reason=DLQReason(data["reason"]),
                    error_message=data["error_message"],
                    error_type=data["error_type"],
                    stage=data["stage"],
                    metadata=data.get("metadata"),
                    record_id=data["id"],
                )
                record.timestamp = datetime.fromisoformat(data["timestamp"])
                record.retry_count = data.get("retry_count", 0)
                record.status = data.get("status", "pending")
                records.append(record)
            except Exception as e:
                logger.warning(f"Failed to read DLQ file {filepath}: {e}")

        return records

    def _query_from_memory(
        self,
        pipeline_name: Optional[str],
        reason: Optional[DLQReason],
        stage: Optional[str],
        status: Optional[str],
        limit: int,
    ) -> List[DeadLetterRecord]:
        """Query records from memory."""
        records = self._in_memory_queue

        # Apply filters
        if pipeline_name:
            records = [r for r in records if r.pipeline_name == pipeline_name]
        if reason:
            records = [r for r in records if r.reason == reason]
        if stage:
            records = [r for r in records if r.stage == stage]
        if status:
            records = [r for r in records if r.status == status]

        return records[:limit]

    async def retry_record(self, record_id: str) -> bool:
        """
        Mark a record for retry.

        Args:
            record_id: ID of the record to retry

        Returns:
            True if successful, False otherwise
        """
        if self.storage_backend == "database" and self.db_session:
            from sqlalchemy import text
            from sqlalchemy.exc import ProgrammingError
            from sqlalchemy.ext.asyncio import AsyncSession

            # Determine schema name
            schema = self.schema_name if self.schema_name is not None else "pycharter"
            table_name = f'"{schema}"."dead_letter_queue"' if schema else '"dead_letter_queue"'
            
            is_async = isinstance(self.db_session, AsyncSession)

            try:
                update_sql = text(
                    f"""
                    UPDATE {table_name}
                    SET status = 'retrying',
                        retry_count = retry_count + 1,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                )
                
                if is_async:
                    result = await self.db_session.execute(update_sql, {"id": record_id})
                    await self.db_session.commit()
                    return result.rowcount > 0
                else:
                    result = self.db_session.execute(update_sql, {"id": record_id})
                    self.db_session.commit()
                    return result.rowcount > 0
            except ProgrammingError as e:
                error_str = str(e).lower()
                if 'does not exist' in error_str or 'undefinedtable' in error_str or 'relation' in error_str:
                    logger.debug(f"DLQ table does not exist - cannot retry record")
                else:
                    logger.warning(f"Failed to retry DLQ record: {e}")
                return False
            except Exception as e:
                logger.warning(f"Failed to retry DLQ record: {e}")
                return False
        elif self.storage_backend == "memory":
            for record in self._in_memory_queue:
                if record.id == record_id:
                    record.status = "retrying"
                    record.retry_count += 1
                    return True

        return False

    def get_statistics(
        self,
        pipeline_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get DLQ statistics.

        Args:
            pipeline_name: Optional pipeline name filter

        Returns:
            Dictionary with statistics
        """
        if self.storage_backend == "database" and self.db_session:
            from sqlalchemy import text, func
            from sqlalchemy.exc import ProgrammingError

            # Determine schema name
            schema = self.schema_name if self.schema_name is not None else "pycharter"
            table_name = f'"{schema}"."dead_letter_queue"' if schema else '"dead_letter_queue"'

            try:
                # Build base query
                where_clause = ""
                params = {}
                if pipeline_name:
                    where_clause = "WHERE pipeline_name = :pipeline_name"
                    params["pipeline_name"] = pipeline_name
                
                # Total count
                count_sql = text(f'SELECT COUNT(*) FROM {table_name} {where_clause}')
                result = self.db_session.execute(count_sql, params)
                total = result.scalar()
                
                # By reason
                reason_sql = text(
                    f"""
                    SELECT reason, COUNT(*) as count
                    FROM {table_name}
                    {where_clause}
                    GROUP BY reason
                    """
                )
                result = self.db_session.execute(reason_sql, params)
                by_reason = {row[0]: row[1] for row in result.fetchall()}
                
                # By stage
                stage_sql = text(
                    f"""
                    SELECT stage, COUNT(*) as count
                    FROM {table_name}
                    {where_clause}
                    GROUP BY stage
                    """
                )
                result = self.db_session.execute(stage_sql, params)
                by_stage = {row[0]: row[1] for row in result.fetchall()}
                
                # By status
                status_sql = text(
                    f"""
                    SELECT status, COUNT(*) as count
                    FROM {table_name}
                    {where_clause}
                    GROUP BY status
                    """
                )
                result = self.db_session.execute(status_sql, params)
                by_status = {row[0]: row[1] for row in result.fetchall()}

                return {
                    "total": total,
                    "by_reason": by_reason,
                    "by_stage": by_stage,
                    "by_status": by_status,
                }
            except ProgrammingError as e:
                error_str = str(e).lower()
                if 'does not exist' in error_str or 'undefinedtable' in error_str or 'relation' in error_str:
                    logger.debug(f"DLQ table does not exist - returning empty statistics")
                else:
                    logger.warning(f"Failed to get DLQ statistics: {e}")
                return {
                    "total": 0,
                    "by_reason": {},
                    "by_stage": {},
                    "by_status": {},
                }
            except Exception as e:
                logger.warning(f"Failed to get DLQ statistics: {e}")
                return {
                    "total": 0,
                    "by_reason": {},
                    "by_stage": {},
                    "by_status": {},
                }
        else:
            # Memory or file backend - simple count
            records = self._in_memory_queue if self.storage_backend == "memory" else []
            if pipeline_name:
                records = [r for r in records if r.pipeline_name == pipeline_name]

            return {
                "total": len(records),
                "by_reason": {},
                "by_stage": {},
                "by_status": {},
            }

