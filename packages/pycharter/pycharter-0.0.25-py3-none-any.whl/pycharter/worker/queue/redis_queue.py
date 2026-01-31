"""
Redis-based message queue for async validation jobs.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class ValidationJobQueue:
    """Message queue for async validation jobs using Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis job queue.

        Args:
            redis_url: Redis connection URL
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required. Install with: pip install redis>=5.0.0"
            )
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required")
        self.redis_client = await redis.from_url(self.redis_url)

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def enqueue_job(self, job: Dict[str, Any]) -> str:
        """
        Enqueue a validation job.

        Args:
            job: Job dictionary with schema_id, data_source, options

        Returns:
            Job ID
        """
        if not self.redis_client:
            await self.connect()

        job_id = str(uuid.uuid4())
        job["job_id"] = job_id
        job["status"] = "queued"
        job["created_at"] = datetime.utcnow().isoformat()

        # Push to queue
        await self.redis_client.lpush("validation-jobs", json.dumps(job))

        # Store job metadata
        await self.redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps({"status": "queued", "created_at": job["created_at"]}),
        )

        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary or None if not found
        """
        if not self.redis_client:
            await self.connect()

        status_json = await self.redis_client.get(f"job:{job_id}")
        if status_json:
            return json.loads(status_json)
        return None

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status ("queued", "processing", "completed", "failed")
            result: Optional result dictionary
            error: Optional error message
        """
        if not self.redis_client:
            await self.connect()

        status_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if result:
            status_data["result"] = result
        if error:
            status_data["error"] = error

        await self.redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps(status_data),
        )

    async def dequeue_job(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """
        Dequeue a job from the queue (blocking).

        Args:
            timeout: Blocking timeout in seconds

        Returns:
            Job dictionary or None if timeout
        """
        if not self.redis_client:
            await self.connect()

        result = await self.redis_client.brpop("validation-jobs", timeout=timeout)
        if result:
            return json.loads(result[1])
        return None

