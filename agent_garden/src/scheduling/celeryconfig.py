"""
Celery Configuration
Advanced settings for task queue and scheduling
"""

from celery.schedules import crontab

# Broker and Backend
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'America/Los_Angeles'  # Adjust to your timezone
enable_utc = True

# Task execution
task_acks_late = True  # Acknowledge tasks after completion, not before
task_reject_on_worker_lost = True  # Reject tasks if worker crashes
task_time_limit = 3600  # Maximum execution time: 1 hour
task_soft_time_limit = 3000  # Soft limit: 50 minutes
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks

# Result backend
result_expires = 3600  # Results expire after 1 hour

# Beat Schedule Configuration
# NOTE: Schedules are now managed dynamically via the database.
# See database.py (ScheduleConfig model) and schedule_loader.py (load_schedules_from_db)
# This allows runtime updates via the web UI without requiring Celery Beat restart.
#
# The hardcoded schedules below have been removed to prevent conflicts.
# All schedules are loaded from the database in celery_app.py
beat_schedule = {}  # Empty - loaded dynamically from database

# Task Routing
task_routes = {
    'autonomous_agents.*': {'queue': 'agent_tasks'}
}

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
