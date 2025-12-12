# Queue Architecture Analysis

## Current Setup: Redis + Celery

### What We Have
- **Redis**: Message broker (port 6379)
- **Celery**: Distributed task queue
- **FastAPI**: Async web framework

### Current Flow
```
User → FastAPI → Celery (via Redis) → Worker → Agent → Response
```

## Kafka vs Redis+Celery Analysis

| Feature | Redis + Celery | Kafka |
|---------|---------------|-------|
| **Setup Complexity** | Low | High |
| **Message Persistence** | Limited | Excellent |
| **Throughput** | ~10K msg/s | ~100K msg/s |
| **Memory Usage** | Low | Medium-High |
| **Use Case Fit** | Task queues | Event streaming |
| **Multi-consumer** | Via fanout | Native |
| **Learning Curve** | Easy | Steep |

### Verdict: Keep Redis + Celery

**For this use case, Redis + Celery is the right choice because:**

1. **Scale**: We're handling individual AI requests, not millions of events
2. **Latency**: Celery provides better latency for request-response patterns
3. **Simplicity**: Already configured and working
4. **Cost**: Kafka needs Zookeeper, more resources

---

## Improvements to Current Architecture

### 1. Enable Async Endpoints (Already Done)
```python
async def execute_task(...):  # FastAPI is already async
```

### 2. Connection Pooling for Redis
```python
# src/utils/database.py - Add connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,
    decode_responses=True
)
```

### 3. Celery Configuration Optimization
```python
# Already in celery_app.py
celery_app.conf.update(
    worker_prefetch_multiplier=1,  # Better for long tasks
    worker_concurrency=4,           # Parallel workers
    task_acks_late=True,           # Reliability
)
```

### 4. FastAPI Response Streaming (For Long Tasks)
```python
from fastapi.responses import StreamingResponse

@router.get("/v1/agent/stream/{task_id}")
async def stream_result(task_id: str):
    async def generate():
        while True:
            status = get_task_status(task_id)
            yield f"data: {json.dumps(status)}\n\n"
            if status["done"]:
                break
            await asyncio.sleep(0.5)
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## When to Consider Kafka

Consider Kafka only if:
- You need to process >10,000 requests/second
- You need event replay capabilities
- Multiple services consume the same events
- You need exactly-once delivery semantics

**For PeerAgent's current scope, Redis + Celery is optimal.**

---

## Quick Wins for Faster Response

1. **Reduce LLM latency**: Use faster models (gpt-3.5-turbo vs gpt-4)
2. **Caching**: Cache identical requests
3. **Streaming**: Stream LLM responses to UI
4. **Connection reuse**: Keep LLM connections alive
