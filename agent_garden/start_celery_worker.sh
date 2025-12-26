#!/bin/bash

# Start Celery Worker for Agent Garden
# Processes background tasks for autonomous agents

echo "🚀 Starting Celery Worker for Agent Garden..."
echo ""

# Check if Redis is accessible
echo "Checking Redis connection..."
python -c "import redis, os; from dotenv import load_dotenv; load_dotenv(); r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0')); r.ping(); print('✅ Redis connection successful!')" || {
    echo "❌ Cannot connect to Redis!"
    echo ""
    echo "Please ensure:"
    echo "  1. You have set REDIS_URL in .env"
    echo "  2. Upstash Redis is accessible"
    echo "  3. Or local Redis is running: redis-server"
    exit 1
}

echo ""
echo "Starting Celery worker..."
echo "Press Ctrl+C to stop"
echo ""

# Start Celery worker
# -A: Celery app module (now in src/scheduling/)
# worker: Run worker mode
# --loglevel=info: Show detailed logs
# -Q agent_tasks: Listen to agent_tasks queue
PYTHONPATH=. celery -A src.scheduling.celery_app worker --loglevel=info -Q agent_tasks

# Alternative with more options:
# celery -A celery_app worker \
#     --loglevel=info \
#     -Q agent_tasks \
#     --concurrency=4 \
#     --max-tasks-per-child=1000 \
#     --hostname=agent_worker@%h
