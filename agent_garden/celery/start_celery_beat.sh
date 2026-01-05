    #!/bin/bash

# Start Celery Beat Scheduler for Agent Garden
# Triggers scheduled tasks (morning reports, health checks, etc.)

echo "📅 Starting Celery Beat Scheduler for Agent Garden..."
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
echo "📊 Loading schedules from database..."
PYTHONPATH=. python -c "
from src.scheduling.schedule_loader import get_schedule_summary
summary = get_schedule_summary()
print(f\"  • Total schedules: {summary['total_schedules']}\")
print(f\"  • Enabled: {summary['enabled']}\")
for s in summary['schedules']:
    if s['enabled']:
        print(f\"  • {s['display_name']}: {s['schedule']}\")
"
echo ""
echo "Starting Celery Beat scheduler with DatabaseScheduler..."
echo "✨ Schedules will auto-reload every 30 seconds"
echo "Press Ctrl+C to stop"
echo ""

# Start Celery Beat with DatabaseScheduler
# -A: Celery app module (now in src/scheduling/)
# beat: Run scheduler mode
# -S: Scheduler class (custom DatabaseScheduler)
# --max-interval: Maximum time between schedule checks (30 seconds)
# --loglevel=info: Show detailed logs
PYTHONPATH=. celery -A src.scheduling.celery_app beat \
    -S src.scheduling.custom_scheduler:DatabaseScheduler \
    --max-interval 30 \
    --loglevel=info

# Alternative with scheduler storage:
# celery -A celery_app beat \
#     --loglevel=info \
#     -s celerybeat-schedule \
#     --pidfile=celerybeat.pid
