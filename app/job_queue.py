"""Redis-based job queue for async scrape triggers."""
import json
import os
from typing import Optional

import redis
from redis.exceptions import RedisError

from app.config import REDIS_URL

SCRAPE_QUEUE_KEY = "job_scraper:scrape_queue"
SCRAPE_STATUS_KEY = "job_scraper:scrape_status"


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client if Redis is available."""
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except RedisError:
        return None


def enqueue_scrape(sources: list[str] | None = None) -> bool:
    """Add a scrape job to the queue.
    
    Args:
        sources: Optional list of sources to scrape. None = all sources.
        
    Returns:
        True if enqueued successfully, False if Redis unavailable.
    """
    client = get_redis_client()
    if not client:
        return False
    
    job_data = {
        "sources": sources,
    }
    try:
        client.lpush(SCRAPE_QUEUE_KEY, json.dumps(job_data))
        # Track status
        client.hset(SCRAPE_STATUS_KEY, "last_triggered", "queued")
        return True
    except RedisError:
        return False


def dequeue_scrape() -> Optional[dict]:
    """Pop a scrape job from the queue (blocking with timeout).
    
    Returns:
        Job dict with 'sources' key, or None if queue empty/Redis unavailable.
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        result = client.brpop(SCRAPE_QUEUE_KEY, timeout=5)
        if result:
            _, job_json = result
            return json.loads(job_json)
        return None
    except RedisError:
        return None


def update_scrape_status(status: str, **extra) -> bool:
    """Update scrape status in Redis."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        data = {"status": status, **extra}
        client.hset(SCRAPE_STATUS_KEY, mapping=data)
        return True
    except RedisError:
        return False


def get_scrape_status() -> dict:
    """Get current scrape status."""
    client = get_redis_client()
    if not client:
        return {"status": "redis_unavailable"}
    
    try:
        return client.hgetall(SCRAPE_STATUS_KEY) or {"status": "unknown"}
    except RedisError:
        return {"status": "redis_error"}