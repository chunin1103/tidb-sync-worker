"""
Celery Application - Distributed Task Queue
Handles autonomous agent scheduling with Redis backend
"""

import os
import ssl
import logging
from celery import Celery
from dotenv import load_dotenv
from src.scheduling.schedule_loader import load_schedules_from_db, initialize_default_schedules
from src.core.database import get_timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize default schedules in database
try:
    initialize_default_schedules()
    logger.info("Default schedules initialized")
except Exception as e:
    logger.error(f"Error initializing schedules: {e}")

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Add SSL parameters for Upstash Redis (rediss://)
if REDIS_URL.startswith('rediss://'):
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
else:
    broker_use_ssl = None
    redis_backend_use_ssl = None

# Initialize Celery application
celery_app = Celery(
    'agent_garden',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Auto-discover tasks from autonomous_agents package
# This will automatically find all @celery_app.task decorated functions
# in any module within the autonomous_agents directory
celery_app.autodiscover_tasks(['autonomous_agents'])

# Ensure tasks are imported and registered
import autonomous_agents  # noqa: F401

# Celery configuration
celery_app.conf.update(
    # SSL settings for Upstash Redis
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=redis_backend_use_ssl,

    # Timezone - loaded from database settings
    timezone=get_timezone(),
    enable_utc=True,

    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Beat schedule - loaded dynamically from database
    beat_schedule=load_schedules_from_db(),

    # Task routing
    task_routes={
        'autonomous_agents.*': {'queue': 'agent_tasks'}
    }
)

def reload_schedules():
    """
    Reload schedules from database
    Call this after updating schedules to refresh Celery Beat
    """
    from src.scheduling.schedule_loader import get_schedule_summary

    logger.info("Reloading schedules from database...")
    new_schedule = load_schedules_from_db()
    celery_app.conf.beat_schedule = new_schedule

    # Reload timezone as well
    new_timezone = get_timezone()
    celery_app.conf.timezone = new_timezone
    logger.info(f"Timezone set to: {new_timezone}")

    # Log summary
    summary = get_schedule_summary()
    logger.info(f"Loaded {summary['enabled']} enabled schedules")

    return new_schedule

if __name__ == '__main__':
    celery_app.start()
