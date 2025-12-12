# Celery Application Configuration
from celery import Celery
from src.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "peeragent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Task routing (optional)
    task_routes={
        "src.worker.tasks.execute_agent_task": {"queue": "agents"},
        "src.worker.tasks.execute_business_task": {"queue": "business"},
    },
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=360,  # 6 minutes hard limit
)

# Optional: Configure retry settings
celery_app.conf.task_default_retry_delay = 30
celery_app.conf.task_max_retries = 3
